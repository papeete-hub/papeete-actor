"""The CLI — argument handling, and the registry discovery that hangs off it.

A GATE'S VERDICT MUST NOT DEPEND ON HOW IT WAS INVOKED. Everything here is about that: the same
cards, linted in a different order or from a different directory, must produce the same answer.
"""
import yaml

from papeete_actor import cli

from conftest import _minimal


def write(root, name: str, card: dict):
    root.mkdir(parents=True, exist_ok=True)
    (root / "papeete-actor.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
    return root / "papeete-actor.yaml"


def workspace(tmp_path):
    """A repo whose card sits at the root and a nested example card, plus a registry two levels
    up — the shape that made the gate order-dependent."""
    repo = tmp_path / "org" / "the-repo"
    own = write(repo, "own", dict(_minimal(), repo="org/the-repo"))
    nested = write(repo / "examples" / "actors" / "auditor", "nested",
                   dict(_minimal(), repo="org/the-repo",
                        dependencies=[{"id": "EXA.ARCHIVIST", "ref": "0.1.0"}]))
    reg = tmp_path / "org" / "ecosystem-governance" / "ecosystem" / "registry.yaml"
    reg.parent.mkdir(parents=True)
    reg.write_text(yaml.safe_dump({"repos": [
        {"repo": "org/the-repo", "card": "papeete-actor.yaml", "card_status": "adopted"}]}))
    return own, nested, reg


# ── the order bug ─────────────────────────────────────────────────────────────────────────────

def test_the_verdict_does_not_depend_on_argument_order(tmp_path, capsys):
    """THE REGRESSION. `workspace = cards[0].resolve().parent.parent` found the registry when the
    root-level card was listed first and missed it when the nested one was — so the same two cards
    failed or passed on ordering alone."""
    own, nested, _ = workspace(tmp_path)

    first = cli.main(["lint-card", str(own), str(nested)])
    capsys.readouterr()
    second = cli.main(["lint-card", str(nested), str(own)])
    capsys.readouterr()

    assert first == second


def test_a_nested_card_still_finds_the_registry(tmp_path, capsys):
    """`parent.parent` is only ever right for a card at a repo root. Linting the nested card alone
    used to search `examples/actors/` and its parent — neither of which means anything."""
    _, nested, reg = workspace(tmp_path)
    cli.main(["lint-card", str(nested)])
    assert str(reg) in capsys.readouterr().out


def test_the_report_says_which_registry_produced_the_verdict(tmp_path, capsys):
    """'resolves nowhere in registry.yaml' is unactionable when the reader cannot tell WHICH
    registry.yaml was read — and with an upward walk there is more than one candidate."""
    own, _, reg = workspace(tmp_path)
    cli.main(["lint-card", str(own)])
    assert f"resolved against {reg}" in capsys.readouterr().out


def test_an_isolated_checkout_skips_resolution_rather_than_failing(tmp_path, capsys):
    card = write(tmp_path / "lonely", "own", _minimal())
    assert cli.main(["lint-card", str(card)]) == 0
    assert "registry.yaml not found" in capsys.readouterr().out


def test_an_explicit_registry_wins_over_discovery(tmp_path, capsys):
    own, _, _ = workspace(tmp_path)
    mine = tmp_path / "mine.yaml"
    mine.write_text(yaml.safe_dump({"repos": []}))
    cli.main(["lint-card", str(own), "--registry", str(mine)])
    assert f"resolved against {mine}" in capsys.readouterr().out


# ── the rest of the surface ───────────────────────────────────────────────────────────────────

def test_a_missing_card_is_reported_not_raised(tmp_path, capsys):
    assert cli.main(["lint-card", str(tmp_path / "nope.yaml")]) == 1
    assert "no such file" in capsys.readouterr().err


def test_strict_promotes_warns_to_errors(tmp_path, capsys):
    """An unmigrated card is each pair's own business by default; `--strict` is how a pipeline
    that has finished migrating says so."""
    card = write(tmp_path / "old", "old", dict(_minimal(), card="actor-card/v0"))
    assert cli.main(["lint-card", str(card)]) == 0
    capsys.readouterr()
    assert cli.main(["lint-card", str(card), "--strict"]) == 1


def test_contracts_prints_the_versions_and_the_profile(capsys):
    assert cli.main(["contracts"]) == 0
    out = capsys.readouterr().out
    assert "papeete-actor-card/v1" in out
    assert "inter-agent-message/v0" in out
    assert "publication/v2" in out
    assert "papeete-banking" in out


def test_contracts_reports_another_profile_when_given_one(tmp_path, capsys):
    prof = tmp_path / "acme.yaml"
    prof.write_text("profile: acme\ncontract: deployment-profile/v0\n")
    cli.main(["contracts", "--profile", str(prof)])
    out = capsys.readouterr().out
    assert "acme" in out and "(unconstrained)" in out


def test_a_missing_profile_is_a_usable_message_not_a_traceback(tmp_path, capsys):
    """Both loaders raise with instructions; a traceback buries them under a stack the reader
    cannot act on, and reads as a crash in the gate rather than a mistake in the invocation."""
    assert cli.main(["contracts", "--profile", str(tmp_path / "nope.yaml")]) == 2
    assert "no such deployment profile" in capsys.readouterr().err


def test_check_without_a_registry_reports_rather_than_crashing(tmp_path, capsys):
    """`cmd_check` falls back to a candidate path that does not exist, so this is the ordinary
    case of running the join in a checkout without the lab repo beside it."""
    assert cli.main(["check", "--workspace", str(tmp_path)]) == 1
    assert "no index to walk" in capsys.readouterr().err


def test_lint_publication_reads_the_card_beside_the_log(tmp_path, capsys):
    repo = tmp_path / "repo"
    write(repo, "own", dict(_minimal(), publications=[
        {"id": "a-fact", "means": "m", "shape": "events/a-fact/schema.yaml", "surface": "s",
         "breaking_flag": "REQUIRED"}]))
    log = repo / "events" / "a-fact"
    log.mkdir(parents=True)
    (log / "schema.yaml").write_text("required: [publication, at, ref, summary]\n")
    (log / "v1.0.0.yaml").write_text(yaml.safe_dump(
        {"publication": "a-fact", "at": "2026-07-24", "ref": "v1.0.0", "summary": "s"}))
    assert cli.main(["lint-publication", str(repo)]) == 1
    assert "no 'breaking'" in capsys.readouterr().err


def test_lint_message_reads_a_payload_file(tmp_path, capsys):
    payload = tmp_path / "finding.yaml"
    payload.write_text(yaml.safe_dump({
        "type": "engineering-debt", "rail": "engineering-debt", "severity": "low",
        "scope": "BNK.RLVR", "subject": "BNK.RLVR", "description": "d"}))
    assert cli.main(["lint-message", "--payload", str(payload)]) == 0


# ── lint-registry, and the profile-declared location ──────────────────────────────────────────

def test_lint_registry_gates_the_index(tmp_path, capsys):
    reg = tmp_path / "registry.yaml"
    reg.write_text(yaml.safe_dump({"repos": [
        {"repo": "example/up", "papeete_actor": "UP.STREAM", "card_status": "adopted"}]}))
    assert cli.main(["lint-registry", str(reg)]) == 1
    assert "unfindable_card" in capsys.readouterr().err


def test_lint_registry_passes_a_conformant_index(tmp_path, capsys):
    reg = tmp_path / "registry.yaml"
    reg.write_text(yaml.safe_dump({"repos": [
        {"repo": "example/up", "card": "papeete-actor.yaml", "card_status": "adopted"}]}))
    assert cli.main(["lint-registry", str(reg)]) == 0


def test_contracts_reports_the_registry_contract_and_its_location(capsys):
    cli.main(["contracts"])
    out = capsys.readouterr().out
    assert "ecosystem-registry/v0" in out
    assert "ecosystem-governance/ecosystem/registry.yaml" in out


def test_discovery_follows_the_profile_not_a_hard_coded_path(tmp_path, capsys):
    """A deployment that keeps its registry somewhere else is found there, and only there."""
    repo = tmp_path / "ws" / "the-repo"
    card = write(repo, "own", dict(_minimal(), repo="the-repo"))
    reg = tmp_path / "ws" / "governance" / "index.yaml"
    reg.parent.mkdir(parents=True)
    reg.write_text(yaml.safe_dump({"repos": [
        {"repo": "the-repo", "card": "papeete-actor.yaml", "card_status": "adopted"}]}))
    prof = tmp_path / "acme.yaml"
    prof.write_text("profile: acme\ncontract: deployment-profile/v0\n"
                    "registry:\n  locations: [governance/index.yaml]\n")

    cli.main(["lint-card", str(card), "--profile", str(prof)])
    assert f"resolved against {reg}" in capsys.readouterr().out

    cli.main(["lint-card", str(card)])            # shipped profile: looks elsewhere, finds nothing
    assert "registry.yaml not found" in capsys.readouterr().out
