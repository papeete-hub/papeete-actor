---
id: ADR-PA-0006
title: "Publications ride a transactional outbox — one binding per direction, not one per ecosystem"
status: Proposed
date: 2026-07-20
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml
  - ../AGENT-OPERATING-MODEL.md
  - ../INTER-AGENT-MESSAGES.md
  - ../cards/README.md
---

# ADR-PA-0006 — Publications ride a transactional outbox

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0011`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0011` elsewhere in the ecosystem refer to this record.

## Context

The six actor cards ([ADR-PA-0005](./ADR-PA-0005-the-actor-card.md)) made a
gap legible that had been distributed across three separate symptoms: **publications have no medium.**

- Only one subscription in the ecosystem is fully wired (business → the settler work-pipeline
  template, pinned and drift-checked). Design's corpus pulls are real but rely on bespoke detectors;
  implementation's Stage-0 pull has no declared mechanism at all.
- `BNK.KNOW` publishes the meta-model and method standards that every map vendors behind a pin, and
  **nothing announces a bump**. The direction rule forbids knowledge from pushing, so consumers must
  poll — and no consumer declares a cadence for it. A breaking method change is currently
  undiscoverable except by someone remembering to say so.
- `notify-settler.yml` pushes `DecisionRatified` point-to-point to one subscriber — the ecosystem's
  one standing violation of *published, never delivered*, tolerated at N=1.

The medium has in fact been specified since AGENT-OPERATING-MODEL §5 was written — *"an append-only
`events/` log committed atomically with the change is a transactional outbox"* — and never built.
Git-append logs are the third mailbox mechanism that section names.

A second question arrived with it: should publications simply become another binding of
`inter-agent-message/v0`, alongside `github-issue`?

## Decision

**1. One binding per *direction*, not one per ecosystem.** The two directions of the direction rule
have different transport requirements and do not share a medium:

| | Request (addressed upstream) | Publication (published downstream) |
|---|---|---|
| Addressed to | exactly one actor | nobody |
| Lands in | the **recipient's** repo | the **producer's** repo |
| Identity | `(type, subject)`, upsert | append-only, ordered |
| Refusable | yes — triage is the owner's act | no — it is a fact |
| Read by | the recipient, on receipt | consumers, on their own cadence |
| Binding | `github-issue` — unchanged | `event-log` — new |

**2. `github-issue` stays the request binding.** It is the one built mechanism, it notifies, and it
works. A `file-mailbox` binding was considered and deferred: the gain (idempotency via filename,
delivery as a reviewable PR) is real but small at N=1 human, where sender and recipient are the same
person. It remains available — that is what the binding layer is for.

**3. A publication is NOT an inter-agent message.** `publication/v0` lands as a **sibling contract**
under `contracts/`, not as a third binding of `inter-agent-message/v0`. That contract's single payload
kind is `finding` and its identity is `(type, subject)` with upsert semantics — all of which presume
*addressed*. An append-only ordered log of unaddressed facts is a different shape; forcing it in
would re-fuse the two directions immediately after separating them. `interchange` (ADR-PA-0005) is
the superset term that covers both.

**4. The `event-log` binding.** In the producer's repo, one file per fact:

```
events/{publication}/{ref}.yaml
```

- **Atomicity — the one hard rule.** The event file is committed **in the same commit as the change
  it describes**. That is what makes it a transactional outbox rather than a dual write. An entry
  landing in its own later commit is non-conformant: between the two commits the repo asserts a state
  its log denies.
- **Ordering is git commit order.** Not encoded in the record — `git log <pinned_ref>..HEAD --
  events/` is "what happened since my pin". No sequence numbers to allocate, no ordering field to get
  wrong, no concurrent-append conflicts.
- **`breaking: true`** is what makes a vendored upstream safe to depend on, and is why this closes
  the knowledge hole specifically.

**5. Consumption stays pull, and stays consumer-declared.** The producer never notifies, never
acknowledges, never records who consumes it. Fan-out is the join of `publications` against
`subscriptions` across actor cards — unchanged from ADR-PA-0002 Decision 4 and ADR-PA-0005.

**6. Contract and layout only; no tooling.** No renderer, no gate, no generator. The first logs are
appended by hand, deliberately: the shape proves itself before anything automates it — the order
`inter-agent-message/v0` followed.

## Rationale

The split is not an optimization; it was already law. §5 states that *a publisher must never open
issues in consumer repos*, which means a publication could never have used the issue binding. What
looked like an open choice of medium was a mandate with no implementation.

Choosing git as the transaction log rather than a broker follows the same reasoning that keeps tasks
in git (ADR-PA-0002 Decision 5): the model is repo-as-durable-state and Autonomy Level 0 requires
every write to be reviewable. A broker's queue is state outside git — not diffable, not committable,
and a consumed message leaves no artifact to review. A broker becomes appropriate at Level 2+, with
concurrent autonomous consumers where backpressure and consumer groups are real problems; at Level 0
its semantics are unused and its statefulness is a liability. §5 already said it: *no broker until
volume justifies one — the discipline matters, not the infrastructure.*

Keeping publications out of `inter-agent-message/v0` is the same discipline ADR-PA-0004 applied to
transport: name the thing separately *before* a second case forces a rewrite.

## Consequences

- `https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml` lands; `contracts/README.md` gains its row. Nothing loads it
  yet.
- The six actor cards name `events/{publication}/` as the surface for each publication, and each is
  marked as **not yet written** — the honest state.
- **Subscriptions become executable** rather than documentary: `to: BNK.RLVR/CapabilityReadyForDesign`
  resolves to `git log <pin>..HEAD -- events/CapabilityReadyForDesign/`.
- **`notify-settler.yml`'s violation dissolves when settler subscribes** by reading the log instead of
  being dispatched to. The N=2 trigger from ADR-PA-0002 no longer needs a registry-driven fan-out
  mechanism to be designed — pull *is* the mechanism, at any N.
- **`BNK.KNOW` gets an announced-bump path** for the first time, via `breaking: true`. Consumers still
  have to poll; that is now a declarable, checkable cadence on each card rather than an omission.
- Two `charter check` classes from ADR-PA-0005 become computable against real data once logs exist:
  `dangling-subscription`, `unsubscribed-publication`. A third suggests itself here —
  `undeclared-publication`: an `events/` entry whose id appears on no card.
- Deferred, not decided: the `file-mailbox` request binding; whether `ContractPublished` can be
  emitted before `kontract` exists (design's publication currently has no surface at all); and whether
  a `query`-nature request (ADR-PA-0005) needs a reply binding, which neither contract addresses.
- Not addressed here: nothing migrates. Existing tags, corpus refs, and the dispatch keep working;
  the log is additive, and the first actor to write one is choosing to.
