"""Loading the contract.

It IS authored in this repo, under `schemas/`, as ordinary committed source. The package IS the
contract — it is not a gate that goes looking for it. So a build needs no network and no
credential.

The path is the same in a source checkout and in an installed wheel, so there is no fallback and
no second location to reason about.
"""
from pathlib import Path

import yaml

_NAMES = {
    "manifest": "papeete-actor-manifest.schema.yaml",
}

_DIR = Path(__file__).resolve().parent / "schemas"


def contracts_dir() -> Path:
    return _DIR


def load(kind: str) -> dict:
    """Return one contract by kind: 'manifest'."""
    path = _DIR / _NAMES[kind]
    if not path.exists():
        raise FileNotFoundError(
            f"{_NAMES[kind]} not found in {_DIR}.\n"
            f"  The contract is committed source in this package, so this should be "
            f"unreachable.\n"
            f"  In a source checkout: the file was deleted — restore it from git.\n"
            f"  In an installed wheel: the build shipped without its contract — a gate with "
            f"nothing to enforce. Report it against the release."
        )
    return yaml.safe_load(path.read_text())
