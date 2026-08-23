"""The papeete-actor-manifest/v0 gate — one manifest against the contract.

WHAT THIS IS NOT. Not a card, and shares no code with `cards.py` on purpose — this is a separate,
standalone lineage that says only who an actor is (ADR-PA-0019). No offers, no publications, no
releases, no dependencies, no subscriptions belong here.

A MISMATCHED MANIFEST IS UNMIGRATED, NOT NON-CONFORMANT — the same discipline `cards.py` already
applies to `card:`: a manifest declaring some other `manifest:` value (or none at all) is read,
warned, and not checked further, because adoption and migration are each pair's own act.
"""
from dataclasses import dataclass
from pathlib import Path

import yaml

from .report import Report
from .schemas import load

CONTRACT = "papeete-actor-manifest/v0"


@dataclass(frozen=True)
class Manifest:
    name: str
    description: str


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


def describe(path: Path | str) -> Manifest:
    """Typed identity fetch. Raises if the manifest is missing, malformed, or UNMIGRATED —
    callers are expected to have already run lint() and confirmed no errors, the same
    precondition load()-style call sites elsewhere in this ecosystem already rely on."""
    path = Path(path)
    manifest = yaml.safe_load(path.read_text())
    if not isinstance(manifest, dict) or manifest.get("manifest") != CONTRACT:
        raise ValueError(f"{path}: not a conformant {CONTRACT} manifest — run lint() first")
    return Manifest(name=str(manifest["name"]), description=str(manifest.get("description") or ""))
