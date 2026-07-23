---
id: ADR-PA-0013
title: "papeete-actor — the ecosystem's actor is a particular construct, and is named as one"
status: Proposed
date: 2026-07-23
supersedes: [ADR-PA-0005]      # §2 (the term `actor`) and §5 (`charter` as the verb) only
references:             # canonical sources where this decision is implemented (link, don't restate)
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml   # the contract, renamed
  - ../cards/README.md                            # the doctrine and the vocabulary table
  - ../registry.yaml                              # the `papeete_actor:` key, papeete-hub/papeete-actor
  - ../../papeete-actor.yaml                      # ECO.GOV's own card, at the new name
  - ./ADR-PA-0005-the-actor-card.md
  - ./ADR-PA-0012-papeete-actor-the-gates-as-a-distributed-tool.md
---

# ADR-PA-0013 — `papeete-actor`

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0018`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0018` elsewhere in the ecosystem refer to this record.

## Context

[ADR-PA-0005](./ADR-PA-0005-the-actor-card.md) §2 minted **`actor`** as the
ecosystem-layer noun for a box: one repo, one human+agent pair, one mailbox, one card. The word was
chosen well — it was already this repo's own, and it carries the actor-model inheritance the whole
operating model rests on (AGENT-OPERATING-MODEL §3).

It is also a generic word. The actor model has actors, A2A has agents, event storming has actors —
0010 had to move that last one aside, renaming the sticky to **persona**, precisely so `actor` could
carry the sense the cards use. What this ecosystem means by it is much narrower than any of them,
and is about to get narrower still: a 2026-07-23 modelling session added five facets no generic
actor has — a context of execution, the artefacts it produces, the qualified information it
exchanges, the knowledge base it decides from, and gates that *enrich* rather than merely refuse.
Those facets are not decided here (see §4), but they are why the name matters now.

A second thing was wrong in the same record. §5 minted **`charter`** as the ecosystem-layer verb —
in the same document whose §1 forbids exactly that move.

## Decision

**1. The ecosystem-layer noun is `papeete-actor`.**

> A **papeete-actor** is one repo, one human+agent pair, durable state others depend on, and an
> address that can receive a request.

The actorhood test of [ADR-PA-0009](./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md)
§1 is unchanged in substance; it is now the test for **papeete-actorhood**. What changes is the name
and what the name asserts.

The rename carries through every surface that names the construct:

| | was | is |
|---|---|---|
| the noun | `actor` | **`papeete-actor`** |
| the card | `actor.yaml` | **`papeete-actor.yaml`** |
| the contract | `actor-card/v1` | **`papeete-actor-card/v1`** |
| the schema | `contracts/actor-card.schema.yaml` | **`contracts/papeete-actor-card.schema.yaml`** — and one day later it left this repo entirely (ADR-ECO-0019) |
| the registry key | `actor:` | **`papeete_actor:`** |
| the gates | `charter` | **`papeete-actor`** (§3) |

**`actor-card/v0` is not renamed.** Six repos declare that string literally today. Renaming it in
this record would name a contract that never existed, and the honest migration is `actor-card/v0` →
`papeete-actor-card/v1` — one hop, which is the one those six repos already owe.

**The version stays at `v1`.** The shape is untouched; only the identity moved.
`papeete-actor-card/v1` is a new contract name carrying `actor-card/v1`'s shape, and saying so is
cheaper than a v2 that would imply a shape change and cost the six pairs a second migration.

**2. This is an act of definition, not a conformance fix — and the difference is load-bearing.**

`actor` collides with nothing. §1's layer rule does **not** compel this rename, and claiming it did
would be false in a record whose own doctrine is built on naming the collision that justifies a term
(0010 §2: *"a term that cannot name its collision should not be minted"*).

The justification is the other direction. The generic word understates a particular construct, and
the construct is about to acquire facets that make it unmistakably particular. Naming it
`papeete-actor` is the assertion that **this is a specific thing with a specific shape**, not an
instance of a general pattern — and it is the anchor the template of §4 is built against.

**3. `charter` is retired, and that half IS a conformance fix.**

§1 of 0010 states: *"No word may carry different meanings at both layers — and when one is needed at
both, the ecosystem layer yields and picks another."* `charter` carries five domain-layer senses,
every one of them predating the tool:

| Sense | Where |
|---|---|
| a **task type** in the work vocabulary (`charter \| asset \| map`) | `reliever-business/CLAUDE.md`, its skills, `work-pipeline.vendor.yaml`; parameterised into `settler/templates/work-pipeline` as `<WORK_TASK_TYPES>` |
| **"ADR governance charter"** | `adr/README.md` in `banking-governance`, `banking-knowledge`, `banking-tech`, + two settler templates |
| **"domain charter"** | `banking-knowledge/domain-vision/domain.md` |
| **"context charter"** | `reliever-design/adr/ADR-DSN-0001-solution-context-charter.md`, `ADR-GCM-URBA-0006` |
| **"chartered by"**, as a verb | `AGENT-OPERATING-MODEL.md` §2, `ADR-PA-0002`, `ADR-ECO-0007` — *inside this repo* |

So **ADR-PA-0005 contradicts itself**: §5 mints at the ecosystem layer a word §1 requires the
ecosystem layer to yield. The tool takes the name of the thing it validates —
[`papeete-actor`](./ADR-PA-0012-papeete-actor-the-gates-as-a-distributed-tool.md), distributed as
`papeete-actor` on PyPI, importing as `papeete_actor` because Python forbids the hyphen. That
collapses 0010 §5's noun/verb split, which is the point: there is one word now, and it names the
construct, its card, its contract and its gate.

**4. What this does not decide.** The five facets are named here as the reason the term must be
particular. They are **not** contracted: each collides with standing doctrine — execution context
against harness-independence (ADR-PA-0007 §3), enriching gates against *refuse-don't-repair*
(AGENT-OPERATING-MODEL §4), and the granularity question (are `e2e test builder` and `e2e Tester`,
which differ only by execution context, two papeete-actors?) against *one repo, one actor*
(ADR-PA-0007 §2). A successor ADR decides them. Naming the term first is what gives that ADR
something to extend rather than something to invent.

## Rationale

Renaming a core noun is normally a bad trade, and it is a good one here for a reason that expires:
**the contract this touches is barely adopted.** One card of seven is on `actor-card/v1` — ECO.GOV's
own — and the other six already carry an open migration issue asking their pair to touch the card.
Folding the rename into a migration those repos already owe costs one edit instead of two. In a
month, when six repos have migrated, the same decision costs six more migrations. The window is now,
and it is the only reason to do this before the facets rather than with them.

The alternative — keep `actor` and let the template's name carry the particularity — was rejected
because it puts the specificity in the artifact rather than in the vocabulary. The word is what
appears in every card, every ADR and every conversation; a template nobody reads daily cannot do
that work.

## Consequences

- **`ECO.GOV`'s own card moves** to `papeete-actor.yaml` and declares `papeete-actor-card/v1`. The
  contract, template, doctrine, registry and gates follow in the same commit.
- **The six open migration issues are rewritten** to target `papeete-actor-card/v1` and the file
  rename — one migration, not two. `ECO.GOV` files them and never places them (ADR-PA-0007 §6).
- **ADR-PA-0005 §2 and §5 are superseded**; §1, §3, §4 and §6 stand. 0010, 0012 and 0014 keep their
  text and carry a banner pointing here — this log records what was decided when, and amending a
  past record to speak today's vocabulary would destroy exactly the fact it exists to hold.
- **`papeete-hub/charter` becomes `papeete-hub/papeete-actor`**, and the PyPI name becomes
  `papeete-actor`. Nothing has been published under the old name, so there is no deprecation window
  and no consumer migration — the one piece of luck in the timing.
- **The org name is now in the core vocabulary.** Accepted deliberately, and worth recording as a
  cost rather than discovering later: this org has renamed itself before (`TOPOLOGY.md` records
  `papeete-hubplace` → `papeete-hub`), and every card in every client repo will carry `papeete-`
  from here. The trade is that the word now says whose construct it is, which is the entire point.
- **Unchanged:** `persona` (0010's storming term — moving it again would undo the move that made
  room for `actor` in the first place), `BNK.*` / `ECO.*` ids, and the sibling contracts
  `inter-agent-message/v0`, `publication/v2` and `work-observability/v0`, none of which are about
  actorhood.
- Not decided: the five facets, and whether the template that stamps a papeete-actor is a new
  `papeete-hub` repo, an extension of `settler/templates`, or a subcommand of the gate tool.
