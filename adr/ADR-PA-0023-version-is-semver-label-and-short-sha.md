---
id: ADR-PA-0023
title: "Version is semver core (from a tag) + an uninterpreted label + short SHA"
status: Superseded by ADR-PA-0024
date: 2026-08-21
supersedes: []
references:
  - src/papeete_actor/build.py
  - src/papeete_actor/cli.py
  - tests/test_build.py
---

# ADR-PA-0023 — Version is semver core (from a tag) + an uninterpreted label + short SHA

## Context

`ADR-PA-0022` computed an actor's version as a bare short SHA — enough to make a rebuild
deterministic and replace-not-accumulate, but nothing else. In practice that turned out to be too
little: a short SHA carries no notion of "which one is newer" at a glance, no way to say "this is
the same release, harnessed against a different test scenario before GA," and nothing a human
would recognize as a version at all.

The ask: semver, so a human can read `1.4.2` and know where it stands; a short SHA, so two builds
of the same semver are still distinguishable and traceable to an exact commit; and a qualifier,
so the same semver can be hardened through more than one pre-GA scenario (a smoke build, a
staging build, a soak-tested build, …) before the one that ships GA. What that qualifier's own
taxonomy should be (`dev`/`rc.1`/`staging`/GA-has-none/…) is explicitly **not** decided here —
the ask was to keep the format strict and the qualification loose, and let the taxonomy emerge
once there's real usage to learn from.

## Decision

**The version format is exactly `{semver}-{label}-{shortSha}`**, e.g. `1.4.2-dev-a1b2c3d`, always
three parts, in that order.

- **`{semver}`** is the `X.Y.Z` core off the actor's own nearest git tag, `<name>/vX.Y.Z` —
  `<name>` the same normalized form `image_tag()` already uses. GitVersion-style: computed from
  git's own history, never a declared field — `ADR-PA-0022`'s no-declared-field rule extends to
  the semver core exactly as it already covered the SHA. **Namespaced per actor**, not a plain
  `vX.Y.Z` tag, because this repo can hold more than one actor folder (`examples/`) — a shared,
  unscoped tag would move every actor's semver together even when only one of them changed.
  `semver_base()` resolves it via `git describe --tags --abbrev=0 --match "<name>/v*"`.
- **`{label}`** is supplied by the caller, at build time, via `papeete-actor build FOLDER
  --label L` — required, never inferred from a branch name, a CI variable, or anything else.
  This function does not decide what a label *means*; it only enforces that one is present and
  lands in the right slot in the format.
- **`{shortSha}`** is exactly `git_version(folder)` from `ADR-PA-0022`, unchanged — the short SHA
  of the actor folder's own last touching commit.
- **No fallback for a missing tag.** `semver_base()` raises a clear `ValueError` naming the exact
  `git tag` command that would fix it, the same discipline `git_version()` already applies to a
  folder with no commit history at all (`ADR-PA-0022`).

`image_version(folder, name, label)` composes the three parts; `build_actor(folder, label)` feeds
the result to `image_tag()` exactly as it fed a bare SHA before.

## Rationale

**This does not reopen `ADR-PA-0022`'s actual thesis.** That decision's point was "no declared
field" — a version restated by hand drifts from what git already knows. Nothing here declares
anything in `actor.yaml`; the manifest still carries exactly `manifest`, `name`, `description`.
What changes is the *formula* computed from git, not the "computed, never declared" rule itself —
this ADR extends `ADR-PA-0022`, it does not supersede it.

**A tag, not a declared field, because a tag is git's native way to say "this commit is a
release."** The alternative considered — a `version:` field back on `actor.yaml` with the SHA and
label appended at build time — was rejected for exactly the reason `ADR-PA-0022` already gives: it
reintroduces a fact a human can forget to bump, sitting right next to a fact (the tag) that would
say the same thing more reliably.

**Per-actor tag namespace, because this repo is a monorepo of actors, not just this repo's own
manifest.** A plain `vX.Y.Z` convention is the right default for a single-actor repo; the moment a
second actor's folder exists alongside the first (`examples/car-inspector`, today), an unscoped
tag stops meaning "this actor's version" and starts meaning "something in this repo's version,"
which is a different and less useful claim.

**The label stays uninterpreted, on purpose, per the explicit ask.** Every taxonomy considered —
branch-driven, CI-environment-driven, a fixed enum of qualifiers — bakes in an opinion about what
"pre-GA hardening" looks like before there's been a single real build to learn from. Format
strictness (always three parts, always in this order) is enforced now, because that's what lets
tooling downstream parse a version reliably; *meaning* is deliberately deferred.

## Consequences

- **`papeete-actor version FOLDER... --label L`** exposes `image_version()`/`actor_version()`
  standalone, printing the same computed string with no Docker involved — a smaller, cheaper
  claim than `build`, for a CI step or a human checking where an actor stands before spending the
  time to build it.
- **Breaking for `build_actor()`'s signature.** It now takes `label` as a required second
  argument; `papeete-actor build` now requires `--label`. Nothing shipped depends on the old
  bare-SHA tag yet, so there is no migration to write.
- **New tag convention to adopt: `<name>/vX.Y.Z`.** An actor with no such tag cannot be built —
  `examples/car-inspector` needs `git tag car-inspector/v0.1.0` (after its first commit) before
  `papeete-actor build examples/car-inspector --label dev` will succeed.
- **`tests/test_build.py` rewritten** around `semver_base()` and `image_version()`, including a
  monorepo-scoping test (a same-repo, differently-namespaced tag must not leak into another
  actor's semver).
- **Open — what a label means.** No enum, no GA-vs-pre-GA rule, no branch inference exists yet.
  The next session that wants to *enforce* something about labels (e.g. "GA builds carry no
  label" or "only these values are legal") makes that its own decision, layered on top of this
  strict-format, loose-taxonomy baseline.
- **Open — commit distance since the tag.** GitVersion itself typically folds "N commits past the
  tag" into the version too; this decision does not carry that number anywhere in the format.
  Revisit if two builds at the same semver, same label, but different (uncommitted-vs-committed)
  states ever need to be told apart by more than the SHA already occupying the last slot.
