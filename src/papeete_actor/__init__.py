"""papeete-actor — the three Papeete ecosystem contracts, and the gates that enforce them.

THIS REPO OWNS THEM. They were ECO.GOV's until 2026-07-23, when ADR-PA-0001 / ADR-ECO-0019 moved
the contracts here and ADR-PA-0014 / ADR-ECO-0021 moved the doctrine that explains them. ECO.GOV
now consumes this package like any other actor, at a pin.

    papeete-actor-card/v1    a repo's self-description        -> papeete-actor lint-card
    inter-agent-message/v0   an addressed request             -> papeete-actor lint-message
    publication/v2           a fact and its payload schema    -> papeete-actor lint-publication
    the cross-card join      the conformance classes          -> papeete-actor check

Every gate LOADS its schema; none hard-codes a field, an enum or a rule. Change a contract in
src/papeete_actor/schemas/ once and every gate follows — the discipline that keeps a gate from
drifting from the contract it claims to enforce. The schemas ship INSIDE the wheel, so a consumer
needs no access to any Papeete repo to be bound by them.
"""

from importlib.metadata import PackageNotFoundError, version as _version

# READ FROM THE INSTALLED METADATA, never restated here. pyproject.toml is the single source, and
# a second copy in this file is a second thing to forget: `papeete-actor contracts` reported 0.1.0
# out of a 0.2.0 wheel for exactly as long as this line was a literal.
try:
    __version__ = _version("papeete-actor")
except PackageNotFoundError:      # running from a source tree that was never installed
    __version__ = "0.0.0+source"

CONTRACTS = {
    "papeete-actor-card": "papeete-actor-card/v1",
    "message": "inter-agent-message/v0",
    "publication": "publication/v2",
}
