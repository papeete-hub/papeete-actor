---
id: ADR-PA-0012
title: "papeete-actor — the conformance gates as a pinned distribution artifact, not a vendored script"
status: Proposed
date: 2026-07-22
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../registry.yaml                          # papeete-hub/papeete-actor + the pins edge
  - ../TOPOLOGY.md                            # the lab / distribution split this decision obeys
  - https://github.com/papeete-hub/papeete-actor    # the package: source, contracts.pin, release lane
  - ./ADR-ECO-0005-ecosystem-governance-context.md   # ECO.GOV owns contract + gate; runtime lives where it runs
  - ./ADR-PA-0010-offers-subscription-disposition-and-dependencies.md
  - ./ADR-PA-0011-publication-payload-schema-and-human-view.md
---

# ADR-PA-0012 — `papeete-actor`

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0017`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0017` elsewhere in the ecosystem refer to this record.

## Context

`papeete-actor-card/v1` shipped with a gate, `scripts/lint_card.py`, and the gate had nowhere to go.

ECO.GOV owns three contracts and enforces them three different ways. `lint_message.py` is
**vendored** into `settler`'s `work-pipeline` template beside a pinned copy of
`message.schema.yaml`, and repos byte-diff it with `check_pipeline_sync.py`. `publication/v2` has
**no ecosystem-wide gate at all** — `banking-knowledge` and `reliever-business` each wrote their
own. `lint_card.py` ran only from ECO.GOV's own checkout, over sibling repos.

Three problems with extending the vendoring path to the card gate:

1. **It reaches half the ecosystem.** Only `reliever-business`, `reliever-design` and
   `reliever-implementation` hold `work-pipeline.vendor.yaml`. The three `banking-*` repos pin no
   template, so nothing would deliver a gate to them.
2. **It is only ⅓ realised where it does reach.** Of those three repos, only
   `reliever-implementation` has actually vendored `lint_message.py`.
3. **It inverts the message gate's own lesson.** That gate runs in the **owner's** CI so a defect
   fails at home. A card gate that only ECO.GOV can run means a card defect waits for ECO.GOV to
   look — and ECO.GOV has no CI either.

Meanwhile `pyproject.toml` had been holding a slot for the answer since before this session:
*"Scripts-only repo for now (no importable package until the `papeete-actor` CLI lands)"*, and
`cards/README.md` already names the verb — *"`card` is the noun; `papeete-actor check` / `papeete-actor status`
(ADR-ECO-0005) is the verb"*.

## Decision

**1. The gates become one installable tool, `papeete-actor`.**

```
papeete-actor lint-card         papeete-actor.yaml…  papeete-actor-card/v1
papeete-actor lint-message      --issue-body         inter-agent-message/v0
papeete-actor lint-publication  REPO…                publication/v2
papeete-actor check             --workspace DIR      the cross-card join
papeete-actor contracts                              which contract versions this build enforces
```

One pin replaces three delivery mechanisms. A consumer runs `pip install papeete-actor==X` instead of
vendoring a script and diffing it.

**2. It is a dedicated source repo in the distribution org: `papeete-hub/papeete-actor`.**

`registry.yaml` is explicit: `papeete-foundry` is the **lab** — *"nobody pins the lab; it is the
origin"* — and `papeete-hub` is **distribution**, *"client-pinned side — versioned,
immutable-per-tag artifacts"*. A pip-installable, version-pinned tool is by definition
client-pinned, so it cannot live in the lab.

**This was decided twice.** The first form of this ADR kept the source here and made
`papeete-hub/papeete-actor` a generated publish target, on the `settler` → `plugins` model. That was
rejected on review, correctly: `papeete-hub` is not only build outputs — `kpack` and `kmint` are
hand-authored engines living there, pip- and image-pinned. `papeete-actor` is a third. The record shows
both because the rejected form's argument survives as decision 3's cost.

**3. The contracts are fetched at build time from a pinned ECO.GOV ref, never committed.**

`contracts.pin` names `papeete-foundry/ecosystem-governance` and an exact ref;
`scripts/fetch_contracts.py` resolves it into `src/papeete_actor/schemas/`, which is gitignored. A
committed copy would drift and would need a checker to catch the drift — the exact pattern this
package exists to delete.

Every gate **loads** its schema. None hard-codes a field, an enum, or a rule.

**THE COST, STATED PLAINLY.** Because the gate lives in one repo and the contract in another, **a
contract change and its gate change cannot land in one commit.** Between the two merges, a
published `papeete-actor` enforces a contract that has moved. That is a dual write, and ECO.GOV's own
publication contract names it as the thing a transactional outbox exists to prevent — this ADR
accepts one, knowingly, in a place the outbox does not reach.

Three things bound it. The pin makes every build reproducible against one exact contract state. The
window sits **between releases**, never inside one. And `papeete-actor contracts` prints which contract
versions any installed build enforces, so the disagreement is always visible rather than inferred.
Revisit if the window ever bites — the alternative shape is in this ADR's history, not lost.

Auth for the fetch falls on **one pipeline**, which is what distinguishes this from a private index:
the burden is not multiplied across seven consumer CIs.

**4. Published to public PyPI.** Both orgs are private today, so this is the ecosystem's first
public source artifact and it publishes the contract vocabulary with it. Accepted deliberately: the
alternative — a wheel on a private release, installed with a token — puts an auth requirement in
seven CIs, which is the friction `banking-tech` already documents against
`META_MODEL_READ_TOKEN`. `kpack`'s image is the partial precedent: a public artifact from a private
repo.

**5. `scripts/lint_message.py` is not touched, and is deliberately duplicated for now.** It is
vendored into settler's template and **byte-pinned** by `check_pipeline_sync.py` in the repos that
consume it; editing it would fail their pin check. `papeete_actor.messages` is a port beside it. The
duplication retires when those repos install `papeete-actor` instead of vendoring — which is a request to
`settler`, not something ECO.GOV can do.

**6. The tool version and the contract versions are different things.** `papeete-actor==0.1.0` implements
`papeete-actor-card/v1` + `inter-agent-message/v0` + `publication/v2`. A card declares the *contract*
version; CI pins the *tool*. `papeete-actor contracts` prints the mapping, so a consumer can see what a
given build enforces without reading its source. And because consumers pin it, **the pinning rule
binds**: a breaking release owes a record in `events/`.

## Rationale

The deciding argument is not convenience, it is **drift surface**. Vendoring a schema means every
consumer holds a copy that can disagree with the authority, and the ecosystem's answer to that has
been to write a checker per copy — `check_vendor_sync.py`, `check_pipeline_sync.py`,
`check_publications.py`. Each of those checkers exists because something was copied. A version pin
removes the copy, and with it the checker: there is nothing to diff when there is one artifact.

That is the same move ADR-PA-0008 made on obligations — replace an enumeration with the property
that generates it — applied to distribution. And it is the move the cards themselves already
document as the harder one: three cards state that their sync checks prove *identity* against a pin
and never *freshness* against upstream. A pinned package has the same property, but the pin is a
version with a changelog and a release, not a byte-diff of a file someone copied.

Publishing publicly is the uncomfortable half. The contracts are method IP, and this makes them
readable by anyone. It is accepted because a governance contract that cannot be installed without a
credential will not be installed, and an unenforced contract is the thing every ADR in this log has
been written to avoid.

## Consequences

- **`papeete-hub/papeete-actor` exists**, private, with a CI lane and a tag-triggered release lane using
  **PyPI Trusted Publishing** — no token is stored for the upload. Two things it still needs, and
  neither can be done from this repo: a *pending publisher* on pypi.org naming that repo and
  workflow, and a `CONTRACTS_READ_TOKEN` secret — a fine-grained, read-only, Contents-scoped PAT on
  `ecosystem-governance`. **Deliberately not minted from an existing broad-scope token**: the
  account token to hand carries `admin:org` and `admin:enterprise`, and storing that as a repo
  secret to read three YAML files would be a real security downgrade for a convenience.
- **`papeete-actor` is probably a papeete-actor, and is not treated as one yet.** By the ADR-PA-0009 §1 test it
  has a repo, durable state others depend on, and an address that can receive a request — but no
  human+agent pair. That is exactly `kledger`'s position, which stays `card_status: none` until a
  pair exists. Following that precedent rather than inventing a new one. It also *consumes*
  ECO.GOV's contracts, which is a subscription under §5 — undeclared, because it has no card to
  declare it in. A known, recorded gap.
- **ECO.GOV now depends on `papeete-actor`, and `papeete-actor` depends on ECO.GOV's contracts.** A cycle at
  the artifact level, resolved the way cycles always are here: by version pins in both directions.
  `papeete-actor` pins a contracts ref; ECO.GOV pins a `papeete-actor` version. Neither is ever built against a
  moving target — but the cycle is real and worth naming rather than discovering later.
- **Nothing is published yet.** The wheel builds, installs into a clean venv, and resolves its
  schemas from `site-packages` — verified. The publish step is deliberately not taken in the same
  pass as the decision to take it.
- **`scripts/lint_card.py` is removed**, and the package source with it. ECO.GOV keeps
  `check_ecosystem.py` and `lint_message.py` and gets the other three gates the way every consumer
  does — by installing `papeete-actor`. The ADR-ECO-0005 split, applied to its own author.
- **`papeete-actor check` closes the join** that ADR-PA-0009 §5 specified and nothing computed —
  ECO.GOV's standing nonconformity (#10.5). It reports four classes and explicitly **does not**
  compute the fifth: undeclared consumption is not decidable from cards, by construction.
- **The join's first run corrected two of its own bugs.** `papeete-hub/kpack` was reported as a
  dangling subscription in two repos because the source id was split at the first `/`, yielding the
  org; ADR-PA-0009 §2 exists precisely so that edge reports as *external*. And the publication
  count was double-counting, because the index is keyed under both a papeete-actor id and a repo name so a
  consumer may name either.
- **A papeete-actor release is itself a publication.** ECO.GOV's card gains it, and — since consumers
  will pin it — it carries `breaking_flag`. This is the first ECO.GOV publication whose consumers
  pin something other than prose.
- **Not decided: whether `settler`'s template stops vendoring `lint_message.py`.** That is
  settler's call and needs a request on a rail; ECO.GOV can only file it.
- **Not decided: whether the gates run in each repo's CI, and on what trigger.** Installing a tool
  is not running it. The message gate's reference workflow is the model, but every repo owns its
  own CI.
