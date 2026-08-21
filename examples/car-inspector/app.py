"""car-inspector — a minimal HTTP intake for visual damage reports on returned second-hand cars.

Stdlib only, on purpose: this is a worked example of the actor.yaml + Dockerfile convention
(ADR-PA-0019, ADR-PA-0021), not a production service. Reports live in memory and are gone on
restart — swap `_INSPECTIONS` for a real store when this stops being a scaffold.
"""
import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_INSPECTIONS: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict | list) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        if self.path == "/inspections":
            return self._send(200, list(_INSPECTIONS.values()))
        if self.path.startswith("/inspections/"):
            inspection_id = self.path.removeprefix("/inspections/")
            inspection = _INSPECTIONS.get(inspection_id)
            if inspection is None:
                return self._send(404, {"error": f"no inspection '{inspection_id}'"})
            return self._send(200, inspection)
        return self._send(404, {"error": f"no route {self.path}"})

    def do_POST(self):
        if self.path != "/inspections":
            return self._send(404, {"error": f"no route {self.path}"})

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "body is not valid JSON"})

        vehicle_id = body.get("vehicle_id")
        damages = body.get("damages")
        if not vehicle_id or not isinstance(damages, list):
            return self._send(
                400,
                {"error": "expected {'vehicle_id': str, 'damages': [{'panel', 'severity', 'note'}, ...]}"},
            )

        inspection_id = str(uuid.uuid4())
        inspection = {"id": inspection_id, "vehicle_id": vehicle_id, "damages": damages}
        _INSPECTIONS[inspection_id] = inspection
        return self._send(201, inspection)

    def log_message(self, format, *args):  # noqa: A002 — silence per-request stderr noise
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
