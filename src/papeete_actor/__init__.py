"""papeete-actor — the papeete-actor-manifest/v0 contract, and the gate that enforces it.

A MINIMAL, STANDALONE IDENTITY CONTRACT (ADR-PA-0019): three fields — `name`, `version`,
`description` — plus the `manifest:` key that names the contract itself. Deliberately
independent of any larger actor-card, messaging, or registry contract; none of that lives here.

    papeete-actor-manifest/v0   a minimal, standalone actor identity   -> papeete-actor lint-manifest

Every gate LOADS its schema; none hard-codes a field, an enum or a rule. The schema ships INSIDE
the wheel, so a consumer needs no access to any Papeete repo to be bound by it.
"""

from importlib.metadata import PackageNotFoundError, version as _version

# READ FROM THE INSTALLED METADATA, never restated here. pyproject.toml is the single source, and
# a second copy in this file is a second thing to forget.
try:
    __version__ = _version("papeete-actor")
except PackageNotFoundError:      # running from a source tree that was never installed
    __version__ = "0.0.0+source"

CONTRACTS = {
    "manifest": "papeete-actor-manifest/v0",
}
