---
id: ADR-PA-0025
title: "An actor's folder may declare its own k8s and Terraform deploy config"
status: Accepted
date: 2026-08-22
references:
  - src/papeete_actor/build.py
  - src/papeete_actor/manifest.py
---

# ADR-PA-0025 — An actor's folder may declare its own k8s and Terraform deploy config

## Context

[`papeete-deploy`](https://github.com/papeete-hub/papeete-deploy) is gaining a k8s deployment path
alongside its existing local Docker Compose one. A real, production-shaped k8s deploy needs more
than `papeete-deploy` can synthesize on the fly from an actor's `name` and image tag alone —
resource shape, replica count, probes, and environment-specific overlays are all things a real
Deployment/Service pair needs, and inventing a generic one that fits every actor is the wrong
layer to solve that at. The natural owner of that shape is the actor itself, the same way
`Dockerfile` already lives in the actor's own folder rather than being synthesized by whatever
builds it.

## Decision

**An actor's folder MAY contain a `deploy/` subfolder**, alongside `actor.yaml` and `Dockerfile`,
with two optional parts:

- **`deploy/k8s/`** — a [kustomize](https://kustomize.io) layout: `base/` (a plain Deployment +
  Service, the actor's own baseline) and `overlays/<name>/` (one folder per deploy target — e.g.
  `develop` — each a self-contained kustomization referencing only `../../base`, no shared remote
  base). Fully actor-authored; this repo does not generate, validate, or read any of it.
- **`deploy/terraform/`** — convention only, not executed by anything yet. Reserved for
  infrastructure an actor needs that outlives a single deploy (a database, a queue) and doesn't
  belong in a Kubernetes manifest.

**The base Deployment's container image must be named exactly the actor's own normalized name,
with no tag** (e.g. `image: customer`, never `image: customer:0.1.0-alpha-abc1234` or a registry
prefix) — this is the hook a deploy tool needs to inject the resolved image and tag at deploy time
via `kustomize edit set image` or an equivalent overlay, without editing the actor's own files.

## Rationale

**This mirrors `Dockerfile`'s own precedent.** `ADR-PA-0021` already established that an actor's
folder is a self-contained unit an actor author writes, and that building from it is a mechanical
step performed by tooling — not a shape that tooling invents. `deploy/k8s/` and `deploy/terraform/`
extend that same folder with more actor-authored, tool-consumed content; they don't change what
kind of thing an actor's folder is.

**Kustomize's `base`+`overlays` split is a widely-used, production-proven pattern** (reviewed
against a real internal deploy folder while designing this) for keeping one baseline manifest and
layering per-environment differences on top without duplicating YAML. Adopting it here rather than
inventing a bespoke shape means an actor author who already knows kustomize needs to learn nothing
new, and a deploy tool can drive it with kustomize's own CLI/library rather than a custom parser.

**The fixed, tagless image name is the minimum contract a deploy tool needs, and no more.** It
doesn't prescribe replica counts, resource limits, probes, or labels — those stay entirely the
actor author's call, same as `Dockerfile`'s own contents always have been. A deploy tool only ever
needs to find the container by name and overwrite its tag.

## Consequences

- **No code change in this repo.** `build.py` and `manifest.py` read nothing under `deploy/` today
  and continue not to — this ADR documents a convention a *different* repo
  (`papeete-deploy`) consumes, not a contract this one enforces or validates.
- **`deploy/` is entirely optional.** An actor with no k8s deploy target (Compose-only, for
  example) simply omits it; nothing in this repo or `papeete-actor-manifest/v0` requires its
  presence.
- **No shared remote kustomize base.** Every actor's `overlays/<name>/` points only at its own
  `../../base` — deliberately, so one actor's deploy config never depends on another's, or on
  infrastructure external to its own folder.
- **Terraform folder is convention-only for now.** Nothing in the Papeete ecosystem executes it
  yet; it exists so actor authors have a documented place to put it when something does.
- **Open — who validates the base image name.** Nothing here enforces "the base Deployment's image
  matches the actor's normalized name" at authoring time; a mismatch surfaces only when a deploy
  tool tries and fails to find the container to retag. Whether that becomes a lint check (here or
  in the consuming deploy tool) is undecided.
