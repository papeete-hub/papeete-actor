# Agent operating model — bounded contexts as human + agent pairs

How the ecosystem's agents are organized: which contexts exist, what an agent "box" is, how boxes
talk, and who decides what. Captured from the 2026-07-09/10 design dialogue; the decision record is
[ADR-PA-0002](../adr/ADR-PA-0002-agent-bounded-context-operating-model.md).

## 1. The principle: bounded contexts = human + agent pairs

A bounded context is a boundary within which a model and its language are consistent, owned by one
team. Swap "team" for **human + agent pair** and you have this ecosystem's unit of organization.
Each context owns a model, a ubiquitous language, and **exactly one repo — the repo is the papeete-actor's
durable state**.

The core principle, and the reason repo boundaries matter more here than under plain Conway's law:

> **boundary of knowledge = boundary of responsibility = boundary of context window.**

Repo boundaries are context-window engineering for LLM agents. An agent hydrates its context from
its own repo; what is outside the repo arrives only as a typed message. This is not an analogy to
strategic DDD — it *is* strategic DDD: the kpack envelope is an Open Host Service with a Published
Language, the membrane bookends (§4) are Anti-Corruption Layers, and the findings rail (§6) is the
feedback half of a Customer–Supplier relationship.

## 2. The context set

Three product-line contexts plus the two that already exist physically:

| Context | Agent | Human role(s) | Repo | Strategic class |
|---------|-------|---------------|------|-----------------|
| Business | "Urbanist" | lead BA + architect | `reliever-business` | core domain |
| Solution | "Designer" | BA + lead dev | `reliever-design` | supporting — the functional/engineering pivot |
| Implementation | "Builder" | lead dev | `reliever-implementation` | where software runs |
| Platform | *(none yet — human-operated)* | architect/ops | `banking-tech` | supporting substrate (`BNK.TECH`) |
| Governance | *(none yet — human-operated)* | architect | `banking-governance` | upstream published policy (`BNK.GOV`) |

### Business — "the Urbanist" · `reliever-business`

- **Purpose:** decide WHAT the IS is — capabilities, events, objects — and WHY (ADRs).
- **Language:** capability, zone, business event, carrier, subscription, FUNC/URBA, Accepted.
- **Inbound:** domain/strategy sessions (human); `FunctionalGapFound` (from Implementation —
  [reliever-business #1](https://github.com/papeete-foundry/reliever-business/issues/1)).
- **Outbound:** kpack envelopes (OHS/PL); `DecisionRatified` (the
  [`notify-settler`](https://github.com/papeete-foundry/reliever-business/blob/main/.github/workflows/notify-settler.yml) dispatch already
  emits this); corpus tags.
- **Membrane gates:** SHACL (`validate_ontology.py`), semantic review, the Accepted-ADR rule.
- **Verified by:** coverage report stages 1–4, ADR maturity histogram.

### Solution — "the Designer" · `reliever-design`

Founded and chartered by its own ADR-DSN-0001: context `BNK.RSOL` (`kind: solution`, refines
`BNK.RLVR` in the `banking-governance` registry). New product lines get this context scaffolded by
`settler found` from `templates/solution-repo`.

- **Purpose:** shape HOW capabilities are contracted — aggregates, commands, APIs, schemas. The
  mixed BA + lead-dev zone.
- **Language:** aggregate, command, policy, read-model, bus topology, contract, schema.
- **Inbound:** `CapabilityReadyForDesign` (corpus tag + FUNC/TACT accepted);
  `ContractDeviationFound` (from Implementation).
- **Outbound:** kontract envelopes (OHS/PL — see §7); design-level findings upstream to Business.
- **Membrane gates:** `validate_process`, JSON-Schema validation, mandatory `.bcm-provenance.json` pin.
- **Verified by:** process coverage, reconciliation-queue emptiness.

### Implementation — "the Builder" · `reliever-implementation`

- **Purpose:** turn published contracts into running, tested, deployed services.
- **Language:** task, branch, service, test, deploy, incident.
- **Inbound:** `ContractPublished` (via kontract, Stage-0 gate).
- **Outbound:** the three finding types (§6), routed by decision ownership; release events.
- **Membrane gates:** CI, Stage-0 readiness, test suites.
- **Interior (not contract):** `/roadmap`, `/task` as orchestration, `/launch-task` as
  orchestrator-workers, code review as evaluator.

### Platform · `banking-tech` and Governance · `banking-governance`

Already exist as repos and kpack contexts (`BNK.TECH`, `BNK.GOV`); no dedicated agent yet —
human-operated, same membrane discipline (SHACL gates, `notify-settler` dispatch, kpack serving).
Platform supplies the runtime substrate (TECH-STRAT platform delegations pin it); Governance is
upstream of everyone as published policy. Their canvases fill in when an agent is assigned.

### Planning is an interior module of Implementation, not a context

Its owned state is coordination state that must stay consistent with Implementation's branches; its
outputs are consumed by exactly one context, in that context's cadence. **A context that talks to
only one neighbour, in that neighbour's rhythm, with no distinct owned state, is a module.**
Promotion signals (any one justifies graduating it): language drift, cadence conflict, ownership
conflict, coordination across multiple implementation repos, or planning artifacts needing their own
review gate.

Also deliberately **not** contexts: Verification/Review (validators and reviewers are stateless pure
functions — membrane equipment); Operations/Run is plausible later, but only once something runs.

## 3. Why this shape: distributed computing with nondeterministic nodes

The whole model is the actor model — service boundaries, mailboxes, at-least-once delivery — with
exactly one new variable: **the nodes are nondeterministic**. Every agent pattern below (routing,
bookends, evaluator-optimizer) is a compensation for probabilistic handlers; the forty years of
distributed-systems lessons carry over intact, plus one new layer of gates.

## 4. The fat-agent box

**The external contract is the architecture; interior patterns are decoration that must never
leak.** Nobody consuming the Designer's contract should be able to tell whether the answer came from
one model call or an orchestrator fanning out twelve workers. The moment interior patterns leak into
the contract, you have rebuilt the distributed monolith — agents coupled to each other's internals.

```
            ┌──────────────────────── the box ────────────────────────┐
 mailbox ──▶ input bookend ──▶ router ──▶ orchestrator ──▶ workers (∥) │
 (typed,    (deterministic     (which     (deterministic   (agents)    │
  durable)   validation,        interior   control flow)      │        │
             cheap triage)      workflow?)                    ▼        │
                                              evaluator-optimizer loop │
                                                              │        │
             output bookend ◀─────────────────────────────────┘        │
             (schema gate, validators, refuse-don't-repair)            │
            └──────────────────────────────────────────────▶ emits events
```

- **Bookends are the membrane** — deterministic code at both ends. Input side: validate the
  message, hydrate context from the repo, triage cheaply (most messages shouldn't wake the expensive
  machinery). Output side: schema-gate, run the tier's validators (SHACL / `validate_process`,
  generalized), and **refuse rather than repair** — a rejected output loops back through the
  evaluator; it never crosses the boundary dirty.
- **Interior patterns** — routing, orchestrator-workers, parallelization, evaluator-optimizer —
  live strictly inside.
- **Rule of combination: orchestration inside the box, choreography between boxes.** Within one
  papeete-actor a deterministic workflow engine driving parallel workers is right — you own the state.
  Between papeete-actors, events and eventual consistency — you don't own their state, so you don't get to
  orchestrate them. (The stack already obeys this: `urbanist-workflow` orchestrates within a
  session; repos coordinate through issues and dispatch events.)

## 5. Messaging

**Design-time mailboxes are GitHub issues + `repository_dispatch` + git-append logs.** No broker
until volume justifies one — the discipline matters, not the infrastructure.

Messages are **fat events** (event-carried state transfer): capability id, `bcm_ref`, evidence,
reconcile-by — never "see my previous message". The distributed-computing inheritance is adopted
deliberately, not by accident:

| Inherited pattern | Here |
|-------------------|------|
| Idempotent handling | redelivery must be safe; pinned refs + single-writer repos give most of it |
| Circuit breakers | budgets — token spend is the timeout |
| Dead-letter queue | a finding nobody ingests; the coverage report's reconciliation view (§6) |
| Traces | agent transcripts |

### A message is not its transport

The mailbox is GitHub issues *today*; the **message** is a first-class thing independent of it. An
**inter-agent message** is an *envelope* — its `(type, subject)` identity plus the marker that
declares "this is a message" — wrapping a *payload* (a finding) over a *binding* (a GitHub issue now,
another medium later). The rule every agent applies: **an artifact is a message iff it carries the
envelope.** A repo's own local issues carry none, so they are not messages and no agent treats them
as one. Messages are **rendered, never hand-authored** (`render_message.py`) and **gated on the
envelope** in the recipient's CI (`lint_message.py`) — so a message that dropped its envelope fails
rather than passing as noise. Contract: [`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml);
doctrine: [`INTER-AGENT-MESSAGES.md`](./INTER-AGENT-MESSAGES.md) (ADR-PA-0004). Switching transport
later is a new *binding*, not a new message — which is the whole reason to name it.

### The direction rule: addressed upstream, published downstream

The anti-coupling rule for every edge:

- **Findings/requests flow upstream, addressed** to the decision owner. Downstream may know
  upstream — that is the Customer–Supplier direction.
- **Events flow downstream, published — never delivered.** The publisher writes only to its own
  repo: the tag/release IS the event; an append-only `events/` log committed atomically with the
  change is a transactional outbox. Consumers subscribe by pulling on their own cadence (scheduled
  agents checking their pinned ref for staleness). **A publisher must never open issues in consumer
  repos.** If push is ever needed, fan-out is driven by the ecosystem registry (subscriptions as
  data), never by publisher knowledge of consumers.

The outbox is contracted as `publication/v0`
([`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml), ADR-PA-0006): one file
per fact under `events/{publication}/{ref}.yaml`, committed **in the same commit as the change it
describes**, ordered by git rather than by a sequence field. A publication is a **sibling** of the
inter-agent message, not a binding of it — one binding per direction: `github-issue` carries
requests, `event-log` carries facts.

Honest current state:
[`notify-settler.yml`](https://github.com/papeete-foundry/reliever-business/blob/main/.github/workflows/notify-settler.yml) is hardcoded
point-to-point to one subscriber — acceptable at N=1 consumers, must become registry-driven at N=2.
ADR-PA-0006 dissolves rather than fixes this: once settler subscribes by reading the log, pull *is*
the fan-out mechanism at any N. No log is written yet.

### Meaning, intent, and where behaviour lives

Classic event-driven design puts a **handler** at every edge: the consumer writes `on(X): do Y`,
against a schema, having anticipated the event. Two things are wrong with that here. Wiring cost is
O(publications × consumers) and every pair must be foreseen — and the *meaning* of the fact, why it
exists and who should worry about it, lives in neither the schema nor the handler. It sits in a wiki,
or in the head of whoever wrote the handler.

The publications already written point at the alternative. `ApplicationStubbed` declares itself as
*"a disclosure of construction under knowledge scarcity, **addressed to whoever would otherwise
mistake this papeete-actor's invention for a decision**"*. That closing clause is a **self-selection test**:
any reader applies it to itself and gets a yes or no, and it names nobody — which is how fan-out
happens without a producer knowing its consumers. It is a prompt, not a type.

So the split, which `papeete-actor-card/v1` makes structural:

> **The producer supplies meaning. The consumer declares intent. Behaviour is proposed, never
> contracted.**

| | who may author it | why only them |
|---|---|---|
| **meaning** — `publications[].means` | the producer | only they know why they emitted it, and under what duress |
| **intent** — `subscriptions[].then` | the consumer | it is their behaviour, in their repo, under their review |
| **behaviour** — whatever actually runs | the actor running it | it is local and revisable, and binds nobody else |

**The line that must not be crossed:** a publication reading *"Urbanist, refine the capability when
you see this"* would put a producer in charge of a consumer's behaviour. This is
[MCP](https://modelcontextprotocol.io)'s rule applied to facts instead of tools: a server says what a
tool **is**, never what the client should do with it. Meaning is producer-owned; the decision to act
is consumer-owned.

**A handler is not forbidden — it is simply not the contract.** `then.run:` names a script, and that
is a handler by any honest reading. What a consumer runs may be a handler, a poll, an agent reading
the prose, or a human with a checklist; the model does not rule on it, and a contract that did would
be dictating an implementation. What behaviour may never be is the *only* record of the edge.

**Because the declaration must survive.** Wiring cost falls to O(publications) — it must not fall to
zero. If dispatch becomes wholly semantic ("the agent will notice what's relevant"), there is nothing
left for `papeete-actor check` to join, and every conformance class in ADR-PA-0009 §5 evaporates.
Drop the wiring; keep the declaration. The declaration was never the heavy part.

### Determinism sits at existence, never at interpretation

The membrane rule of §4, applied to consumption. Two questions, opposite answers:

- **"Has anything appeared after my position?"** — cheap deterministically, unreliable from a model.
  If a model decides whether it has already seen a record, consumption stops being idempotent and
  facts are silently lost or replayed. This one must stay dumb.
- **"Does this fact matter to my capability?"** — irreducibly judgement. It depends on the corpus, on
  what has been decided, on whether the missing information was ever anyone's to decide. No detector
  computes it.

Hence a subscription has two blocks rather than one: `notice:` (deterministic by rule) and `then:`
(judged, or scripted, or both — where `run:` is the input bookend and `intent:` reasons over what it
produced). Naming a script in `then.run:` is **not** an interior leak: a subscription's reaction *is*
the bookend, which §4 places at the membrane. What §4 forbids is expanding `gates:` into an inventory
of interior validators.

### Three kinds of consumer, one contract

A papeete-actor's counterpart may be another agent, a **human** (`agent: none` — three papeete-actors today), or a
**deterministic script**. Prose serves only the first, and **a producer cannot see which it has**:
subscriptions are declared consumer-side and listing consumers is forbidden. So it can never decide
that prose alone will serve.

> **The schema is the floor, the prose is the ceiling, and the human view is a rendering of the
> floor.**

That is why `publication/v2` requires a payload `shape` unconditionally, beside the `means` prose,
and adds `bindings.human-view` — rendered from the schema, never hand-authored, because you cannot
deterministically render from prose. The shape was already proven one layer down:
`inter-agent-message/v0` carries one payload plus bindings-as-projections, with `render_message.py`
generating the human-facing issue. Publications simply never got the same treatment.

## 6. The findings rail

Findings flow upstream to the tier that **owns the decision**, with provenance; coordination state
stays downstream.

| Finding type | Routed to | Becomes |
|--------------|-----------|---------|
| `functional-gap` | Business | issue → ADR candidate |
| `contract-deviation` | Solution | reconciliation item |
| `engineering-debt` | Implementation | stays home |

Ground truth for the routing rule:
[reliever-business #1](https://github.com/papeete-foundry/reliever-business/issues/1) (functional
gap — right door) vs [#2](https://github.com/papeete-foundry/reliever-business/issues/2) (kpack
plumbing regression — wrong door: engineering, not a Business decision). The coverage report's
"awaiting reconciliation" view is the dead-letter queue / supervision surface.

How a finding is detected, routed, and triaged into a repo's work state is contracted in
[`WORK-OBSERVABILITY.md`](./WORK-OBSERVABILITY.md) (ADR-PA-0003): gates write structured
detection entries, routing travels this rail as **rendered inter-agent messages** (§5 — the finding
is the payload, the labeled issue one binding), and triage into the kanban is the owner's exclusive
act. The rail label above is a message's *rail*, not what makes it a message — the envelope is
(§5).

## 7. Serving contracts — two surfaces, one transport

One shared transport (kpack's address book + courier: `config` / `registry` / `remote`), one fetch
surface per knowledge tier:

- **`kpack`** — the corpus tier ([`papeete-hub/kpack`](https://github.com/papeete-hub/kpack)).
- **`kontract`** *(planned)* — the process/design tier, served from Solution.

**Reuse boundary: transport modules only, never the corpus knowledge engine.** The
[`tools/index/bundles.yaml`](https://github.com/papeete-foundry/reliever-business/blob/main/tools/index/bundles.yaml) MCP-style bundle
contracts are the same discipline at the tool surface.

## 8. Tasks live in git

Tasks here are agent-operated work orders with provenance (`bcm_ref`, caller ids, kanban
worktrees). Git gives atomic task+code+finding commits, pinnable state, and no API friction. A
tracker (YouTrack et al.) enters only if a *human-coordination* problem appears — and then only for
coordination state, **never as the store of record for findings** (§6: findings live in the
decision owner's repo).

The layout and lifecycle of the in-git work state — `work.yaml`, detection ledgers, the
`tasks/` + `BOARD.md` kanban — are contracted ecosystem-wide in
[`WORK-OBSERVABILITY.md`](./WORK-OBSERVABILITY.md) (ADR-PA-0003).

## 9. Autonomy ladder

**Level 0 — now: every agent write is reviewed through a PR by a human. No exceptions.** Higher
levels arrive only via explicit harness/scripts once the shapes are understood. Each context's card
states its autonomy line: what its agent may do alone vs must escalate (e.g. may the Designer
publish an additive contract revision if all gates pass? may the Builder self-approve a deviation
it marked provisional fail-closed?). Until a card says otherwise, the answer is: escalate.

## 10. The agent card

One page per box that *is* its contract:

| Field | Meaning |
|-------|---------|
| Role | which context, core/supporting |
| Owned state | the repo — `records` |
| `offers` | what it may be asked to do (`query` / `action`); the caller reasons, it may refuse |
| `publications` | facts it emits — `means` (the prose) **and** `shape` (the payload schema), always both |
| `subscriptions` | facts it pulls — `notice` (deterministic) and `then` (what it does about them) |
| `dependencies` | whose contract it resolves, and at what ref |
| Membrane gates | what the bookends validate |
| Work surface | its `work.yaml`: detection ledgers + kanban — how it reports and consumes findings ([WORK-OBSERVABILITY](./WORK-OBSERVABILITY.md)) |
| Budget | token/time circuit breaker |
| Eval set | golden messages — the contract's test suite for a nondeterministic node; version-pinned prompts/skills are its binary |
| Human role | who pairs with the agent, which decisions are theirs |
| Autonomy line | what the agent does alone vs escalates (Level 0: nothing alone) |

A schema validates the *shape* of an agent's output, not its judgment — the eval set is the CI of a
nondeterministic node, run whenever the box's prompts or skills change. The existing skills + hooks
+ CLAUDE.md files are already the *implementation* of two or three of these boxes; the card is what
makes them peers in a system rather than tools in a toolbox.
