---
id: ADR-PA-0014
title: "The agent doctrine moves here — a repo that ships the contract must also hold the reasoning"
status: Proposed
date: 2026-07-23
supersedes: []
references:
  - ../doc/                                # the doctrine, moved
  - ./README.md                            # the log, and the ADR-ECO-* -> ADR-PA-* map
  - https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0021-the-agent-doctrine-leaves.md
---

# ADR-PA-0014 — The agent doctrine moves here

## Context

[ADR-PA-0001](./ADR-PA-0001-papeete-actor-is-sovereign.md) moved the three *schemas* here so that
spec and checker version atomically and an organisation could hold the contracts without a
credential to the Papeete lab. It left everything that *explains* them behind: the operating model,
the message doctrine, the work-observability contract, the card doctrine and its template, and
eleven ADRs recording why each is shaped as it is.

That is half a move, and the wrong half to stop at. A package that ships
`papeete-actor-card/v1` and refuses a card that violates it, while the reasoning for every rule it
enforces lives in a **private repo in another org**, is not self-sufficient — it can tell you that
your card is wrong and not why the rule exists. The autonomy argument of ADR-PA-0001 applies with
exactly the same force to the doctrine: an organisation must be able to **design** a papeete-actor,
not only validate one.

`ecosystem/cards/TEMPLATE.md` is the sharpest instance. It is the fill-in form a pair copies to
author a card — the single most-used artifact in adoption — and it sat in the repo that owns none
of what it describes.

## Decision

**1. The doctrine moves to [`doc/`](../doc/).** `AGENT-OPERATING-MODEL.md`,
`INTER-AGENT-MESSAGES.md`, `WORK-OBSERVABILITY.md`, and `cards/` (the doctrine and the template).

**2. Eleven ADRs move to this log, renumbered `ADR-PA-*`.** Each keeps its text, its date and its
decision; each carries a banner naming the `ADR-ECO-*` id it had. The map is in
[`README.md`](./README.md).

**3. `ADR-ECO-0010` is split rather than moved.** It held two decisions: a two-layer *vocabulary
rule* governing all naming in the ecosystem, and the *actor card*. The rule stays with the ecosystem
as `ADR-ECO-0020`; the card and the words it is written in are
[`ADR-PA-0005`](./ADR-PA-0005-the-actor-card.md).

**4. The line is the same one ADR-PA-0001 drew, applied to prose.**

> If the artifact a decision changes lives here, the decision is recorded here.

What stays with `ECO.GOV`: the cross-org registry, the topology, the org split, dogfooding, decision
altitude, the capability↔application pivot, and its own boundary. Those describe **an ecosystem of
actors**, not **an actor**.

**5. Renumbering is a break, and it is announced as one.** ~200 citations of `ADR-ECO-*` exist in
seven repos, 83 of them to `ADR-ECO-0006` alone. Every one now names a record that has moved and
changed id. This is deliberate — a single-prefix log is worth it — and it obliges an announcement
rather than a silent rename. The old log keeps a tombstone per moved record giving the new id.

## Rationale

The alternative was keeping the `ADR-ECO-*` ids to avoid the citation break. It was rejected because
a log holding two prefixes, one of which names a repo that no longer owns the decisions, is a
permanent source of confusion for a small one-off cost — and the cost is bounded and visible, where
the confusion would be neither. A citation that names a moved id still resolves: the tombstone is
one hop.

The deeper reason to move the prose at all is that **a contract without its reasoning is a rule
nobody can argue with.** `offers: contract-deviation` on this repo's card invites a pair to say "your
shape does not fit my repo" — and a pair can only make that case against the reasoning, which was in
a repo they may not be able to read. Moving the doctrine is what makes that offer real.

## Consequences

- **This repo is now self-sufficient for designing and validating a papeete-actor**: the contract,
  the gates, the template, the doctrine and the decisions, in one installable, public-installable
  place.
- **Seven repos hold stale ADR citations.** `ECO.GOV` files an issue against each; it cannot edit
  them, and adoption is each pair's own act. A citation is not *broken* — the tombstone maps it —
  but it names an id that no longer exists.
- **`ecosystem-governance` keeps tombstones** for the eleven moved records plus `ADR-ECO-0010`, and
  a mapping table in its index. Its counterpart record is `ADR-ECO-0021`.
- **`work-observability/v0` is now published from here**, so this repo's own nonconformity with it —
  no `work.yaml`, no ledger, no kanban — moves from "inherited" to "owned by the contract's author".
  That was already true of `ECO.GOV` and is not improved by relocation.
- Not decided: whether `doc/` should be rendered and published (a docs site), or stay
  markdown-in-repo. Nothing depends on the answer.
