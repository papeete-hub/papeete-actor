"""The papeete-actor-manifest/v0 gate — a minimal actor identity, standalone from the card.

TWO FIELDS PLUS THE CONTRACT KEY. No `version` — that's git's fact, computed by `build.py`, never
declared here (ADR-PA-0022). Nothing here shares fixtures with the card contract's suite — this
lineage is deliberately not mingled with it (ADR-PA-0019).
"""
import pytest
import yaml

from papeete_actor import manifest


def write(tmp_path, data) -> "object":
    path = tmp_path / "actor.yaml"
    path.write_text(data if isinstance(data, str) else yaml.safe_dump(data, sort_keys=False))
    return path


MANIFEST = {"manifest": "papeete-actor-manifest/v0", "name": "Archivist",
            "description": "Keeps a ledger and answers about it."}


# ── the required fields ───────────────────────────────────────────────────────────────────────

def test_a_minimal_manifest_conforms(tmp_path):
    assert manifest.lint(write(tmp_path, MANIFEST)).errors == []


@pytest.mark.parametrize("key", ["name", "description"])
def test_each_field_is_required(tmp_path, key):
    data = dict(MANIFEST)
    del data[key]
    rep = manifest.lint(write(tmp_path, data))
    assert any(f"missing required key '{key}'" in e for e in rep.errors)


def test_version_is_not_a_field_at_all(tmp_path):
    """Removed on purpose (ADR-PA-0022) — a manifest carrying one anyway is simply an unnamed
    extra, never checked, never required."""
    assert manifest.lint(write(tmp_path, dict(MANIFEST, version="1.0.0"))).errors == []


# ── the manifest's own migration lineage ──────────────────────────────────────────────────────

def test_a_mismatched_manifest_is_unmigrated_not_failed(tmp_path):
    rep = manifest.lint(write(tmp_path, dict(MANIFEST, manifest="papeete-actor-manifest/v1")))
    assert rep.errors == []
    assert any("UNMIGRATED" in w for w in rep.warns)


def test_a_missing_manifest_key_is_unmigrated_too(tmp_path):
    """Absence takes the same path as a mismatch — `None != CONTRACT` — the same way a missing
    `card:` on a card is UNMIGRATED rather than a bare required-key error."""
    data = dict(MANIFEST)
    del data["manifest"]
    rep = manifest.lint(write(tmp_path, data))
    assert rep.errors == []
    assert any("UNMIGRATED" in w for w in rep.warns)


# ── malformed input ───────────────────────────────────────────────────────────────────────────

def test_a_manifest_that_does_not_parse_is_reported_not_raised(tmp_path):
    rep = manifest.lint(write(tmp_path, "name: [unclosed\n"))
    assert any("does not parse" in e for e in rep.errors)


def test_a_manifest_that_is_not_a_mapping_is_reported(tmp_path):
    rep = manifest.lint(write(tmp_path, ["a", "list"]))
    assert any("not a mapping" in e for e in rep.errors)
