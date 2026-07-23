#!/usr/bin/env python3
"""Resolve contracts.pin into src/papeete_actor/schemas/ — the build-time half of `papeete-actor`.

The contracts are ECO.GOV's, in papeete-foundry/ecosystem-governance. They are fetched at the
pinned ref and never committed here: a committed copy is a copy that drifts, and deleting copies is
the entire argument for shipping papeete-actor as a package rather than vendoring gates repo by repo.

Run before any build:  python3 scripts/fetch_contracts.py

Auth: the source repo is private, so this needs a token with read access — GITHUB_TOKEN in CI, or
`gh auth token` locally. That burden falls on ONE pipeline, which is the difference between this
and asking seven consumer repos to authenticate.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PIN = ROOT / "contracts.pin"
DEST = ROOT / "src" / "papeete_actor" / "schemas"


def token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    pin = yaml.safe_load(PIN.read_text())
    repo, ref, wanted = pin["repo"], pin["ref"], pin["contracts"]

    tok = token()
    url = f"https://{tok + '@' if tok else ''}github.com/{repo}.git"

    with tempfile.TemporaryDirectory() as tmp:
        # A full fetch of one ref: the repo is small, and a partial clone would add failure modes
        # for no gain. `--depth 1` keeps it cheap.
        subprocess.run(["git", "init", "-q", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "remote", "add", "origin", url], check=True)
        r = subprocess.run(["git", "-C", tmp, "fetch", "-q", "--depth", "1", "origin", ref],
                           capture_output=True, text=True)
        if r.returncode:
            print(f"FAIL: cannot fetch {repo}@{ref} — {r.stderr.strip()}", file=sys.stderr)
            print("      (private repo: set GITHUB_TOKEN, or `gh auth login`)", file=sys.stderr)
            return 1
        subprocess.run(["git", "-C", tmp, "checkout", "-q", "FETCH_HEAD"], check=True)

        DEST.mkdir(parents=True, exist_ok=True)
        for rel in wanted:
            src = Path(tmp) / rel
            if not src.exists():
                print(f"FAIL: {rel} absent at {repo}@{ref[:12]}", file=sys.stderr)
                return 1
            shutil.copy2(src, DEST / src.name)
            print(f"  ok   {src.name} <- {repo}@{ref[:12]}")

    print(f"\ncontracts resolved into {DEST.relative_to(ROOT)} ({len(wanted)} schemas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
