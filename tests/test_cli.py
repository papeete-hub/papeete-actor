"""The CLI — argument handling for the one contract this build enforces."""
import yaml

from papeete_actor import cli


def test_lint_manifest_gates_the_identity(tmp_path, capsys):
    m = tmp_path / "actor.yaml"
    m.write_text(yaml.safe_dump({"manifest": "papeete-actor-manifest/v0"}))
    assert cli.main(["lint-manifest", str(m)]) == 1
    assert "missing required key 'name'" in capsys.readouterr().err


def test_lint_manifest_passes_a_conformant_manifest(tmp_path, capsys):
    m = tmp_path / "actor.yaml"
    m.write_text(yaml.safe_dump({"manifest": "papeete-actor-manifest/v0", "name": "Archivist",
                                  "description": "Keeps a ledger."}))
    assert cli.main(["lint-manifest", str(m)]) == 0


def test_a_missing_manifest_is_reported_not_raised(tmp_path, capsys):
    assert cli.main(["lint-manifest", str(tmp_path / "nope.yaml")]) == 1
    assert "does not parse or cannot be read" in capsys.readouterr().err


def test_contracts_prints_the_manifest_contract(capsys):
    assert cli.main(["contracts"]) == 0
    assert "papeete-actor-manifest/v0" in capsys.readouterr().out
