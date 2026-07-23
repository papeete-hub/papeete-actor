---
id: ADR-PA-0002
title: "Agents operate as bounded contexts — human + agent pairs with repo-as-state"
status: Proposed
date: 2026-07-10
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../AGENT-OPERATING-MODEL.md
  - https://github.com/papeete-foundry/reliever-business/issues/2
  - https://github.com/papeete-hub/kpack
  - ~/.claude/plans/kontract-two-surface-serving.md (sibling workstream, not yet landed)
---

# ADR-PA-0002 — Agents operate as bounded contexts — human + agent pairs with repo-as-state

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0004`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0004` elsewhere in the ecosystem refer to this record.

## Context

The ecosystem is growing agents (Urbanist workflow skills today, more to come) without a stated
model of how they relate: which agent owns what, how work and findings move between repos, when an
agent may act alone. The 2026-07-09/10 design dialogue settled that model; this record captures the
decisions, and [`AGENT-OPERATING-MODEL.md`](../doc/AGENT-OPERATING-MODEL.md) carries the full doctrine.

## Decision

1. **Contexts are human + agent actor pairs; the repo is the actor's durable state.** Boundary of
   knowledge = boundary of responsibility = boundary of context window.
2. **Five contexts:** Business ("Urbanist", `reliever-business`), Solution ("Designer",
   `reliever-design`), Implementation ("Builder", `reliever-implementation`), Platform
   (`banking-tech`), Governance (`banking-governance`). **Planning is an interior module of
   Implementation**, not a context, until a promotion signal appears.
3. **Two-surface serving:** `kpack` serves the corpus tier, `kontract` (planned) the process/design
   tier — one shared transport, reuse of transport modules only, never the corpus knowledge engine.
4. **Findings rail:** findings flow upstream, addressed to the decision owner (`functional-gap` →
   Business, `contract-deviation` → Solution, `engineering-debt` → Implementation). Events flow
   downstream **published, never delivered** — the direction rule: *addressed upstream, published
   downstream*; a publisher never writes to consumer repos.
5. **Tasks live in git** — no external tracker; one may enter later for coordination state only,
   never as the store of record for findings.
6. **Autonomy Level 0:** every agent write is reviewed through a PR by a human, no exceptions;
   higher levels only via explicit harness once the shapes are understood.

## Rationale

The system is distributed computing with nondeterministic nodes: the actor model plus one new gate
layer. Bounded contexts give the ownership and language boundaries; repo-per-context makes those
boundaries *also* the agent's context window — the same split-by-who-consumes-what legibility rule
that shaped the two-org topology (ADR-ECO-0001), applied one level down.
[reliever-business #2](https://github.com/papeete-foundry/reliever-business/issues/2) showed the
cost of the missing model: an engineering regression filed through the functional-gap door.

## Consequences

- `reliever-design` is founded and chartered by its own ADR-DSN-0001 (context `BNK.RSOL`,
  `kind: solution`, refines `BNK.RLVR`); `templates/solution-repo` now ships in settler and
  `settler found` scaffolds a `<domain>-design` repo (tier gate, membrane hooks, DSN ADR scaffold,
  solution registry entry) for every new product line.
- `reliever-implementation` Stage-0 must repoint to the kontract surface once it exists (sibling plan).
- ADR-BCM-URBA-0016 (process-layer serving) to be authored in `reliever-business` (sibling plan).
- `notify-settler.yml` stays point-to-point at N=1 subscribers; becomes registry-driven at N=2.
- Each context needs its agent card (doctrine §10), including its eval set and autonomy line.
