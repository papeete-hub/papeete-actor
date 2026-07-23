---
id: ADR-PA-0011
title: "publication/v2 — a payload schema every consumer can read, and a human view rendered from it"
status: Proposed
date: 2026-07-22
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml          # the precedent: payload + bindings-as-projections
  - ../../events/publication-contract/schema.yaml   # the first shape written under this rule
  - ../AGENT-OPERATING-MODEL.md               # §5 — three kinds of consumer, one contract
  - ./ADR-PA-0006-publication-outbox-and-binding-split.md
  - ./ADR-PA-0008-publication-obligations-pinning-backfill-interior-bindings.md
  - ./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md
---

# ADR-PA-0011 — `publication/v2`

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0016`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0016` elsewhere in the ecosystem refer to this record.

## Context

`publication/v1` schematises the **record envelope** — `publication`, `at`, `ref`, `summary`, and the
optional `scope`, `subject`, `breaking`, `evidence`, `supersedes`, `backfilled`. That envelope is
identical for every publication in the ecosystem. It says nothing about what an `ApplicationStubbed`
record carries that a `meta-model` record does not.

**Per-publication payload shape exists nowhere.** `ApplicationStubbed` is described in its producer's
card as *"a disclosure of construction under knowledge scarcity, addressed to whoever would otherwise
mistake this papeete-actor's invention for a decision"* — excellent prose, and nothing a script can validate
against. The invariants that actually govern it (an application is a deployable component, not a
capability; identity is `(ref, subject)` and never `ref` alone; no `ApplicationCreated` may share a
ref with it) live in card prose, where no tool can reach them.

This went unnoticed because the design conversation that produced `subscriptions[].then` assumed the
reader would be an agent. Two of the three kinds of counterpart in this ecosystem cannot read prose
at all:

| Consumer | Reads | Present today |
|---|---|---|
| an **agent** papeete-actor | the schema *and* the prose, then judges | `Urbanist`, `Designer`, `Builder` |
| a **human** papeete-actor | a rendering | `banking-tech`, `banking-governance`, `ECO.GOV` — all `agent: none` |
| a **scripted** papeete-actor | typed fields; fails closed; must pin | every `tools/check_*_sync.py` in the ecosystem |

And the precedent for serving all three was already in this repo, one layer down.
`inter-agent-message/v0` carries **one** `payload:` (required fields, enums, a `scope_grammar` regex)
**plus** `bindings.github-issue` with `title:` and `body_block_lang:`, and `render_message.py`
generates the human-facing issue from it. That is why the doctrine can say messages are *"rendered,
never hand-authored"*. Publications never got the same treatment.

## Decision

**1. Every publication declares a payload schema, and it is required.**

> `publications[].shape` — a path to a payload schema, owned by the producing papeete-actor and living in
> the producer's repo at `events/{publication}/schema.yaml`.

`ECO.GOV` owns this meta-contract; it does **not** own anyone's payload. A payload schema is domain
knowledge, and the tier emitting the fact is the only one that can author it.

**2. The obligation is unconditional.** Not *"required when a consumer scripts against it"*.

A producer **cannot see its consumers**: `consumption.no_consumer_list` forbids it from knowing, and
subscriptions are declared consumer-side. A producer asked to judge when a schema is owed would be
guessing at information this contract deliberately denies it. That is the trap ADR-PA-0008 escaped
when it replaced `breaking_required_for: [vendored-artifact]` — an enumeration the producer had to
guess — with the pinning rule, a property. Here the property that generates the obligation is simply:
*the fact was published at all.*

**3. `bindings.human-view` is added** — a projection rendered **from the schema**, never
hand-authored, landing on the **consumer's** own surface (its `BOARD.md`, an issue in its own repo, a
digest). Rendering happens consumer-side on the consumer's cadence; a producer rendering into a
consumer's repo would breach `no_delivery`. The renderer should be extracted from
`render_message.py` rather than written afresh.

**4. Existing records are grandfathered.** A `shape` describes records written **from v2 onward**.
Nothing is retrofitted. This is the stance v1 took toward v0 (*"records written under v0 remain valid
as written"*), and for the same reason: the log is append-only, and editing history to satisfy a
contract written after it breaks the one property consumers rely on.

**5. `schema.yaml` is a reserved filename inside `events/{publication}/`.** It sits beside the facts
so a publication's shape lives with them, but it is not a record, and a gate walking `events/*/*.yaml`
must exclude it — otherwise it parses as a record whose `ref` is `schema`. `ref` is a version
identifier or a sha (the ref rule), so `schema` can never be a real ref.

## Rationale

One sentence carries the whole decision:

> **The schema is the floor, the prose is the ceiling, and the human view is a rendering of the
> floor.**

The prose is not decoration — `means` is what lets an agent consumer decide relevance without a
handler, which is the mechanism ADR-PA-0010 rests on. But it is **additive, never substitutive**,
and v1 permitted a producer to ship prose alone. Given that the producer cannot see its consumers,
permitting that was permitting it to guess wrong silently.

Decision 3 follows from decision 1 rather than standing beside it: **you cannot deterministically
render from prose.** A human-readable view that is hand-written is a second source of truth that
drifts from the log it claims to show. Requiring the schema is what makes the rendering possible; the
message contract proved the pattern before this ADR existed.

The cost is honestly a widened producer obligation, which ADR-PA-0008 flagged as a live tension when
it widened one before. It is accepted here because grandfathering bounds it to new records, and
because the alternative — a shape owed only when someone scripts against it — asks producers to know
the one thing the direction rule forbids them from knowing.

## Consequences

- **Five publications owe a `shape`**: `banking-knowledge`'s `meta-model` and `method-standards`,
  `reliever-business`'s `CorpusEnvelope`, `reliever-implementation`'s `ApplicationCreated` and
  `ApplicationStubbed`. `banking-tech` and `banking-governance` publish nothing and owe nothing.
- **`reliever-implementation` gains the most.** Its two publications' invariants — mutual exclusivity
  on a ref, `(ref, subject)` identity — are exactly what a payload schema should carry and are
  currently prose in a card, checkable by nobody.
- **`banking-knowledge` is where grandfathering matters.** It holds the most records already written;
  without decision 4 this ADR would demand retrofitting an append-only log.
- **Two gates must learn the reserved filename**: `banking-knowledge/tools/check_publications.py` and
  `reliever-business/tools/check_publication_outbox.py` walk the log and would read `schema.yaml` as a
  malformed record.
- **`ECO.GOV` goes first, and is subject to its own rule.** `events/publication-contract/schema.yaml`
  is the first shape written under v2, and the `publication-v2` record announcing this contract ships
  in the same commit as the schema change — the atomicity rule, applied to the papeete-actor that wrote it.
- **`breaking: true` on that record.** v2 retires no key, so an old reader still finds every field it
  knew. But it *adds a required field to its consumers' obligations*, and a contract that does that
  has broken them whatever it did to their parsers.
- **Not decided: how a `means` revision is announced.** The two faces break differently. A `shape`
  change breaks a script silently — that is what `breaking` exists for. A `means` change breaks no
  script and may change what an **agent** consumer decides, because that prose is what it judges
  against. Nothing records a meaning revision, and it is not obvious `breaking` is the right
  instrument. Revisit when a papeete-actor first rewrites a `means` under a live `intent:` subscription.
