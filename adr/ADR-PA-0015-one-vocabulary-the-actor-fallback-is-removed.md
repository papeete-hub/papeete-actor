---
id: ADR-PA-0015
title: "One vocabulary — the `actor:` fallback is removed, and replaced by a refusal"
status: Proposed
date: 2026-07-23
supersedes: []          # nothing formally: the tolerance was never a recorded decision. See Context.
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../src/papeete_actor/check.py                 # `_actor_id`, and the refusal in `run`
  - ../src/papeete_actor/cards.py                 # `registry_classes`, the registry-side twin
  - ./ADR-PA-0013-papeete-actor-the-term.md       # the rename that created the transitional period
  - ./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md   # v0 is unmigrated, not non-conformant
---

# ADR-PA-0015 — One vocabulary

## Context

[ADR-PA-0013](./ADR-PA-0013-papeete-actor-the-term.md) renamed the card's identity key from
`actor:` to `papeete_actor:`. It could not rename anyone's card: a card is a papeete-actor's account
of itself, held in its own repo, and only its own pair may write it
([ADR-PA-0007](./ADR-PA-0007-actor-card-is-a-root-descriptor.md)). So for three days the ecosystem
ran a **mixed vocabulary** — two cards at the new key, six at the old — and the join read both:

```python
return card.get("papeete_actor") or card.get("actor")
```

**That tolerance was never a recorded decision.** It exists in a code comment and in one open
question on `ECO.GOV`'s card, which called it *"deliberate, and also a smell — it must be removed
once the six have migrated, or it becomes permanent."* This record is the removal, and it is also
the first time the tolerance is written down as something that was chosen. A transitional
provision that is never recorded has no expiry: nobody owns the question of when it ends, and the
code comment justifying it is read only by whoever is already editing the line.

On 2026-07-23 the six pairs migrated, each in their own repo, on their own PR. Every card in the
ecosystem now declares `papeete_actor:`. The fallback describes nothing.

## Decision

**The gate reads one vocabulary: `papeete_actor:`.** `actor:` is not read as a fallback on the card
side (`check.py::_actor_id`) or on the registry side (`cards.py::registry_classes`).

**A card still carrying `actor:` is a hard error, not a card with an unresolved id.** This is the
substance of the decision; deleting the fallback is the trivial half.

The naive removal — return `card.get("papeete_actor")` and nothing else — is *worse than keeping
the tolerance*, because the join does not need an id to include a card. It indexes publications
under both the id and the repo directory name, so a card whose id resolves to `None` stays in the
join, keyed only by repo name. Its publications land as `banking-tech/PlatformCorpusEnvelope` while
every consumer subscribes to `BNK.TECH/PlatformCorpusEnvelope`, and the join then reports each one
as a **dangling subscription** and an **unsubscribed publication**.

Measured, on the real workspace, with one card reverted to `actor:`:

| | headline | what it says |
|---|---|---|
| fallback kept | `1 passed, 17 warned, 4 noted` | correct |
| **naive removal** | `1 passed, 17 warned, 4 noted` | **BNK.TECH's three publications silently re-keyed** |
| this decision | `1 error(s)` | names the file, the key, and the fix |

The middle row is the finding. **The summary line does not move** — same passed, same warned, same
noted — because the corrupted entries merely change their names, not their count. A reader checking
the figures sees a healthy ecosystem. That is precisely the failure this tool exists to prevent
(*"a green, plausible, WRONG join is worse than no join, because it reads as coverage"*), reproduced
inside the tool itself.

So the fallback is replaced by a **refusal**: `run` appends an error naming the file and the fix,
and drops the card from the join rather than resolving it to `None`.

## Consequences

- **This is a behaviour change for consumers, and it is breaking for anyone still on `actor:`.**
  Nobody is: all eight cards migrated first, which is the ordering this record depends on. The
  version goes to **`0.2.0`**, and `ECO.GOV` — which pins `papeete-actor==0.1.0` — adopts it by a
  deliberate bump with its own review, like any other consumer. The six repos now pin the same way
  in CI and are unaffected until they choose to move.
- **`actor-card/v0` is untouched.** A v0 card remains *unmigrated, not non-conformant*
  ([ADR-PA-0010](./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md)) and
  `lint-card` still warns rather than failing it. This record is about the identity KEY, which is
  orthogonal: a v0 card that declares `papeete_actor:` resolves fine, and a v1 card that declares
  `actor:` does not. The two were only ever correlated because one rename produced both.
- **The registry side could only mis-classify, never mis-resolve** — `card_status` decides the
  class and the id is one lookup alias among two. The fallback goes anyway: two vocabularies read
  in two places is one more place for them to diverge, and there is no longer a reason for either.
- **The doctrine keeps the old vocabulary where it is history.** `ADR-PA-0007` and `ADR-PA-0013`
  still read `actor` throughout, under the banner 0013 added. Records are not rewritten to speak
  today's words; only running code is.

## What this does not decide

Whether a *future* transitional tolerance should be allowed at all. This one was correct — the
alternative was ECO.GOV writing six other repos' cards, which ADR-PA-0007 forbids — and the lesson
is narrower: **a tolerance needs a recorded owner and a stated end condition, or it is permanent by
default.** This one survived on a code comment for three days and was removed on the first day it
could have been. That it was noticed is not a property of the process.
