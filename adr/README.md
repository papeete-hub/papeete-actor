# Decision log (`ADR-PA-*`)

Decisions owned by **this repo**: the contracts it carries, the gates that enforce them, the
doctrine in [`../doc/`](../doc/) that explains them, and its own boundary. `papeete-actor` is
sovereign — it does not borrow another repo's decision log for choices about its own payload
([ADR-PA-0001](./ADR-PA-0001-papeete-actor-is-sovereign.md),
[ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)).

**What belongs here.** A change to `papeete-actor-card/*`, `inter-agent-message/*` or
`publication/*`; a change to what a gate computes or refuses; the agent operating model, the message
doctrine, work-observability, the card doctrine; this package's own boundary and release policy.

**What does not.** Questions about an *ecosystem of* actors rather than about *an* actor — the
two-org split, the cross-org registry, the topology, decision altitude, the capability↔application
pivot. Those stay in `papeete-foundry/ecosystem-governance`'s `ADR-ECO-*` log. The line is
ownership, not subject matter: **if the artifact a decision changes lives here, the decision is
recorded here.**

## The log

| ID | Title | Status |
|----|-------|--------|
| [ADR-PA-0001](./ADR-PA-0001-papeete-actor-is-sovereign.md) | papeete-actor is sovereign — it carries the contracts, the gates, and its own decisions | Proposed |
| [ADR-PA-0002](./ADR-PA-0002-agent-bounded-context-operating-model.md) | Agents operate as bounded contexts — human + agent pairs with repo-as-state | Proposed |
| [ADR-PA-0003](./ADR-PA-0003-work-observability-contract.md) | Work-observability contract — every context repo self-reports its lingering work the same way | Proposed |
| [ADR-PA-0004](./ADR-PA-0004-inter-agent-message-contract.md) | The inter-agent message contract — a message is not its transport | Proposed |
| [ADR-PA-0005](./ADR-PA-0005-the-actor-card.md) | The actor card — discovery for a choreographed ecosystem, and the words it is written in | Proposed |
| [ADR-PA-0006](./ADR-PA-0006-publication-outbox-and-binding-split.md) | Publications ride a transactional outbox — one binding per direction | Proposed |
| [ADR-PA-0007](./ADR-PA-0007-actor-card-is-a-root-descriptor.md) | The card is a root descriptor in the actor's own repo, independent of any agent harness | Proposed |
| [ADR-PA-0008](./ADR-PA-0008-publication-obligations-pinning-backfill-interior-bindings.md) | Publication obligations — pinning generates the breaking flag, backfills are declared | Proposed |
| [ADR-PA-0009](./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md) | Actorhood, terminal tiers, and conformance routing | Proposed |
| [ADR-PA-0010](./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md) | `papeete-actor-card/v1` — offers, subscription disposition, and dependencies | Proposed |
| [ADR-PA-0011](./ADR-PA-0011-publication-payload-schema-and-human-view.md) | `publication/v2` — a payload schema beside the prose, and a rendered human view | Proposed |
| [ADR-PA-0012](./ADR-PA-0012-papeete-actor-the-gates-as-a-distributed-tool.md) | The conformance gates as a pinned distribution artifact, not a vendored script | Proposed |
| [ADR-PA-0013](./ADR-PA-0013-papeete-actor-the-term.md) | `papeete-actor` — the ecosystem's actor is a particular construct, and is named as one | Proposed |
| [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md) | The agent doctrine moves here — a repo that ships the contract must also hold the reasoning | Proposed |
| [ADR-PA-0015](./ADR-PA-0015-one-vocabulary-the-actor-fallback-is-removed.md) | One vocabulary — the `actor:` fallback is removed, and replaced by a refusal | Proposed |

**Numbering is allocation order, not chronology.** `ADR-PA-0001` is this repo's founding decision and
is dated after most of the records below it, which were made in `ecosystem-governance` between
2026-07-10 and 2026-07-23 and moved here by `ADR-PA-0014`. Each record's `date:` is the day it was
decided and has not been touched.

## Where a record came from

Eleven records were renumbered on the move. **A citation to an `ADR-ECO-*` id below is not broken —
it names a record that lives here now**, under a new id:

| was | is | |
|---|---|---|
| `ADR-ECO-0004` | [`ADR-PA-0002`](./ADR-PA-0002-agent-bounded-context-operating-model.md) | the operating model |
| `ADR-ECO-0006` | [`ADR-PA-0003`](./ADR-PA-0003-work-observability-contract.md) | *83 citations across the ecosystem — the most-cited of all* |
| `ADR-ECO-0008` | [`ADR-PA-0004`](./ADR-PA-0004-inter-agent-message-contract.md) | |
| `ADR-ECO-0010` | **split** — [`ADR-PA-0005`](./ADR-PA-0005-the-actor-card.md) (the card + its vocabulary) and `ADR-ECO-0020` (the layer rule, which stays) | the one record that did not move whole |
| `ADR-ECO-0011` | [`ADR-PA-0006`](./ADR-PA-0006-publication-outbox-and-binding-split.md) | |
| `ADR-ECO-0012` | [`ADR-PA-0007`](./ADR-PA-0007-actor-card-is-a-root-descriptor.md) | |
| `ADR-ECO-0013` | [`ADR-PA-0008`](./ADR-PA-0008-publication-obligations-pinning-backfill-interior-bindings.md) | |
| `ADR-ECO-0014` | [`ADR-PA-0009`](./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md) | |
| `ADR-ECO-0015` | [`ADR-PA-0010`](./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md) | |
| `ADR-ECO-0016` | [`ADR-PA-0011`](./ADR-PA-0011-publication-payload-schema-and-human-view.md) | |
| `ADR-ECO-0017` | [`ADR-PA-0012`](./ADR-PA-0012-papeete-actor-the-gates-as-a-distributed-tool.md) | |
| `ADR-ECO-0018` | [`ADR-PA-0013`](./ADR-PA-0013-papeete-actor-the-term.md) | |

The old log keeps a tombstone per record pointing here. `ADR-ECO-*` numbers that still exist —
`0001`, `0002`, `0003`, `0005`, `0007`, `0009`, `0019`, `0020`, `0021` — are ecosystem-level and were
never about an actor.

## Authoring

Copy [`template.md`](./template.md), take the next `NNNN`, keep it short, and link the canonical
source where the decision is implemented rather than restating it. Where a decision supersedes one
in the ecosystem log, say so in `supersedes:` and expect the other log to record its own side —
`ADR-PA-0001`/`ADR-ECO-0019` and `ADR-PA-0014`/`ADR-ECO-0021` are the two such pairs.
