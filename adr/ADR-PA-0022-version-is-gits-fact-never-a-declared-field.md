---
id: ADR-PA-0022
title: "Version is git's fact, never a declared field"
status: Accepted
date: 2026-08-20
supersedes: []
references:
  - src/papeete_actor/schemas/papeete-actor-manifest.schema.yaml
  - src/papeete_actor/build.py
---

# ADR-PA-0022 — Version is git's fact, never a declared field

## Context

`papeete-actor-manifest/v0` carried a self-declared `version:` field from the start — free-form,
no scheme mandated, modeled directly on `papeete-actor-card/v2`'s `identity.version`
(`ADR-PA-0018`). Reviewed and reversed: a self-declared version drifts the moment a human forgets
to bump it, and for an actor built from its own folder, the answer to "where does this stand" is
already sitting in git history — the last commit that touched it. Declaring it a second time in
`actor.yaml` is a fact restated by hand, with nothing keeping the two in sync.

The trigger was a concrete need: images built locally should be reproducible and comparable
across rebuilds — the same actor, unchanged, must always resolve to the same tag — and a version
worth using later to track an actor's maturation through different testing harnesses needs to be
unique per meaningful change without a human remembering to bump anything.

## Decision

**`version` is removed from `papeete-actor-manifest/v0` entirely.** `actor.yaml` now declares
exactly two fields — `name` and `description` — plus the `manifest:` contract key. `required:
[manifest, name, description]` in the schema; nothing checks for `version` at all, and a manifest
that carries one anyway is just an unnamed extra (a note, never an error).

**`papeete-actor build` computes it instead, every time.** `build.py`'s new `git_version(folder)`
returns the short SHA of the most recent commit that touched that folder — scoped to the folder,
not the whole repo's `HEAD`, so an actor's version changes only when its own content changes.
`build_actor()` uses `image_tag(name, git_version(folder))` as the tag; nothing about version is
ever read from `actor.yaml`.

**Deterministic across uncommitted edits, by construction.** `git log` only sees commits, so an
in-progress edit — the ordinary local dev loop, before anything is committed — computes the exact
same version as before. Rebuilding under those conditions therefore targets the exact same tag,
and `build_actor()` removes the image that tag used to point to, so the new one **replaces** the
old one locally rather than accumulating beside it.

**No git history is a hard failure, not a fallback.** `git_version()` raises a clear `ValueError`
if the folder has no commits touching it — there is no "version 0.0.0" default, because a version
that means nothing is worse than no version at all.

## Rationale

**One version, one source of truth.** Two prior directions were considered and rejected in this
same conversation: a GitVersion-style computed string living *alongside* a separately-declared
manifest version (rejected — two numbers is exactly the duplication this decision removes), and
folding a computed value *into* `actor.yaml` on every commit (rejected — that rewrites a file just
to carry a fact git already carries, and reintroduces the "did anyone remember to update it"
problem this decision exists to close).

**Scoped to the folder, not the repo.** A monorepo holding several actors (or an actor beside a
product's own code) must not bump every actor's version when an unrelated file changes elsewhere.
Pathspec-scoped `git log` is what makes "the folder is the actor" (the manifest's own folder-root
convention) hold at the version level too, not just the identity level.

**A hard failure over a silent default.** A fabricated placeholder version would make an unbuilt
actor look identical to a real one until something downstream broke. Refusing outright — telling
the caller exactly what's missing — is the same discipline `schemas.load()` already applies to a
missing contract file.

## Consequences

- **Breaking for the schema, harmless in practice.** Nothing has shipped or been committed under
  the old three-field shape, so there is no migration story to write — this is a straight
  revision, not a v0 → v1 bump.
- **`build_actor()`'s signature and behavior changed**: it now requires the actor's folder to be
  a git working tree with at least one commit touching it. `tests/test_build.py` rewritten
  around throwaway, self-contained git repos in `tmp_path`, since there is no other way to
  produce a version to test against.
- **`papeete-actor`'s own `actor.yaml`** dropped its `version:` line — it was never built into an
  image (`papeete-product`'s `ADR-PP-0001` already noted this repo's own manifest isn't part of
  any product), so this is purely a contract-conformance cleanup, not a functional change.
- **Open — downstream of `papeete-product`.** `examples/product.yaml` (in `papeete-product`)
  names each actor by `{name, version}`, and those `version` values were written as arbitrary
  strings (`"1.0.0"`) before this decision existed. They are not wrong — `papeete-product` never
  reads `actor.yaml` and treats `version` as an opaque identity string either way — but they no
  longer correspond to anything `papeete-actor build` would actually produce for those folders
  (a git short SHA, once committed). Making the full worked example resolve end to end (`papeete-
  actor build` → `papeete-product run`, both against real tags) needs those example actor
  folders committed at least once; that commit hasn't been made, on purpose, pending a separate
  go-ahead.
