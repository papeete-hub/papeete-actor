"""Build hook — resolve contracts.pin before any sdist or wheel is built.

WHY THIS EXISTS. `scripts/fetch_contracts.py` as a manual pre-build step is fine for CI, where the
workflow can call it, and useless for `pip install git+…`: pip builds from a fresh checkout where
nothing ran the fetch, and the wheel ships with no schemas. That failure is not loud at install
time — it surfaces later as a gate that enforces nothing. It was found by installing charter into
ECO.GOV from git and watching `charter contracts` report an empty contracts directory.

So the fetch becomes part of the build itself. A source build is now self-sufficient, and the
manual script stays for local iteration.

If the contracts are ALREADY present (a CI run that fetched them, or a rebuild) this is a no-op —
the build never reaches the network twice, and an offline rebuild of a prepared tree still works.
"""
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "src" / "charter" / "schemas"
EXPECTED = 3


class FetchContracts(BuildHookInterface):
    PLUGIN_NAME = "fetch-contracts"

    def initialize(self, version, build_data):
        present = list(DEST.glob("*.schema.yaml")) if DEST.is_dir() else []
        if len(present) >= EXPECTED:
            self.app.display_info(f"contracts already resolved ({len(present)} schemas) — no fetch")
            return
        self.app.display_waiting("resolving contracts.pin…")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_contracts.py")],
                           capture_output=True, text=True)
        if r.returncode:
            # Fail the BUILD, not the install-time import. A wheel without contracts is a gate
            # with nothing to enforce, and shipping one quietly is worse than not shipping.
            raise RuntimeError(
                "cannot resolve contracts.pin — refusing to build a charter with no contracts.\n"
                f"{r.stdout}{r.stderr}"
            )
        self.app.display_info(r.stdout.strip())
