---
id: ADR-PA-0007
title: "The actor card is a root descriptor in the actor's own repo, independent of any agent harness"
status: Proposed
date: 2026-07-20
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../cards/README.md
  - ../cards/TEMPLATE.md
  - ../../papeete-actor.yaml
  - ../registry.yaml
---

# ADR-PA-0007 — The actor card is a root descriptor in the actor's own repo

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0012`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0012` elsewhere in the ecosystem refer to this record.

> **Renamed by [ADR-PA-0013](./ADR-PA-0013-papeete-actor-the-term.md).** Read *actor* as
> **papeete-actor**, `actor.yaml` as **`papeete-actor.yaml`**, and `actor-card/v1` as
> **`papeete-actor-card/v1`** throughout. Every decision here stands unchanged in substance — only
> the noun moved. The text is left as written, in the vocabulary of 2026-07-20.

## Context

The six actor cards from [ADR-PA-0005](./ADR-PA-0005-the-actor-card.md) were
drafted here, in `ecosystem-governance`, because that is where the storming that produced them
happened. That is the wrong home, for reasons this repo already states about every other kind of
fact:

- **ADR-PA-0002 §1**: the repo *is* the actor's durable state. A card is an actor's account of
  itself; hosting it elsewhere means `ECO.GOV` authors another actor's self-description — the same
  violation as authoring another context's kanban.
- **Drift.** A card names gates, ledgers, and a work surface that live in another repo and change
  there. Held here it goes stale silently; held beside the code it changes in the same PR as the
  thing it describes. `registry.yaml`'s own authority boundary already forbids exactly this shape of
  duplication.
- **`ECO.GOV` is read-only over every other repo.** A card it hosts is a claim about a repo it cannot
  write to and does not watch.

There is also a precedent sitting in the repo: **`work.yaml`**. A root descriptor each context repo
carries, conforming to a contract `ECO.GOV` owns, so any consumer reads the repo's work surface with
zero per-repo knowledge (WORK-OBSERVABILITY §2, which states the idiom directly — *"one descriptor
per concern"*, alongside `knowledge.yaml`). The actor card is a third concern of the same kind.

A second question arrived with the first: **no decision has been made about what an agent is built
with** — Claude Code skills, LangChain, or something not yet chosen. An actor's responsibilities and
the way it communicates must not be entangled with that choice.

## Decision

**1. The card is `actor.yaml` at the repo root.** One descriptor per concern, beside `work.yaml` and
`knowledge.yaml`, conforming to `actor-card/v0`.

**2. One repo, one actor, one card.** No `actors/{name}/` directory: a path variable implies a repo
can host several actors, which contradicts ADR-PA-0002 §1 — one repo, one actor, one context window.
If the eval set of AGENT-OPERATING-MODEL §10 materializes, it earns a sibling `actor/` folder for
fixtures; the descriptor stays at the root.

**3. The card is harness-independent, by rule.** It never lives under `.claude/`, or any
framework-specific directory, and it names no framework. AGENT-OPERATING-MODEL §4 already fixes why:
*the external contract is the architecture; interior patterns are decoration that must never leak.*
Whether an actor is implemented as Claude Code skills, a LangChain graph, or a human with a checklist
is **interior**. The card is membrane. A harness swap must not touch it — and if it does, the card
was describing the wrong thing.

**4. `ECO.GOV` owns the contract; each repo owns its card.** The third instance of the ADR-ECO-0005
split, matching the two already in place:

| Contract (here) | Instance (in the repo) | Runtime (where it runs) |
|---|---|---|
| `work-observability/v0` | each repo's `work.yaml` | the repo's detectors + kanban |
| `inter-agent-message/v0` | messages in owner repos | `render_message.py` (settler template) |
| `actor-card/v0` | each repo's `actor.yaml` | *(no tooling yet)* |

**5. `registry.yaml` is the index.** Each repo entry that is an actor gains `actor:` (the id) and
`card:` (the path, `actor.yaml`). Distributed cards need one place that enumerates them — the same
role A2A's well-known path convention plays, filled here by the registry `ECO.GOV` already owns.
`charter check` walks the registry and reads each repo's card; `check_ecosystem.py` already reaches
into sibling trees this way.

**6. Adoption, not migration.** `ECO.GOV` cannot move these cards — it is read-only over every other
repo. The five non-`ECO.GOV` cards become **seeds**: proposals their pairs adopt, in their own repos,
as their own commits. `ECO.GOV` deletes each seed as its owner adopts it. This is how `work.yaml`
rolled out (WORK-OBSERVABILITY §7: contract first, then a per-repo adoption table).

**7. `ECO.GOV`'s own card lands at its own root** — [`actor.yaml`](../papeete-actor.yaml) — by the same
rule it applies to everyone. It is not a seed; it is adopted.

## Rationale

The three splits in Decision 4 are one pattern applied consistently: **the contract is
ecosystem-layer and central; the conformant artifact is domain-layer and local.** Every time this
repo has been tempted to hold the artifact instead of the contract, drift has been the cost — that is
the lesson `registry.yaml` was built around, and cards are no exception.

Per-repo hosting is also the faithful half of the A2A analogy the cards are built on. An agent card
is served *by* the agent at a well-known path; discovery fetches from the provider, not from a
central directory. A central card registry would have kept the resemblance while inverting the
mechanism.

Harness-independence is not caution about an undecided tool choice — it is the same boundary the
whole model rests on. An actor's responsibilities and its communication contract are orthogonal to
its implementation, and a card that mentioned a framework would have made the contract a function of
the interior.

## Consequences

- [`actor.yaml`](../papeete-actor.yaml) lands at this repo's root; `cards/card-ecosystem-governance.md` is
  removed (its prose already lives in the repo README's context table).
- `cards/` keeps the **contract, the doctrine, and the template**, plus the five seeds and an
  adoption table. It stops being "where the cards live" and becomes what `contracts/` is for
  `work.yaml`.
- `registry.yaml` gains `actor:` / `card:` keys, with honest per-repo status: one adopted
  (`ECO.GOV`), five seeded, `banking-tech` unwritten.
- Adoption is each pair's act. At N=1 human that is still the same person — but in the other repo,
  as its own commit, reviewed on its own terms. The distinction is not ceremony: it is what keeps
  the boundary real when N stops being 1.
- `check_ecosystem.py` gains an obvious future check — every repo the registry marks as an actor has
  a parsing, conformant `actor.yaml`. Not implemented here; the contract lands first, as always.
- Unchanged: `actor-card/v0` is still a working shape, still enforced by nothing, still graduating to
  `contracts/` when `charter check` is built (ADR-PA-0005 Decision 6).
- Open: whether the prose half of a card (purpose, ubiquitous language, open questions) is contracted
  at all, or stays each repo's own business. Today `actor.yaml` is the contracted artifact and prose
  is optional — `ECO.GOV` keeps its own in the repo README rather than duplicating it.
