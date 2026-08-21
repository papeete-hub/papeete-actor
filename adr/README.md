# Decision log (`ADR-PA-*`)

Decisions owned by **this repo**: the `papeete-actor-manifest/v0` contract, the gate that
enforces it, and this package's own boundary and release policy.

## The log

| ID | Title | Status |
|----|-------|--------|
| [ADR-PA-0018](./ADR-PA-0018-a-card-declares-its-own-version.md) | A card declares its own version | Accepted |
| [ADR-PA-0019](./ADR-PA-0019-a-minimal-standalone-actor-manifest.md) | A minimal, standalone actor manifest, deliberately apart from the card contract | Accepted |
| [ADR-PA-0021](./ADR-PA-0021-building-an-actor-is-this-repos-job.md) | Building an actor is this repo's job, not a product's | Accepted |
| [ADR-PA-0022](./ADR-PA-0022-version-is-gits-fact-never-a-declared-field.md) | Version is git's fact, never a declared field | Accepted |
| [ADR-PA-0023](./ADR-PA-0023-version-is-semver-label-and-short-sha.md) | Version is semver core (from a tag) + an uninterpreted label + short SHA | Accepted |

`ADR-PA-0018` documents a decision made on the `papeete-actor-card` contract, which this repo no
longer carries — kept for its reasoning about self-declared versioning, not because that contract
still exists here. Numbers below `0018` were allocated to decisions about that removed contract
and the doctrine around it (the agent operating model, the message contract, the publication
outbox, the registry shape), and were removed along with it rather than renumbered.

**`ADR-PA-0020` moved.** A product contract and Docker-based launcher were built directly on this
manifest, then split into their own standalone package —
[`papeete-hub/papeete-product`](https://github.com/papeete-hub/papeete-product), `ADR-PP-0001`.
Nothing that decision describes remains in this repo, so it does not stay in this log either.

## Authoring

Copy [`template.md`](./template.md), take the next `NNNN`, keep it short, and link the canonical
source where the decision is implemented rather than restating it.
