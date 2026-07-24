"""Loading the contracts.

They ARE authored in this repo, under `schemas/`, as ordinary committed source (ADR-PA-0001). The
package IS the contracts — it is not a gate that goes looking for them. So a build needs no
network and no credential, which is what lets an organisation stand up a papeete-actor without
depending on Papeete for anything.

They were previously fetched at build time from a private lab repo. That split spec from checker
across two repos — the drift generator ADR-ECO-0005 was written to prevent — and made the package
unbuildable by anyone without read access to the lab.

The path is the same in a source checkout and in an installed wheel, so there is no fallback and
no second location to reason about.
"""
from pathlib import Path

import yaml

_NAMES = {
    "papeete-actor-card": "papeete-actor-card.schema.yaml",
    "message": "message.schema.yaml",
    "publication": "publication.schema.yaml",
    "registry": "registry.schema.yaml",
}

_DIR = Path(__file__).resolve().parent / "schemas"


def contracts_dir() -> Path:
    return _DIR


def load(kind: str) -> dict:
    """Return one contract by kind: 'papeete-actor-card' | 'message' | 'publication' | 'registry'."""
    path = _DIR / _NAMES[kind]
    if not path.exists():
        raise FileNotFoundError(
            f"{_NAMES[kind]} not found in {_DIR}.\n"
            f"  The contracts are committed source in this package, so this should be "
            f"unreachable.\n"
            f"  In a source checkout: the file was deleted — restore it from git.\n"
            f"  In an installed wheel: the build shipped without its contracts — a gate with "
            f"nothing to enforce. Report it against the release."
        )
    return yaml.safe_load(path.read_text())
