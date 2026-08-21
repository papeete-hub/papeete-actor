"""The papeete-actor-manifest/v0 gate — one manifest against the contract.

WHAT THIS IS NOT. Not a card, and shares no code with `cards.py` on purpose — this is a separate,
standalone lineage that says only who an actor is (ADR-PA-0019). No offers, no publications, no
releases, no dependencies, no subscriptions belong here.

A MISMATCHED MANIFEST IS UNMIGRATED, NOT NON-CONFORMANT — the same discipline `cards.py` already
applies to `card:`: a manifest declaring some other `manifest:` value (or none at all) is read,
warned, and not checked further, because adoption and migration are each pair's own act.
"""
from pathlib import Path

import yaml

from .report import Report
from .schemas import load

CONTRACT = "papeete-actor-manifest/v0"


def lint(path: Path | str, schema: dict | None = None) -> Report:
    """Validate one manifest against papeete-actor-manifest/v0."""
    path = Path(path)
    schema = schema or load("manifest")
    rep = Report()

    try:
        manifest = yaml.safe_load(path.read_text())
    except (yaml.YAMLError, OSError) as e:
        rep.errors.append(f"{path}: does not parse or cannot be read: {e}")
        return rep
    if not isinstance(manifest, dict):
        rep.errors.append(f"{path}: not a mapping")
        return rep

    if manifest.get("manifest") != CONTRACT:
        rep.warns.append(
            f"{path}: declares '{manifest.get('manifest')}' — UNMIGRATED, not checked against "
            f"{CONTRACT}"
        )
        return rep

    for key in schema["required"]:
        if key not in manifest:
            rep.errors.append(f"{path}: missing required key '{key}'")

    if not rep.errors:
        rep.oks.append(f"{path} conforms to {CONTRACT}")
    return rep
