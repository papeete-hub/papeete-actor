---
id: ADR-PA-0004
title: "The inter-agent message contract — a message is not its transport; GitHub issues are one binding"
status: Proposed
date: 2026-07-15
supersedes: []
references:             # canonical sources where this decision is implemented (link, don't restate)
  - ../INTER-AGENT-MESSAGES.md
  - https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml
  - ../../scripts/lint_message.py
  - https://github.com/papeete-foundry/settler/blob/main/templates/work-pipeline/tools/render_message.py
  - ../WORK-OBSERVABILITY.md
  - https://github.com/papeete-foundry/reliever-design/issues/3
---

# ADR-PA-0004 — The inter-agent message contract — a message is not its transport; GitHub issues are one binding

> **Moved from `papeete-foundry/ecosystem-governance`, where it was `ADR-ECO-0008`.**
> The decision is unchanged and so is its date — what moved is the repo that owns it
> ([ADR-ECO-0019](https://github.com/papeete-foundry/ecosystem-governance/blob/main/ecosystem/decisions/ADR-ECO-0019-eco-gov-relinquishes-the-contracts.md)
> and [ADR-PA-0014](./ADR-PA-0014-the-agent-doctrine-moves-here.md)). Citations to
> `ADR-ECO-0008` elsewhere in the ecosystem refer to this record.

## Context

ADR-PA-0003 §5 routes a cross-context finding as a rail-labeled GitHub issue in the owner's repo,
"a copy-paste act" carrying the detection entry's full payload. Two things went wrong, one concrete
and one conceptual.

**Concrete:** the copy-paste degraded to re-authoring.
[reliever-design#3](https://github.com/papeete-foundry/reliever-design/issues/3) was written as prose
and silently dropped `severity` and left `scope` implicit — the two fields §3 says a producer "may
not omit." Worse, a *second* producer then shipped the same failure automatically: reliever-design's
`/process` corpus-gap escalation (reliever-design#16, merged) hand-authors its outbound issues too
(e.g. reliever-business#14).

**Conceptual:** the doctrine had fused "the message" with "the GitHub issue." That fusion has two
costs. Nobody can tell a cross-context *message* apart from a repo's own *local* issue — so a gate
can't know what to check. And the day the ecosystem carries messages over something other than GitHub
issues, the whole notion has to be rebuilt. The medium is not the message.

## Decision

Name the **inter-agent message** as a first-class, transport-independent thing, and make the GitHub
issue one *binding* of it. Full doctrine: [`INTER-AGENT-MESSAGES.md`](../doc/INTER-AGENT-MESSAGES.md).

1. **Three layers, one schema.** A message is an **envelope** (what makes it a message + its
   `(type, subject)` identity) wrapping a **payload** (today: a finding), delivered over a **binding**
   (today: a GitHub issue). `https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml` (`inter-agent-message/v0`) is
   the single source of all three; both tools below load it, neither hard-codes it.
2. **The discriminator rule.** An artifact is a message **iff it carries the envelope.** On the
   github-issue binding the envelope rides as the hidden marker `finding: {type}:{subject}`. This is
   the whole point of naming messages: a repo's local issues carry no envelope and are, by
   definition, not messages — the tooling ignores them, no confusion.
3. **A renderer makes creation deterministic.** `render_message.py` (authored in the settler
   `work-pipeline` template) maps a valid payload to the one message it projects to under a binding —
   envelope identity for idempotency (search before create → a re-run upserts), `scope` in the title,
   rail as the label, payload embedded verbatim. It refuses to render a non-conformant payload, and at
   **Autonomy Level 0** only prints the delivery commands for a human to run.
4. **A gate makes conformance non-optional, keyed on the envelope.** `scripts/lint_message.py`
   classifies an artifact on a binding: envelope present → validate it; no envelope and no rail label
   → not a message, skip; no envelope *but* a rail label → a message that dropped its envelope, fail
   (this is exactly #3 and #14). It fires on the envelope, never on labels alone — the first concrete
   slice of the `charter check` conformance detector ADR-PA-0003 promised.

Ownership stays split as ADR-ECO-0005 fixed it: **ECO.GOV owns the doctrine, schema, and gate**; the
**settler template owns the renderer** (per-repo runtime, vendor-pinned). Full automation — CI
delivering the message itself — is deliberately *not* adopted; it is the same renderer behind a
cross-repo token at a higher autonomy level, a policy change ADR-PA-0003 §5 already says needs no
contract change.

## Rationale

- **The medium is not the message.** Separating envelope/payload from the binding means a future
  transport is one new `bindings:` entry, not a rewrite — and every message stays recognizable by its
  envelope. Fusing the two is what made "which issues are messages?" unanswerable.
- **Render, don't re-type.** #3 and #14 both failed because a human/skill retyped a structured
  payload as prose. Making the message a total function of the payload removes the surface that
  failure lives on — the renderer cannot emit what the gate rejects.
- **The envelope is the right discriminator.** A label says a message's *rail*, not whether it *is* a
  message. Keying the gate on the envelope lets it skip local issues silently yet still catch an
  artifact that claims a rail but dropped its envelope — the drift the contract exists to prevent.
- **Vendor, don't publish.** The renderer ships the way every shared tool does — a settler-template
  copy, vendor-pinned — not a PyPI package; that reintroduces a release/token surface the git-native
  pin model avoids until a non-ecosystem consumer appears.

## Consequences

- **Owner repos** add a lint workflow on `issues` that runs `lint_message.py` (envelope-keyed, so it
  never fails a repo's own local issues). Reference workflow: [`../contracts/README.md`](../src/papeete_actor/schemas/).
- **The settler `work-pipeline` template** carries the finding bundle (`render_message.py` authored;
  `message.schema.yaml` + `lint_message.py` vendored from here).
- **Two worked examples, both currently non-conformant messages:** reliever-design#3 (inbound to
  design) and reliever-business#14 (outbound from design's `/process`). Both carry a rail label but no
  envelope, so the gate fails them — correctly. The fix is to re-render each body via
  `render_message.py`; #3 is already triaged into `reliever-design/tasks/BNK.RLVR.CAP.BSP.004.ENV/`,
  so only its body changes, not the triage. Migrating `/process`'s escalation onto the renderer is
  reliever-design follow-up.
- **Watch for:** the title/marker template drifting from owner-repo search strings (the round-trip is
  the guard); the vendored schema/gate drifting from this authority (a template-side sync check is
  follow-up); and the schema graduating to formal JSON Schema if a non-Python binding ever needs it.
