---
id: ADR-PA-0016
title: "The deployment profile — a contract describes shapes; it may not name one domain's values"
status: Proposed
date: 2026-07-24
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../src/papeete_actor/profiles/papeete.yaml       # this deployment's answer
  - ../src/papeete_actor/profile.py                  # the loader
  - ../src/papeete_actor/schemas/message.schema.yaml # `profiled:` replaces the hard-coded values
  - ../doc/INTER-AGENT-MESSAGES.md
  - ./ADR-PA-0001-papeete-actor-is-sovereign.md
  - ./ADR-PA-0008-publication-obligations-pinning-backfill-interior-bindings.md
---

# ADR-PA-0016 — The deployment profile

## Context

`inter-agent-message/v0` hard-coded two values that are facts about **one deployment's domain**, not
about the contract:

```yaml
enums:
  rail: [functional-gap, contract-deviation, engineering-debt]
scope_grammar: '^BNK\.[A-Z]+(\.CAP\.[A-Z0-9]+(\.[0-9]+(\.[A-Z0-9]+)?)?)?$'
```

`papeete-actor-card/v1` carried the same rail enum on `offers[].rail`.

**This is not a wart, it is a wall.** `scope` is in `payload.required`, and the grammar admits
nothing without the literal `BNK.` prefix. Measured on this build before the change:

```
scope: HELLO.APP.001    -> FAIL  not a well-formed capability node
rail: needs-translation -> FAIL  not one of [functional-gap, contract-deviation, engineering-debt]
```

So an organisation outside the banking domain **could not emit a conformant message at all**. The
only route to conformance was to name its own contexts `BNK.something` — adopt another domain's
prefix for a domain that is not that one.

That contradicts the decision this package exists to serve. `ADR-PA-0001` moved the contracts here so
*"an organisation must be able to stand up a papeete-actor without depending on Papeete for
anything,"* and argued that *"a contract that can only be read by someone holding a credential to the
author's private repo is not a published contract, it is an internal one with extra steps."* A
contract that can only be **satisfied** by someone inside the author's domain fails the same test for
the same reason — the barrier is a vocabulary rather than a credential, and it binds harder, because
a credential can be granted.

It was found by asking what the first non-banking implementation would need, and it blocks that work
completely: a request-only implementation uses `inter-agent-message/v0` and nothing else, so it meets
the one contract that is domain-locked.

## Decision

**1. A contract describes shapes. A deployment profile supplies this deployment's values.**

The two schemas keep the FIELDS required — `rail` and `scope` are contracted, and a finding that
routes nowhere or names no owner is exactly the noise floor `ADR-PA-0003` exists to prevent. What
moves out is *which values are legal*, into a profile:

```yaml
profile: papeete-banking
contract: deployment-profile/v0
rails: [functional-gap, contract-deviation, engineering-debt]
scope_grammar: '^BNK\.[A-Z]+(\.CAP\.[A-Z0-9]+(\.[0-9]+(\.[A-Z0-9]+)?)?)?$'
```

Each schema names what it delegates in a `profiled:` block, so the delegation is legible where the
value used to be rather than being an absence a reader must notice.

**2. A profile may under-constrain, deliberately.** Omit `scope_grammar` and `scope` stays required
but unconstrained; omit `rails` and any rail is accepted. This is the honest position for a
deployment that has not built a taxonomy or fixed its routing yet — and it is where a first
implementation starts. The alternative, forcing a new deployment to invent a taxonomy before it can
send one message, is how a contract acquires ceremonial fields nobody means.

**3. The shipped profile is a reference, not a privilege.** `profiles/papeete.yaml` is the default,
so the ecosystem this package grew in keeps working with no flag and no migration. It is one
deployment's answer that happens to ship here. `--profile FILE` takes another.

**4. `papeete-actor contracts` prints the profile beside the contract versions.** A consumer asking
which shapes a build enforces needs to know which deployment's values it will enforce them against.
Reporting one without the other is how the disagreement stays invisible — the same reasoning that put
`contracts` in the CLI at all (`ADR-PA-0012` §6).

## Rationale

This is the house method, applied to vocabulary: **replace an enumeration with the property that
generates it.** `ADR-PA-0008` retired `breaking_required_for: [vendored-artifact]` because it named
one mechanism where the reason was *consumers pin it*. `ADR-PA-0010` retired `external: true` because
externality derives from the registry. Here `[functional-gap, contract-deviation, engineering-debt]`
is a list of one factory's tiers, mistaken for the concept; *a rail is a routing dimension the
deployment defines* is the concept, and it covers a factory with two tiers or five.

The three rails are also the sharpest instance of the layer rule the ecosystem already enforces on
itself. `ADR-PA-0005` §1: *"Domain-layer words describe what a business is. Ecosystem-layer words
describe how papeete-actors interoperate."* `functional-gap` describes what **this** business's tiers
decide. It was sitting in an ecosystem-layer contract, and `BNK.` — a domain id prefix — was sitting
in a regex beside it.

The counter-argument is that a profile is one more file to keep in step with reality, and that the
old shape at least could not drift. It does not survive contact with the numbers: the old shape could
not drift because it could not be *used*, by anyone but its author.

## Consequences

- **Nothing changes for the existing ecosystem.** Verified: all nine cards return exactly the results
  they returned before, `check --workspace` is identical at `1 passed, 12 warned, 4 noted`, and a
  banking payload still passes while `HELLO.APP.001` still fails — under the default profile.
- **A foreign deployment can now conform.** Verified with a `hello-world` profile declaring
  `rails: [needs-translation, needs-review]` and `^HELLO\.[A-Z0-9]+(\.[0-9]+)?$`: the same payload
  that fails under the banking profile passes under its own, and a card carrying `rail:
  needs-review` lints clean.
- **A bare profile leaves values free and fields required.** Verified: a payload with no `rail` and
  no `scope` fails on both, under a profile that constrains neither.
- **The rail-label discriminator weakens under a profile with no rails.** `lint_issue` uses the rail
  set to catch an artifact that CLAIMS to be a message and dropped its envelope. With no rails
  declared, only the envelope discriminates. Stated in the code rather than left to be discovered: a
  silently weaker gate is worse than a declared one.
- **`work-observability/v0` still hard-codes the grain ladder** in `WORK-OBSERVABILITY` §3, with
  `BNK.*` ids in the table. Its `scope` field has the same problem, and no gate enforces it today —
  which is why it is not fixed here. It owes the same treatment when a gate for it exists.
- Not decided: **whether the reference profile ships in this package permanently.** The endgame of
  the interface split is that a deployment's values live with the deployment, which would put
  `papeete.yaml` in `ecosystem-governance` and leave this package with none. Shipping it is what
  makes this change non-breaking today; nothing depends on that staying true.
- Not decided: **where a deployment declares its profile without a flag.** `--profile` is explicit
  and works; a discovered default (beside the registry, or named in a card) would be less typing and
  one more thing to resolve. Deferred until a second deployment exists to make the question concrete.
