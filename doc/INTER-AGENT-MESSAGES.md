# Inter-agent messages — the unit of communication between contexts

A context repo (a human+agent pair, ADR-PA-0002) sometimes needs to tell **another** context
something: "your corpus under-resolves here", "this artifact deviates from the tier contract",
"I detected a gap you own." That act of telling is an **inter-agent message**. This doctrine makes
the message a first-class thing — deliberately *separate* from the GitHub issue that happens to
carry it today. Decision record: [ADR-PA-0004](../adr/ADR-PA-0004-inter-agent-message-contract.md).

Why the separation matters: **the medium is not the message.** GitHub issues are how messages
travel now; a queue, a file drop, or a direct agent-to-agent channel could carry them later. If
"message" and "GitHub issue" stay fused, that switch is a rewrite and, worse, nobody can tell a
message apart from a repo's own local bug-tracking issue. Naming the message independently fixes
both.

## 1. The three layers

A message is an **envelope** wrapping a **payload**, delivered over a **binding**:

| Layer | What it is | Today |
|-------|------------|-------|
| **Envelope** | what makes an artifact a message, plus its identity — transport-independent | discriminator `finding: {type}:{subject}`; identity `(type, subject)` |
| **Payload** | the content being sent | a **finding** (the detection entry — WORK-OBSERVABILITY §3) |
| **Binding** | how envelope+payload ride a concrete medium | a **GitHub issue** (the only binding today) |

There is exactly **one payload kind** (`finding`) and **one binding** (`github-issue`) right now.
That is deliberate — the contract is the two of them named and separated, not a speculative
framework. New kinds (a request, an ack, a decision) and new bindings (a non-GitHub medium) slot in
without disturbing the layers already there.

## 2. The discriminator rule — which artifacts are messages

> **An artifact is an inter-agent message if and only if it carries the envelope.**

On the github-issue binding the envelope rides as a hidden marker on the first line of the body:

```
<!-- finding: MISSING_PROVENANCE:process/BNK.RLVR.CAP.BSP.004.ENV/ -->
```

The consequences are the whole point of naming messages explicitly:

- **A repo's own local issues carry no envelope, so they are not messages.** A design-local bug,
  a "spike this idea" note, a release checklist — none of these are inter-context communication,
  none carry the envelope, and the message tooling ignores them entirely. No confusion, by
  construction.
- **The conformance gate fires on the envelope, never on issue labels.** A label (`functional-gap`)
  says what *rail* a message is on; it does not say whether the artifact *is* a message. The gate
  keys on the envelope so it can (a) skip local issues silently and (b) still catch an artifact
  that *claims* to be a message — carries a routing rail label — but dropped its envelope. That
  second case is exactly reliever-design#3 and reliever-business#14: real messages, no envelope,
  and they must fail rather than pass as "not a message."
- **A future medium is a new binding, not a new message.** Because the envelope and payload are
  defined independently of GitHub (§1), moving to another transport means writing one more binding;
  every existing message is still recognizable by its envelope.

## 3. Producing and checking a message

Messages are **rendered, not hand-authored** — the failure that motivated all of this was a human
retyping a structured finding as prose and dropping mandatory fields (reliever-design#3).

- **`render_message.py`** (authored in the settler `work-pipeline` template) maps one payload to the
  single message it projects to under a binding — deterministic, idempotent on the envelope
  identity, refuses to render a non-conformant payload. Autonomy Level 0: it prints the delivery
  commands for a human to run (WORK-OBSERVABILITY §5).
- **`lint_message.py`** (owned here) is the conformance gate: given an artifact on a binding, it
  decides whether it is a message and, if so, validates the envelope + payload against
  [`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/message.schema.yaml). Owner repos run it in CI.

The machine contract that both tools load is `message.schema.yaml` (`inter-agent-message/v0`); it is
the single source of the layers in §1. Change the contract there, once, and both the renderer and
the gate follow.

## 4. Relationship to the rest of the model

- **Findings** (WORK-OBSERVABILITY.md) are the one payload kind today. The *detection ledger* holds
  findings a repo found in itself; a **message** is how a finding crosses to the context that owns
  it (WORK-OBSERVABILITY §5, the routing step). Message ≠ finding: a finding is content, a message
  is content addressed to someone else.
- **A publication is not a message.** This doctrine covers interchange that is *addressed* — a
  request travelling to the papeete-actor that owns a decision. A **publication** — a fact a papeete-actor emits
  about its own state, addressed to nobody and refusable by no one — is a sibling with its own
  contract ([`https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml`](https://github.com/papeete-hub/papeete-actor/blob/main/src/papeete_actor/schemas/publication.schema.yaml),
  ADR-PA-0006) and its own binding (`event-log`, not `github-issue`). The layers in §1 are not
  extended to cover it: identity `(type, subject)` and upsert semantics presume an addressee.
- **Tasks feed from messages; messages never become tasks directly.** Triage — turning a received
  message into a task in the owner's own kanban — is the owner's exclusive act (WORK-OBSERVABILITY
  §5 step 3). A message is a letter in the mailbox, not an entry in the recipient's backlog; the
  recipient decides what work it becomes. Nobody authors another context's kanban.
