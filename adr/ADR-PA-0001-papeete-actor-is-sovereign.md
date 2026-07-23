---
id: ADR-PA-0001
title: "papeete-actor is sovereign — it carries the contracts, the gates, and its own decisions"
status: Proposed
date: 2026-07-23
supersedes: [ADR-ECO-0017]     # and retires ADR-ECO-0005 §3's placement of the contract
references:
  - ../src/papeete_actor/schemas/          # the contracts, committed source
  - ../papeete-actor.yaml                  # this repo's own card, under its own contract
  - https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0018-papeete-actor-the-term.md
---

# ADR-PA-0001 — papeete-actor is sovereign

## Context

`papeete-actor` shipped as a **gate without a spec**. The three contracts it enforces —
`papeete-actor-card/v1`, `inter-agent-message/v0`, `publication/v2` — lived in
`papeete-foundry/ecosystem-governance`, and this package fetched them at build time from a pinned
commit (`contracts.pin` → `scripts/fetch_contracts.py` → a hatchling build hook).

That design was chosen deliberately and it failed on three counts, two of them recorded in advance
by the very documents that chose it.

**1. It broke the atomicity rule that created ECO.GOV in the first place.** `ADR-ECO-0005`'s first
rationale bullet:

> **Spec and checker must version atomically.** A contract change and its gate change land in one
> commit, one tag; **splitting them across repos is a drift generator.**

`contracts.pin` admitted the violation in its own header — *"a contract change and its gate change
CANNOT LAND IN ONE COMMIT … That is a dual write"* — and closed with *"revisit if the window ever
bites."*

**2. It bit immediately.** `ADR-ECO-0018` renamed the card contract and its schema file. The gate
and the contract could not move together; between the two merges this package pinned a commit whose
schema filename no longer existed.

**3. It made the package unbuildable by anyone outside the lab.** `ecosystem-governance` is private,
so the build needed a `CONTRACTS_READ_TOKEN`. That secret was never set, and **every CI run since
this repo was created failed on it** — three for three, including two that predate the rename. This
is the decisive one, and it is not a configuration oversight: a distribution artifact whose build
requires a credential to a private lab repo **cannot be built by the organisations it exists for**.
If Papeete's own pipeline could not authenticate, a client standing up its own papeete-actor never
could.

`TOPOLOGY.md` states the org test as *"does a consumer pin/depend on it? → distribution"*. Every
actor's card declares `papeete-actor-card/v1`; the contract is pinned by every actor in the
ecosystem. It was in the lab, and the test says that was wrong. `ADR-ECO-0005` placed it there in
2026-07, before the card contract existed as a pinned artifact at all.

## Decision

**1. This repo carries the contracts.** The three schemas are ordinary committed source under
`src/papeete_actor/schemas/`. `contracts.pin`, `scripts/fetch_contracts.py` and `hatch_build.py` are
deleted, as is the `CONTRACTS_READ_TOKEN` requirement. A build reaches nothing outside its own
checkout.

> **The package IS the contracts.** It is not a gate that goes looking for them.

**2. Spec and checker version atomically, as ADR-ECO-0005 always required.** A contract change and
its gate change land in one commit and one tag. The dual write is dissolved rather than bounded.

**3. This repo is sovereign, and carries its own decisions.** `adr/ADR-PA-*` is this repo's decision
log — the shape `reliever-design` already uses (`ADR-DSN-0001`, its own context charter). Decisions
*about the contracts* are recorded here, beside the schemas they change. `ADR-ECO-*` remains the
ecosystem's log for ecosystem-level decisions: the org split, the registry, the operating model,
the topology.

**4. `ECO.GOV` becomes a consumer like any other.** It pins `papeete-actor` to obtain the contracts
and the gates, exactly as `banking-knowledge` or `reliever-business` will. It keeps the registry,
the operating model, the topology, the decision log for ecosystem-level questions, and supervision.
It stops owning the contract artifacts — recorded from its side in `ADR-ECO-0019`.

**5. This repo carries its own card**, `papeete-actor.yaml`, conforming to
`papeete-actor-card/v1` — the contract it ships. The tool that validates papeete-actors is itself a
papeete-actor, and its CI validates its own card with its own gate on every push. That recursion is
the cheapest possible end-to-end test: if the schemas failed to ship, or the gate could not read
them, the card check fails.

## Rationale

The autonomy argument is the one that decides it, and it is not about convenience. **An organisation
must be able to stand up a papeete-actor without depending on Papeete for anything at runtime.** The
whole point of a distributed actor model is that a box is self-describing and self-validating; a
contract that can only be read by someone holding a credential to the author's private repo is not a
published contract, it is an internal one with extra steps.

The counter-argument for the old design was *"a copy in git is a copy that drifts, and deleting
copies is why this package exists."* It does not apply here, because **this is not a copy.** After
this decision there is exactly one home for each schema. The drift risk existed precisely while
there were two places — a source in the lab and a fetched artifact in distribution — with a window
between their merges. Moving the source removes the second place rather than adding one.

What is genuinely given up: ECO.GOV can no longer change a contract and see the gate change in the
same review. That was already false — it is what `contracts.pin` documented. What replaces it is
better: the contract and its gate are now in one repo, one commit, one tag, one review.

## Consequences

- **CI goes green with no secret.** The pipeline builds, installs the wheel into a clean venv,
  asserts the contracts shipped, and lints this repo's own card. None of it touches the network
  beyond the checkout.
- **`pip install papeete-actor` yields the contracts.** A consumer holds the spec and the gate from
  one pin. `papeete-actor contracts` reports which versions a given build enforces.
- **`ecosystem-governance` deletes `ecosystem/contracts/*.schema.yaml`** and pins this package
  instead. Its `contracts/README.md` becomes a pointer. See `ADR-ECO-0019`.
- **The registry's back-pointing edge disappears.** `registry.yaml` recorded a `pins` edge from
  distribution *back to* the lab and called it *"the one edge that points from distribution BACK to
  the lab … a cycle at the artifact level."* There is no cycle now; the dependency runs one way.
- **This repo needs a pair to be a conformant papeete-actor.** It has one — human `architect`,
  `agent: none` — the same position `banking-tech` and `ECO.GOV` hold. The registry's
  `card_status: none` becomes `adopted`.
- **The version story is unchanged**: the tool version and the contract versions still move
  independently, and `papeete-actor contracts` still prints the mapping. What changed is that a
  given tool version now *contains* the contracts it claims, rather than having fetched them.
- Not decided here: whether the template that scaffolds a new papeete-actor ships in this package
  (`papeete-actor new`) or in a separate artifact. Sovereignty makes the former possible; it does
  not make it right, and nothing depends on the answer yet.
