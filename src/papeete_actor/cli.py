"""papeete-actor — the CLI. One tool, one pin, four contracts.

    papeete-actor lint-card        PAPEETE-ACTOR.YAML...  papeete-actor-card/v1
    papeete-actor lint-message     --issue-body FILE      inter-agent-message/v0
    papeete-actor lint-publication REPO...                publication/v2
    papeete-actor lint-registry    REGISTRY.YAML...       ecosystem-registry/v0
    papeete-actor check            --workspace DIR        the cross-card join
    papeete-actor contracts                               which contracts + which deployment profile

The contracts describe shapes; a DEPLOYMENT PROFILE supplies the values they cannot know — this
deployment's rails, the grammar of its taxonomy, and where it keeps its registry. `--profile FILE`
on the gates that read them; the shipped reference profile is the default (ADR-PA-0016).
"""
import argparse
import os
import sys
from pathlib import Path

import yaml

from . import CONTRACTS, __version__
from . import cards, check, messages, profile, publications, registry
from .report import Report
from .schemas import contracts_dir, load


PROFILE_HELP = ("this deployment's profile — its rails and the grammar of its taxonomy. "
                "Defaults to the shipped reference profile (ADR-PA-0016)")


def _registry_candidates(root: Path, prof: dict | None = None):
    """Where this deployment's registry may sit relative to `root`.

    THE PATHS COME FROM THE PROFILE, not from this file. They were three hard-coded literals
    naming one organisation's directory layout, which meant a consumer holding every published
    contract could author a conformant registry and still never be found (ADR-PA-0017). A profile
    that declares none falls back to the reference layout, so nothing that resolved before stops.

    Several candidates because a checkout may be flat (repos are siblings) or nested (repos under
    <org>/) — same reason `check` tries several card paths."""
    locations = profile.registry_locations(prof if prof is not None else profile.load())
    return [root / rel for rel in locations]


def _search_root(cards) -> Path:
    """The directory registry discovery starts from: the deepest ancestor holding every card.

    NEVER `cards[0]`, and never a fixed number of hops. It was both, and the two together made the
    gate's VERDICT DEPEND ON ARGUMENT ORDER — the same set of cards passed or failed according to
    which one happened to be listed first:

        lint-card own.yaml examples/a/card.yaml   -> root two levels above own.yaml   -> registry
                                                     found -> 'EXA.A resolves nowhere' -> FAIL
        lint-card examples/a/card.yaml own.yaml   -> root two levels above the example -> no
                                                     registry -> resolution skipped     -> PASS

    A conformance gate whose answer moves with the order of its arguments is the confident,
    precise, wrong answer this tool exists to prevent, so the root is now derived from ALL of them.
    `parent.parent` was also only ever right for a card at a repo root; for one nested at
    examples/actors/<name>/ it names a directory of no significance.
    """
    parents = [Path(c).resolve().parent for c in cards]
    return Path(os.path.commonpath([str(p) for p in parents]))


def _registry(explicit: Path | None, near: Path, prof: dict | None = None):
    """Find ecosystem/registry.yaml — given, or above the cards being checked.

    Walks UP from `near`, because the registry sits in a sibling repo and how far up that is
    depends on where the cards live: a repo root is one hop from the workspace, a nested example
    is three. Returns (registry, path) so the caller can say WHICH index produced its verdict —
    "resolves nowhere in registry.yaml" is unactionable when the reader cannot tell which
    registry.yaml was read. Absent in an isolated checkout, where dependency resolution is
    skipped rather than failed.
    """
    if explicit:
        return (yaml.safe_load(Path(explicit).read_text()), Path(explicit)) \
            if Path(explicit).exists() else (None, None)
    for base in [near, *near.parents]:
        for cand in _registry_candidates(base, prof):
            if cand.exists():
                return yaml.safe_load(cand.read_text()), cand
    return None, None


def cmd_lint_card(args) -> int:
    schema = load("papeete-actor-card")
    prof = profile.load(args.profile)
    reg, reg_path = _registry(args.registry, _search_root(args.cards), prof)
    if reg is None:
        print("  note registry.yaml not found — dependency resolution not checked")
    else:
        print(f"  note dependencies resolved against {reg_path}")
    rep = Report()
    for p in args.cards:
        path = Path(p)
        if not path.exists():
            rep.errors.append(f"{path}: no such file")
            continue
        rep.merge(cards.lint(path, schema, reg, prof))
    if args.strict:
        rep.errors += rep.warns
        rep.warns = []
    return rep.emit("papeete-actor-card gate")


def cmd_lint_message(args) -> int:
    schema = load("message")
    prof = profile.load(args.profile)
    if args.payload:
        rep = messages.lint_payload_file(Path(args.payload), schema, prof)
    else:
        body = sys.stdin.read() if args.issue_body == "-" else Path(args.issue_body).read_text()
        label = "issue body" if args.issue_body == "-" else args.issue_body
        labels = [x.strip() for x in args.labels.split(",") if x.strip()]
        rep = messages.lint_issue(body, labels, label, schema, prof)
    return rep.emit("message gate")


def cmd_lint_publication(args) -> int:
    schema = load("publication")
    rep = Report()
    for r in args.repos:
        root = Path(r)
        card_path = root / "papeete-actor.yaml"
        card = yaml.safe_load(card_path.read_text()) if card_path.exists() else None
        rep.merge(publications.lint_log(root, schema, card))
    return rep.emit("publication gate")


def cmd_check(args) -> int:
    workspace = Path(args.workspace).resolve()
    if args.registry:
        reg_path = Path(args.registry)
    else:
        cands = _registry_candidates(workspace, profile.load(args.profile))
        reg_path = next((c for c in cands if c.exists()), cands[0])
    return check.run(workspace, reg_path).emit("papeete-actor check")


def cmd_lint_registry(args) -> int:
    schema = load("registry")
    rep = Report()
    for r in args.registries:
        rep.merge(registry.lint(Path(r), schema))
    return rep.emit("ecosystem-registry gate")


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
    # A CONTRACT IS NOT COMPLETE WITHOUT THE VALUES IT CANNOT KNOW. Printed beside the contract
    # versions because a consumer reading "which shapes does this build enforce" needs to know
    # which deployment's rails and taxonomy it will enforce them against (ADR-PA-0016).
    prof = profile.load(args.profile)
    rails = profile.rails(prof)
    grammar = profile.scope_grammar(prof)
    src = args.profile or profile.default_path()
    print(f"\nprofile '{prof.get('profile', '?')}' from {src}")
    print(f"  rails          {', '.join(rails) if rails else '(unconstrained)'}")
    print(f"  scope_grammar  {grammar or '(unconstrained)'}")
    print(f"  registry       {', '.join(profile.registry_locations(prof))}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="papeete-actor", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"papeete-actor {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint-card", help="validate papeete-actor.yaml against papeete-actor-card/v1")
    p.add_argument("cards", nargs="+", type=Path)
    p.add_argument("--registry", type=Path, help="path to ecosystem/registry.yaml")
    p.add_argument("--profile", type=Path, help=PROFILE_HELP)
    p.add_argument("--strict", action="store_true", help="fail on unmigrated (v0) cards too")
    p.set_defaults(fn=cmd_lint_card)

    p = sub.add_parser("lint-message", help="validate an inter-agent message")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--payload", metavar="FILE", help="a YAML file holding one finding")
    g.add_argument("--issue-body", metavar="FILE", help="a GitHub issue body ('-' for stdin)")
    p.add_argument("--labels", default="", help="comma-separated issue labels")
    p.add_argument("--profile", type=Path, help=PROFILE_HELP)
    p.set_defaults(fn=cmd_lint_message)

    p = sub.add_parser("lint-publication", help="validate a repo's events/ log against publication/v2")
    p.add_argument("repos", nargs="+", type=Path, help="repo roots (each holding events/ and papeete-actor.yaml)")
    p.set_defaults(fn=cmd_lint_publication)

    p = sub.add_parser("lint-registry", help="validate the index that makes cards discoverable")
    p.add_argument("registries", nargs="+", type=Path, help="path(s) to a registry.yaml")
    p.set_defaults(fn=cmd_lint_registry)

    p = sub.add_parser("check", help="the cross-card join over the whole ecosystem")
    p.add_argument("--workspace", type=Path, default=Path("."), help="directory holding the sibling repos")
    p.add_argument("--registry", type=Path, help="path to ecosystem/registry.yaml")
    p.add_argument("--profile", type=Path, help=PROFILE_HELP)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("contracts", help="which contract versions this build enforces, and against which profile")
    p.add_argument("--profile", type=Path, help=PROFILE_HELP)
    p.set_defaults(fn=cmd_contracts)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (FileNotFoundError, ValueError) as e:
        # A missing or malformed profile/schema is a USER-FIXABLE misconfiguration, and both
        # loaders raise with instructions. A traceback buries them under a stack the reader cannot
        # act on, and reads as a crash in the gate rather than a mistake in the invocation.
        print(f"  FAIL {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
