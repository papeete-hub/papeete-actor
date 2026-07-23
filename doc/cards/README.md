# Actor cards — `papeete-actor-card/v1`

The contract, the doctrine, and the template for the card every papeete-actor publishes about itself:
**what it can be asked to do, what facts it emits, what facts it pulls and what it does about them,
and whose contract it resolves.** Machine-readable contract:
[`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml). Decision records:
[ADR-PA-0005](../../adr/ADR-PA-0005-the-actor-card.md) (the shape),
[ADR-PA-0007](../../adr/ADR-PA-0007-actor-card-is-a-root-descriptor.md) (where it lives),
[ADR-PA-0009](../../adr/ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md)
(actorhood and conformance routing) and
[ADR-PA-0010](../../adr/ADR-PA-0010-offers-subscription-disposition-and-dependencies.md) (v1).

> **The cards do not live here.** A card is `papeete-actor.yaml` at the **papeete-actor's own repo root**, beside
> `work.yaml` — the repo *is* the papeete-actor's durable state (ADR-PA-0002 §1), and a card held anywhere
> else drifts from the gates and ledgers it names. This directory holds what `ECO.GOV` owns: the
> contract and the template — nothing per-actor. The same split as `work-observability/v0` versus each repo's
> `work.yaml`, and `inter-agent-message/v0` versus the messages in owner repos.

## The layer these words belong to

Everything here is **ecosystem layer** (`ECO.*`) — how papeete-actors interoperate. It is deliberately *not*
domain-layer vocabulary (`BNK.*` — capabilities, business events, aggregates). The rule from
ADR-PA-0005:

> **Domain-layer words describe what a business is. Ecosystem-layer words describe how papeete-actors
> interoperate. No word may carry different meanings at both layers — and when one is needed at both,
> the ecosystem layer yields and picks another.**

| Term | Means |
|---|---|
| **papeete-actor** | a box: one repo, one human+agent pair, one mailbox, one card |
| **card** | `papeete-actor.yaml` — the papeete-actor's self-description |
| **request** | interchange addressed to one papeete-actor, which it may refuse. `nature: query \| action` |
| **offer** | an ability a papeete-actor advertises — the door a request arrives at. The card section; `request` stays the name of the interchange itself |
| **publication** | a fact a papeete-actor emits, addressed to nobody, which no one may refuse |
| **means** | a publication's prose: what the fact **is**, and why it might concern a reader. Producer-owned |
| **shape** | a publication's payload schema. Producer-owned, required (`publication/v2`) |
| **subscription** | a papeete-actor's declaration that it pulls another papeete-actor's publication, **and what it does about it** |
| **notice** | the deterministic half of a subscription: binding, position, cadence |
| **intent** | the judged half: what this consumer does about facts like that. Consumer-owned |
| **dependency** | a papeete-actor whose contract this one resolves, and at what ref |
| **nonconformity** | what `ECO.GOV` emits about a papeete-actor's conformance — *not* a finding |

`card` is the noun; **`papeete-actor check` / `papeete-actor status`** (ADR-ECO-0005) is the verb — walk
[`registry.yaml`](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/registry.yaml), read each repo's `papeete-actor.yaml`, and validate.

## Relation to A2A

The card is an [A2A](https://a2a-protocol.org) agent card with the choreography half added:

| A2A | Here |
|---|---|
| `url` — the endpoint you call | **`mailbox`** — the binding + address you post to |
| `capabilities` (streaming, push) | **delivery semantics** — at-least-once, idempotent on `(type, subject)`, no push at Level 0 |
| `skills[]` — what you may invoke | **`offers`** — what this papeete-actor accepts, `query` or `action` |
| the return value | **`publications`** + **`subscriptions`** — the loop closes here instead |
| served at a well-known path by the agent | **`papeete-actor.yaml` at the repo root**, indexed by the registry |
| the client's own server list | **`dependencies`** — whose card I resolve, and at what ref |
| `authentication` | **`autonomy`** — Level 0: every write through a human-reviewed PR |

The A2A lineage is documented **here, in prose** — deliberately not in a field name. A card is YAML
at a repo root, not a document served over A2A, and a field called `a2a_dependencies` would claim a
protocol this ecosystem does not speak. The same reason the card names no agent framework.

**A request has no return value.** It completes as a *refusal*, or *later, as a publication the
sender may have subscribed to*. That is the whole delta from A2A, and it follows from asynchrony —
not from the handlers being agents. Accepting a request never obliges the papeete-actor to honour it: triage
is the owner's exclusive act.

**Subscriptions are declared consumer-side, never by the producer.** A producer listing its
subscribers is precisely the coupling ADR-PA-0002 Decision 4 forbids. Fan-out is derived by
*joining* publications against subscriptions across cards. Two conformance classes fall out of that
join, and are why the card is worth building rather than merely writing:

- **dangling subscription** — nobody publishes that id.
- **unsubscribed publication** — information no one pulls: dead output, or a missing consumer.

ADR-PA-0009 §5 added a third, **undeclared consumption**, and v1 adds two more that fall out of the
new fields: **unschematised publication** (no `shape:`) and **unpinned scripted subscription** (a
`then.run:` resolving to a floating ref). The full list lives in the schema's `conformance:` block.

**A subscription carries what you *do* about the fact, not only that you pull it.** `notice:` is the
deterministic half — *has anything appeared after my position?* — which must stay dumb, because if a
model decides what it has already seen, consumption stops being idempotent. `then:` is the judged
half, and it is **consumer-authored by rule**: a publication supplies *meaning*, never *intent*. In
MCP a server says what a tool **is** and never what the client should do with it; a publication
reading *"Urbanist, refine the capability when you see this"* would put a producer in charge of a
consumer's behaviour — worse coupling than the handler it replaces, because a handler at least lives
where a reviewer looks.

**Three kinds of papeete-actor read a publication, and only one of them reads prose.** An agent reads the
schema and the prose and judges; a human reads a rendering; a script parses fields and fails closed.
A producer cannot see which it has — it is forbidden from listing consumers — so it can never decide
that prose alone will serve. Hence `shape:` beside `means:`, required unconditionally
([`publication/v2`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml), ADR-PA-0011): **the schema is the floor,
the prose is the ceiling, and the human view is a rendering of the floor.**

**The card names no agent framework.** Claude Code skills, LangChain, a human with a checklist —
that is interior, and the card never moves under `.claude/` or any framework directory
(ADR-PA-0007 Decision 3). A harness swap must not touch it.

## Adoption — v0 complete, v1 migrating

Every tier adopted a v0 card, in its own repo, as its own commit (2026-07-20). `ECO.GOV` is
read-only over every other repo, so it could not place them; each arrived as a PR its pair reviewed.
The same is true of the v1 migration: what `ECO.GOV` can do is file the issue.

| Papeete-actor | Repo | v0 card (on disk today) | migration to `papeete-actor-card/v1` |
|-------|------|---------|--------------|
| `ECO.GOV` | `ecosystem-governance` | ✅ [`papeete-actor.yaml`](../../papeete-actor.yaml) | ✅ with the contract |
| `BNK.GOV` | `banking-governance` | ✅ `actor.yaml` | ⏳ [#6](https://github.com/papeete-foundry/banking-governance/issues/6) — small: 3 empty logs, 2 ad-hoc fields to fold |
| `BNK.KNOW` | `banking-knowledge` | ✅ `actor.yaml` | ⏳ [#7](https://github.com/papeete-foundry/banking-knowledge/issues/7) — owes 2 `shape:`, 12 records grandfathered |
| `BNK.RLVR` | `reliever-business` | ✅ `actor.yaml` | ⏳ [#28](https://github.com/papeete-foundry/reliever-business/issues/28) — owes 1 `shape:`, 4 subscriptions to split |
| `BNK.RSOL` | `reliever-design` | ✅ `actor.yaml` | ⏳ [#24](https://github.com/papeete-foundry/reliever-design/issues/24) — **rehome the authority-boundary prose** |
| *(no id)* | `reliever-implementation` | ✅ `actor.yaml` | ⏳ [#18](https://github.com/papeete-foundry/reliever-implementation/issues/18) — largest debt, owes 2 `shape:` |
| `BNK.TECH` | `banking-tech` | ⏳ pending ([#3](https://github.com/papeete-foundry/banking-tech/pull/3)) | ⏳ [#4](https://github.com/papeete-foundry/banking-tech/issues/4) — may adopt at v1 directly, skipping v0 |
| — | `settler` | ✗ none | **three cards depend on `settler/work-pipeline`** — [#13](https://github.com/papeete-foundry/ecosystem-governance/issues/13) |
| — | `kledger` | ✗ none | appliance; actorhood undecided |

Write a new card from [`TEMPLATE.md`](./TEMPLATE.md); migrate an existing one with the checklist at
the end of the same file. A v0 card is **unmigrated, not non-conformant** — `lint_card.py` reports it
as such rather than failing it, because adoption is each pair's own act.

### What adoption taught — verify, never transcribe

The five seeds drafted here on 2026-07-20 are **deleted**; the pattern is not repeated. Their prose
was marked as reasoning-not-contract and their `(inferred)`/`(open)` markers were used honestly, but
**their YAML front-matter read as settled fact and was trusted as such** — and one seed was wrong.
`card-governance.md` declared a `method-policy` publication over `ADR-GCM-URBA-0002` and `-0005`:
the first had been handed to `BNK.KNOW` and lives there as `ADR-KCM-URBA-0002`, the second never
existed. Governance spent a day advertising authority over a standard it had given away
([#10](https://github.com/papeete-foundry/ecosystem-governance/issues/10)).

> **A card is written by reading the repo, not by transcribing a draft.** Every claim — gates,
> ledgers, pins, publications — is checked in place. `banking-tech` adopted with no seed at all and
> hit none of this.

The other lesson runs the opposite way: **adoption is where the interior leaks in.** Every one of
the five adoptions initially expanded `gates:` into an inventory of `tools/*.py`. All five have since
trimmed it back to the bookends — the output gate and the input gate, and nothing else. What runs
inside the box is decoration; a consumer must not be able to tell which internal validators exist
(AGENT-OPERATING-MODEL §4). The seeds were doctrinally right here and the first adoptions regressed.

## Status

`papeete-actor-card/v1` **has graduated** to [`../contracts/`](../../src/papeete_actor/schemas/): there is a schema
([`papeete-actor-card.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml)) and a checker
([`papeete-actor lint-card`](https://github.com/papeete-hub/papeete-actor)) that loads it rather than hard-coding its fields — the
path `inter-agent-message/v0` took (ADR-PA-0004). v0's status line said *"nothing validates these
files and nothing depends on them"*, and that is no longer true of a single card.

**It is still true of the join.** `lint_card.py` validates ONE card against the schema. The
cross-card conformance classes — dangling subscription, unsubscribed publication, undeclared
consumption — need `papeete-actor check`, which does not exist. Every figure quoted in `ECO.GOV`'s own card
is hand-computed, and that remains `ECO.GOV`'s standing nonconformity (#10.5).

Where a card states something the storming settled, it says so plainly. Where it states something
derived from doctrine rather than decided, it is marked **(inferred)**; real questions are marked
**(open)** and are the next agenda.
