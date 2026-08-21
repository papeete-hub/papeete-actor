---
id: ADR-PA-0018
title: "A card declares its own version"
status: Accepted
date: 2026-08-20
supersedes: []
references:
  - src/papeete_actor/schemas/papeete-actor-card.schema.yaml
  - src/papeete_actor/cards.py
  - events/papeete-actor-card-contract/0.6.0.yaml
---

# ADR-PA-0018 — A card declares its own version

## Context

A downstream deployment wanted to load different versions of "the same" papeete-actor (one
`papeete_actor` id, e.g. `EXA.ARCHIVIST`) from plain-text card files that coexist on disk at
once — one directory declaring where the actor stood at one point, another declaring where it
stands now — with a loader resolving a specific one by id and a caller-supplied ref.

Nothing on `papeete-actor-card/v1` says where a papeete-actor itself stands. Three mechanisms
look like they might, and none does:

- **A git tag** identifies a commit, not a working tree. Two directories checked out from two
  tags of the same repo is the ordinary case this contract already assumes never happens — one
  repo, one card, one place on disk (ADR-ECO-0004 §1) — and nothing here changes that. The
  question is a *second*, deliberately co-located directory, which a tag cannot express at all.
- **`releases[]`** ships an *artefact* this papeete-actor produces, not a statement about the
  papeete-actor itself. It is `empty_is_legal`, and a restricted deployment may have no releases
  ever, e.g. `papeete-actor-simple`'s own restriction forbids the `publications[]` entry
  `releases[].announced_by` requires (this repo's own `open:` records exactly that deviation).
- **`publications[]`** has the same gap for the same reason — a restricted actor may declare
  none, so a mechanism that requires one to exist cannot be the general answer.

So there was no axis on the card itself, checkable by lint alone, that says where *this*
papeete-actor stands, independent of whether it ships artefacts or emits facts at all.

## Decision

**Add `identity.version`, required, free-form.** No format, no regex, no mandated scheme —
exactly as unenforced as `releases[].versioning` already is. `_require()` checks presence only.

It is a **third, distinct axis**, alongside two the contract already carries on the same card:

    card:              which CONTRACT this file conforms to (papeete-actor-card/v2 itself)
    releases[].id      what an ARTEFACT this papeete-actor ships is called
    version             where THIS PAPEETE-ACTOR itself stands, self-declared

Bumped as `papeete-actor-card/v2`, reusing the warn-not-fail UNMIGRATED path that
`cards.py:112-114` already runs for any card whose `card:` does not match `CONTRACT` — the same
mechanism that made v0 → v1 non-breaking for every card that had not yet moved.

Cross-card `(papeete_actor, version)` uniqueness is explicitly **not** decided here. It is not
decidable from one card — it is a registry-wide or ecosystem-wide question, and belongs to
`papeete-actor check` (which does not yet join on it) or to whatever consumer needs the
guarantee, the same way this contract already declines to decide `unresolved_release`.

## Rationale

**Free-form, because every other version-shaped field on this contract already is.**
`releases[].versioning` is declared but the scheme itself — semver, calver, a tag convention — is
left to the producer; `_require()` never fuzzy-matches or format-checks anything it enforces. A
`version` that mandated semver would be the first field on this contract to impose a scheme by
fiat rather than let a consumer choose one, and there is no evidence every papeete-actor's notion
of "where I stand" fits one scheme.

**On `identity`, not a new top-level section.** `version` answers "who is this papeete-actor,
right now" — the same question `papeete_actor`, `name` and `repo` already answer on this block.
It is not state consumed by anyone (`releases`) and not a fact emitted to anyone
(`publications`); it says something about the card itself, which is what `identity` is for.

**Deliberately unmandated, so a consumer can mandate more.** This contract does not require
`version` to parse as anything in particular. That is what *lets* a consumer layer a real scheme
on top without this contract having to pick one for the whole ecosystem —
`papeete-actor-simple` does exactly that for `dependencies[].ref` resolution (PEP 440 range
matching, ADR-PAS-0006), entirely at its own discretion, never forced back onto this contract.
The alternative — mandating semver here — would have made every restricted actor with no
opinion on version schemes carry one anyway.

## Consequences

- **Breaking, so 0.5.0 → 0.6.0.** A v1 card with no `identity.version` no longer conforms to v2 —
  but it does not fail. It warns as UNMIGRATED and lints clean otherwise, exactly as an
  unmigrated v0 card does today. Adoption of v2 is each pair's own act, same as every prior
  contract bump on this repo.
- **This repo's own card carries `version: "1.0.0"`**, distinct from `releases[].id:
  papeete-actor`'s PyPI version and from `card: papeete-actor-card/v2` — three numbers on one
  file, and nothing forces them to move together (they do not, today).
- **Open — cross-card `(id, version)` uniqueness.** Two cards may now legitimately declare the
  same `papeete_actor` id with different `version`s (the case this ADR was written for), or,
  through simple author error, the same id with the *same* version. Neither is a class
  `lint-card` can report — it sees one card at a time — and `papeete-actor check` does not yet
  join on it. Whether it ever should is undecided; a consumer that needs the guarantee enforces
  it itself in the meantime (`papeete-actor-simple`'s `AmbiguousCoupling`, ADR-PAS-0006).
- **Open — whether `version` and `releases[].id` should ever be required to agree**, for a
  papeete-actor whose one release IS the papeete-actor (this repo's own shape). Left alone here:
  conflating them would break every restricted actor that ships no release at all.
