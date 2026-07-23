"""Loading the contracts.

They are NOT authored in this repo. ECO.GOV owns them (ADR-ECO-0005); `contracts.pin` names the
ref, and `scripts/fetch_contracts.py` resolves it into this directory before a build. Nothing here
is committed — a copy in git is a copy that drifts, and deleting copies is why papeete-actor exists.

The path is the same in a source checkout and in an installed wheel, so there is no fallback and
no second location to reason about.
"""
from pathlib import Path

import yaml

_NAMES = {
    "papeete-actor-card": "papeete-actor-card.schema.yaml",
    "message": "message.schema.yaml",
    "publication": "publication.schema.yaml",
}

_DIR = Path(__file__).resolve().parent / "schemas"


def contracts_dir() -> Path:
    return _DIR


def load(kind: str) -> dict:
    """Return one contract by kind: 'papeete-actor-card' | 'message' | 'publication'."""
    path = _DIR / _NAMES[kind]
    if not path.exists():
        raise FileNotFoundError(
            f"{_NAMES[kind]} not found in {_DIR}.\n"
            f"  In a source checkout: python3 scripts/fetch_contracts.py\n"
            f"  In an installed wheel: the build shipped without its contracts — a gate with "
            f"nothing to enforce. Report it against the release."
        )
    return yaml.safe_load(path.read_text())
