"""`resolve_source` and `registry_classes` — the two functions the join is only as correct as.

Both have a documented history of confident, precise, wrong answers, and both are pure. They get
their own file because a bug in either does not crash: it reports a defect against a card that
does not have one, which is exactly what a conformance tool must never do.
"""
from papeete_actor.cards import registry_classes, resolve_source


# ── resolve_source ────────────────────────────────────────────────────────────────────────────
# THREE SHAPES SHARE ONE FIELD and the separator is ambiguous in all of them, because a source id
# may itself contain a slash. Splitting on the FIRST slash yields the org, which resolves to
# nothing — the bug fixed in 36d89e8, which reported papeete-hub/kpack as a dangling subscription
# in both repos holding it.

def test_an_actor_id_and_a_publication():
    assert resolve_source("BNK.KNOW/meta-model", {"BNK.KNOW": "v1"}) == "BNK.KNOW"


def test_a_whole_artifact_with_no_publication_id():
    assert resolve_source("papeete-hub/kpack", {"papeete-hub/kpack": "main"}) == "papeete-hub/kpack"


def test_a_repo_path_source_and_a_publication():
    """The shape that appeared when ECO.GOV began consuming a contract from a repo-path source.
    Naively splitting reported `papeete-hub` as an undeclared dependency."""
    known = {"papeete-hub/papeete-actor": "0.4.0"}
    assert resolve_source("papeete-hub/papeete-actor/gates", known) == "papeete-hub/papeete-actor"


def test_the_longest_known_prefix_wins_not_the_first():
    """Both `papeete-hub` and `papeete-hub/kpack` known: the longer one is the source."""
    known = {"papeete-hub": "main", "papeete-hub/kpack": "v2"}
    assert resolve_source("papeete-hub/kpack/corpus", known) == "papeete-hub/kpack"


def test_an_unknown_source_falls_back_to_the_first_segment():
    """So the join can still report a dangling subscription against something nameable."""
    assert resolve_source("BNK.NOBODY/a-fact", {}) == "BNK.NOBODY"


def test_a_bare_id_with_no_slash():
    assert resolve_source("BNK.KNOW", {"BNK.KNOW": "v1"}) == "BNK.KNOW"


# ── registry_classes ──────────────────────────────────────────────────────────────────────────
# KEYED ON card_status, NEVER ON `papeete_actor:`. The first draft keyed on the id and
# misclassified two of seven dependencies immediately.

def test_an_adopted_card_is_an_actor():
    reg = {"repos": [{"repo": "example/up", "papeete_actor": "UP", "card_status": "adopted"}]}
    assert registry_classes(reg)["UP"] == "actor"


def test_a_pending_card_is_an_actor():
    reg = {"repos": [{"repo": "example/up", "papeete_actor": "UP", "card_status": "pending"}]}
    assert registry_classes(reg)["UP"] == "actor"


def test_an_actor_with_no_context_id_is_still_an_actor():
    """`reliever-implementation` carries `papeete_actor: none` and its card is ADOPTED. Calling it
    external would silence the very defect the class exists to surface."""
    reg = {"repos": [{"repo": "example/impl", "papeete_actor": "none", "card_status": "adopted"}]}
    assert registry_classes(reg)["example/impl"] == "actor"


def test_card_status_none_is_dangling_not_external():
    """`settler` — an actor that owes a card (ADR-PA-0009 §1)."""
    reg = {"repos": [{"repo": "example/settler", "card_status": "none"}]}
    assert registry_classes(reg)["example/settler"] == "dangling"


def test_an_entry_with_no_card_status_at_all_is_external():
    """An engine or an artifact, never an actor (ADR-ECO-0014 §2)."""
    reg = {"repos": [{"repo": "papeete-hub/kpack"}]}
    assert registry_classes(reg)["papeete-hub/kpack"] == "external"


def test_a_repo_is_indexed_under_its_bare_name_too():
    """Cards write `kpack`, the registry writes `papeete-hub/kpack`. Both must resolve."""
    classes = registry_classes({"repos": [{"repo": "papeete-hub/kpack"}]})
    assert classes["kpack"] == "external"
    assert classes["papeete-hub/kpack"] == "external"


def test_the_literal_none_is_never_indexed():
    """Otherwise every actor carrying `papeete_actor: none` collides under one key."""
    reg = {"repos": [
        {"repo": "example/a", "papeete_actor": "none", "card_status": "adopted"},
        {"repo": "example/b", "papeete_actor": "none", "card_status": "none"},
    ]}
    assert "none" not in registry_classes(reg)


def test_an_empty_registry_classifies_nothing():
    assert registry_classes({}) == {}
