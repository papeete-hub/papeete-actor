"""The deployment profile — the values a contract cannot know (ADR-PA-0016).

THE CLAIM UNDER TEST is the one that justified the breaking change: an organisation outside this
ecosystem could not emit a conformant message AT ALL, because `scope` is required and no value
without the literal `BNK.` prefix matched. If that is fixed, a foreign deployment's own profile
must carry its own cards and messages — and the shipped profile must stay a reference rather than
become a privilege.
"""
import pytest

from papeete_actor import profile


def test_the_shipped_profile_is_the_default():
    prof = profile.load()
    assert prof["profile"] == "papeete-banking"
    assert prof["contract"] == "deployment-profile/v0"


def test_the_shipped_profile_ships_in_the_package():
    """It is ordinary committed source beside the schemas — a build reaches nothing outside its
    own checkout, and this is what proves it arrived."""
    assert profile.default_path().exists()
    assert profile.profiles_dir().is_dir()


def test_the_papeete_profile_declares_three_rails():
    """Three, because this deployment's factory has three tiers that decide things. The CONTRACT
    requires a rail; it never counted them."""
    assert profile.rails(profile.load()) == [
        "functional-gap", "contract-deviation", "engineering-debt"]


def test_a_missing_profile_raises_with_instructions(tmp_path):
    """A user-fixable misconfiguration, not a crash. The message must name the default."""
    with pytest.raises(FileNotFoundError) as exc:
        profile.load(tmp_path / "nope.yaml")
    assert "no such deployment profile" in str(exc.value)
    assert str(profile.default_path()) in str(exc.value)


def test_a_profile_that_is_not_a_mapping_is_refused(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("- not\n- a mapping\n")
    with pytest.raises(ValueError):
        profile.load(path)


def test_a_profile_may_under_constrain_on_purpose(tmp_path):
    """Omit `rails` and any rail is accepted; omit `scope_grammar` and scope is required but
    unconstrained. Both are the honest position for a deployment that has not built a taxonomy."""
    path = tmp_path / "loose.yaml"
    path.write_text("profile: loose\ncontract: deployment-profile/v0\n")
    prof = profile.load(path)
    assert profile.rails(prof) is None
    assert profile.scope_grammar(prof) is None


def test_an_empty_rails_list_constrains_nothing_rather_than_everything(tmp_path):
    """`rails: []` must not mean "no rail is legal" — that would make every card unsatisfiable."""
    path = tmp_path / "empty.yaml"
    path.write_text("profile: empty\ncontract: deployment-profile/v0\nrails: []\n")
    assert profile.rails(profile.load(path)) is None


def test_another_deployment_supplies_its_own_rails(tmp_path):
    path = tmp_path / "other.yaml"
    path.write_text("profile: other\ncontract: deployment-profile/v0\n"
                    "rails: [escalation, remediation]\nscope_grammar: '^ACME\\.[A-Z]+$'\n")
    prof = profile.load(path)
    assert profile.rails(prof) == ["escalation", "remediation"]
    assert profile.scope_grammar(prof) == r"^ACME\.[A-Z]+$"


@pytest.mark.parametrize("scope,ok", [
    ("BNK.RLVR", True),                       # context
    ("BNK.RLVR.CAP.BSP", True),               # zone
    ("BNK.RLVR.CAP.BSP.001", True),           # L1
    ("BNK.RLVR.CAP.BSP.001.ENV", True),       # L2
    ("ACME.THING", False),                    # another org's taxonomy
    ("BNK", False),
    ("bnk.rlvr", False),
])
def test_the_papeete_scope_grammar_is_its_grain_ladder(scope, ok):
    import re
    grammar = profile.scope_grammar(profile.load())
    assert bool(re.match(grammar, scope)) is ok
