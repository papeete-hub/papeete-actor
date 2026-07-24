# Actor card template — `papeete-actor-card/v1`

The card is **`papeete-actor.yaml` at your repo's root**, beside `work.yaml` and `knowledge.yaml` — one
descriptor per concern ([ADR-PA-0007](../../adr/ADR-PA-0007-actor-card-is-a-root-descriptor.md)).
Copy the block below into it and fill it in. The machine-readable contract is
[`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml); this page is the
fill-in form, and where the two disagree the schema wins.

Three rules that keep a card honest:

- **Harness-independent, always.** The card never moves under `.claude/` or any framework directory,
  and names no framework. What your papeete-actor is built with — Claude Code skills, a LangChain graph, a
  human with a checklist — is *interior*, and the external contract must not depend on it
  (AGENT-OPERATING-MODEL §4). A harness swap must not touch this file.
- **Link, don't restate.** A card points at the doctrine and the repo; it never becomes a second copy
  of either. If a card and `AGENT-OPERATING-MODEL.md` disagree, the doctrine wins and the card is the
  bug. In particular: **the rail table (§6) is not yours to re-transcribe** — that is what removing
  v0's `requests_out` relies on.
- **Mark what you don't know.** `(inferred)` for something derived from doctrine rather than decided,
  `(open)` for a real question. A card full of confident fiction is worse than a card with holes —
  the holes are the next agenda.

Prose — purpose, ubiquitous language, open questions — is **not contracted**. Keep it wherever your
pair already reads (the repo README, an `ACTOR.md`), or fold the short version into `open:` below.

---

```yaml
# papeete-actor.yaml — the papeete-actor card for this repo (papeete-actor-card/v1, ADR-PA-0005 / ADR-PA-0007 /
# ADR-PA-0010). Contract: https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/papeete-actor-card.schema.yaml

card: papeete-actor-card/v1
papeete-actor: BNK.RLVR                     # ecosystem-layer id; `none` if unregistered
tier: business                      # governance | knowledge | business | design | implementation
name: Urbanist                      # the agent's name, or `none` — human-operated
repo: papeete-foundry/reliever-business   # exactly one (ADR-PA-0002 §1: one repo, one papeete-actor)
strategic_class: core-domain        # core-domain | supporting | generic | published-policy
pair:
  human: [lead BA, architect]       # who decides
  agent: Urbanist                   # or `none`

# ── the address (A2A `url` + `capabilities`, transposed to messaging) ───
mailbox:
  contract: inter-agent-message/v0
  binding: github-issue
  address: papeete-foundry/reliever-business/issues
  delivery: at-least-once
  idempotency: [type, subject]      # the envelope identity — redelivery upserts
  push: false                       # Level 0: nothing is delivered to me; I pull

# ── OFFERS — what I can be asked to do. The caller reasons; I may refuse ─
# Renamed from v0's `requests`: the old name named the message, this names the
# ability. A2A's `skills[]`. Accepting never obliges me to honour — triage is my
# exclusive act (WORK-OBSERVABILITY §5 step 3); nobody authors another's kanban.
# NO RETURN VALUE: a request completes as a refusal, or LATER as a publication
# the sender may have subscribed to (ADR-PA-0009 §4).
offers:
  - id: finding
    means: >-                       # what this door is FOR — so a CALLER can self-select.
      what this offer accepts and on what ground, written so a sender can work out whether I am
      the right actor to address. It must NOT route the caller elsewhere: where else a request
      belongs is the §6 rail table's answer, not mine to author.
    nature: action                  # query (return information) | action (decide or do)
    rail: functional-gap            # the domain rail that makes me the right door
    from: [BNK.RSOL, implementation]
    completion: refusal | <publication id>   # NOT a return value
    becomes: ADR candidate → task in tasks/<scope>/

# ── PUBLICATIONS — facts I emit; addressed to nobody; nobody may refuse ─
# Binding: event-log (publication/v2) — one file per fact under
# events/{publication}/{ref}.yaml, committed in the SAME COMMIT as the change it
# describes. I never deliver, never acknowledge, and never list my consumers.
#
# MEANING AND FORM, ALWAYS BOTH. I cannot see whether my consumer is an agent, a
# human or a script — so I may never decide that prose alone will serve.
publications:
  - id: CapabilityReadyForDesign
    means: >-                       # the CEILING: prose a human or agent reasons over.
      what this fact IS and why it might matter — written so a reader can work out
      whether it concerns them. It must NOT say what a consumer should do about it:
      that is the consumer's to author, in its own card, under its own review.
    shape: events/CapabilityReadyForDesign/schema.yaml   # the FLOOR: required (publication/v2)
    surface: kpack envelope @ pinned ref; events/CapabilityReadyForDesign/
    breaking_flag: <REQUIRED if consumers pin this by any mechanism — the announced-bump path>

# ── SUBSCRIPTIONS — what I pull, and what I do about it ─────────────────
# Consumer-side by rule: a producer listing its subscribers is the coupling
# ADR-PA-0002 Decision 4 forbids. Fan-out is the JOIN of publications against
# subscriptions across all cards. Consumption BY ANY MECHANISM is a subscription —
# pulled, vendored, sibling path, image pin (ADR-PA-0009 §5).
subscriptions:
  - to: BNK.KNOW/meta-model         # <source>/<publication id>; source is in `dependencies`

    notice:                         # THE MEMBRANE — deterministic by rule. If a model
                                    # decides what it has already seen, consumption stops
                                    # being idempotent and facts are lost or replayed.
      binding: event-log            # the swappable part; a new transport is a new binding
      position: <ref>               # OPAQUE: a git ref now, a broker offset later
      use: <purpose>                # the consumer group — one position per purpose
      cadence: on change

    then:                           # MY INTENT — mine alone to author. The presence of
                                    # `run:`/`intent:` IS the discriminator; there is no
                                    # `disposition:` label to drift from them.
      run: tools/check_vendor_sync.py     # a deterministic reaction (optional)
      intent: >-                          # a judged reaction (optional)
        what I do about facts like this, in my own words. Both may be present: `run`
        is then the input bookend and `intent` reasons over what it produced.
      outcome: records              # records | request | publication — CLOSED AT THREE

# ── DEPENDENCIES — the papeete-actors whose contract I resolve ──────────────────
# Consumer-side, like subscriptions. NOT a routing table: whose card I READ, never
# whom I message — a request declares itself by arriving. `id` resolves against
# ecosystem/registry.yaml, which stays the sole authority for WHERE a card lives:
# never restate a card path here.
# A `then.run:` subscription MUST resolve to a PINNED ref; an `intent:`-only one may float.
dependencies:
  - id: BNK.KNOW
    ref: v1.0.0
  - id: papeete-hub/kpack           # no `papeete-actor:` in the registry → external, DERIVED
    ref: v2.0.0                     # (v0's `external: true` is retired)

# ── records, membrane, autonomy ────────────────────────────────────────
records:                            # owned state — the store of record, mine alone to write
  - what: capability taxonomy
    where: ontology/maps/bcm.ttl
gates:                              # THE BOOKENDS ONLY — not an inventory of tools/*.py (§4)
  - SHACL (validate_ontology.py)
work_surface: work.yaml             # or `none` — see WORK-OBSERVABILITY §2
autonomy: level-0                   # every write through a human-reviewed PR

open:                               # the next agenda for this box
  - <a real question, not a to-do>
```

---

## Filling the four sections

They are not interchangeable, and putting information in the wrong one is the coupling bug the
direction rule exists to prevent (AGENT-OPERATING-MODEL §5):

| Section | Direction | Rule |
|---------|-----------|------|
| `records` | inward | The store of record. Only this papeete-actor writes it. |
| `offers` | inbound | What I may be asked to do. The **caller** reasons about whether it is the right door; I may refuse. |
| `publications` | downstream | Published, never delivered. The record *is* the event; consumers pull. **A publisher never opens issues in a consumer's repo, and never names its consumers.** |
| `subscriptions` | consumer-side | The mirror of someone else's `publications` — declared here, by you, never by them. Carries what you *do* about the fact. |
| `dependencies` | consumer-side | Whose contract you resolve, and at what ref. Never whom you message. |

## Meaning, intent, and where behaviour lives

The split that makes `then:` work, and the reason a publication must never carry a `then:` of its
own:

- **The producer supplies meaning.** Only they know why they emitted the fact and under what duress.
  Good `means:` prose contains a *self-selection test* — `ApplicationStubbed` reads *"addressed to
  whoever would otherwise mistake this papeete-actor's invention for a decision"*, which any reader can apply
  to itself. That is how fan-out happens without the producer naming anyone.
- **The consumer declares intent.** In its own card, in its own repo, under its own PR review.
- **Behaviour is proposed, never contracted.** What you actually run to honour that intent — a
  handler, a poll, an agent reading the prose, a human with a checklist — is yours: local,
  revisable, binding nobody else. `then.run:` names a handler and is perfectly legitimate. Wiring
  cost falls from O(publications × consumers) to O(publications) — but it must not fall to zero, so
  behaviour may never be the *only* record of the edge: the declaration is the only thing
  `papeete-actor check` can join on.

A publication saying *"Urbanist, refine the capability when you see this"* would be a producer
authoring a consumer's behaviour. In MCP the server says what a tool **is**, never what the client
should do — this is that rule, applied to facts instead of tools.

## Determinism sits at existence, never at interpretation

*"Has anything appeared after my position?"* is cheap deterministically and unreliable from a model:
if a model decides what it has already seen, consumption stops being idempotent. *"Does this fact
matter to my capability?"* is the exact inverse — no detector can compute it.

That is the whole reason `notice:` and `then:` are separate blocks rather than one. And it is why
`run:` naming a script is **not** an interior leak: a subscription's reaction *is* the input bookend,
which §4 places at the membrane. What §4 forbids is expanding `gates:` into an inventory of interior
validators — which every one of the five v0 adoptions did before trimming it back.

## Migrating a v0 card

1. `card: actor-card/v0` → `v1`.
2. `requests:` → `offers:`. Fields unchanged.
3. Delete `requests_out:`. Before you do — if its `when:` prose says something about **the boundary
   of your own authority** (*"this is not mine to decide, therefore it is X's"*), that is knowledge,
   not routing. Move it to `open:` or your repo prose. If it merely restates the §6 rail table, it
   goes with no loss.
4. Split each `subscriptions[].how:` into `notice:` and `then:`. This is an **audit, not a
   transcription**: `how:` currently holds a transport in some cards and a behaviour in others, and
   deciding which is which is the point of the migration.
5. Add `dependencies:`, one entry per source named in `subscriptions[].to`, plus anything you read by
   sibling path, vendor pin or image tag. Move per-subscription `pin:` here. Delete `external: true`.
6. Add `means:` (renamed from `what:`) and `shape:` to every publication, and write the payload
   schema at `events/{publication}/schema.yaml`. Records already written are **not** retrofitted.
