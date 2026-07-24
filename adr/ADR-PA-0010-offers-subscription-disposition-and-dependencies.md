---
id: ADR-PA-0010
title: "papeete-actor-card/v1 — offers, subscription disposition, and dependencies"
status: Proposed
date: 2026-07-22
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml
  - ../cards/TEMPLATE.md
  - ../cards/README.md
  - ../AGENT-OPERATING-MODEL.md      # §5 — meaning/intent, determinism at existence
  - ./ADR-PA-0005-the-actor-card.md
  - ./ADR-PA-0009-actorhood-terminal-tiers-and-conformance-routing.md
  - ./ADR-PA-0011-publication-payload-schema-and-human-view.md
---

# ADR-PA-0010 — `papeete-actor-card/v1`

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0015`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0015` elsewhere in the ecosystem refer to this record.

## Context

`actor-card/v0` was adopted across seven repos on 2026-07-20. Reading all seven **live cards** —
rather than the template — surfaced three defects and one absence.

**1. `subscriptions[].how` holds two different kinds of thing.** In `banking-tech` it is a transport
(`ontology/model/vendor.yaml + tools/check_vendor_sync.py`); in `reliever-design` it is a behaviour
(`UNMODELED_CAPABILITY detector → views/findings-corpus.yaml`). Both readings are defensible against
v0, which is the problem. And neither says what the papeete-actor *does* about a fact once it has it.

**2. `requests_out` declares an edge that is already visible.** ADR-PA-0009 §5 justifies
`subscriptions` on a precise ground: *pulling is invisible to the producer*, so undeclared
consumption is the class that causes an outage. A request is the exact opposite — it arrives in the
recipient's mailbox carrying the envelope, `origin` stamped by `render_message.py`, gated by
`lint_message.py` in the recipient's CI. Nobody needs to read a card to discover it was sent.

What the field actually contains is the §6 rail table, re-transcribed per papeete-actor. `reliever-implementation`'s
two entries restate it verbatim; four of seven cards leave it `[]`. The template's own rule is
"Link, don't restate".

**3. `requests` names the message, not the ability.** All three non-empty cards hold one identical
entry, `id: finding`, and `nature: query` has never been used. A section meant to advertise what an
papeete-actor can be asked to do had collapsed to a single generic door — because nothing in it described
anything a caller could reason about.

**4. Nothing says where a peer's contract is.** `registry.yaml` indexes cards (*"the role A2A's
well-known path plays"*), but no card states which peers it resolves or at what ref. That
information exists today only as a `pin:` smeared across individual subscriptions, and as
ADR-PA-0009 §2's hand-maintained `external: true`.

## Decision

**1. `requests` is renamed `offers`.** Fields unchanged — this is a rename, not a redesign. The old
name named the interchange; the section names an ability, which is A2A's `skills[]` and MCP's
`tools`. `request` survives as the name of the interchange itself in the ADR-PA-0005 vocabulary.

`contract` was considered and rejected. It already carries five meanings here (the `card:` header,
`mailbox.contract`, `ecosystem/contracts/`, `ContractPublished`/`contract-deviation`, the planned
`kontract`) and is `BNK.RSOL`'s domain-layer core noun — ADR-PA-0005's layer rule forbids a sixth.
It also claims the whole for a part: §10 says the card **is** the contract, and `offers` is one
quarter of it. `capabilities` is unavailable (domain word, `BNK.*.CAP.*`) and `skills` is risky
(`.claude/skills/` exists in these repos and a card names no framework).

**2. `requests_out` is removed.** Routing lives once, in §6. An outbound edge needs no declaration
because it declares itself by arriving.

**3. `subscriptions[].how` is replaced by `notice:` and `then:`.**

- `notice:` — `binding`, `position`, `use`, `cadence`. **Deterministic by rule.**
- `then:` — at least one of `run:` (a script) or `intent:` (prose), plus `outcome:`.

The presence of `run:`/`intent:` **is** the discriminator. A separate `disposition:` label was
rejected as a second source of truth free to drift from the fields it describes — the same reasoning
that makes the envelope its own discriminator in `inter-agent-message/v0`.

`outcome:` is **closed at three values**: `records`, `request`, `publication`. These are the only
things a papeete-actor may produce, and the enum is what stops `then:` from becoming an escape hatch around
the direction rule. With `requests_out` gone, `outcome: request` names no recipient — the rail
determines the owner.

**4. `dependencies` is added** — `id` and `ref`, nothing else. The papeete-actors whose contract this one
resolves. It is **not** a routing table: whose card I read, never whom I message. It does not restate
the card path, because `registry.yaml` owns that and duplicating it is the drift its authority
boundary exists to remove.

**5. A `then.run:` subscription must resolve to a pinned `ref`.** A scripted consumer breaks silently
when an upstream shape moves; a judging consumer reads the change and adapts. So `ref: main` is a
defect under `run:` and a legitimate choice under `intent:` alone. The obligation follows the
consumer kind, which only the consumer knows.

**6. `external: true` is retired.** A dependency whose `id` resolves in the registry to an entry
carrying no `papeete-actor:` is external by construction, and is reported as external rather than as a
dangling subscription. ADR-PA-0009 §2's intent is preserved; only the hand-maintained flag goes.

**7. The card graduates.** `https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml` and `scripts/lint_card.py`
exist, the checker loads the schema rather than hard-coding it, and v0's status line — *"nothing
validates these files and nothing depends on them"* — is retired for a single card. It remains true
of the join.

## Rationale

Decisions 2 and 4 are the same observation twice. `requests_out` and `dependencies` both look like
"the papeete-actors I deal with", and the difference is **which direction is invisible**. Outbound is
self-announcing; inbound resolution is not. v0 declared the visible half and omitted the invisible
one — precisely inverted. Fixing it recovers what `requests_out` was reaching for while dropping the
coupling that made it a restatement.

Decision 3 encodes a philosophy the ecosystem had already half-adopted without naming: **determinism
belongs at existence, never at interpretation** (AGENT-OPERATING-MODEL §5). *"Has anything appeared
after my position?"* must stay dumb or consumption stops being idempotent; *"does this matter to my
capability?"* is irreducibly judgement. One `how:` field could not hold both, which is why it held
each in different cards.

Decision 3 also draws a line the reverse direction. It would have been lighter to let `then:` be pure
prose — the fully semantic dispatch the design dialogue started from. That was rejected: if dispatch
becomes wholly semantic, subscriptions stop being data and `papeete-actor check` loses every class it can
join on. **Drop the wiring, keep the declaration.** The declaration was never the heavy part — and
the declaration is all that is contracted: what a consumer *runs* to honour its intent, handler or
otherwise, stays its own. **Behaviour is proposed, never contracted.**

Decision 5 is the first rule in this ecosystem whose obligation is set by the *consumer's own
nature*. The pinning rule (ADR-PA-0008) binds a producer by a property of its consumers; this binds
a consumer by a property of itself, which is strictly easier to satisfy honestly.

## Consequences

- **Every card migrates.** The `card:` line, `requests`→`offers`, `requests_out` deleted,
  `subscriptions` split, `dependencies` added. A v0 card is **unmigrated, not non-conformant** —
  `lint_card.py` reports it as such, because `ECO.GOV` cannot place a card in another repo and
  adoption is each pair's own act.
- **The split of `how:` is an audit, not a transcription.** Deciding whether a given subscription is
  scripted or judged is the work; the field is only where the answer is written down. The
  "verify, never transcribe" lesson (`cards/README.md`) applies with full force.
- **`reliever-design` owes a rehoming.** Its `requests_out` entry is the only one carrying knowledge
  rather than restatement: *"a missing capability-keyed ADR-TECH-TACT is a whole-capability answer and
  therefore Business's to author"*. That is an **authority-boundary** statement — where this papeete-actor
  declares itself the wrong owner — and v1 has no slot for it. It must land in `open:` or repo prose,
  deliberately, not evaporate with the field.
- **`ECO.GOV`'s own `requests_out` also goes**, and it held the nonconformity re-emission. That is
  **doctrine in ADR-PA-0009 §6**, so the card was restating it: removing the entry does not revoke
  the rail. Stated here explicitly because it would otherwise read as a revocation.
- **Two new conformance classes** join the three from ADR-PA-0009: `unschematised-publication` and
  `unpinned-scripted-subscription`. Both are decidable from cards alone, unlike undeclared
  consumption.
- `papeete-actor check` still does not exist. `lint_card.py` validates one card; every cross-card figure in
  `ECO.GOV`'s card remains hand-computed, and that remains `ECO.GOV`'s standing nonconformity.
- **`offers[].means` is REQUIRED** — decided after this revision shipped, on the evidence this record
  itself filed: three cards, one door, `nature: query` unused. `offers` was the only section of the
  four to get no prose: publications carry `means` + `shape`, subscriptions `notice` + `then`, and
  an offer carried four flat fields against which a caller could reason about nothing. It takes the
  same self-selection burden `publications[].means` carries, pointed the other way — a publication's
  prose lets a reader decide whether a fact concerns it; an offer's lets a sender decide whether this
  is the actor to address. Folded into v1 rather than versioned: one card is at v1 today, so the
  window costs one edit (the ADR-PA-0013 timing argument, applied again).
- **Not decided:** whether `from:` — the recipient enumerating its senders — should go the way
  `no_consumer_list` sent the producer's equivalent. Deferred with this revision and still open.
