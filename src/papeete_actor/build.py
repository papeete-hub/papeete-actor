"""Building one actor into a runnable Docker image, tagged on the local image store.

WHERE BUILDING BELONGS. An actor's own folder — `actor.yaml` + `Dockerfile` + its code, the
folder-root convention `papeete-actor-manifest/v0` already documents — is this package's own
business, start to finish. Turning it into a runnable image never needs anything about any OTHER
actor, so it belongs here, not in a product's cross-actor orchestration
(`papeete-product`, `ADR-PA-0021`).

VERSION IS COMPUTED, NEVER DECLARED (ADR-PA-0022). `actor.yaml` carries no `version:` field —
it is git's fact about an actor, not the actor's claim about itself, and this module is the one
place that computes it.
"""
import subprocess
from pathlib import Path

import yaml


def image_tag(name: str, version: str) -> str:
    """The `<name>:<version>` tag a built actor answers to — an actor's name, normalized to a
    DNS-safe, Docker-tag-safe form, paired with its version."""
    return f"{name.strip().lower().replace(' ', '-')}:{version}"


def git_version(folder: Path | str) -> str:
    """An actor's version: the short SHA of the most recent commit that touched its folder.

    NEVER SELF-DECLARED, COMPUTED FRESH ON EVERY BUILD (ADR-PA-0022). Scoped to the folder, not
    the whole repo's HEAD — an actor's version changes only when ITS OWN content changes, not
    when an unrelated sibling folder does.

    DETERMINISTIC ACROSS UNCOMMITTED EDITS. Only a COMMIT changes the answer — the ordinary local
    dev loop (edit, rebuild, edit again, all before committing) computes the exact same version
    every time, which is what lets `build_actor()`'s rebuild-replaces-the-old-image behavior work
    for work in progress, not just for tagged history.
    """
    folder = Path(folder)
    result = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", "."],
        cwd=folder, capture_output=True, text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        raise ValueError(
            f"{folder}: no git history for this folder — version is computed from the most "
            f"recent commit that touched it, so it must be committed at least once before it "
            f"can be built."
        )
    return sha


def _image_id(tag: str) -> str:
    return subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", tag],
        capture_output=True, text=True,
    ).stdout.strip()


def build_actor(folder: Path | str) -> str:
    """Build one actor's Dockerfile and tag it `<name>:<version>` — `name` from its own
    `actor.yaml`, `version` computed fresh from git (`git_version`), never read from the
    manifest, which carries no such field.

    LANDS ON THE LOCAL DOCKER IMAGE STORE — no registry involved, no push. Returns the tag.

    REBUILDING REPLACES, NEVER ACCUMULATES. The tag is deterministic — the same folder, at the
    same git state, always targets the same tag. Docker itself re-points that tag at the freshly
    built image; this function goes one step further and removes the image the tag used to point
    to, so a repeated local rebuild REPLACES the previous image rather than leaving it behind,
    untagged, taking up space.
    """
    folder = Path(folder)
    m = yaml.safe_load((folder / "actor.yaml").read_text())
    tag = image_tag(m["name"], git_version(folder))

    previous = _image_id(tag)
    subprocess.run(["docker", "build", "-t", tag, str(folder)], check=True)

    if previous and previous != _image_id(tag):
        # BEST-EFFORT, NEVER FATAL. The old image may be in use elsewhere (another tag, a
        # running container) — that is a reason to leave it alone, not a reason to fail the
        # build that just succeeded.
        subprocess.run(["docker", "rmi", previous], capture_output=True)

    return tag
