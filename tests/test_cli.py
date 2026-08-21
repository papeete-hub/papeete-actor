"""The CLI — argument handling for the one contract this build enforces."""
import subprocess

import yaml

from papeete_actor import cli, build


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


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_version_prints_the_computed_version_with_no_docker(tmp_path, capsys):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump(
        {"manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)
    _git("tag", "archivist/v2.2.0", cwd=folder)

    assert cli.main(["version", str(folder), "--label", "dev"]) == 0
    assert capsys.readouterr().out.strip() == build.actor_version(folder, "dev")


def test_version_fails_clearly_with_no_matching_tag(tmp_path, capsys):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump(
        {"manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)

    assert cli.main(["version", str(folder), "--label", "dev"]) == 2
    assert "no tag matching 'archivist/v*'" in capsys.readouterr().err
