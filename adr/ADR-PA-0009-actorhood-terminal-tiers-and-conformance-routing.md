---
id: ADR-PA-0009
title: "Actorhood, terminal tiers, and conformance routing — what is an actor, what it owes, and where a nonconformity goes"
status: Proposed
date: 2026-07-20
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../cards/README.md
  - ./ADR-PA-0005-the-actor-card.md
  - ./ADR-PA-0007-actor-card-is-a-root-descriptor.md
  - https://github.com/papeete-foundry/ecosystem-governance/issues/13   # settler has no card; three actors subscribe to it
  - https://github.com/papeete-foundry/ecosystem-governance/issues/15   # terminal tier: completion channel, publishing at all
  - https://github.com/papeete-foundry/ecosystem-governance/issues/10   # no legal path for conformance findings
  - https://github.com/papeete-foundry/ecosystem-governance/issues/12   # undeclared consumption
---

# ADR-PA-0009 — Actorhood, terminal tiers, and conformance routing

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0014`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0014` elsewhere in the ecosystem refer to this record.

> **Renamed by [ADR-PA-0013](./ADR-PA-0013-papeete-actor-the-term.md).** Read *actor* as
> **papeete-actor** throughout; the actorhood test in Decision 1 is now the test for
> **papeete-actorhood**, unchanged in substance. `charter check` is now `papeete-actor check`. The
> text is left as written, in the vocabulary of 2026-07-20.

## Context

Adoption of `actor-card/v0` across every tier surfaced four questions the contract could not answer,
each reported with a worked instance.

**1. Half the ecosystem subscribes to something that is not an actor.** Three adopted cards declare
`to: settler/work-pipeline` with pins; `settler` has no card, so the join reports a **dangling
subscription held by half the ecosystem**. The registry models `settler` under `publishes` edges,
hinting it is a distribution channel — but it behaves like an actor in every practical way: a repo,
versions and tags, consumers that pin it, and requests arriving (settler#12 was filed as a plain
GitHub issue precisely because no rail existed to send it on) (#13).

**2. The contract is written for actors in the middle of the flow.** `reliever-implementation` is the
only terminal tier — source of two upstream rails, destination of neither — and it fails the card
shape at both ends. Its inbound: it polls the disposition of its own outbound requests
(`refresh_escalations.py` → `views/escalations.yaml`), which fits none of the four slots, and its
card says so in an unlovely `to: (no publication id — see open)` rather than dressing it up. Its
outbound: `ReleasePublished` is seed residue — no tag, no release, no log, **never emitted**, and no
actor subscribes to it. Nothing in the doctrine says a card may legitimately publish nothing, so a
conformant terminal tier reads as non-conformant on both counts (#15).

**3. Verified conformance defects have no lawful destination.** Two of `banking-governance`'s three
audit findings had to be filed *downstream*, into `settler` and `reliever-implementation`, against
§5's rule that a publisher never opens issues in consumer repos. The three rails all terminate at
business, design and implementation; nothing addresses governance, and nothing carries a
*conformance* finding in either direction. Filing broke the rule; not filing would have lost real
defects (#10.4).

**4. The most dangerous coupling is invisible to the join.** `reliever-business/report_coverage.py`
reads `../reliever-design/process/<CAP_ID>/` off a sibling filesystem checkout, and neither card
declares the edge. Dangling subscriptions and unsubscribed publications are hygiene — the consumer
waits on nothing, or output goes nowhere. **Undeclared consumption is the class that causes an
outage**, because the producer cannot see the edge it is about to break, which makes "announce your
breaking changes" unenforceable against it. It also means `reliever-design`'s interior directory
layout is a de-facto consumed contract — the §4 leak — and no card shows it (#12).

## Decision

**1. The actorhood test, and `settler` is an actor.**

> An **actor** is: one repo, one human+agent pair, durable state others depend on, and an address
> that can receive a request.

`settler` passes on all four and adopts a card publishing `work-pipeline`; the three subscriptions
resolve. The registry's `publishes` edge describes the lab→distribution *flow*, not actorhood — a
repo can be both a distribution channel and an actor, and `settler` is.

`kledger` passes the first three and has no pair; it stays `card_status: none` until one exists.
Nothing subscribes to it today, so the question is not load-bearing.

**2. A subscription may name a non-actor source, explicitly.** Actorhood does not close #13's other
half: `reliever-implementation` pins `papeete-hub/kpack`, which is an engine in the distribution org
with no pair and no card. A subscription MAY carry `external: true`, meaning *the producer is
outside the actor set and no card will ever publish this id*. `charter check` reports these as
**external**, never as dangling. Without this the join would push every actor toward either a false
dangling or a silent omission — and silent omission is decision 5's failure mode.

**3. A publication-less actor is conformant.** `publications: []` is a legal, complete card. A
terminal tier owes the ecosystem findings, not artefacts, and must not invent a publication to fill
a slot. `charter check` never faults an empty list, and `reliever-implementation` may remove
`ReleasePublished` — seed residue for a fact it has never emitted and nobody consumes. Its instinct
not to delete a storming artefact unilaterally was right; this is the ruling it was waiting for.

**4. A request's completion is a publication of the answering actor — no fourth slot.** The doctrine
already says a request completes *"as a refusal, or later, as a publication the sender may have
subscribed to"*. That is not a new obligation; it is an existing one nobody implemented.

So: **an actor that answers a request SHOULD publish the terminal disposition** — accepted,
rejected, resolved — under an id of its own naming, and the sender subscribes to it like anything
else. `refresh_escalations.py` is therefore a **workaround for an unpublished fact**, not a missing
card field, and it is declared as an ordinary subscription once the upstream publication exists.
Until then it stays declared as the deviation it is, with `external: true` (it watches GitHub issue
state, the binding of its own `requests_out`).

`actor-card/v0` gains no fourth direction. The four slots are complete.

**5. Consumption by any mechanism is a subscription, and must be declared.**

> **Reading another actor's artefact — pulled, vendored, sibling path, image pin, generated
> output — is a subscription. Undeclared consumption is a conformance defect owned by the
> consumer.**

`charter check` carries three classes: `dangling-subscription`, `unsubscribed-publication`, and
`undeclared-consumption`. The third is **not decidable from cards alone** — by construction, since
the evidence is in consumer code — so detection is a heuristic (sibling-repo paths, hard-coded
refs, cross-repo reads in consumer source) plus the honesty rule above. A heuristic finding is a
prompt to declare, never an automatic verdict.

**6. `ECO.GOV` is the sole re-emitter of nonconformities.** An actor that detects a conformance
defect in another actor sends it to `ECO.GOV`; `ECO.GOV` verifies and re-emits it to the owner as a
**nonconformity**. No actor addresses another about its conformance directly.

This preserves the direction rule rather than carving an exception out of it: a conformance defect
*is* a finding travelling to its decision owner, and conformance decisions are owned by `ECO.GOV`
(ADR-PA-0005's vocabulary already reserves the word). It is also the one rail `ECO.GOV`'s read-only
boundary permits, because a nonconformity is exactly what ADR-ECO-0005 said violations exit as.

**`ECO.GOV` gets no exemption.** Nonconformities about `ECO.GOV` — its own contracts, its own
unconformant work surface — are sent to `ECO.GOV`, which must accept and triage them like any owner.
A supervisor that cannot be contradicted is the failure its own cards flagged; the recursion is
uncomfortable and correct, and the alternative is worse.

## Rationale

Decisions 1–4 all follow from one observation: **`actor-card/v0` was written from the middle of the
flow.** Every question came from an edge — the tool nobody classified, the tier that only receives,
the actor that only sends. Rather than add slots per edge case, each is resolved by naming a property
that was already implied: actorhood is an address plus durable state; a completion is a publication;
an actor with nothing to publish publishes nothing.

Decision 5 is the one that changes what conformance *means*. A card-only join can be perfectly clean
while the ecosystem's most dangerous coupling sits in a consumer's source file. Naming the class
stops "the join is clean" from implying "the couplings are declared" — and the honesty rule puts the
duty on the consumer, who is the only party that knows the edge exists.

Decision 6 accepts a cost deliberately: routing conformance through `ECO.GOV` adds a hop and makes it
a bottleneck. The alternative — every actor free to file conformance findings anywhere — dissolves
the direction rule, which is the one invariant holding the choreography together. A bottleneck is
recoverable; a dissolved boundary is not.

## Consequences

- **`settler` adopts a card** publishing `work-pipeline`, resolving three dangling subscriptions. It
  also inherits the pending requests already filed against it as plain issues (settler#11–#14).
- `actor-card/v0` gains `external: true` on subscriptions and a stated rule that
  `publications: []` is legal. No new direction. The version stays `v0` — these are additions, not
  changes to what an existing card means.
- `cards/README.md` gains the actorhood test, the three conformance classes, and the nonconformity
  routing rule.
- **`reliever-implementation` may remove `ReleasePublished`**, and re-declare the escalation watch
  with `external: true` pending an upstream disposition publication.
- **`reliever-business` and `reliever-design` owe declarations**: the sibling-path read is a
  subscription (reliever-business#26), and design's `process/<CAP_ID>/` layout is a consumed surface
  it did not know it had.
- **The rails are unchanged at three.** `nonconformity` is an ecosystem-layer class, not a fourth
  domain rail — it addresses an actor about its *card and contracts*, never about its domain
  content. Conflating them would put ecosystem vocabulary on a domain-layer rail, against
  ADR-PA-0005's layer rule.
- `charter check` now has a specification: three classes, the external marker, the empty-publications
  rule, and the actorhood test. It still does not exist, and everything above remains hand-computed
  until it does — which is `ECO.GOV`'s own standing nonconformity (#10.5).
- Not decided: whether a disposition publication is *required* rather than SHOULD. Making it
  mandatory obliges every actor to write an `events/` log, and today only two do. Revisit when the
  outbox is in practice rather than in contract.
