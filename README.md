# papeete-actor

Conformance gates for the [Papeete](https://github.com/papeete-foundry) ecosystem contracts.

```
papeete-actor lint-card         papeete-actor.yaml…  papeete-actor-card/v1
papeete-actor lint-message      --issue-body         inter-agent-message/v0
papeete-actor lint-publication  REPO…                publication/v2
papeete-actor check             --workspace DIR      the cross-card join
papeete-actor contracts                              which contract versions this build enforces
```

```bash
pip install papeete-actor
```

## What it enforces

An **actor** in this ecosystem is one repo, one human+agent pair, one mailbox, one card. The card —
`papeete-actor.yaml` at the repo root — declares four things, and each has exactly one owner:

| Section | Says | Owned by |
|---|---|---|
| `offers` | what I can be asked to do | me; the **caller** decides whether to ask |
| `publications` | facts I emit — `means` (prose) **and** `shape` (payload schema) | me |
| `subscriptions` | facts I pull, and **what I do about them** | me, about someone else's publication |
| `dependencies` | whose contract I resolve, and at what ref | me |

Two rules do most of the work:

> **The producer supplies meaning. The consumer declares intent. Nobody writes a handler.**

A publication says what a fact *is* and why it might concern a reader — never what a reader should
do about it. That belongs in the consumer's own card, under the consumer's own review. It is
[MCP](https://modelcontextprotocol.io)'s rule applied to facts instead of tools.

> **Determinism sits at existence, never at interpretation.**

*"Has anything appeared after my position?"* must stay deterministic — if a model decides what it
has already seen, consumption stops being idempotent. *"Does this fact matter to me?"* is
irreducibly judgement. A subscription declares both halves separately, and `papeete-actor` checks that
the deterministic half stays deterministic.

## The contracts are not in this repo

They are owned by `papeete-foundry/ecosystem-governance` and **fetched at build time** from the ref
in [`contracts.pin`](./contracts.pin). Nothing under `src/papeete_actor/schemas/` is committed: a copy in
git is a copy that drifts, and deleting copies is the entire reason this package exists rather than
each repo vendoring a script and byte-diffing it.

Every gate **loads** its schema. None hard-codes a field, an enum, or a rule.

```bash
python3 scripts/fetch_contracts.py   # resolves contracts.pin (needs read access to the source repo)
uv build
```

## Versioning

The tool version and the contract versions are different things and move independently.
`papeete-actor contracts` prints the mapping for any installed build:

```
papeete-actor 0.1.0  —  contracts from …/site-packages/papeete_actor/schemas
  ok   papeete-actor-card papeete-actor-card/v1
  ok   message            inter-agent-message/v0
  ok   publication        publication/v2
```

A card declares the **contract** version; your CI pins the **tool**.

## What it does not do

`papeete-actor check` computes four conformance classes — dangling subscription, unsubscribed
publication, unschematised publication, unpinned scripted subscription. It deliberately does not
compute the fifth, **undeclared consumption**: the evidence for that lives in consumer source code,
not in cards, so detection is a heuristic and a heuristic finding is a prompt to declare, never a
verdict.

## Licence

MIT.
