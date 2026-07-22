"""charter — the CLI. One tool, one pin, three contracts.

    charter lint-card        ACTOR.YAML...      actor-card/v1
    charter lint-message     --issue-body FILE  inter-agent-message/v0
    charter lint-publication REPO...            publication/v2
    charter check            --workspace DIR    the cross-card join
    charter contracts                           which contract versions this build enforces
"""
import argparse
import sys
from pathlib import Path

import yaml

from . import CONTRACTS, __version__
from . import cards, check, messages, publications
from .report import Report
from .schemas import contracts_dir, load


def _registry(explicit: Path | None, near: Path) -> dict | None:
    """Find ecosystem/registry.yaml — given, or beside the cards being checked. Absent in an
    isolated checkout, where dependency resolution is skipped rather than failed."""
    for cand in (explicit, near / "ecosystem-governance" / "ecosystem" / "registry.yaml"):
        if cand and Path(cand).exists():
            return yaml.safe_load(Path(cand).read_text())
    return None


def cmd_lint_card(args) -> int:
    schema = load("actor-card")
    workspace = Path(args.cards[0]).resolve().parent.parent
    reg = _registry(args.registry, workspace)
    if reg is None:
        print("  note registry.yaml not found — dependency resolution not checked")
    rep = Report()
    for p in args.cards:
        path = Path(p)
        if not path.exists():
            rep.errors.append(f"{path}: no such file")
            continue
        rep.merge(cards.lint(path, schema, reg))
    if args.strict:
        rep.errors += rep.warns
        rep.warns = []
    return rep.emit("actor-card gate")


def cmd_lint_message(args) -> int:
    schema = load("message")
    if args.payload:
        rep = messages.lint_payload_file(Path(args.payload), schema)
    else:
        body = sys.stdin.read() if args.issue_body == "-" else Path(args.issue_body).read_text()
        label = "issue body" if args.issue_body == "-" else args.issue_body
        labels = [x.strip() for x in args.labels.split(",") if x.strip()]
        rep = messages.lint_issue(body, labels, label, schema)
    return rep.emit("message gate")


def cmd_lint_publication(args) -> int:
    schema = load("publication")
    rep = Report()
    for r in args.repos:
        root = Path(r)
        card_path = root / "actor.yaml"
        card = yaml.safe_load(card_path.read_text()) if card_path.exists() else None
        rep.merge(publications.lint_log(root, schema, card))
    return rep.emit("publication gate")


def cmd_check(args) -> int:
    workspace = Path(args.workspace).resolve()
    registry = Path(args.registry) if args.registry else workspace / "ecosystem-governance" / "ecosystem" / "registry.yaml"
    return check.run(workspace, registry).emit("charter check")


def cmd_contracts(args) -> int:
    print(f"charter {__version__}  —  contracts from {contracts_dir()}")
    for kind, expected in CONTRACTS.items():
        try:
            actual = load(kind).get("contract")
        except FileNotFoundError as e:
            print(f"  FAIL {kind}: {e}", file=sys.stderr)
            return 1
        mark = "ok  " if actual == expected else "FAIL"
        print(f"  {mark} {kind:12} {actual}" + ("" if actual == expected else f"  (build expects {expected})"))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="charter", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"charter {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint-card", help="validate actor.yaml against actor-card/v1")
    p.add_argument("cards", nargs="+", type=Path)
    p.add_argument("--registry", type=Path, help="path to ecosystem/registry.yaml")
    p.add_argument("--strict", action="store_true", help="fail on unmigrated (v0) cards too")
    p.set_defaults(fn=cmd_lint_card)

    p = sub.add_parser("lint-message", help="validate an inter-agent message")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--payload", metavar="FILE", help="a YAML file holding one finding")
    g.add_argument("--issue-body", metavar="FILE", help="a GitHub issue body ('-' for stdin)")
    p.add_argument("--labels", default="", help="comma-separated issue labels")
    p.set_defaults(fn=cmd_lint_message)

    p = sub.add_parser("lint-publication", help="validate a repo's events/ log against publication/v2")
    p.add_argument("repos", nargs="+", type=Path, help="repo roots (each holding events/ and actor.yaml)")
    p.set_defaults(fn=cmd_lint_publication)

    p = sub.add_parser("check", help="the cross-card join over the whole ecosystem")
    p.add_argument("--workspace", type=Path, default=Path("."), help="directory holding the sibling repos")
    p.add_argument("--registry", type=Path, help="path to ecosystem/registry.yaml")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("contracts", help="which contract versions this build enforces")
    p.set_defaults(fn=cmd_contracts)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
