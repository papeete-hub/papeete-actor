---
id: ADR-PA-0017
title: "The registry shape is a contract; the registry is not"
status: Accepted
date: 2026-07-24
supersedes: []
references:
  - src/papeete_actor/schemas/registry.schema.yaml
  - src/papeete_actor/registry.py
  - src/papeete_actor/profiles/papeete.yaml
---

# ADR-PA-0017 — The registry shape is a contract; the registry is not

## Context

A papeete-actor carries its card at its own repo root, because the repo IS the actor's durable
state (ADR-PA-0007). That buys sovereignty and costs discoverability: no card says where any other
card lives, and the cross-card join needs every card at once. An index answers that — the role
A2A's well-known path plays, for an ecosystem whose actors are repos.

**Two published contracts already depend on that index, and it had no contract of its own.**
`papeete-actor-card/v1` makes externality *derive* from `card_status`, and names
`ecosystem/registry.yaml` "the sole authority for WHERE a card lives". The shape those rules read
was stated in Python — a dict comprehension in `cards.registry_classes` — and nowhere else.

So a consumer could install the package, hold all three contracts, satisfy every one of them, and
still be unable to author the file the gates read. The path was hard-coded to one organisation's
directory layout (`ecosystem-governance/ecosystem/registry.yaml`), the entry fields were whatever
the code happened to look up, and the classification rule — including the load-bearing fact that
*absent* `card_status` means "not an actor" — existed only as an `else` branch.

That is the failure ADR-PA-0001 refused to ship, one level down. Its argument was that a contract
readable only by someone holding a credential to the author's private repo "is not a published
contract, it is an internal one with extra steps". A contract whose *index* can only be authored
by reading the author's source fails the same test.

## Decision

**Ship `ecosystem-registry/v0` as a fourth contract, describing the INDEX and nothing else.**

- `src/papeete_actor/schemas/registry.schema.yaml` — ordinary committed source, in the wheel, like
  the other three.
- `papeete-actor lint-registry` gates it. `papeete-actor contracts` reports it.
- `registry.classes` reads `classification` out of the schema rather than restating it, so the
  gate that reports a misclassification and the join that acts on one cannot drift apart.
- **Where the registry lives moves to the deployment profile** (`registry.locations`), for exactly
  the reason the rails and the taxonomy grammar did (ADR-PA-0016). A profile that omits the key
  falls back to the reference layout, so nothing that resolved before stops.

**The contract describes four fields: `repo`, `papeete_actor`, `card`, `card_status`.** Those are
what the gates read. Everything else in a registry is the deployment's own and is reported as a
note, never an error.

## Rationale

**The shape is mine; the map is not.** This repo's `hard_boundary` says it "does not own the
ecosystem's map, its operating model or its topology — those stay with ECO.GOV". That line is
what makes the scope decision easy rather than arbitrary: the reference registry carries `orgs`,
`edges`, `contexts_ref`, and eleven per-row fields modelling how two organisations converge. None
of that is a shape any other deployment must share, and a rule about it here would be the altitude
violation ADR-ECO-0007 names.

The distinction is one this repo already made twice. ADR-PA-0016 separated *a contract describes
shapes* from *a deployment supplies values*. This is the same cut applied to the index: the shape
of a discoverability record is ecosystem-layer and belongs with the contracts; which repos exist,
who governs them and how they are laid out is one deployment's content and belongs to whoever owns
that deployment. **A conformant registry is a subset claim, never a whole-file one.**

**Absence had to stay meaningful.** The obvious schema makes `card_status` required. That would
have erased the only way a registry can say "this repo is not an actor" — the distinction that
keeps `papeete-hub/kpack` from being reported as a dangling subscription in every repo that
consumes it (ADR-ECO-0014 §2). So `card_status` is optional and its absence is a positive
statement, stated in the contract as such.

**The gate earns its place with one class the join cannot report.** A row saying `card_status:
adopted` with no `card:` path is skipped by `check.run` *in silence* — the card is absent from
every cross-card result and nothing says so. The registry asserts the card exists while withholding
the one field needed to read it. That is the confident, precise, wrong answer this tool exists to
prevent, and it is decidable from the index alone.

## Consequences

- **Additive, so 0.4.0 → 0.5.0.** No existing shape moved and no card, message or publication
  changes meaning. The one behavioural change is registry *discovery*, which now follows the
  profile; the shipped profile lists the previous hard-coded paths, so the reference deployment
  resolves exactly as before.
- **`cards.registry_classes` is kept as the name consumers import** and delegates to
  `registry.classes`. The rule moved; the entry point did not.
- **The reference registry conforms as it stands** — 15 rows, 9 actor, 6 external, one note
  summarising the twelve fields that are the deployment's own. It was not edited to fit.
- **Reporting had to agree with the contract.** The first cut noted every unnamed key on every
  row: 65 notes against a registry that conforms perfectly. A contract saying `unknown_key: NOT A
  DEFECT` cannot have a gate that reports each one, so they are counted and summarised once.
- **Open — the placeholder row.** `<client>/<name>` is a template row that indexes nothing. It is
  noted rather than failed, on the grounds that a registry scaffolding per-client orgs has a real
  use for it. Whether a contract should bless a placeholder at all, or whether that belongs in a
  separate template file, is undecided.
- **Open — `card:` is a path, and nothing checks it resolves.** `lint-registry` reads the index
  alone by design, so "this path points at no file" is `check`'s to report and `check` currently
  does not: it skips a missing card with a note only when `card_status` is not `none`. The two
  gates between them still cannot distinguish "the row is wrong" from "the repo is not checked
  out here".
