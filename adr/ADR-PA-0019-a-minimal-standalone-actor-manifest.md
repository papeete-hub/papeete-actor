---
id: ADR-PA-0019
title: "A minimal, standalone actor manifest, deliberately apart from the card contract"
status: Accepted
date: 2026-08-20
supersedes: []
references:
  - src/papeete_actor/schemas/papeete-actor-manifest.schema.yaml
  - src/papeete_actor/manifest.py
---

# ADR-PA-0019 — A minimal, standalone actor manifest, deliberately apart from the card contract

## Context

`papeete-actor-card/v2` carries a lot: offers, publications, releases, dependencies,
subscriptions, and now (ADR-PA-0018) its own `version`. Reviewing that surface raised a bigger
question — does the card contract carry too much for the cases where all a consumer needs is "who
is this actor, where does it stand, and what is it"?

A "card + messaging" split was designed to answer this by trimming the existing contract, then set
aside. The chosen direction instead: **start fresh, naively, in the same repo, without
reconciling with what already exists anywhere** — not `papeete-actor-card`, not
`papeete-actor-simple`, not any other consumer of the card contract. A brand-new, standalone
lineage, small enough that its whole shape fits in four lines.

## Decision

**A new contract, `papeete-actor-manifest/v0`, with exactly three required fields beyond its own
contract key:**

```yaml
manifest: papeete-actor-manifest/v0
name: Archivist
version: "2.2.0"
description: >-
  Keeps a ledger and answers about it.
```

- `manifest:` names the contract, exactly the role `card:` plays on `papeete-actor-card` — so
  this lineage gets its own version-migration story (v0 → v1 later, warn-not-fail, the same
  UNMIGRATED mechanism `cards.py` already runs for a `card:` mismatch) from day one, independent
  of the card's.
- `name` — the actor's name. `version` — where this actor stands, self-declared, free-form, no
  scheme mandated — the same non-mandate `identity.version` already established on the card
  contract (ADR-PA-0018), just relocated to a much smaller, standalone shape.
- `description` — free prose, what this actor is.
- **Filename: `actor.yaml`, not `papeete-actor.yaml`.** The latter stays exactly what it is
  today — the card contract's file — so there is no ambiguity about which gate a given file
  belongs to, and no risk of `cards.lint()` misreporting a fresh `actor.yaml` as an UNMIGRATED
  card: `cards.lint()` never checks the filename, only the `card:` key, and a manifest-only file
  has no such key.
- **The folder-root convention is documented, not mechanically checked.** "Everything under this
  folder belongs to the actor" isn't a claim a single-file lint can verify — there is nothing to
  compare it against. It lives as prose in the schema, the same spirit as
  `registry.schema.yaml`'s "the repo IS the actor's durable state" note (ADR-ECO-0012, this
  repo's own ADR-PA-0007 today).
- **Fully standalone.** `manifest.py` shares no code with `cards.py`. Its module shape mirrors
  `registry.py`'s `lint(path, schema=None) -> Report` — no `registry`/`profile` plumbing, this
  contract needs neither — and it adds one thing `registry.py` doesn't need: a `manifest:`
  self-declaration check mirroring `cards.py`'s `card:`-mismatch → UNMIGRATED warn. A deliberate
  combination, not an inconsistency: the module *shape* copies `registry.py`; the
  self-declaration *behavior* copies `cards.py`, because unlike a registry, a manifest is meant
  to carry its own version-migration lineage from day one.

## Rationale

**Three fields, because that is what "who is this actor" needs and nothing more.** Every field on
`papeete-actor-card` beyond identity — offers, publications, releases, dependencies,
subscriptions — answers a question this manifest deliberately does not ask. Reconciling the two
contracts, or deriving one from the other, was considered and rejected: it would re-couple a
contract designed to be minimal to one that is not, for no benefit to either.

**No relation to `papeete-actor-card`, on purpose.** This is not `papeete-actor-card/v3` with
fields removed, and it does not supersede anything. It is a second, independent lineage that
happens to live in the same repo. A consumer that wants both a manifest and a card carries both
files side by side; neither references the other.

## Consequences

- **Additive — no version bump beyond what was already staged.** Nothing existing depends on this
  contract, so there is no breaking change to announce and no `events/` record for it yet.
- **`papeete-actor contracts` now lists five contracts.** `CONTRACTS["manifest"] =
  "papeete-actor-manifest/v0"`, and both `__init__.py`'s and `cli.py`'s module docstrings were
  updated from "four" to "five" to match.
- **`cards.py`, `papeete-actor-card.schema.yaml`, `check.py`, and `papeete-actor-simple` are
  entirely untouched.** This ADR adds something new and independent; it reverts nothing built
  under ADR-PA-0018.
- **Two much larger ideas surfaced while designing this, deliberately not built here** — captured
  below as a non-binding reference only, so a future session does not have to re-derive them:

  - **The split, and its precedent.** The manifest stays pure identity. A second, separate
    artifact — not yet named or built — would map `{actor: name@version, target: ...}` to a
    running thing, reconciled by a pluggable backend per target. This is the same split Helm
    draws between `Chart.yaml` (identity) and `values.yaml`+templates (how to run it), and the
    same split Kubernetes draws between an image and a Deployment/Pod spec. The closest full
    precedent for "identity+state, agnostic of where it runs" as a runtime model is a
    virtual-actor framework (Dapr Actors, Orleans); the closest "just use containers" precedent
    is a Kubernetes StatefulSet (image + stable name + attached volume per instance).
  - **The entrypoint would be Docker-based, uniformly, including local.** Every target — local
    dev, FaaS, k8s — would run the same OCI image; no separate in-process or Procfile-style
    convention. One code path: `resolve(name, version, target) -> image ref`, then `docker run` /
    a container-image FaaS invocation / a k8s Deployment referencing it. The image's own
    `ENTRYPOINT`/`CMD` would be the actor's start command — the manifest never touches it.
  - **The build step would always be a hand-written `Dockerfile`**, one per actor, sitting beside
    `actor.yaml` in the same folder-root-convention directory (buildpack auto-detection was
    considered and rejected, in favor of full control and zero new build-tooling dependency). The
    folder-root convention would then resolve concretely to: `actor.yaml` (identity) +
    `Dockerfile` (build recipe) + the actor's own code, nothing more required.
  - **`name`+`version` → image reference would be resolved by the target, not the manifest.**
    Locally: no registry, no naming scheme — build on demand (`docker build -t <name>:<version>
    <folder>`), relying on Docker's own layer cache. For a remote target (FaaS/k8s), the *target*
    would supply a registry prefix, and CI would push `<registry>/<name>:<version>` at build
    time. The manifest itself would never name a registry — only the target would — so one actor
    stays portable across registries without its identity changing.
  - **Git's role would be build-time only.** Git is the *source* the Dockerfile builds from; once
    an image exists, git is out of the runtime loop entirely. `ADR-PA-0006`'s git-committed
    transactional outbox (an actor writing `events/{publication}/{ref}.yaml` back into its own
    repo at runtime) belongs to the existing, larger `papeete-actor-card` model this manifest
    deliberately does not inherit — messaging, publications, and any outbox needing live commit
    access are out of scope for this lineage and stay fully deferred to whatever an opt-in
    messaging layer becomes, if it ever gets built. This note takes no position on it.
  - **`product.yaml` — a registry-shaped file scoped to one deployable product.** Same row shape
    `ecosystem-registry/v0` already defines (`repo`, `papeete_actor`, `card`, `card_status`, ...)
    — only the file's own name and scope would differ. `registry.yaml` answers "what exists in
    this ecosystem" (potentially huge); `product.yaml` would answer "which of those compose *this
    one, runnable set of actors*" (small, deliberately scoped). Reusing the shape means
    `registry.classes()` (already built, unchanged) would keep working against either file — only
    rows it classifies `actor` would be candidates to run at all.
  - **Local discovery would need no new infrastructure — Docker's own network DNS already does
    it.** One shared, product-scoped Docker user-defined network; every actor's container started
    with `--name` set to its manifest `name` (normalized). Docker's embedded DNS then resolves
    that name to the container automatically for every other container on the same network —
    `docker-compose` already relies on exactly this mechanism. The remaining gap, the port, would
    be filled either by a fixed convention (every actor's `Dockerfile` `EXPOSE`s the same
    well-known port) or by the launcher — which would already know the full topology from
    `product.yaml` before starting anything — injecting one env var per peer into each container
    at launch (`ARCHIVIST_URL=http://archivist:8080`, the standard 12-factor/compose pattern).
    Neither requires a service registry, mesh, or sidecar, which would be solving a scale problem
    this "bare, local" tier doesn't have yet.
  - **A one-command bare-deployment launcher, to make e2e testing possible.** The practical
    target: `papeete-actor run-product product.yaml` would build each listed actor's image,
    create the shared network, and start every container; `papeete-actor stop-product
    product.yaml` would tear it back down. The pragmatic implementation would generate a
    `docker-compose.yml` from `product.yaml`'s rows (one service per actor) and shell out to
    `docker compose up -d` / `docker compose down` — Compose already owns the network/DNS
    mechanics above, so the only new code would be translating registry-shaped rows into compose
    services, not reimplementing container lifecycle management. This is what would make e2e
    testing practical: a test fixture (or CI step) running `run-product` before a suite and
    `stop-product` after, against real, fully networked containers rather than mocks.

  None of this is built or even contract-shaped yet — no schema, no module, no further ADR
  decision. It is recorded so the next session that picks up "make a manifest runnable" does not
  have to re-derive it.

  **Update.** This direction was built, in a later session, then split into its own standalone
  package once it existed — see [`papeete-hub/papeete-product`](https://github.com/papeete-hub/papeete-product),
  `ADR-PP-0001`. `product.yaml` ended up naming actors by `name`+`version` alone rather than
  reusing any registry row shape (there was no registry left to reuse from by then); everything
  else here — Docker-based, Compose-generated, network-DNS discovery, no env-var injection needed
  — landed close to this note.

  **Second update.** The manifest's own `version:` field described in the Design section above
  no longer exists — removed entirely by `ADR-PA-0022`. It is git's fact about an actor,
  computed fresh by `papeete-actor build` from the folder's own commit history, never declared in
  `actor.yaml`. `papeete-actor-manifest/v0` is down to two fields, `name` and `description`.
