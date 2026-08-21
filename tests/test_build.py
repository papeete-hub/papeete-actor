"""build_actor() — one actor's Dockerfile, built and tagged <name>:<git-sha> locally.

VERSION IS COMPUTED FROM GIT, NEVER DECLARED (ADR-PA-0022) — every fixture here commits the
actor's folder to a fresh, throwaway git repo, because there is no version to fabricate any
other way.
"""
import subprocess

import pytest
import yaml

from papeete_actor import build


def _docker_available() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_actor_repo(folder, name, description):
    """A throwaway git repo, one commit, holding one actor — the minimum git_version() needs."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "actor.yaml").write_text(yaml.safe_dump({
        "manifest": "papeete-actor-manifest/v0", "name": name, "description": description}))
    (folder / "Dockerfile").write_text("FROM scratch\n")
    _git("init", "-q", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=folder)
    _git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init", cwd=folder)


def test_image_tag_normalizes_the_name():
    assert build.image_tag("The Archivist", "2.2.0") == "the-archivist:2.2.0"


def test_git_version_is_the_last_commit_touching_the_folder(tmp_path):
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "Archivist", "Keeps a ledger.")
    expected = subprocess.run(["git", "log", "-1", "--format=%h"], cwd=folder,
                               capture_output=True, text=True, check=True).stdout.strip()
    assert build.git_version(folder) == expected


def test_git_version_is_stable_across_uncommitted_edits(tmp_path):
    """The ordinary local dev loop — edit, don't commit yet — must not change the version, or a
    rebuild-in-progress would never land on the same tag twice."""
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "Archivist", "Keeps a ledger.")
    before = build.git_version(folder)
    (folder / "Dockerfile").write_text("FROM scratch\nLABEL touched=yes\n")
    assert build.git_version(folder) == before


def test_git_version_fails_clearly_with_no_git_history(tmp_path):
    folder = tmp_path / "archivist"
    folder.mkdir()
    (folder / "actor.yaml").write_text(yaml.safe_dump({
        "manifest": "papeete-actor-manifest/v0", "name": "Archivist", "description": "d"}))
    with pytest.raises(ValueError, match="no git history"):
        build.git_version(folder)


@pytest.mark.e2e
@pytest.mark.skipif(not _docker_available(), reason="no Docker daemon reachable")
def test_build_actor_tags_the_image_with_the_computed_version(tmp_path):
    """RUNS REAL DOCKER. The tag is exactly `<name>:<git_version(folder)>` — never anything
    restated by the caller, never anything read from actor.yaml."""
    folder = tmp_path / "archivist"
    _init_actor_repo(folder, "test-archivist-xyz", "throwaway, for this test only")
    tag = f"test-archivist-xyz:{build.git_version(folder)}"
    try:
        assert build.build_actor(folder) == tag
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
    _init_actor_repo(folder, "test-rebuild-xyz", "throwaway, for this test only")
    version = build.git_version(folder)
    tag = f"test-rebuild-xyz:{version}"
    try:
        (folder / "Dockerfile").write_text("FROM scratch\nLABEL build=one\n")
        build.build_actor(folder)
        first_id = build._image_id(tag)

        (folder / "Dockerfile").write_text("FROM scratch\nLABEL build=two\n")   # uncommitted
        assert build.git_version(folder) == version
        build.build_actor(folder)
        second_id = build._image_id(tag)

        assert first_id and second_id and first_id != second_id
        assert subprocess.run(["docker", "image", "inspect", first_id],
                               capture_output=True).returncode != 0
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
