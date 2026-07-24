"""The inter-agent-message/v0 gate.

THE DISCRIMINATOR RULE (INTER-AGENT-MESSAGES §2): an artifact is a message IFF it carries the
envelope. Both halves matter and they fail differently — a repo's own local issue is silently
skipped, and an artifact that CLAIMS to be a message but dropped its envelope FAILS rather than
passing as noise. That second half is the reliever-design#3 / reliever-business#14 failure.
"""
import pytest
import yaml

from papeete_actor import messages, profile


def body(payload_yaml: str, marker: str | None = "engineering-debt:BNK.RLVR.CAP.BSP.001") -> str:
    head = f"<!-- finding: {marker} -->\n\n" if marker else ""
    return f"{head}Some prose a human wrote.\n\n```yaml\n{payload_yaml}```\n"


CONFORMANT = """\
type: engineering-debt
rail: engineering-debt
severity: medium
scope: BNK.RLVR.CAP.BSP
subject: BNK.RLVR.CAP.BSP.001
description: the detector reports STALE_PROVENANCE with no way to tell why
"""


# ── the discriminator ─────────────────────────────────────────────────────────────────────────

def test_an_ordinary_issue_is_not_a_message_and_is_skipped():
    rep = messages.lint_issue("Just a local bug report. No envelope here.", [])
    assert rep.errors == []
    assert any("not an inter-agent message" in o for o in rep.oks)


def test_an_enveloped_conformant_message_passes():
    assert messages.lint_issue(body(CONFORMANT), []).errors == []


def test_a_rail_label_without_an_envelope_fails_rather_than_passing_as_noise():
    """THE SECOND DISCRIMINATOR. It catches an artifact that claims to be a message and dropped
    its envelope — it IS a message, rendered wrong."""
    rep = messages.lint_issue("prose only, no marker, no block", ["engineering-debt"])
    assert any("no envelope" in e for e in rep.errors)


def test_an_envelope_with_no_payload_block_fails():
    rep = messages.lint_issue("<!-- finding: engineering-debt:X -->\n\njust prose\n", [])
    assert any("no fenced ```yaml payload block" in e for e in rep.errors)


def test_a_marker_disagreeing_with_the_payload_identity_fails():
    """type/subject edited by hand — the envelope and the payload are then two sources of truth."""
    rep = messages.lint_issue(body(CONFORMANT, marker="engineering-debt:SOMETHING.ELSE"), [])
    assert any("disagrees with the payload identity" in e for e in rep.errors)


def test_a_payload_block_that_does_not_parse_is_reported_not_raised():
    rep = messages.lint_issue(body("type: [unclosed\n"), [])
    assert any("does not parse" in e for e in rep.errors)


# ── the payload ───────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["type", "rail", "severity", "scope", "subject", "description"])
def test_every_required_payload_field_is_checked(field):
    payload = yaml.safe_load(CONFORMANT)
    del payload[field]
    assert any(f"missing required field '{field}'" in e
               for e in messages.validate_payload(payload, _schema()))


def test_an_empty_string_is_not_a_value():
    payload = yaml.safe_load(CONFORMANT)
    payload["description"] = "   "
    assert any("missing required field 'description'" in e
               for e in messages.validate_payload(payload, _schema()))


def test_severity_is_the_contracts_enum():
    payload = yaml.safe_load(CONFORMANT)
    payload["severity"] = "critical"
    assert any("'severity' is 'critical'" in e
               for e in messages.validate_payload(payload, _schema()))


def test_a_payload_file_is_linted_from_disk(tmp_path):
    path = tmp_path / "finding.yaml"
    path.write_text(CONFORMANT)
    assert messages.lint_payload_file(path).errors == []


def test_a_payload_that_is_not_a_mapping_is_reported():
    assert messages.validate_payload(["a", "list"], _schema()) == [
        "payload is not a mapping (got list)"]


# ── the profiled fields ───────────────────────────────────────────────────────────────────────

def test_rail_reads_the_deployments_rails_not_the_contracts(tmp_path):
    payload = yaml.safe_load(CONFORMANT)
    payload["rail"] = "escalation"
    assert any("'rail' is 'escalation'" in e
               for e in messages.validate_payload(payload, _schema()))

    other = tmp_path / "other.yaml"
    other.write_text("profile: other\ncontract: deployment-profile/v0\nrails: [escalation]\n"
                     "scope_grammar: '^ACME\\.[A-Z]+$'\n")
    payload["scope"] = "ACME.THING"
    payload["subject"] = "ACME.THING"
    assert messages.validate_payload(payload, _schema(), profile.load(other)) == []


def test_a_foreign_deployment_can_emit_a_conformant_message(tmp_path):
    """THE FAILURE ADR-PA-0016 EXISTS TO FIX. Before it, `scope` was required and a hard-coded
    `^BNK\\.` regex meant no value outside this domain matched — so an organisation outside this
    ecosystem could not emit a conformant message at all."""
    prof = tmp_path / "acme.yaml"
    prof.write_text("profile: acme\ncontract: deployment-profile/v0\nrails: [defect]\n")
    payload = yaml.safe_load(CONFORMANT)
    payload.update(rail="defect", scope="whatever acme calls it", subject="acme thing")
    assert messages.validate_payload(payload, _schema(), profile.load(prof)) == []


def test_scope_must_be_a_prefix_grain_of_subject():
    """Scope is the NARROWEST node containing the subject (WORK-OBSERVABILITY §3)."""
    payload = yaml.safe_load(CONFORMANT)
    payload["scope"] = "BNK.KNOW"
    assert any("is not a prefix-grain of" in e
               for e in messages.validate_payload(payload, _schema()))


def test_a_malformed_scope_names_the_profile_that_judged_it():
    payload = yaml.safe_load(CONFORMANT)
    payload["scope"] = "not a node"
    errors = messages.validate_payload(payload, _schema())
    assert any("papeete-banking" in e for e in errors)


def test_scope_stays_required_under_a_loose_profile(tmp_path):
    """A finding that names no owner is the noise floor WORK-OBSERVABILITY exists to prevent —
    whatever the ids look like."""
    prof = tmp_path / "loose.yaml"
    prof.write_text("profile: loose\ncontract: deployment-profile/v0\n")
    payload = yaml.safe_load(CONFORMANT)
    del payload["scope"]
    assert any("missing required field 'scope'" in e
               for e in messages.validate_payload(payload, _schema(), profile.load(prof)))


def test_a_loose_profile_disables_only_the_label_half_of_the_discriminator(tmp_path):
    """The envelope still discriminates, and an enveloped message is still validated. Stated
    because a silently weaker gate is worse than a declared one."""
    prof = tmp_path / "loose.yaml"
    prof.write_text("profile: loose\ncontract: deployment-profile/v0\n")
    rep = messages.lint_issue("prose only", ["engineering-debt"], prof=profile.load(prof))
    assert rep.errors == []                                   # no rails: the label discriminates nothing
    rep = messages.lint_issue(body(CONFORMANT), [], prof=profile.load(prof))
    assert rep.errors == []                                   # the envelope still does


def _schema():
    from papeete_actor.schemas import load
    return load("message")
