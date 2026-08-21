# car-inspector — a worked example actor

A minimal actor, built from this repo's own `actor.yaml` + `Dockerfile` convention
([ADR-PA-0019](../../adr/ADR-PA-0019-a-minimal-standalone-actor-manifest.md)), so `papeete-actor
build` has something real to build. It stands in for a car dealership's inspector: someone
records the visual damage found on a returned second-hand car before it goes back up for resale.

It is intentionally a scaffold, not a finished service — in-memory storage, no auth, stdlib
only. The point is to have a folder you can build, run, poke at, and grow.

## What's here

| File | Role |
|---|---|
| `actor.yaml` | identity — `papeete-actor-manifest/v0`: name + description, nothing else |
| `Dockerfile` | the build recipe — `python:3.12-slim`, no dependencies |
| `app.py` | the actor itself — a tiny stdlib HTTP server |

## Try it

```bash
papeete-actor build examples/car-inspector
docker run --rm -p 8080:8080 car-inspector:<tag-it-printed>
```

```bash
curl http://localhost:8080/health

curl -X POST http://localhost:8080/inspections \
  -H 'Content-Type: application/json' \
  -d '{
    "vehicle_id": "VF3ABC123",
    "damages": [
      {"panel": "front-bumper", "severity": "minor", "note": "scuff, ~4cm, no paint break"},
      {"panel": "rear-left-door", "severity": "moderate", "note": "dent, paint chipped"}
    ]
  }'

curl http://localhost:8080/inspections
```

`papeete-actor build` computes the image tag from git — the folder needs at least one commit
touching it before it can be built (`ADR-PA-0022`).

## Where this could go

This is deliberately the smallest thing that runs, so it's a starting point, not a spec:

- take a photo upload instead of (or alongside) hand-typed `damages[]`
- score severity from the image instead of trusting the caller
- persist inspections somewhere durable instead of an in-memory dict
- add a second actor (e.g. a `resale-pricer`) that subscribes to what this one reports
