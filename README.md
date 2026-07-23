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

## The contracts are in this repo

[`src/papeete_actor/schemas/`](./src/papeete_actor/schemas/) — ordinary committed source. **The
package IS the contracts**, not a gate that goes looking for them
([ADR-PA-0001](./adr/ADR-PA-0001-papeete-actor-is-sovereign.md)).

That is what makes an organisation able to stand up a papeete-actor without depending on Papeete for
anything. The previous design fetched the schemas at build time from a private lab repo, which meant
a build needed a credential nobody outside the lab could have — and spec and gate could not change
in one commit, the drift generator `ADR-ECO-0005` was written to prevent.

Every gate **loads** its schema. None hard-codes a field, an enum, or a rule.

```bash
uv build      # no network, no token, no fetch step
```

`papeete-actor` also holds its own card, [`papeete-actor.yaml`](./papeete-actor.yaml), under the
contract it ships — and CI lints it on every push. If the schemas failed to ship in the wheel, or a
gate could not read them, that check fails.

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
