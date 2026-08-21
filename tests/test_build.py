"""build_actor() — one actor's Dockerfile, built and tagged <name>:<version> locally.

VERSION COMES FROM papeete-version (ADR-PA-0024). This module only tests build.py's OWN job:
reading `name` from actor.yaml, turning `{name, version}` into a Docker tag, and shelling out to
`docker build` — not the version computation itself, which is papeete-version's own, already
tested there. Every fixture still commits the actor's folder to a fresh, throwaway git repo and
tags it `<name>/vX.Y.Z`, because papeete_version.version.compute() needs real git state.
"""
import subprocess

import pytest
import yaml
from papeete_version.version import compute, normalize_name

from papeete_actor import build


def _docker_available() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_actor_repo(folder, name, description, tag=None):
    """A throwaway git repo, one commit, holding one actor — the minimum papeete_version needs.
    Optionally tagged `<name>/v<tag>`."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "actor.yaml").write_text(yaml.safe_dump({
        "manifest": "papeete-actor-manifest/v0", "name": name, "description": description}))
    (folder / "Dockerfile").write_text("FROM scratch\n")
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)
    if tag:
        _git("tag", f"{normalize_name(name)}/v{tag}", cwd=folder)


def test_image_tag_normalizes_the_name():
    assert build.image_tag("The Archivist", "2.2.0-alpha-abc1234") == "the-archivist:2.2.0-alpha-abc1234"


def test_actor_version_reads_the_name_from_actor_yaml_and_delegates_to_papeete_version(tmp_path):
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "Archivist", "Keeps a ledger.", tag="2.2.0")
    assert build.actor_version(folder, "alpha") == compute(folder, "Archivist", "alpha")


def test_actor_version_passes_feature_name_through(tmp_path):
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "Archivist", "Keeps a ledger.", tag="2.2.0")
    assert (build.actor_version(folder, "feature", feature_name="my-branch")
            == compute(folder, "Archivist", "feature", feature_name="my-branch"))


def test_actor_version_surfaces_papeete_versions_own_errors(tmp_path):
    """No matching tag — papeete_version.semver_base()'s ValueError propagates unchanged; this
    module adds no error handling of its own."""
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "Archivist", "Keeps a ledger.")
    with pytest.raises(ValueError, match="no tag matching 'archivist/v\\*'"):
        build.actor_version(folder, "alpha")


@pytest.mark.e2e
@pytest.mark.skipif(not _docker_available(), reason="no Docker daemon reachable")
def test_build_actor_tags_the_image_with_the_computed_version(tmp_path):
    """RUNS REAL DOCKER. The tag is exactly `<name>:<actor_version(folder, label)>` — never
    anything restated by the caller, never anything read from actor.yaml."""
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "test-archivist-xyz", "throwaway, for this test only", tag="1.0.0")
    tag = f"test-archivist-xyz:{build.actor_version(folder, 'alpha')}"
    try:
        assert build.build_actor(folder, "alpha") == tag
        assert subprocess.run(["docker", "image", "inspect", tag],
                               capture_output=True).returncode == 0
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)


@pytest.mark.e2e
@pytest.mark.skipif(not _docker_available(), reason="no Docker daemon reachable")
def test_rebuilding_uncommitted_changes_replaces_the_old_image(tmp_path):
    """ONE VERSION, NO PER-BUILD SUFFIX. An uncommitted Dockerfile edit — the ordinary local dev
    loop — doesn't change the computed version, so a rebuild must land on the exact same tag,
    and the image that tag used to point to must be gone afterward, not left dangling."""
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "test-rebuild-xyz", "throwaway, for this test only", tag="1.0.0")
    version = build.actor_version(folder, "alpha")
    tag = f"test-rebuild-xyz:{version}"
    try:
        (folder / "Dockerfile").write_text("FROM scratch\nLABEL build=one\n")
        build.build_actor(folder, "alpha")
        first_id = build._image_id(tag)

        (folder / "Dockerfile").write_text("FROM scratch\nLABEL build=two\n")   # uncommitted
        assert build.actor_version(folder, "alpha") == version
        build.build_actor(folder, "alpha")
        second_id = build._image_id(tag)

        assert first_id and second_id and first_id != second_id
        assert subprocess.run(["docker", "image", "inspect", first_id],
                               capture_output=True).returncode != 0
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
