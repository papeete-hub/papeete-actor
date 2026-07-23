"""papeete-actor — the conformance gates for the Papeete ecosystem contracts.

ECO.GOV owns three contracts. This package is the one place they are ENFORCED:

    papeete-actor-card/v1            a repo's self-description        -> papeete-actor lint-card
    inter-agent-message/v0   an addressed request             -> papeete-actor lint-message
    publication/v2           a fact and its payload schema    -> papeete-actor lint-publication
    the cross-card join      the conformance classes          -> papeete-actor check

Every gate LOADS its schema; none hard-codes a field, an enum or a rule. Change a contract in
ecosystem/contracts/ once and every gate follows — the discipline that keeps a gate from drifting
from the contract it claims to enforce.

Authored in papeete-foundry/ecosystem-governance (the lab), distributed as papeete-hub/papeete-actor
(the client-pinned side). ADR-ECO-0017.
"""

__version__ = "0.1.0"

CONTRACTS = {
    "papeete-actor-card": "papeete-actor-card/v1",
    "message": "inter-agent-message/v0",
    "publication": "publication/v2",
}
