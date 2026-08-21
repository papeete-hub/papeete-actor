"""Building one actor into a runnable Docker image, tagged on the local image store.

WHERE BUILDING BELONGS. An actor's own folder — `actor.yaml` + `Dockerfile` + its code, the
folder-root convention `papeete-actor-manifest/v0` already documents — is this package's own
business, start to finish. Turning it into a runnable image never needs anything about any OTHER
actor, so it belongs here, not in a product's cross-actor orchestration
(`papeete-product`, `ADR-PA-0021`).

VERSION COMES FROM `papeete-version` (ADR-PA-0024) — this module no longer computes it. The
semver-from-tag + ciType-label + short-SHA formula (`ADR-PA-0022`, `ADR-PA-0023`) moved to its
own package (`papeete-version`'s `ADR-PV-0001`, `ADR-PV-0002`), which this repo now depends on
rather than carrying a second copy of the same computation. This module's own job stays narrow:
read an actor's `name` from its `actor.yaml`, ask `papeete_version` for the version string that
name and folder currently compute to, and turn `{name, version}` into a Docker tag.
"""
import subprocess
from pathlib import Path

import yaml
from papeete_version import version as pv


def image_tag(name: str, version: str) -> str:
    """The `<name>:<version>` tag a built actor answers to."""
    return f"{pv.normalize_name(name)}:{version}"


def _actor_name(folder: Path | str) -> str:
    return yaml.safe_load((Path(folder) / "actor.yaml").read_text())["name"]


def actor_version(folder: Path | str, label: str, feature_name: str | None = None) -> str:
    """The version string one actor's next build would carry — `papeete_version.version.compute()`
    after reading the actor's own `name` from `actor.yaml` — without touching Docker at all.

    `label` IS A ciType (`alpha`/`beta`/`prod`/`feature`), NOT A FREE-FORM STRING (`ADR-PA-0024`,
    `papeete-version`'s `ADR-PV-0002`). `prod` computes to a bare semver — no label, no SHA;
    `feature` requires `feature_name` and prints that instead of the literal word `feature`.

    WHAT THIS IS FOR. Computing a version is a smaller, cheaper claim than building an image —
    useful standalone, e.g. a CI step that records what a build *would* tag before spending the
    time to build it, or a human checking where an actor stands right now.
    """
    folder = Path(folder)
    return pv.compute(folder, _actor_name(folder), label, feature_name)


def _image_id(tag: str) -> str:
    return subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", tag],
        capture_output=True, text=True,
    ).stdout.strip()


def build_actor(folder: Path | str, label: str, feature_name: str | None = None) -> str:
    """Build one actor's Dockerfile and tag it `<name>:<version>` — `name` from its own
    `actor.yaml`, the version computed fresh by `papeete_version` (`actor_version`), never read
    from the manifest, which carries no such field.

    LANDS ON THE LOCAL DOCKER IMAGE STORE — no registry involved, no push. Returns the tag.

    REBUILDING REPLACES, NEVER ACCUMULATES. The tag is deterministic — the same folder, at the
    same git state, with the same label (and feature name), always targets the same tag. Docker
    itself re-points that tag at the freshly built image; this function goes one step further and
    removes the image the tag used to point to, so a repeated local rebuild REPLACES the previous
    image rather than leaving it behind, untagged, taking up space.
    """
    folder = Path(folder)
    tag = image_tag(_actor_name(folder), actor_version(folder, label, feature_name))

    previous = _image_id(tag)
    subprocess.run(["docker", "build", "-t", tag, str(folder)], check=True)

    if previous and previous != _image_id(tag):
        # BEST-EFFORT, NEVER FATAL. The old image may be in use elsewhere (another tag, a
        # running container) — that is a reason to leave it alone, not a reason to fail the
        # build that just succeeded.
        subprocess.run(["docker", "rmi", previous], capture_output=True)

    return tag
