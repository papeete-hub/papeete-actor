# papeete-actor

A minimal, standalone actor identity contract for the [Papeete](https://github.com/papeete-foundry)
ecosystem: `papeete-actor-manifest/v0`.

```
papeete-actor lint-manifest   ACTOR.YAML...                                papeete-actor-manifest/v0
papeete-actor version         FOLDER... --label CITYPE [--feature-name F]  print the computed version, no Docker
papeete-actor build           FOLDER... --label CITYPE [--feature-name F]  tag <name>:<version>
papeete-actor contracts                                                     which contract version this build enforces
```

```bash
pip install papeete-actor
```

## What it enforces

An actor's manifest — `actor.yaml`, at the root of a folder whose entire contents belong to the
actor — declares two things, and nothing else:

| Field | Says |
|---|---|
| `name` | the actor's name |
| `description` | free prose — what this actor is |

No `version` field. `manifest: papeete-actor-manifest/v0` names the contract itself, the same
role `card:` plays on a larger card contract — so this lineage can migrate (v0 → v1,
warn-not-fail) on its own, and a manifest declaring some other value is read and warned as
UNMIGRATED rather than failed.

See [ADR-PA-0019](./adr/ADR-PA-0019-a-minimal-standalone-actor-manifest.md) for why this stays
apart from a larger card contract on purpose — no offers, no publications, no releases, no
dependencies, no subscriptions.

**Turning one actor's own folder into a runnable image is this repo's job:**

```bash
git tag car-inspector/v0.1.0        # once, before the first build — see below
papeete-actor build examples/car-inspector --label alpha
```

`build` reads that folder's `actor.yaml` for its `name`, and gets its **version** from
[`papeete-version`](https://github.com/papeete-hub/papeete-version) — a real PyPI dependency,
never a field `actor.yaml` declares (`ADR-PA-0022`, `ADR-PA-0024`). `--label` is a ciType, not a
free string:

| `--label` | Prints |
|---|---|
| `alpha`, `beta` | `{semver}-{label}-{shortSha}` |
| `feature` (needs `--feature-name F`) | `{semver}-{F}-{shortSha}` |
| `prod` | `{semver}` alone — GA, no label, no SHA |

`{semver}` is the `X.Y.Z` core of the actor's own nearest `<name>/vX.Y.Z` git tag — namespaced per
actor, since one repo can hold several. The image is tagged `<name>:<version>` on the local
Docker image store — no registry, no push. Rebuilding at the same git state and label (including
uncommitted edits — the ordinary local dev loop) always targets the exact same tag, and
**replaces** the image that tag used to point to, rather than leaving it behind. An actor with no
matching tag yet cannot be built — `git tag <name>/v0.1.0` first. See
[ADR-PA-0021](./adr/ADR-PA-0021-building-an-actor-is-this-repos-job.md) for why building stays a
single-actor operation, kept here rather than in a product's cross-actor orchestration, and
[ADR-PA-0024](./adr/ADR-PA-0024-papeete-actor-depends-on-papeete-version.md) for why version
computation itself now lives in a separate package this repo depends on.

**Just want the version, no Docker?**

```bash
papeete-actor version examples/car-inspector --label alpha
# 0.1.0-alpha-5b8ffdf
```

`version` runs the exact same computation `build` uses to pick a tag, without touching Docker at
all — a CI step recording what a build *would* tag before spending the time to build it, or a
human checking where an actor stands right now. It prints a bare string per folder, one per line,
so it composes in a shell: `VERSION=$(papeete-actor version examples/car-inspector --label alpha)`.

**Running a SET of actors together lives elsewhere.** A Docker-Compose-based launcher for naming
and running several already-built actors together — reachable and discoverable by name — is a
separate, standalone package: [`papeete-product`](https://github.com/papeete-hub/papeete-product),
`ADR-PP-0001`. This repo carries actor identity and how to build one actor; nothing about
composing or running a set of them.

## The contract is in this repo

[`src/papeete_actor/schemas/papeete-actor-manifest.schema.yaml`](./src/papeete_actor/schemas/papeete-actor-manifest.schema.yaml)
— ordinary committed source. **The package IS the contract**, not a gate that goes looking for
it, so a build needs no network and no credential *for the schema itself*.

```bash
uv build      # no network, no token, no fetch step for the contract
```

(`papeete-version`, a real PyPI dependency since `ADR-PA-0024`, still needs the ordinary package
resolution step any dependency does — the claim above is about the contract, not the whole build.)

`papeete-actor` also holds its own manifest, [`actor.yaml`](./actor.yaml), under the contract it
ships — and CI lints it on every push.

## Versioning

The tool version and the contract version are different things and move independently.
`papeete-actor contracts` prints the mapping for any installed build:

```
papeete-actor 0.1.0  —  contracts from …/site-packages/papeete_actor/schemas
  ok   manifest           papeete-actor-manifest/v0
```

A manifest declares the **contract** version; your CI pins the **tool**.

## Releasing

Tag-triggered, via [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC).
**No API token is stored anywhere** — GitHub mints a short-lived OIDC token per run and PyPI trades
it for an upload token. There is nothing to rotate and nothing to leak.

```bash
git tag v0.1.0 && git push origin v0.1.0     # .github/workflows/release.yml does the rest
```

### One-time setup — **done for this repo**, both steps

Kept as a record of what is configured, and as the recipe for the next package that needs it.

**1. A pending publisher on PyPI** ✅ *registered 2026-07-23*. The project did not exist yet, so it
is registered from the publisher side rather than by a first manual upload. At
<https://pypi.org/manage/account/publishing/>, as a **GitHub** pending publisher:

| Field | Value |
|---|---|
| PyPI Project Name | `papeete-actor` |
| Owner | `papeete-hub` |
| Repository name | `papeete-actor` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

All five must match exactly — PyPI checks the OIDC claims against them and rejects the upload
otherwise. `release.yml` already declares `permissions: id-token: write` and
`environment: pypi`, which is what makes those claims present.

**2. The `pypi` GitHub environment** ✅ *created*. No secrets in it — it exists so the OIDC claim
carries an environment name for PyPI to match. Protection rules are **not** set and are worth
considering, because a release is irreversible: PyPI never allows re-uploading a version, even after
a delete. Required reviewers, and restricting deployments to tags matching `v*`, are the two that
earn their keep.

**A private repo is fine.** Trusted Publishing authenticates the *workflow*, not the source, so
nothing here needs to be public for the package to be.

After the first successful release PyPI converts the pending publisher into a normal one
automatically; there is no second setup step.

**Nothing has been published yet.** `papeete-actor` is unclaimed on PyPI and the release lane has
never run.

### What a release asserts

The workflow builds, installs the wheel into a clean venv, and runs `papeete-actor contracts`
before publishing — so a build that lost its schema fails the release instead of shipping a gate
that enforces nothing.

## Licence

MIT.
