---
id: ADR-PA-0008
title: "Publication obligations — pinning generates the breaking flag, backfills are declared, and a binding may be interior"
status: Proposed
date: 2026-07-20
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml
  - ./ADR-PA-0006-publication-outbox-and-binding-split.md
  - https://github.com/papeete-foundry/ecosystem-governance/issues/14   # pinning vs vendoring — two breaks under PATCH
  - https://github.com/papeete-foundry/ecosystem-governance/issues/10   # backfill, producer side (banking-knowledge)
  - https://github.com/papeete-foundry/ecosystem-governance/issues/16   # backfill, consumer side + interior bindings (banking-tech)
---

# ADR-PA-0008 — Publication obligations

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0013`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0013` elsewhere in the ecosystem refer to this record.

## Context

`publication/v0` ([ADR-PA-0006](./ADR-PA-0006-publication-outbox-and-binding-split.md)) landed as
contract and layout with no tooling, on the stated bet that the shape should prove itself before
anything generated it. Within a day, five actors adopted cards, two wrote `events/` logs, and the
conformance audits returned three defects in the contract itself. All three are reported with
evidence rather than argued from first principles, which is the bet paying off.

**1. The breaking-flag condition names the wrong property.** The contract requires a breaking flag
for `vendored-artifact` publications, reasoning that a vendored artefact is *copied* into the
consumer, so an unflagged break is undetectable. The reasoning is right; the condition is too
narrow. `BNK.RLVR/CorpusEnvelope` is pinned and pulled through kpack, not vendored — so the contract
demanded nothing — and the consumer's position is **strictly worse**: a vendoring consumer at least
byte-diffs its copy, while a pin-and-pull consumer diffs nothing and can only observe that its pin
moved. Two breaking changes duly shipped from `reliever-business` under PATCH tags with no
announcement: `7f3ae57` (the whole YAML corpus body retired for rdf-shacl) under `v1.0.1`, and
`5d4c449` (the `bcm` namespace IRI renamed with no aliasing) under `v1.0.2`. The damage is legible
downstream today: four `reliever-design` process models pinned at `v1.0.0-1-gb06a4af`, before both
breaks, reported as `STALE_PROVENANCE / severity: medium / resolve: /process`. Design's detector is
working correctly — *that is all it can know*. A routine re-pin nudge is standing in for a
breaking-change notice (#14).

**2. A late record has nowhere contracted to say so.** `banking-knowledge` backfilled
`events/meta-model/v1.0.0.yaml` and disclosed the lateness in `summary`, explaining that it would
not extend a contract it consumes. `banking-tech` hit the identical gap from the other side, owing a
backfilled announcement for `08ee2c5` (published modules retired under a plain `feat(platform):`
subject). Both correctly rejected `supersedes`, which means *corrects a prior record*, not *is a late
record* (#10.3, #16.3).

**3. A publication may have no surface a card is allowed to name.** `banking-tech` publishes an
authoring method whose only binding today is a set of Claude Code skills, vendored through
`settler/extract_map.yaml`. It is real and mechanically depended upon, and
[ADR-PA-0007](./ADR-PA-0007-actor-card-is-a-root-descriptor.md) forbids a card from naming a
framework or a framework directory. `banking-knowledge` met the same wall from a different angle and
withdrew an `exports:` field rather than let a path list churn the card on every corpus refactor
(#16.2).

## Decision

**1. Pinning generates the obligation, not vendoring.** Replace the enumeration with the property
that actually produces it:

> **A publication whose consumers pin it MUST carry a breaking flag when it breaks.**

Pinning is precisely what makes a consumer unable to see the change for itself; vendoring is one way
to pin, not the distinguishing feature. Every mechanism is covered — byte-vendored copies, tag/sha
pins pulled through kpack, image tags, git refs. `breaking_required_for` is retired as a field; the
rule is stated once, as a property.

**2. A backfilled record declares itself in a field, not in prose.** Add optional
`backfilled: <ISO-8601 date>` — the date the record was *written*, where `at` remains the date the
fact became true.

This is not a stylistic preference over `summary`. The `event-log` binding contracts **git commit
order as the ordering** — a consumer reads "what happened since my pin" with
`git log <pin>..HEAD -- events/`. A backfilled record violates that invariant by construction: its
commit order and its truth order disagree. A consumer reconciling against its pin must be able to
detect that mechanically, and a sentence in `summary` is not detectable. `supersedes` stays what it
was: a correction of a prior record, which a backfill is not.

**3. A publication's binding may be interior, named through a level-1 descriptor.** A card MAY give
a publication's `surface` as a pointer to a descriptor the actor owns —
`settler/extract_map.yaml`, `banking-knowledge/exports.yaml` — rather than a path list or a
framework directory. Two requirements make it honest rather than a loophole:

- **The descriptor must be named in the card.** "Declare the fact, delegate the binding" is
  sanctioned; "declare the fact, hide the binding" is not. The join must be able to follow the
  pointer, or the edge is invisible — the failure mode
  [ADR-PA-0009](./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md) names as
  undeclared consumption.
- **The descriptor is interior and may churn; the card must not.** That is the whole reason for the
  indirection: a card that listed paths would change on every refactor, making the external contract
  a function of internal layout.

## Rationale

Each decision replaces an enumeration with the property that generates it — the same move
ADR-PA-0005 made when it stopped listing terms and stated the layer rule. `[vendored-artifact]` was
a list of one mechanism mistaken for the reason; *consumers pin it* is the reason, and it covers
mechanisms nobody has invented yet.

The backfill field is justified by an invariant, not by taste: `publication/v0` bought its
simplicity by making git the transaction log, and that trade is only sound while commit order and
truth order agree. A backfill is the one case where they don't, so it is exactly the case that must
be machine-visible. Two actors independently choosing `summary` and both explaining why is strong
evidence the gap is real; that they were both *right* not to extend a contract they consume is why
the fix belongs here.

Interior bindings follow ADR-PA-0007's rule to its logical end. If a card may not name a framework,
then a publication served only by framework machinery must be declarable some other way, or the rule
would force a choice between lying and omitting. The level-1 descriptor is that other way, and
`banking-knowledge` reached it unprompted — a good sign it is the natural shape rather than an
invention.

## Consequences

- `https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml` revises to `publication/v1`: `breaking_required_for` retired,
  the pinning rule stated, `backfilled` added to optional fields, interior bindings sanctioned with
  the naming requirement. Consumers vendor a pinned copy; the version bump is itself a breaking
  change to a pinned publication, so it is announced under its own rule.
- **`reliever-business`'s local invention becomes conformance.** It already made `breaking_flag`
  REQUIRED for `CorpusEnvelope`, backfilled `events/CorpusEnvelope/` for both breaches, and added
  `tools/check_publication_outbox.py` gating exactly those commits. That work stands unchanged; it
  is now the reference implementation rather than a repo-local rule. Its two backfilled records gain
  a `backfilled:` field.
- **`banking-knowledge`'s `summary` disclosure migrates** to the field. Its `v1.0.0` records were
  right to disclose and right not to invent a field; nothing about them was wrong.
- **`banking-tech` owes a backfilled record** for `08ee2c5` to `reliever-implementation`, and may
  now declare its authoring-method publication through `extract_map.yaml`.
- Every actor with a pinned publication must audit for unannounced breaks. `banking-knowledge` is
  already flagged on both publications; `reliever-business` has discharged its two; the rest is
  unsurveyed.
- Not addressed here: how a consumer *learns* a breaking record exists, which is still polling on
  the consumer's own cadence — and no consumer declares one. Widening the obligation does not close
  that half.
