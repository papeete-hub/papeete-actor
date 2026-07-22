"""The inter-agent-message/v0 gate — is this artifact a message, and if so is it conformant?

The discriminator rule (INTER-AGENT-MESSAGES §2): an artifact is a message IFF it carries the
envelope. So a repo's own local issue is silently skipped, and an artifact that CLAIMS to be a
message — carries a routing rail label — but dropped its envelope FAILS rather than passing as
noise. That was the reliever-design#3 / reliever-business#14 failure.

Ported from ecosystem-governance/scripts/lint_message.py, which stays where it is: it is vendored
into settler's work-pipeline template and byte-pinned by check_pipeline_sync.py in the repos that
consume it. Editing it would break their pin check. The duplication is deliberate and temporary —
it retires when those repos install charter instead of vendoring the script (ADR-ECO-0017).
"""
import re
from pathlib import Path

import yaml

from .report import Report
from .schemas import load

FENCE_RE = re.compile(r"```([A-Za-z0-9_-]*)\n(.*?)\n```", re.DOTALL)
MARKER_RE = re.compile(r"<!--\s*finding:\s*(.+?)\s*-->")


def validate_payload(payload, schema: dict) -> list[str]:
    """Human-readable errors for one payload; empty means conformant."""
    errors: list[str] = []
    spec = schema["payload"]

    if not isinstance(payload, dict):
        return [f"payload is not a mapping (got {type(payload).__name__})"]

    for field in spec["required"]:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field '{field}'")

    for field, allowed in spec["enums"].items():
        value = payload.get(field)
        if value is not None and value not in allowed:
            errors.append(f"'{field}' is '{value}', not one of {allowed}")

    # scope is an explicit, well-formed capability node at exactly one grain (the scoping rule).
    scope = payload.get("scope")
    if scope is not None:
        if not re.match(spec["scope_grammar"], str(scope)):
            errors.append(
                f"'scope' is '{scope}', not a well-formed capability node "
                f"(context | zone | L1 | L2 per the grain ladder)"
            )
        subject = payload.get("subject")
        if isinstance(subject, str) and re.match(spec["scope_grammar"], subject):
            if subject != scope and not subject.startswith(str(scope) + "."):
                errors.append(
                    f"'scope' ({scope}) is not a prefix-grain of 'subject' ({subject}); "
                    f"scope must be the narrowest node containing the subject"
                )
    return errors


def parse_binding(body: str, schema: dict):
    """(payload, has_envelope, structural_errors) from a github-issue binding body."""
    errors: list[str] = []
    binding = schema["bindings"]["github-issue"]
    lang = binding["body_block_lang"]

    marker = MARKER_RE.search(body)
    has_envelope = marker is not None
    block = next((m.group(2) for m in FENCE_RE.finditer(body) if m.group(1) == lang), None)

    payload = None
    if block is not None:
        try:
            payload = yaml.safe_load(block)
        except yaml.YAMLError as e:
            errors.append(f"the ```{lang} payload block does not parse: {e}")

    if has_envelope and block is None:
        errors.append(
            f"envelope marker present but no fenced ```{lang} payload block — render it, never hand-author"
        )
    if has_envelope and isinstance(payload, dict):
        expected = f"{payload.get('type')}:{payload.get('subject')}"
        if marker.group(1) != expected:
            errors.append(
                f"marker '{marker.group(1)}' disagrees with the payload identity '{expected}' "
                f"(type/subject edited by hand?)"
            )
    return payload, has_envelope, errors


def lint_payload_file(path: Path, schema: dict | None = None) -> Report:
    schema = schema or load("message")
    rep = Report()
    rep.errors += validate_payload(yaml.safe_load(path.read_text()), schema)
    if not rep.errors:
        rep.oks.append(f"{path} conforms to {schema['contract']}")
    return rep


def lint_issue(body: str, labels: list[str], label: str = "issue body", schema: dict | None = None) -> Report:
    schema = schema or load("message")
    rep = Report()
    rails = schema["payload"]["enums"]["rail"]

    payload, has_envelope, errors = parse_binding(body, schema)
    claims_message = has_envelope or any(x in rails for x in labels)

    if not claims_message:
        rep.oks.append(f"{label} is not an inter-agent message (no envelope, no rail label) — skipped")
        return rep
    if not has_envelope:
        errors.insert(
            0,
            f"carries a routing rail label {labels} but no envelope (no '<!-- finding: TYPE:SUBJECT -->' "
            f"marker) — it IS a message, rendered wrong",
        )
    if payload is not None:
        errors += validate_payload(payload, schema)

    rep.errors += errors
    if not rep.errors:
        rep.oks.append(f"{label} conforms to {schema['contract']}")
    return rep
