"""papeete-actor — the CLI. One tool, one pin, one contract.

    papeete-actor lint-manifest    ACTOR.YAML...          papeete-actor-manifest/v0
    papeete-actor version          FOLDER... --label L    print <semver>-<L>-<shortSha>, no Docker
    papeete-actor build            FOLDER... --label L    tag <name>:<semver>-<L>-<shortSha>
    papeete-actor contracts                                which contract version this build enforces

`build` turns one actor's own folder into a runnable image, tagged on the local Docker image
store, versioned `<semver>-<label>-<shortSha>` (ADR-PA-0023) — the semver core from the actor's
own nearest `<name>/vX.Y.Z` git tag, the short SHA from its last touching commit, both git's own
fact, never a declared field; `--label` is yours, uninterpreted. `version` computes and prints the
same string alone, without Docker — the smaller claim, for a CI step or a human to check where an
actor stands before spending the time to build it. Running a SET of actors together is a
different repo's job — [`papeete-product`](https://github.com/papeete-hub/papeete-product) — which
only ever consumes tags `build` already produced.
"""
import argparse
import sys
from pathlib import Path

from . import CONTRACTS, __version__
from . import build, manifest
from .report import Report
from .schemas import contracts_dir, load


def cmd_lint_manifest(args) -> int:
    schema = load("manifest")
    rep = Report()
    for m in args.manifests:
        rep.merge(manifest.lint(Path(m), schema))
    return rep.emit("papeete-actor-manifest gate")


def cmd_version(args) -> int:
    for folder in args.folders:
        print(build.actor_version(folder, args.label))
    return 0


def cmd_build(args) -> int:
    for folder in args.folders:
        tag = build.build_actor(folder, args.label)
        print(f"  ok   {folder}: built and tagged {tag}")
    return 0


def cmd_contracts(args) -> int:
    print(f"papeete-actor {__version__}  —  contracts from {contracts_dir()}")
    for kind, expected in CONTRACTS.items():
        try:
            actual = load(kind).get("contract")
        except FileNotFoundError as e:
            print(f"  FAIL {kind}: {e}", file=sys.stderr)
            return 1
        mark = "ok  " if actual == expected else "FAIL"
        print(f"  {mark} {kind:18} {actual}" + ("" if actual == expected else f"  (build expects {expected})"))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="papeete-actor", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"papeete-actor {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint-manifest", help="validate a minimal actor identity against papeete-actor-manifest/v0")
    p.add_argument("manifests", nargs="+", type=Path, help="path(s) to an actor.yaml")
    p.set_defaults(fn=cmd_lint_manifest)

    p = sub.add_parser("version", help="print one actor's <semver>-<label>-<shortSha>, no Docker involved")
    p.add_argument("folders", nargs="+", type=Path, help="actor folder(s), each holding actor.yaml")
    p.add_argument("--label", required=True,
                   help="uninterpreted qualifier (e.g. dev, rc.1, staging) — taxonomy not yet decided, ADR-PA-0023")
    p.set_defaults(fn=cmd_version)

    p = sub.add_parser("build", help="build one actor's Dockerfile and tag it <name>:<semver>-<label>-<shortSha>")
    p.add_argument("folders", nargs="+", type=Path, help="actor folder(s), each holding actor.yaml and a Dockerfile")
    p.add_argument("--label", required=True,
                   help="uninterpreted qualifier (e.g. dev, rc.1, staging) — taxonomy not yet decided, ADR-PA-0023")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("contracts", help="which contract version this build enforces")
    p.set_defaults(fn=cmd_contracts)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (FileNotFoundError, ValueError) as e:
        # A missing or malformed schema is a USER-FIXABLE misconfiguration, and the loader raises
        # with instructions. A traceback buries them under a stack the reader cannot act on, and
        # reads as a crash in the gate rather than a mistake in the invocation.
        print(f"  FAIL {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
