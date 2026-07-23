# Decision log (`ADR-PA-*`)

Decisions owned by **this repo**: the contracts it carries, the gates that enforce them, and its own
boundary. `papeete-actor` is sovereign — it does not borrow another repo's decision log for choices
about its own payload ([ADR-PA-0001](./ADR-PA-0001-papeete-actor-is-sovereign.md)).

**What belongs here.** A change to `papeete-actor-card/*`, `inter-agent-message/*` or
`publication/*`; a change to what a gate computes or refuses; this package's own boundary and
release policy.

**What does not.** Ecosystem-level questions — the two-org split, the cross-org registry, the agent
operating model, the topology — stay in `papeete-foundry/ecosystem-governance`'s `ADR-ECO-*` log.
The line is ownership, not subject matter: if the artifact changed lives in this repo, the decision
is recorded here.

Where a decision here supersedes one there, it says so in `supersedes:` and the other log records
the counterpart from its own side. `ADR-PA-0001` and `ADR-ECO-0019` are the first such pair.

| ID | Title | Status |
|----|-------|--------|
| [ADR-PA-0001](./ADR-PA-0001-papeete-actor-is-sovereign.md) | papeete-actor is sovereign — it carries the contracts, the gates, and its own decisions | Proposed |
