---
id: ADR-PA-0021
title: "Building an actor is this repo's job, not a product's"
status: Accepted
date: 2026-08-20
supersedes: []
references:
  - src/papeete_actor/build.py
  - src/papeete_actor/cli.py
---

# ADR-PA-0021 — Building an actor is this repo's job, not a product's

## Context

The `build` command — reading one actor's `actor.yaml`, building its `Dockerfile`, tagging the
result `<name>:<version>` on the local Docker image store — was first built inside
`papeete-product`, alongside `lint`/`run`/`stop`, because that was where the whole
manifest-to-runnable-thing question was being worked out (`ADR-PA-0019`'s forward note,
`papeete-product`'s `ADR-PP-0001`).

Reviewed and corrected: building one actor is entirely a **single-actor** operation. It needs
`actor.yaml` and a `Dockerfile`, both of which live in the actor's own folder — the folder-root
convention this repo's own contract already documents — and nothing about any *other* actor.
`papeete-product` exists specifically for the concern that only shows up once there is more than
one actor (naming a set, running it together, letting its members discover each other). Building
one actor doesn't need a product to exist at all.

## Decision

**`papeete-actor build FOLDER...` moves here.** `src/papeete_actor/build.py` exposes
`image_tag(name, version) -> str` and `build_actor(folder) -> str`, the latter reading the
folder's own `actor.yaml`, running `docker build -t <name>:<version> <folder>`, and returning the
tag. `papeete-product` no longer has a `build` command at all, and `product.py` never shells out
to `docker build` or opens an `actor.yaml` — it only ever consumes tags this command already
produced.

**The tag lands on the local Docker image store, never a registry.** No push, no registry prefix
— that remains a real, open question for a remote target (FaaS/k8s), same as it was before this
move; this decision only relocates *where in the codebase* local building happens, not what it
does.

## Rationale

**A contract's own repo owns turning its instances into runnable things.** `papeete-actor`
already owns the whole of an actor's folder — `actor.yaml`, the folder-root convention, and now
the one build step that folder supports. `papeete-product` owns only what spans actors:
composition, naming a set, orchestration, discovery. Splitting `build` out kept a
single-actor concern inside the package that already fully understands a single actor, rather
than reaching for it from the package one layer up.

**This mirrors the manifest/product split itself.** `ADR-PA-0019` kept `papeete-actor` to
identity; `ADR-PP-0001` (in `papeete-product`) kept the product contract to identity-of-a-set. A
`build` command that touches a folder is neither of those — it's the operational step that makes
identity resolvable to something running, and it belongs with the repo that owns the folder, not
the repo that only ever consumes the tag.

## Consequences

- **`papeete-actor` gains its first non-lint capability.** Every prior command in this repo
  validated something; `build` is the first one that produces something (an image). It stays
  scoped to exactly one actor's folder — no cross-actor behavior, no orchestration, nothing a
  product contract would otherwise own.
- **New test**: `tests/test_build.py` — `image_tag()` is a pure, always-run unit test;
  `build_actor()` is marked `e2e` (real `docker build`, skipped automatically when no daemon is
  reachable), building and tearing down a throwaway image so it leaves nothing behind.
- **The worked example (`customer`/`waiter`) stays in `papeete-product`**, not here — it exists
  to demonstrate composing and running a *set* of actors, which is that repo's concern. This
  repo's own `build_actor()` test uses a synthetic, throwaway actor instead of that narrative.
- **`papeete-product`'s docs and `ADR-PP-0001` updated** to say `papeete-actor build` is the
  documented way to produce the images `papeete-product run` expects — see that repo.
