"""Building one actor into a runnable Docker image, tagged on the local image store.

WHERE BUILDING BELONGS. An actor's own folder — `actor.yaml` + `Dockerfile` + its code, the
folder-root convention `papeete-actor-manifest/v0` already documents — is this package's own
business, start to finish. Turning it into a runnable image never needs anything about any OTHER
actor, so it belongs here, not in a product's cross-actor orchestration
(`papeete-product`, `ADR-PA-0021`).

VERSION IS COMPUTED, NEVER DECLARED (ADR-PA-0022) — `actor.yaml` carries no `version:` field, and
still doesn't. What ADR-PA-0023 adds is the FORMULA: `{semver}-{label}-{shortSha}`. The semver
core comes from the actor's own nearest matching git tag (`<name>/vX.Y.Z` — GitVersion-style,
never a declared field either), the short SHA from `git_version()` below, and the label is an
uninterpreted string the caller supplies at build time — strict on the three-part shape, silent
on what a label MEANS, because that taxonomy (dev/rc/staging/GA/...) isn't decided yet.
"""
import re
import subprocess
from pathlib import Path

import yaml


def _normalize_name(name: str) -> str:
    """An actor's name, normalized to a DNS-safe, Docker-tag-safe, git-tag-safe form."""
    return name.strip().lower().replace(" ", "-")


def image_tag(name: str, version: str) -> str:
    """The `<name>:<version>` tag a built actor answers to."""
    return f"{_normalize_name(name)}:{version}"


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


def semver_base(folder: Path | str, name: str) -> str:
    """The `X.Y.Z` an actor answers to right now — the semver core off the nearest tag matching
    `<name>/vX.Y.Z` reachable from HEAD, `<name>` being the same normalized form `image_tag()`
    uses (ADR-PA-0023).

    NAMESPACED PER ACTOR, ON PURPOSE. A plain `vX.Y.Z` tag is repo-wide — fine for a one-actor
    repo, wrong the moment a second actor's folder lives alongside the first, because then one
    tag would move both actors' semver together even though only one of them changed. Matching
    `<name>/v*` keeps each actor's semver its own, in a repo that may hold several.

    HARD FAILURE, NO FALLBACK — the same discipline `git_version()` already applies to a folder
    with no commit history: an actor with no matching tag yet has no semver to report, and a
    fabricated `0.1.0` would look identical to a real, decided one.
    """
    folder = Path(folder)
    prefix = _normalize_name(name)
    pattern = f"{prefix}/v*"
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", pattern],
        cwd=folder, capture_output=True, text=True,
    )
    tag = result.stdout.strip()
    if result.returncode != 0 or not tag:
        raise ValueError(
            f"{folder}: no tag matching '{pattern}' reachable from HEAD — an actor's semver "
            f"core comes from its own tag, never a declared field; tag it once, e.g. "
            f"`git tag {prefix}/v0.1.0`, before it can be built."
        )

    core = tag.removeprefix(f"{prefix}/v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", core):
        raise ValueError(
            f"{folder}: tag '{tag}' does not carry a plain X.Y.Z semver core after '{prefix}/v'"
        )
    return core


def image_version(folder: Path | str, name: str, label: str) -> str:
    """The full version string an actor answers to: `{semver}-{label}-{shortSha}`
    (ADR-PA-0023) — semver core from `semver_base()`, short SHA from `git_version()`, label
    exactly as the caller supplied it, uninterpreted."""
    return f"{semver_base(folder, name)}-{label}-{git_version(folder)}"


def _actor_name(folder: Path | str) -> str:
    return yaml.safe_load((Path(folder) / "actor.yaml").read_text())["name"]


def actor_version(folder: Path | str, label: str) -> str:
    """The version string one actor's next build would carry — `image_version()` after reading
    its own `name` from `actor.yaml` — without touching Docker at all.

    WHAT THIS IS FOR. Computing a version is a smaller, cheaper claim than building an image —
    useful standalone, e.g. a CI step that records what a build *would* tag before spending the
    time to build it, or a human checking where an actor stands right now.
    """
    folder = Path(folder)
    return image_version(folder, _actor_name(folder), label)


def _image_id(tag: str) -> str:
    return subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", tag],
        capture_output=True, text=True,
    ).stdout.strip()


def build_actor(folder: Path | str, label: str) -> str:
    """Build one actor's Dockerfile and tag it `<name>:<semver>-<label>-<shortSha>` — `name` from
    its own `actor.yaml`, the version computed fresh from git (`image_version`), never read from
    the manifest, which carries no such field.

    `label` IS THE CALLER'S, UNINTERPRETED (ADR-PA-0023). This function does not infer it from a
    branch, an environment variable, or anything else — the taxonomy a label might one day carry
    (dev/rc/staging/GA/...) is a later decision, not this one.

    LANDS ON THE LOCAL DOCKER IMAGE STORE — no registry involved, no push. Returns the tag.

    REBUILDING REPLACES, NEVER ACCUMULATES. The tag is deterministic — the same folder, at the
    same git state, with the same label, always targets the same tag. Docker itself re-points
    that tag at the freshly built image; this function goes one step further and removes the
    image the tag used to point to, so a repeated local rebuild REPLACES the previous image
    rather than leaving it behind, untagged, taking up space.
    """
    folder = Path(folder)
    tag = image_tag(_actor_name(folder), actor_version(folder, label))

    previous = _image_id(tag)
    subprocess.run(["docker", "build", "-t", tag, str(folder)], check=True)

    if previous and previous != _image_id(tag):
        # BEST-EFFORT, NEVER FATAL. The old image may be in use elsewhere (another tag, a
        # running container) — that is a reason to leave it alone, not a reason to fail the
        # build that just succeeded.
        subprocess.run(["docker", "rmi", previous], capture_output=True)

    return tag
