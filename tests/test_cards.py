"""The papeete-actor-card/v1 gate, one card at a time.

WHAT THIS SUITE IS FOR. Three breaking changes to this contract shipped between 0.1.0 and 0.4.0
with nothing exercising the gate but the repo's own card — which passes trivially and therefore
catches nothing. The one downstream consumer discovered `offers[].means` had become required by
its test suite going red. These tests are the thing that should have gone red first.
"""
import pytest

from papeete_actor import cards, profile


def test_the_minimal_card_conforms(minimal, write_card):
    """Every section present and empty. The floor the rest of the suite mutates."""
    rep = cards.lint(write_card(minimal))
    assert rep.errors == []
    assert rep.oks


@pytest.mark.parametrize("key", ["card", "papeete_actor", "tier", "name", "repo",
                                 "strategic_class", "pair", "mailbox"])
def test_an_identity_key_is_required(minimal, write_card, key):
    del minimal[key]
    rep = cards.lint(write_card(minimal))
    if key == "card":
        # A card that does not declare the contract is UNMIGRATED, not non-conformant — the gate
        # warns and stops, because adoption is each pair's own act (ADR-PA-0009).
        assert any("UNMIGRATED" in w for w in rep.warns)
    else:
        assert any(f"missing required key '{key}'" in e for e in rep.errors)


@pytest.mark.parametrize("key", ["records", "gates", "work_surface", "autonomy"])
def test_a_remainder_key_is_required(minimal, write_card, key):
    del minimal[key]
    rep = cards.lint(write_card(minimal))
    assert any(f"missing required key '{key}'" in e for e in rep.errors)


@pytest.mark.parametrize("section", ["offers", "publications", "releases",
                                     "subscriptions", "dependencies"])
def test_an_absent_section_is_an_error_but_an_empty_one_is_not(minimal, write_card, section):
    """`[]` and absent are DIFFERENT. An empty list is a claim ("I ship nothing"); a missing key
    is silence, and silence is what the join cannot distinguish from an unwritten card."""
    del minimal[section]
    rep = cards.lint(write_card(minimal))
    assert any(f"missing '{section}'" in e for e in rep.errors)


def test_a_v0_card_is_unmigrated_not_failed(minimal, write_card):
    minimal["card"] = "actor-card/v0"
    rep = cards.lint(write_card(minimal))
    assert rep.errors == []
    assert any("UNMIGRATED" in w for w in rep.warns)


@pytest.mark.parametrize("gone", ["requests", "requests_out"])
def test_a_retired_section_surviving_a_v1_card_fails(minimal, write_card, gone):
    """Half a migration is worse than none — a reader cannot tell which half is authoritative."""
    minimal[gone] = []
    rep = cards.lint(write_card(minimal))
    assert any(f"'{gone}' survives a v1 card" in e for e in rep.errors)


# ── offers ────────────────────────────────────────────────────────────────────────────────────

def test_an_offer_must_say_what_its_door_is_for(minimal, write_card, offer):
    """THE REGRESSION THAT BIT THE DOWNSTREAM. `means` joined offers.required after 0.1.0; a card
    written against the published gate has no such field and now fails."""
    del offer["means"]
    minimal["offers"] = [offer]
    rep = cards.lint(write_card(minimal))
    assert any("missing required key 'means'" in e for e in rep.errors)


@pytest.mark.parametrize("key", ["id", "means", "nature", "rail", "completion"])
def test_every_required_offer_key_is_checked(minimal, write_card, offer, key):
    del offer[key]
    minimal["offers"] = [offer]
    rep = cards.lint(write_card(minimal))
    assert any(f"missing required key '{key}'" in e for e in rep.errors)


def test_nature_is_the_contracts_enum(minimal, write_card, offer):
    offer["nature"] = "command"
    minimal["offers"] = [offer]
    rep = cards.lint(write_card(minimal))
    assert any("nature='command'" in e for e in rep.errors)


def test_an_unknown_offer_key_is_a_note_never_an_error(minimal, write_card, offer):
    """v0 enumerated nothing so authors invented `authority`, `caveat`, `outbox`. Reporting
    rather than rejecting keeps a card able to say a true thing it has no slot for."""
    offer["authority"] = "mine alone"
    minimal["offers"] = [offer]
    rep = cards.lint(write_card(minimal))
    assert rep.errors == []
    assert any("'authority' is not named by the schema" in n for n in rep.notes)


# ── releases — the intra-card join ────────────────────────────────────────────────────────────

def test_a_release_announced_by_a_publication_on_this_card_conforms(
        minimal, write_card, release, publication):
    minimal["publications"] = [publication]
    minimal["releases"] = [release]
    assert cards.lint(write_card(minimal)).errors == []


def test_a_release_announced_by_nothing_is_an_unannounced_release(minimal, write_card, release):
    """An artefact that ships with no fact is invisible to every consumer that pins it — the
    ADR-PA-0008 failure, made structural."""
    release["announced_by"] = "none"
    minimal["releases"] = [release]
    rep = cards.lint(write_card(minimal))
    assert any("unannounced_release" in e for e in rep.errors)


def test_a_release_may_not_be_announced_by_someone_elses_publication(
        minimal, write_card, release, publication):
    """Cutting the release IS emitting the fact — one act, by one actor. The announcing
    publication is therefore this card's own, which is what makes the join decidable here."""
    minimal["publications"] = [publication]
    release["announced_by"] = "UP.STREAM/their-publication"
    minimal["releases"] = [release]
    rep = cards.lint(write_card(minimal))
    assert any("is not a publication on this card" in e for e in rep.errors)


def test_a_card_with_no_releases_conforms(minimal, write_card):
    """'A terminal tier owes the ecosystem findings, not artefacts' (ADR-PA-0009 §3)."""
    assert cards.lint(write_card(minimal)).errors == []


def test_shipping_an_artefact_obliges_a_publication(minimal, write_card, release):
    """THE CONTRACT DEVIATION papeete-actor-simple reports, asserted rather than argued.

    `announced_by` is required and must name a publication on the same card, so `publications: []`
    and a non-empty `releases` cannot both hold. An actor restricted to addressed messages —
    which is what a simple actor IS — can therefore never ship a release.

    This test PASSES while the deviation stands. It is here so that closing it is a deliberate
    act with a failing test attached, not a silent widening nobody notices.
    """
    minimal["publications"] = []
    minimal["releases"] = [release]
    rep = cards.lint(write_card(minimal))
    assert any("unannounced_release" in e for e in rep.errors)


# ── publications ──────────────────────────────────────────────────────────────────────────────

def test_what_is_renamed_means(minimal, write_card, publication):
    publication["what"] = publication.pop("means")
    minimal["publications"] = [publication]
    rep = cards.lint(write_card(minimal))
    assert any("'what' is renamed 'means' in v1" in e for e in rep.errors)


def test_shape_none_is_legal_while_the_log_is_empty(minimal, write_card, publication):
    """A schema for a fact never emitted could only be imagined — the obligation binds at FIRST
    RECORD, not at declaration (publication/v2 `binds_at`)."""
    minimal["publications"] = [publication]
    rep = cards.lint(write_card(minimal))
    assert rep.errors == []
    assert any("obligation binds at first record" in n for n in rep.notes)


def test_shape_none_with_records_in_the_log_fails(minimal, write_card, publication):
    minimal["publications"] = [publication]
    path = write_card(minimal)
    log = path.parent / "events" / publication["id"]
    log.mkdir(parents=True)
    (log / "v1.0.0.yaml").write_text("publication: the-contract\n")
    rep = cards.lint(path)
    assert any("binds at first record" in e for e in rep.errors)


def test_a_shape_that_does_not_resolve_fails(minimal, write_card, publication):
    publication["shape"] = "events/the-contract/schema.yaml"
    minimal["publications"] = [publication]
    rep = cards.lint(write_card(minimal))
    assert any("does not resolve" in e for e in rep.errors)


def test_a_shape_that_resolves_conforms(minimal, write_card, publication):
    publication["shape"] = "events/the-contract/schema.yaml"
    minimal["publications"] = [publication]
    path = write_card(minimal)
    shape = path.parent / publication["shape"]
    shape.parent.mkdir(parents=True)
    shape.write_text("required: [publication, at, ref, summary]\n")
    assert cards.lint(path).errors == []


# ── subscriptions ─────────────────────────────────────────────────────────────────────────────

def test_how_is_replaced_by_notice_and_then(minimal, write_card, subscription):
    subscription["how"] = "polled"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = [{"id": "UP.STREAM", "ref": "v1.0.0"}]
    rep = cards.lint(write_card(minimal))
    assert any("'how' is replaced by 'notice:' + 'then:'" in e for e in rep.errors)


def test_pin_moves_to_dependencies_ref(minimal, write_card, subscription):
    subscription["pin"] = "v1.0.0"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = [{"id": "UP.STREAM", "ref": "v1.0.0"}]
    rep = cards.lint(write_card(minimal))
    assert any("'pin' moves to dependencies[].ref" in e for e in rep.errors)


def test_a_subscription_that_reacts_to_nothing_is_undeclared_consumption(
        minimal, write_card, subscription):
    subscription["then"] = {"outcome": "records"}
    minimal["subscriptions"] = [subscription]
    rep = cards.lint(write_card(minimal))
    assert any("reacts to nothing" in e for e in rep.errors)


def test_outcome_is_closed_at_three(minimal, write_card, subscription):
    """The enum is what stops `then` from becoming an escape hatch that swallows the direction
    rule."""
    subscription["then"]["outcome"] = "email"
    minimal["subscriptions"] = [subscription]
    rep = cards.lint(write_card(minimal))
    assert any("outcome='email'" in e for e in rep.errors)


# ── the pin rule ──────────────────────────────────────────────────────────────────────────────

def test_a_scripted_subscription_over_state_transfer_must_pin(minimal, write_card, subscription):
    """A scripted consumer that BUILDS ON upstream content breaks silently on drift."""
    subscription["then"]["run"] = "tools/detect.py"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = [{"id": "UP.STREAM", "ref": "main"}]
    rep = cards.lint(write_card(minimal))
    assert any("must pin" in e for e in rep.errors)


def test_a_scripted_subscription_over_state_transfer_pinned_conforms(
        minimal, write_card, subscription):
    subscription["then"]["run"] = "tools/detect.py"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = [{"id": "UP.STREAM", "ref": "v1.0.0"}]
    assert cards.lint(write_card(minimal)).errors == []


def test_a_drift_guard_over_a_reference_binding_must_not_pin(minimal, write_card, subscription):
    """YOU CANNOT PIN A DRIFT-GUARD. A check whose output IS the difference must read HEAD, or it
    compares a pin against itself and is tautologically green."""
    subscription["notice"]["binding"] = "repo-read"
    subscription["notice"]["position"] = "none"
    subscription["then"]["run"] = "tools/drift.py"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = [{"id": "UP.STREAM", "ref": "main"}]
    rep = cards.lint(write_card(minimal))
    assert rep.errors == []
    assert any("a pin would blind it" in n for n in rep.notes)


def test_a_scripted_subscription_whose_source_is_undeclared_fails(
        minimal, write_card, subscription):
    subscription["then"]["run"] = "tools/detect.py"
    minimal["subscriptions"] = [subscription]
    minimal["dependencies"] = []
    rep = cards.lint(write_card(minimal))
    assert any("is not in dependencies" in e for e in rep.errors)


# ── dependencies ──────────────────────────────────────────────────────────────────────────────

def test_external_is_retired(minimal, write_card):
    """Externality is DERIVED from the registry's card_status, never declared."""
    minimal["dependencies"] = [{"id": "papeete-hub/kpack", "ref": "main", "external": True}]
    rep = cards.lint(write_card(minimal))
    assert any("'external' is retired" in e for e in rep.errors)


def test_a_dependency_resolving_nowhere_in_the_registry_fails(minimal, write_card, registry):
    minimal["dependencies"] = [{"id": "NO.SUCH.ACTOR", "ref": "main"}]
    rep = cards.lint(write_card(minimal), registry=registry)
    assert any("resolves nowhere in registry.yaml" in e for e in rep.errors)


def test_an_external_dependency_is_noted_never_dangling(minimal, write_card, registry):
    minimal["dependencies"] = [{"id": "papeete-hub/kpack", "ref": "main"}]
    rep = cards.lint(write_card(minimal), registry=registry)
    assert rep.errors == []
    assert any("EXTERNAL" in n for n in rep.notes)


def test_an_actor_that_owes_a_card_is_dangling_not_external(minimal, write_card, registry):
    """`reliever-implementation` carries `papeete_actor: none` and its card is adopted; `settler`
    carries it and owes one. Keying on the id calls both external and silences the defect."""
    minimal["dependencies"] = [{"id": "example/owes-a-card", "ref": "main"}]
    rep = cards.lint(write_card(minimal), registry=registry)
    assert rep.errors == []
    assert any("ACTOR THAT OWES A CARD" in n for n in rep.notes)


def test_without_a_registry_dependency_resolution_is_skipped(minimal, write_card):
    """An isolated checkout has no registry — resolution is skipped, never failed."""
    minimal["dependencies"] = [{"id": "NO.SUCH.ACTOR", "ref": "main"}]
    assert cards.lint(write_card(minimal)).errors == []


# ── the deployment profile ────────────────────────────────────────────────────────────────────

def test_rail_is_the_deployments_not_the_contracts(minimal, write_card, offer, tmp_path):
    """ADR-PA-0016: `nature` is the contract's enum; which rails exist is a fact about ONE
    deployment. A card legal under the shipped profile is illegal under another."""
    offer["rail"] = "contract-deviation"
    minimal["offers"] = [offer]
    path = write_card(minimal)

    assert cards.lint(path).errors == []

    other = tmp_path / "other.yaml"
    other.write_text("profile: other\ncontract: deployment-profile/v0\nrails: [escalation]\n")
    rep = cards.lint(path, prof=profile.load(other))
    assert any("rail='contract-deviation'" in e for e in rep.errors)


def test_a_profile_declaring_no_rails_constrains_none(minimal, write_card, offer, tmp_path):
    """The honest position for a deployment that has not fixed its routing. The FIELD stays
    required; only its values go unconstrained."""
    offer["rail"] = "whatever-this-deployment-calls-it"
    minimal["offers"] = [offer]
    prof = tmp_path / "loose.yaml"
    prof.write_text("profile: loose\ncontract: deployment-profile/v0\n")
    rep = cards.lint(write_card(minimal), prof=profile.load(prof))
    assert rep.errors == []


def test_rail_stays_required_under_a_loose_profile(minimal, write_card, offer, tmp_path):
    del offer["rail"]
    minimal["offers"] = [offer]
    prof = tmp_path / "loose.yaml"
    prof.write_text("profile: loose\ncontract: deployment-profile/v0\n")
    rep = cards.lint(write_card(minimal), prof=profile.load(prof))
    assert any("missing required key 'rail'" in e for e in rep.errors)


# ── malformed input ───────────────────────────────────────────────────────────────────────────

def test_a_card_that_does_not_parse_reports_rather_than_raises(tmp_path):
    path = tmp_path / "papeete-actor.yaml"
    path.write_text("card: [unclosed\n")
    rep = cards.lint(path)
    assert any("does not parse" in e for e in rep.errors)


def test_a_card_that_is_not_a_mapping_reports_rather_than_raises(tmp_path):
    path = tmp_path / "papeete-actor.yaml"
    path.write_text("- a list\n- not a card\n")
    rep = cards.lint(path)
    assert any("not a mapping" in e for e in rep.errors)
