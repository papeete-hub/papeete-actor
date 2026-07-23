---
id: ADR-PA-0005
title: "The actor card — discovery for a choreographed ecosystem, and the words it is written in"
status: Proposed
date: 2026-07-20
supersedes: [ADR-ECO-0010]     # §2 (the nomenclature) and §3–6 (the card). §1's layer rule stays
                               # in ecosystem-governance as ADR-ECO-0020.
references:
  - ../doc/cards/README.md
  - ../doc/cards/TEMPLATE.md
  - ../src/papeete_actor/schemas/papeete-actor-card.schema.yaml
  - ./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md
  - ./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md
  - ./ADR-PA-0013-papeete-actor-the-term.md
---

# ADR-PA-0005 — The actor card

> **Split out of `ADR-ECO-0010`** (2026-07-20, `papeete-foundry/ecosystem-governance`), which held
> two decisions in one file: a two-layer *vocabulary rule* and the *actor card*. The rule governs
> all naming in the ecosystem and stays there as
> [`ADR-ECO-0020`](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0020-the-two-layer-vocabulary-rule.md);
> the card and the words it is written in are this repo's, and are here. Dates are unchanged —
> both records describe what was decided on 2026-07-20. Citations to `ADR-ECO-0010` about the
> card refer to this record; citations about the layer rule refer to `ADR-ECO-0020`.

## Context

The 2026-07-20 event storming asked what information each tier of the software factory produces,
and the first attempt at writing that down surfaced a missing half.

**The A2A analogy exposed it.** An [A2A](https://a2a-protocol.org) agent card describes what an
agent can be *asked* to do, because in a synchronous world the caller already knows whom to call —
there is nothing to discover about production, and the loop closes with a return value. This
ecosystem is choreographed by construction (orchestration inside the box, choreography between
boxes). Here, *who produces what* is exactly what needs discovering, because a consumer must find
its upstream before it can pin it. A descriptor carrying only the request half is missing the half
this ecosystem runs on.

At the time there was no mechanism at all for the downstream direction. The rails routed addressed
traffic upstream and that worked; a consumer learned who publishes what, and that a new ref existed,
only by someone remembering to say so.

## Decision

**1. The nomenclature.** Each term is justified by a demonstrated collision, and a term that cannot
name its collision is not minted:

| Term | Means | Not, because |
|---|---|---|
| **papeete-actor** | a box: one repo, one human+agent pair, one mailbox, one card | not *bounded context* — that is domain-layer, strategic-DDD. Named `actor` until [ADR-PA-0013](./ADR-PA-0013-papeete-actor-the-term.md) made it particular |
| **card** | the descriptor an actor publishes about itself | — |
| **request** | interchange addressed to one actor, which that actor may refuse. Two natures: `query` (return information) and `action` (decide or do) | not *command* — that is the design tier's aggregate vocabulary (`aggregate, command, policy, read-model`) |
| **publication** | a fact an actor emits, addressed to nobody, which no one may refuse | not *event* — business events are corpus content in `BNK.RLVR` |
| **subscription** | an actor's declaration that it pulls another actor's publication | — |
| **nonconformity** | what a conformance supervisor emits about an actor's conformance | not *finding* — a finding rides a domain rail to a decision owner and triages into a kanban; a nonconformity is an audit verdict, different producer, lifecycle and reader |

Unchanged, because they were already correct: `contract`, `envelope`, `payload`, `binding`,
`registry`, `pin`, `org`, `repo`, `role`, `edge`.

Note for storming sessions: the event-storming "actor" sticky — a human persona — is called a
**persona**, so that *actor* keeps the actor-model sense above. That rename is what made the word
available, and it must not be undone.

**2. The card, with three parallel sections** (four since
[ADR-PA-0010](./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md)):

- **`offers`** — what this actor accepts, with `nature: query | action`. Accepting a request never
  obliges the actor to honour it; triage remains the owner's exclusive act.
- **`publications`** — facts this actor emits. Published, never delivered: the record *is* the event.
- **`subscriptions`** — what this actor pulls, **declared consumer-side**.

**3. Subscriptions are declared by the consumer, never by the producer.** A producer that listed its
subscribers would be exactly the coupling the operating model forbids
([ADR-PA-0002](./ADR-PA-0002-agent-bounded-context-operating-model.md) Decision 4). The ecosystem's
fan-out is derived by *joining* the two sides across cards — subscription as data, never publisher
knowledge of consumers.

**4. A request has no return value.** It completes as a **refusal**, or **later, as a publication the
sender may have subscribed to**. This is the one real delta from A2A, and it follows from asynchrony,
not from the handlers being agents. It is also what makes the card whole: the card closes with a
subscription the loop A2A closes with a return value.

**5. The card is checkable, and that is why it is worth building rather than merely writing.**
Joining publications against subscriptions yields conformance classes no human review produces
reliably — a **dangling subscription** (nobody publishes that id) and an **unsubscribed
publication** (information no one pulls: dead output, or a missing consumer).

## Rationale

The nomenclature is *derived*, not invented: the vocabulary (`contract`, `envelope`, `binding`,
`registry`, `pin`) already existed, and so did the actor model in the doctrine. What was missing was
the declaration that these are one layer's words, plus the rule keeping the next word out of the
wrong layer — which is `ADR-ECO-0020`, and stays with the ecosystem because it governs all naming
and not only actors.

Choosing *actor* over *participant* kept the model honest about what it inherited: mailboxes,
at-least-once delivery, idempotency on an envelope identity, and one address per box are actor-model
properties this ecosystem already relies on.

## Consequences

- Cards are authored per repo, at the repo root, by each pair
  ([ADR-PA-0007](./ADR-PA-0007-actor-card-is-a-root-descriptor.md)).
- Two conformance classes become implementable, and the join that computes them ships in this
  package (`papeete-actor check`).
- **Three holes were made legible, none of them new:** no rail addressed governance or knowledge;
  no `query`-nature request existed anywhere; and almost no subscription was declared.
- The card graduated to a machine-readable contract with a checker
  ([ADR-PA-0010](./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md),
  [ADR-PA-0012](./ADR-PA-0012-papeete-actor-the-gates-as-a-distributed-tool.md)), which is the path
  `inter-agent-message/v0` took.
