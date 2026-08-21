---
id: ADR-PA-0024
title: "papeete-actor depends on papeete-version for its version computation"
status: Accepted
date: 2026-08-21
supersedes: [ADR-PA-0023]
references:
  - src/papeete_actor/build.py
  - src/papeete_actor/cli.py
  - pyproject.toml
---

# ADR-PA-0024 — papeete-actor depends on papeete-version for its version computation

## Context

`ADR-PA-0023` gave `build.py` its own `git_version()`/`semver_base()`/`image_version()`,
computing `{semver}-{label}-{shortSha}` with `label` left deliberately free-form. That logic was
then extracted, unchanged in behavior, into a new standalone package —
[`papeete-version`](https://github.com/papeete-hub/papeete-version) — specifically *without*
wiring `papeete-actor` to depend on it yet (`papeete-version`'s own `ADR-PV-0001` records that as
a deliberate, separate, later decision).

`papeete-version` has since published to PyPI (`0.1.0`) and moved past the free-form label:
`--label` is now a fixed ciType — `alpha`, `beta`, `feature`, `prod` — with `prod` printing a bare
semver (GA, no label, no SHA) and `feature` requiring a `--feature-name` (`papeete-version`'s
`ADR-PV-0002`). The later decision `ADR-PA-0023` deferred has now been made, by the package that
owns making it.

## Decision

**`papeete-actor` now depends on `papeete-version>=0.1.0` from PyPI.** `build.py` no longer
computes a version itself — `git_version()`, `semver_base()`, and `image_version()` are deleted
from this repo entirely, replaced by calls into `papeete_version.version.compute()`. `build.py`'s
own remaining job is narrow: read an actor's `name` from `actor.yaml`, ask `papeete_version` for
the version string, and turn `{name, version}` into a Docker tag.

**`--label` on both `papeete-actor version` and `papeete-actor build` becomes a ciType**,
`choices=papeete_version.version.CI_TYPES`, no longer a free string — argparse itself rejects
anything else before any git or Docker work runs. **`--feature-name` is new**, required and only
used when `--label feature`, passed straight through to `papeete_version.version.compute()`.

**This repo carries no local copy of the computation, and no fallback if `papeete-version` is
unavailable.** A missing or broken dependency is a real, visible failure (an import error), not
silently degraded behavior — the same no-silent-fallback discipline `ADR-PA-0022`/`ADR-PA-0023`
already applied to a missing git tag or commit history.

## Rationale

**The deferral this ADR closes was deliberate and time-boxed, not indefinite.** `ADR-PV-0001`
split extraction and cutover into two acts specifically so each could be evaluated on its own —
extraction's soundness didn't depend on a real release existing yet. Now one does, published and
installable, so the second act is no longer premature.

**One version formula, one source of truth, now enforced by the dependency graph rather than by
discipline alone.** Keeping two copies of `semver_base()` in sync by hand — this repo's and
`papeete-version`'s — was always the accepted-temporary cost `ADR-PV-0001` named it as. A real
PyPI release removes the reason to keep paying it.

**Adopting the ciType vocabulary is not optional once this dependency exists.** `build.py` calling
`pv.compute()` inherits whatever `compute()` validates — there is no version of "depend on
papeete-version" that keeps accepting free-form labels `compute()` itself now rejects. This ADR
does not re-litigate whether ciTypes are the right taxonomy; that argument already happened in
`papeete-version`'s own `ADR-PV-0002`.

## Consequences

- **Breaking for `papeete-actor build`/`version`'s `--label` flag.** Any prior invocation with a
  free-form label (`dev`, `staging`, ...) now fails argparse validation outright. Nothing shipped
  depends on the old free-form labels outside this repo yet.
- **`build.py` shrinks.** `git_version()`, `semver_base()`, `image_version()`, and the local
  `_normalize_name()` are gone — `image_tag()` now calls `papeete_version.version.normalize_name()`
  directly. `_actor_name()`, `actor_version()`, `build_actor()`, `_image_id()` remain, the last
  three now `feature_name`-aware.
- **`tests/test_build.py` narrows to build.py's own job** — reading `actor.yaml`, composing a
  Docker tag, shelling out to `docker build` — and no longer re-tests `git_version()`/
  `semver_base()`'s own correctness, which is `papeete-version`'s test suite's job now, not this
  repo's.
- **New dependency: `papeete-version>=0.1.0`, in `pyproject.toml`.** This repo's wheel is no
  longer self-contained for version computation the way `ADR-PA-0021`'s README language ("no
  network, no token, no fetch step") described for the *contract* — that claim still holds for
  the `papeete-actor-manifest/v0` schema, which remains ordinary committed source; it does not
  extend to this new runtime dependency, which is resolved from PyPI like any other.
- **Open — the `papeete-version` pin.** `>=0.1.0` accepts any future `papeete-version` release
  without a corresponding `papeete-actor` review. Whether to pin tighter (`==0.1.0`, or a `<0.2`
  ceiling) once `papeete-version` has a compatibility policy of its own is undecided here.
