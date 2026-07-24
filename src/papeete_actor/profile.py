"""Loading a deployment profile — the values a contract cannot know.

THE CONTRACTS DESCRIBE SHAPES; A PROFILE SUPPLIES THIS DEPLOYMENT'S VALUES. `inter-agent-message/v0`
says a finding carries a `rail` and a `scope`. It cannot say which rails exist, because that follows
from how many tiers a given factory has and which of them decide what; and it cannot say what an id
looks like, because that is the shape of somebody's domain taxonomy.

Both were hard-coded until ADR-PA-0016 — the rail enum in two schemas, and a `^BNK\\.` regex in one.
The consequence was not a wart. An organisation outside this ecosystem could not emit a CONFORMANT
MESSAGE AT ALL: `scope` is required, and no value without the literal `BNK.` prefix matched. A
governance contract that cannot be satisfied outside the domain it grew in is an internal one, which
is exactly what ADR-PA-0001 refused to ship.

THE SHIPPED PROFILE IS A REFERENCE, NOT A PRIVILEGE. `profiles/papeete.yaml` is the default so the
ecosystem this package grew in keeps working with no flag. It is one deployment's answer that
happens to live here, and `--profile` takes another.

A profile may under-constrain on purpose. Omit `scope_grammar` and scope is required but
unconstrained; omit `rails` and any rail is accepted. Both are the honest position for a deployment
that has not built a taxonomy or fixed its routing yet, and both keep the FIELD required — a finding
that names no owner is the noise floor WORK-OBSERVABILITY exists to prevent, whatever the ids look
like.
"""
from pathlib import Path

import yaml

_DIR = Path(__file__).resolve().parent / "profiles"
DEFAULT = "papeete"


def profiles_dir() -> Path:
    return _DIR


def default_path() -> Path:
    return _DIR / f"{DEFAULT}.yaml"


def load(path: Path | str | None = None) -> dict:
    """A profile by path, or the shipped reference profile when none is given."""
    p = Path(path) if path else default_path()
    if not p.exists():
        raise FileNotFoundError(
            f"{p}: no such deployment profile.\n"
            f"  A profile supplies the values the contracts cannot know — this deployment's rails "
            f"and the grammar of its taxonomy.\n"
            f"  Omit --profile to use the shipped reference profile at {default_path()}."
        )
    prof = yaml.safe_load(p.read_text())
    if not isinstance(prof, dict):
        raise ValueError(f"{p}: a profile must be a mapping")
    return prof


def rails(profile: dict) -> list | None:
    """The rails this deployment routes on, or None when it constrains them not at all."""
    return profile.get("rails") or None


def scope_grammar(profile: dict) -> str | None:
    """The id grammar of this deployment's taxonomy, or None when it has not fixed one."""
    return profile.get("scope_grammar") or None


# WHERE THE REGISTRY LIVES IS A DEPLOYMENT'S FACT TOO, and it was hard-coded for the same reason
# the rails were: the first deployment's layout was the only one anybody had. A consumer holding
# the published contracts could author a conformant registry and still not be found by the gates,
# because discovery looked in one organisation's directory and nowhere else (ADR-PA-0017).
DEFAULT_REGISTRY_LOCATIONS = ["ecosystem-governance/ecosystem/registry.yaml"]


def registry_locations(profile: dict) -> list[str]:
    """Where this deployment keeps its registry, relative to a workspace root.

    Falls back to the reference deployment's layout rather than to nothing, so a profile written
    before this key existed keeps resolving exactly as it did. That is a REFERENCE and not a
    privilege — the same standing `profiles/papeete.yaml` has among profiles.
    """
    declared = profile.get("registry") or {}
    locations = declared.get("locations") if isinstance(declared, dict) else None
    return [str(p) for p in locations] if locations else list(DEFAULT_REGISTRY_LOCATIONS)
