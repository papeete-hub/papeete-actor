"""The publication/v2 gate — an actor's events/ log against the contract.

It validates the record ENVELOPE and the v2 additions. It does NOT validate a record against its
own payload schema: that schema is authored by the producer in its own terms, and reading it is
the consuming actor's job, not a gate's.
"""
import pytest
import yaml

from papeete_actor import publications

RECORD = {
    "publication": "the-contract",
    "at": "2026-07-23",
    "ref": "v1.0.0",
    "summary": "the-contract/v1 exists; `means` is now required on every offer",
}


@pytest.fixture
def repo(tmp_path):
    """A repo root with an events/ log, and a helper to drop records into it."""

    class Repo:
        root = tmp_path

        def record(self, pub_id: str, name: str, rec: dict | str):
            log = tmp_path / "events" / pub_id
            log.mkdir(parents=True, exist_ok=True)
            path = log / name
            path.write_text(rec if isinstance(rec, str) else yaml.safe_dump(rec, sort_keys=False))
            return path

        def shape(self, pub_id: str):
            log = tmp_path / "events" / pub_id
            log.mkdir(parents=True, exist_ok=True)
            (log / "schema.yaml").write_text("required: [publication, at, ref, summary]\n")

    return Repo()


def card(**pub) -> dict:
    base = {"id": "the-contract", "means": "a version exists", "shape": "none", "surface": "src/"}
    base.update(pub)
    return {"publications": [base]}


def test_no_events_log_is_not_a_defect(tmp_path):
    """An actor may publish nothing (ADR-ECO-0014 §3)."""
    rep = publications.lint_log(tmp_path)
    assert rep.errors == []
    assert any("no events/ log" in n for n in rep.notes)


def test_a_conformant_record_passes(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    assert publications.lint_log(repo.root, card=card()).errors == []


@pytest.mark.parametrize("field", ["publication", "at", "ref", "summary"])
def test_every_required_record_field_is_checked(repo, field):
    repo.shape("the-contract")
    rec = dict(RECORD)
    del rec[field]
    repo.record("the-contract", "v1.0.0.yaml", rec)
    rep = publications.lint_log(repo.root, card=card())
    assert any(f"missing required field '{field}'" in e for e in rep.errors)


def test_records_with_no_shape_fail(repo):
    """Every emitted publication owes a payload shape — the obligation binds at first record."""
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    rep = publications.lint_log(repo.root, card=card())
    assert any("owes a payload shape" in e for e in rep.errors)


def test_a_shape_with_no_records_ran_ahead_of_the_log(repo):
    repo.shape("the-contract")
    rep = publications.lint_log(repo.root, card=card())
    assert rep.errors == []
    assert any("ran ahead of the log" in n for n in rep.notes)


def test_schema_yaml_is_reserved_not_a_record(repo):
    """It carries no `publication:`/`at:`/`ref:`/`summary:` — counting it as a record would fail
    every conformant log."""
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    assert publications.lint_log(repo.root, card=card()).errors == []


def test_a_record_under_the_wrong_directory_fails(repo):
    repo.shape("the-contract")
    rec = dict(RECORD, publication="something-else")
    repo.record("the-contract", "v1.0.0.yaml", rec)
    rep = publications.lint_log(repo.root, card=card())
    assert any("but sits under" in e for e in rep.errors)


def test_a_log_the_card_does_not_declare_fails(repo):
    repo.shape("undeclared")
    repo.record("undeclared", "v1.0.0.yaml", dict(RECORD, publication="undeclared"))
    rep = publications.lint_log(repo.root, card=card())
    assert any("which the card does not declare" in e for e in rep.errors)


def test_a_declared_shape_with_no_log_fails(tmp_path):
    (tmp_path / "events").mkdir()
    rep = publications.lint_log(tmp_path, card=card(shape="events/the-contract/schema.yaml"))
    assert any("has no events/the-contract/ log" in e for e in rep.errors)


# ── the pinning rule ──────────────────────────────────────────────────────────────────────────

def test_a_breaking_flag_obliges_every_record_to_declare_breaking(repo):
    """THE RULE THIS REPO OWES ITSELF. A card declaring a breaking_flag has said its consumers
    pin it; the gate cannot judge whether a change breaks, only force the judgement to be made."""
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    rep = publications.lint_log(repo.root, card=card(breaking_flag="REQUIRED"))
    assert any("no 'breaking'" in e for e in rep.errors)


@pytest.mark.parametrize("breaking", [True, False])
def test_breaking_declared_either_way_satisfies_the_pinning_rule(repo, breaking):
    """`false` is as much a judgement as `true` — what the rule forbids is silence."""
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", dict(RECORD, breaking=breaking))
    assert publications.lint_log(repo.root, card=card(breaking_flag="REQUIRED")).errors == []


def test_without_a_breaking_flag_no_such_obligation(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    assert publications.lint_log(repo.root, card=card()).errors == []


# ── the ref rule ──────────────────────────────────────────────────────────────────────────────

def test_a_live_record_carrying_a_sha_is_noted(repo):
    """A record ships in the commit it announces, and a commit cannot contain its own hash. Only
    a backfill may carry one."""
    repo.shape("the-contract")
    repo.record("the-contract", "a1b2c3d.yaml", dict(RECORD, ref="a1b2c3d4e5f6"))
    rep = publications.lint_log(repo.root, card=card())
    assert any("only a backfill may carry one" in n for n in rep.notes)


def test_a_backfilled_record_may_carry_a_sha(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "a1b2c3d.yaml",
                dict(RECORD, ref="a1b2c3d4e5f6", backfilled="2026-07-24"))
    rep = publications.lint_log(repo.root, card=card())
    assert not any("only a backfill" in n for n in rep.notes)


def test_a_tag_ref_is_not_mistaken_for_a_sha(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", RECORD)
    rep = publications.lint_log(repo.root, card=card())
    assert not any("looks like a sha" in n for n in rep.notes)


# ── malformed input ───────────────────────────────────────────────────────────────────────────

def test_a_record_that_does_not_parse_is_reported_not_raised(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", "publication: [unclosed\n")
    rep = publications.lint_log(repo.root, card=card())
    assert any("does not parse" in e for e in rep.errors)


def test_an_unknown_record_key_is_a_note_never_an_error(repo):
    repo.shape("the-contract")
    repo.record("the-contract", "v1.0.0.yaml", dict(RECORD, announced_by="me"))
    rep = publications.lint_log(repo.root, card=card())
    assert rep.errors == []
    assert any("not named by the record contract" in n for n in rep.notes)
