"""The publication/v2 gate — an actor's events/ log against the contract.

Validates the record ENVELOPE (the part contracted ecosystem-wide) and the v2 additions: every
publication with records owes a payload `shape`, and `schema.yaml` is a reserved filename, not a
record. It does NOT validate a record against its own payload schema — that schema is authored by
the producer in its own terms, and reading it is the consuming actor's job, not a gate's.

The atomicity rule (a record lands in the same commit as the change it describes) is a property of
history, not of a file, so it is not checkable here. banking-knowledge's check_publications.py
walks git for it; that check belongs where the log lives.
"""
from pathlib import Path

import yaml

from .report import Report
from .schemas import load

RESERVED = "schema.yaml"


def lint_log(repo: Path, schema: dict | None = None, card: dict | None = None) -> Report:
    """Validate every record under <repo>/events/. `card` narrows the check when supplied."""
    schema = schema or load("publication")
    rep = Report()
    events = repo / "events"
    if not events.is_dir():
        rep.notes.append(f"{repo}: no events/ log — an actor may publish nothing (ADR-ECO-0014 §3)")
        return rep

    declared = {p["id"]: p for p in (card.get("publications") or [])} if card else {}
    required = schema["record"]["required"]
    allowed = set(required) | set(schema["record"]["optional"])
    seen_ids: set[str] = set()

    for pub_dir in sorted(d for d in events.iterdir() if d.is_dir()):
        pub_id = pub_dir.name
        seen_ids.add(pub_id)
        records = sorted(p for p in pub_dir.glob("*.yaml") if p.name != RESERVED)
        has_shape = (pub_dir / RESERVED).exists()

        if declared and pub_id not in declared:
            rep.errors.append(f"{pub_dir}: a log for '{pub_id}', which the card does not declare")
        if records and not has_shape:
            rep.errors.append(
                f"{pub_dir}: {len(records)} record(s) and no {RESERVED} — every emitted publication "
                f"owes a payload shape (publication/v2 `payload`, binds at first record)"
            )
        if not records and has_shape:
            rep.notes.append(f"{pub_dir}: a shape with no records yet — the obligation ran ahead of the log")

        for rec_path in records:
            where = f"{rec_path}"
            try:
                rec = yaml.safe_load(rec_path.read_text())
            except yaml.YAMLError as e:
                rep.errors.append(f"{where}: does not parse: {e}")
                continue
            if not isinstance(rec, dict):
                rep.errors.append(f"{where}: not a mapping")
                continue

            for field in required:
                if rec.get(field) in (None, ""):
                    rep.errors.append(f"{where}: missing required field '{field}'")
            for key in sorted(set(rec) - allowed):
                rep.notes.append(f"{where}: '{key}' is not named by the record contract")

            if rec.get("publication") and rec["publication"] != pub_id:
                rep.errors.append(
                    f"{where}: declares publication '{rec['publication']}' but sits under '{pub_id}/'"
                )

            # THE PINNING RULE — the gate cannot judge whether a change breaks, only force the
            # judgement to be made. A card declaring breaking_flag has said its consumers pin it.
            flag = (declared.get(pub_id) or {}).get("breaking_flag")
            if flag and "breaking" not in rec:
                rep.errors.append(
                    f"{where}: no 'breaking' — the card declares a breaking_flag for '{pub_id}', "
                    f"so every record must declare it, true or false (the pinning rule)"
                )

            # A live record's ref cannot be the announcing commit's own sha: the record ships in
            # that commit, and a commit cannot contain its own hash. Only a backfill may carry one.
            ref = str(rec.get("ref", ""))
            if "backfilled" not in rec and len(ref) >= 7 and all(c in "0123456789abcdef" for c in ref):
                rep.notes.append(
                    f"{where}: ref '{ref}' looks like a sha on a record that declares no 'backfilled' "
                    f"— only a backfill may carry one (the ref rule)"
                )

    for pub_id, pub in declared.items():
        if pub_id not in seen_ids and pub.get("shape") not in (None, "none"):
            rep.errors.append(f"{repo}: '{pub_id}' declares a shape but has no events/{pub_id}/ log")

    if not rep.errors:
        rep.oks.append(f"{events} conforms to {schema['contract']}")
    return rep
