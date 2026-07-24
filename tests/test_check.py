"""`papeete-actor check` — the cross-card join.

Everything here needs EVERY card at once, which is why none of it lives in the per-card gate. The
join is only as true as the cards are, and its failure mode is not a crash: it is a confident,
precise, wrong answer — a DANGLING-SUBSCRIPTION reported against a publication that exists.
"""
import pytest
import yaml

from papeete_actor import check


@pytest.fixture
def ecosystem(tmp_path):
    """A workspace of sibling repos plus the registry that indexes them."""

    class Workspace:
        root = tmp_path
        repos: list[dict] = []

        def actor(self, name: str, card: dict, *, papeete_actor: str | None = None,
                  card_status: str = "adopted"):
            root = tmp_path / name
            root.mkdir(parents=True, exist_ok=True)
            (root / "papeete-actor.yaml").write_text(yaml.safe_dump(card, sort_keys=False))
            self.repos.append({"repo": f"example/{name}", "card": "papeete-actor.yaml",
                               "card_status": card_status,
                               "papeete_actor": papeete_actor or card.get("papeete_actor", "none")})
            return root

        def external(self, repo: str):
            self.repos.append({"repo": repo})

        def run(self):
            reg = tmp_path / "registry.yaml"
            reg.write_text(yaml.safe_dump({"repos": self.repos}, sort_keys=False))
            return check.run(tmp_path, reg)

    ws = Workspace()
    ws.repos = []
    return ws


def card(actor: str, **sections) -> dict:
    base = {"card": "papeete-actor-card/v1", "papeete_actor": actor,
            "publications": [], "subscriptions": [], "dependencies": []}
    base.update(sections)
    return base


def pub(pub_id: str, **kw) -> dict:
    return {"id": pub_id, "means": "a fact", "shape": "none", "surface": "src/", **kw}


def sub(to: str, **kw) -> dict:
    base = {"to": to, "notice": {"binding": "event-log", "cadence": "on demand"},
            "then": {"outcome": "records", "intent": "I re-pin"}}
    base.update(kw)
    return base


# ── the preconditions ─────────────────────────────────────────────────────────────────────────

def test_a_missing_registry_is_an_error_not_an_empty_report(tmp_path):
    """The join has no index to walk — reporting "all clear" would be the worst answer."""
    rep = check.run(tmp_path, tmp_path / "nope.yaml")
    assert any("no index to walk" in e for e in rep.errors)


def test_a_registry_naming_cards_that_are_not_checked_out_reports_it(ecosystem):
    ecosystem.repos.append({"repo": "example/absent", "card": "papeete-actor.yaml",
                            "card_status": "adopted"})
    rep = ecosystem.run()
    assert any("no card found" in n for n in rep.notes)


def test_no_cards_at_all_is_an_error(ecosystem):
    ecosystem.external("papeete-hub/kpack")
    rep = ecosystem.run()
    assert any("no cards found" in e for e in rep.errors)


# ── the retired key ───────────────────────────────────────────────────────────────────────────

def test_the_retired_actor_key_is_a_hard_error_not_a_fallback(ecosystem):
    """Resolving it to None would leave the card in the join under its REPO NAME, so its
    publications index as `banking-tech/X` while every consumer writes `BNK.TECH/X` — and the join
    then reports a DANGLING-SUBSCRIPTION against each one. A confident, precise, wrong answer."""
    c = card("BNK.TECH", publications=[pub("a-fact")])
    c["actor"] = "BNK.TECH"
    ecosystem.actor("tech", c)
    rep = ecosystem.run()
    assert any("declares the retired key `actor:`" in e for e in rep.errors)


# ── dangling subscriptions ────────────────────────────────────────────────────────────────────

def test_a_subscription_to_a_published_fact_joins(ecosystem):
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("UP.STREAM/a-fact")],
                                 dependencies=[{"id": "UP.STREAM", "ref": "v1"}]))
    rep = ecosystem.run()
    assert not any("DANGLING" in w for w in rep.warns)


def test_a_subscription_nobody_publishes_is_dangling(ecosystem):
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("UP.STREAM/no-such-fact")],
                                 dependencies=[{"id": "UP.STREAM", "ref": "v1"}]))
    rep = ecosystem.run()
    assert any("DANGLING-SUBSCRIPTION" in w for w in rep.warns)


def test_a_publication_resolves_under_its_repo_name_too(ecosystem):
    """Consumers write one or the other; both keys must reach the same publication."""
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("up/a-fact")],
                                 dependencies=[{"id": "UP.STREAM", "ref": "v1"}]))
    rep = ecosystem.run()
    assert not any("DANGLING" in w for w in rep.warns)


def test_a_subscription_to_an_external_source_is_never_dangling(ecosystem):
    """ADR-ECO-0014 §2 exists precisely so papeete-hub/kpack is reported as external."""
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("papeete-hub/kpack/corpus")],
                                 dependencies=[{"id": "papeete-hub/kpack", "ref": "main"}]))
    ecosystem.external("papeete-hub/kpack")
    rep = ecosystem.run()
    assert any("EXTERNAL" in n for n in rep.notes)
    assert not any("DANGLING" in w for w in rep.warns)


def test_a_dangling_subscription_names_a_source_that_owes_a_card(ecosystem):
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("example/settler/a-fact")],
                                 dependencies=[{"id": "example/settler", "ref": "main"}]))
    ecosystem.repos.append({"repo": "example/settler", "card_status": "none"})
    rep = ecosystem.run()
    assert any("owes a card" in w for w in rep.warns)


def test_a_subscription_naming_no_publication_id_is_not_joinable(ecosystem):
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("UP.STREAM")],
                                 dependencies=[{"id": "UP.STREAM", "ref": "v1"}]))
    rep = ecosystem.run()
    assert any("names no publication id" in n for n in rep.notes)


# ── unsubscribed publications ─────────────────────────────────────────────────────────────────

def test_a_publication_nobody_pulls_is_reported(ecosystem):
    """Dead output, or a missing consumer."""
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    rep = ecosystem.run()
    assert any("UNSUBSCRIBED-PUBLICATION" in w for w in rep.warns)


def test_an_unsubscribed_publication_is_reported_once_not_under_both_keys(ecosystem):
    """It is reachable under its actor id AND its repo name; only the pair should be reported."""
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    rep = ecosystem.run()
    assert len([w for w in rep.warns if "UNSUBSCRIBED-PUBLICATION" in w]) == 1


def test_a_publication_pulled_under_either_alias_is_not_unsubscribed(ecosystem):
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[sub("up/a-fact")],
                                 dependencies=[{"id": "UP.STREAM", "ref": "v1"}]))
    rep = ecosystem.run()
    assert not any("UNSUBSCRIBED" in w for w in rep.warns)


# ── the two v1 classes ────────────────────────────────────────────────────────────────────────

def test_a_publication_with_records_and_no_shape_is_unschematised(ecosystem):
    root = ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    log = root / "events" / "a-fact"
    log.mkdir(parents=True)
    (log / "v1.0.0.yaml").write_text("publication: a-fact\n")
    rep = ecosystem.run()
    assert any("UNSCHEMATISED-PUBLICATION" in w for w in rep.warns)


def test_a_scripted_subscription_on_a_floating_ref_is_unpinned(ecosystem):
    s = sub("UP.STREAM/a-fact")
    s["then"]["run"] = "tools/detect.py"
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[s],
                                 dependencies=[{"id": "UP.STREAM", "ref": "main"}]))
    rep = ecosystem.run()
    assert any("UNPINNED-SCRIPTED-SUBSCRIPTION" in w for w in rep.warns)


def test_a_scripted_subscription_over_a_reference_binding_is_exempt(ecosystem):
    s = sub("UP.STREAM/a-fact", notice={"binding": "repo-read", "cadence": "on demand",
                                        "position": "none"})
    s["then"]["run"] = "tools/drift.py"
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    ecosystem.actor("down", card("DOWN.STREAM", subscriptions=[s],
                                 dependencies=[{"id": "UP.STREAM", "ref": "main"}]))
    rep = ecosystem.run()
    assert not any("UNPINNED" in w for w in rep.warns)


# ── honesty about coverage ────────────────────────────────────────────────────────────────────

def test_the_report_says_how_much_of_the_ecosystem_it_covered(ecosystem):
    """A v0 card cannot express `dependencies` at all, so the join says what it actually reached
    rather than implying it reached everything."""
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    v0 = card("OLD.CARD")
    v0["card"] = "actor-card/v0"
    ecosystem.actor("old", v0)
    rep = ecosystem.run()
    assert any("joined 2 card(s)" in o and "1 at papeete-actor-card/v1" in o for o in rep.oks)
    assert any("still at v0" in n for n in rep.notes)


def test_undeclared_consumption_is_declared_not_computed(ecosystem):
    """NOT decidable from cards, by construction — the evidence is in consumer code. Saying so is
    the difference between a gate with a known blind spot and one that implies it has none."""
    ecosystem.actor("up", card("UP.STREAM", publications=[pub("a-fact")]))
    rep = ecosystem.run()
    assert any("undeclared-consumption is NOT computed" in n for n in rep.notes)
