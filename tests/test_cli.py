"""The CLI — argument handling for the one contract this build enforces."""
import subprocess

import pytest
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

    assert cli.main(["version", str(folder), "--label", "alpha"]) == 0
    assert capsys.readouterr().out.strip() == build.actor_version(folder, "alpha")


def test_version_fails_clearly_with_no_matching_tag(tmp_path, capsys):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump(
        {"manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)

    assert cli.main(["version", str(folder), "--label", "alpha"]) == 2
    assert "no tag matching 'archivist/v*'" in capsys.readouterr().err


def test_version_rejects_a_label_that_is_not_a_citype(tmp_path, capsys):
    """--label is a fixed ciType vocabulary (papeete-version's CI_TYPES), not a free string
    anymore — argparse itself rejects an unknown one before any git or version computation runs."""
    folder = tmp_path / "archivist"
    with pytest.raises(SystemExit):
        cli.main(["version", str(folder), "--label", "dev"])
    assert "invalid choice" in capsys.readouterr().err


def test_version_prod_prints_a_bare_semver(tmp_path, capsys):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump(
        {"manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)
    _git("tag", "archivist/v2.2.0", cwd=folder)

    assert cli.main(["version", str(folder), "--label", "prod"]) == 0
    assert capsys.readouterr().out.strip() == "2.2.0"


def test_version_feature_uses_feature_name(tmp_path, capsys):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump(
        {"manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)
    _git("tag", "archivist/v2.2.0", cwd=folder)

    assert cli.main(["version", str(folder), "--label", "feature", "--feature-name", "my-branch"]) == 0
    assert capsys.readouterr().out.strip() == build.actor_version(folder, "feature", feature_name="my-branch")
