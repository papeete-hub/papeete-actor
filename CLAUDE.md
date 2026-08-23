# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`papeete-actor` ships a minimal, standalone actor identity contract for the Papeete ecosystem —
`papeete-actor-manifest/v0` — plus the CLI that enforces it and turns one actor's folder into a
runnable Docker image. It deliberately does NOT know about cards, offers, publications, releases,
dependencies, subscriptions, or running multiple actors together — those belong to other repos
(`papeete-product` for running a set of actors; a larger card contract elsewhere). See
`adr/ADR-PA-0019-a-minimal-standalone-actor-manifest.md` for why this stays intentionally narrow.

## Commands

Dependency management and running are via `uv`.

```bash
uv run --extra dev pytest -q                        # full test suite
uv run --extra dev pytest -q -m 'not e2e'            # skip tests needing a Docker daemon
uv run --extra dev pytest -q tests/test_cli.py       # one file
uv run --extra dev pytest -q tests/test_cli.py::test_lint_manifest_passes_a_conformant_manifest  # one test

uv build                                             # build the wheel/sdist, no network needed for the contract itself
uv run papeete-actor lint-manifest actor.yaml
uv run papeete-actor version examples/car-inspector --label alpha
uv run papeete-actor build examples/car-inspector --label alpha
uv run papeete-actor contracts
```

The `e2e` pytest marker (`tests/test_build.py`) spawns a real Docker build and needs a Docker
daemon — deselect with `-m 'not e2e'` when none is available (declared in `pyproject.toml`).

CI (`.github/workflows/ci.yml`) runs the test suite first, then `uv build`, then installs the
wheel into a clean venv and runs `papeete-actor contracts` and `papeete-actor lint-manifest
actor.yaml` against it — proving the shipped wheel actually carries and enforces its own
contract, not just that the source tree does.

## Architecture

Four small modules, each with one job — read each module's own docstring before changing it, they
carry the design rationale in full:

- **`manifest.py`** — the `papeete-actor-manifest/v0` gate. Loads the schema, checks required
  keys are present. A manifest declaring anything other than `papeete-actor-manifest/v0` (or
  nothing) is **UNMIGRATED**, reported as a warning, and not checked further — never treated as
  non-conformant. This mirrors the same discipline documented for `card:` in the wider ecosystem.
- **`schemas.py`** — loads the contract YAML from `src/papeete_actor/schemas/`, which is ordinary
  committed source shipped inside the wheel as package data. **The package IS the contract** —
  there's no fetch step, no network call, no credential needed to read it, in a source checkout
  or an installed wheel alike.
- **`build.py`** — turns one actor's folder into a Docker image tagged `<name>:<version>` on the
  local image store (no registry, no push). `name` comes from that folder's own `actor.yaml`;
  `version` is computed by the external `papeete-version` package (`ADR-PA-0024`), never
  self-declared — the manifest schema has no `version` field on purpose (`ADR-PA-0022`).
  Rebuilding at the same git state and label is deterministic and **replaces** the image the tag
  previously pointed to (`_image_id` / `docker rmi`), rather than accumulating untagged images.
- **`cli.py`** — argparse wiring for four subcommands: `lint-manifest`, `version`, `build`,
  `contracts`. `version` and `build` share `--label` (a `ciType` from `papeete_version.CI_TYPES`,
  not a free string) and `--feature-name` (required only when `--label feature`).
- **`report.py`** — the shared `Report` dataclass (`oks`/`notes`/`warns`/`errors`) used by every
  gate for consistent `ok`/`warn`/`note`/`FAIL` output and exit codes. `errors` fail a run;
  `warns`/`notes` never do — a heuristic finding is a prompt to declare, not an automatic verdict.

### Versioning is delegated, not computed here

Version computation (semver-from-tag + ciType label + short SHA) used to live in this repo and
now lives in the separate `papeete-version` PyPI package, a real dependency
(`ADR-PA-0024`, ADR-PA-0025 in this repo's `adr/`). `build.py` only reads an actor's `name` from
its own `actor.yaml` and asks `papeete_version.version.compute()` for the version string. The
semver core comes from that actor's own nearest `<name>/vX.Y.Z` git tag — namespaced per actor,
since one repo can hold several actors (see `examples/car-inspector`, which needs a
`car-inspector/v0.1.0` tag before it can be built).

### Deploy config is authored, not consumed

An actor's folder may carry an optional `deploy/k8s/` (kustomize `base/` + `overlays/<name>/`)
and/or `deploy/terraform/` subfolder for a separate deploy tool (`papeete-deploy`) to read later
— this repo does not read or validate any of it (`ADR-PA-0025`). `examples/car-inspector/deploy/`
shows the convention.

## Releasing

Tag-triggered (`git tag vX.Y.Z && git push origin vX.Y.Z`) via `.github/workflows/release.yml`,
publishing to PyPI over Trusted Publishing (OIDC) — no stored API token. The workflow builds,
installs the wheel into a clean venv, and runs `papeete-actor contracts` before publishing, so a
build that lost its schema fails the release instead of shipping a gate that enforces nothing.

## ADRs

Design decisions live in `adr/` as one file per decision (`ADR-PA-00NN-*.md`, `template.md` for
the format). Consult them before changing behavior that looks like it might be a deliberate
constraint rather than an oversight — most non-obvious choices in this codebase (no `version`
field, the separate manifest filename, the UNMIGRATED-not-failed handling, why building stays
single-actor) are already explained there and referenced from the relevant module's docstring.
