"""THE SURFACE ANOTHER PACKAGE EMBEDS — pinned here because nothing else pins it.

`papeete-actor` was written as a CLI shipping gates, and its card describes it as one. It is also
imported as a LIBRARY: `papeete-actor-simple` calls `papeete_actor.cards.lint` and merges the
`Report` into its own, because the card contract is consumed there and never re-authored
(ADR-PAS-0004). That is the right dependency — one implementation of the card rules, in the repo
that owns them — and it means these names are contracted whether or not the card says so.

The consumer defends itself by calling positionally with one argument, and says why:

    "`papeete_actor.cards.lint(path)` has that one signature across every published version of
     the package, so this gate keeps working when the pin moves"

It is right about the history — 0.1.0 took `(path, schema, registry)` and 0.4.0 takes
`(path, schema, registry, prof)`, so a positional single-arg call survived a signature change
that a keyword call would not have. These tests make that a promise instead of a lucky streak.
"""
import inspect

import pytest

from papeete_actor import CONTRACTS, cards, check, messages, profile, publications
from papeete_actor.report import Report
from papeete_actor.schemas import contracts_dir, load


# ── the call the downstream actually makes ────────────────────────────────────────────────────

def test_cards_lint_takes_one_positional_path(minimal, write_card):
    """The exact call in papeete_actor_simple/card.py. Everything after `path` must stay
    optional, or every consumer that vendored this call breaks on a routine upgrade."""
    rep = cards.lint(write_card(minimal))
    assert isinstance(rep, Report)


def test_every_parameter_after_path_has_a_default():
    params = list(inspect.signature(cards.lint).parameters.values())
    assert params[0].name == "path"
    assert all(p.default is not inspect.Parameter.empty for p in params[1:])


def test_cards_lint_accepts_a_string_path(minimal, write_card):
    """Consumers hold `Path | str` and pass it through."""
    assert cards.lint(str(write_card(minimal))).errors == []


# ── the Report the downstream merges into ─────────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["oks", "notes", "warns", "errors"])
def test_a_report_carries_the_four_lists(field):
    """The consumer appends to all four by name, and its own gate's findings ride the same
    object. Renaming one silently drops findings on the floor downstream."""
    assert isinstance(getattr(Report(), field), list)


def test_a_fresh_report_is_empty():
    rep = Report()
    assert (rep.oks, rep.notes, rep.warns, rep.errors) == ([], [], [], [])


def test_two_reports_merge_in_place_and_return_self():
    a, b = Report(oks=["a"]), Report(errors=["b"], notes=["n"])
    assert a.merge(b) is a
    assert a.oks == ["a"] and a.errors == ["b"] and a.notes == ["n"]


def test_only_errors_fail_the_run(capsys):
    """Warns and notes never do. The distinction is doctrinal: a heuristic finding is a prompt to
    declare, never an automatic verdict (ADR-PA-0009 §5)."""
    assert Report(oks=["x"], warns=["w"], notes=["n"]).emit("gate") == 0
    assert Report(errors=["e"]).emit("gate") == 1


def test_errors_go_to_stderr_and_the_rest_to_stdout(capsys):
    Report(oks=["fine"], errors=["broken"]).emit("gate")
    out = capsys.readouterr()
    assert "fine" in out.out and "broken" not in out.out
    assert "broken" in out.err


# ── the module surface ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("module,fn", [
    (cards, "lint"), (cards, "registry_classes"), (cards, "resolve_source"),
    (messages, "validate_payload"), (messages, "lint_issue"), (messages, "lint_payload_file"),
    (publications, "lint_log"), (check, "run"),
    (profile, "load"), (profile, "rails"), (profile, "scope_grammar"),
])
def test_the_entry_point_exists(module, fn):
    assert callable(getattr(module, fn))


def test_the_card_contract_name_is_importable():
    """Consumers report against it by name rather than restating the string."""
    assert cards.CONTRACT == "papeete-actor-card/v1"


# ── the wheel must carry its contracts ────────────────────────────────────────────────────────
# The same assertion CI makes against a built wheel, made against the source tree too. A gate with
# nothing to enforce is the failure mode worth a test.

@pytest.mark.parametrize("kind", ["papeete-actor-card", "message", "publication"])
def test_every_contract_loads(kind):
    assert isinstance(load(kind), dict)


@pytest.mark.parametrize("kind,expected", sorted(CONTRACTS.items()))
def test_each_schema_declares_the_version_the_build_expects(kind, expected):
    """`papeete-actor contracts` compares these two. A schema edited without moving CONTRACTS —
    or the reverse — is a build that reports a version it does not enforce."""
    assert load(kind)["contract"] == expected


def test_the_contracts_ship_beside_the_code():
    """The path is the same in a source checkout and in an installed wheel, so there is no
    fallback and no second location to reason about."""
    assert contracts_dir().is_dir()
    assert (contracts_dir() / "papeete-actor-card.schema.yaml").exists()


def test_an_unknown_contract_kind_raises():
    with pytest.raises(KeyError):
        load("no-such-contract")
