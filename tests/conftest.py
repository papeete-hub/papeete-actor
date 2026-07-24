"""Fixtures for the gate suite.

A CARD IS BUILT, NEVER PASTED. Every test that needs a card starts from `minimal` — the smallest
thing that conforms — and mutates exactly the field under test. A suite of hand-written YAML
blobs drifts from the schema the moment the schema moves, and then the tests assert the shape of
last year's contract while passing.
"""
from pathlib import Path

import pytest
import yaml


def _minimal() -> dict:
    """The smallest conformant papeete-actor-card/v1 card.

    Every section present and empty. `empty_is_legal: true` is stated on offers, releases and
    publications in the schema — an actor nobody addresses, that ships nothing and emits nothing,
    is a complete card (ADR-PA-0009 §3).
    """
    return {
        "card": "papeete-actor-card/v1",
        "papeete_actor": "none",
        "tier": "none",
        "name": "none",
        "repo": "example/thing",
        "strategic_class": "supporting",
        "pair": {"human": ["architect"], "agent": "none"},
        "mailbox": {
            "contract": "inter-agent-message/v0",
            "binding": "github-issue",
            "address": "example/thing/issues",
            "delivery": "at-least-once",
            "idempotency": ["type", "subject"],
            "push": False,
        },
        "offers": [],
        "releases": [],
        "publications": [],
        "subscriptions": [],
        "dependencies": [],
        "records": [{"what": "the store of record", "where": "src/"}],
        "gates": ["the input bookend"],
        "work_surface": "none",
        "autonomy": "level-0",
    }


@pytest.fixture
def minimal() -> dict:
    return _minimal()


@pytest.fixture
def write_card(tmp_path):
    """Write a card dict to a repo root and return its path."""

    def _write(card: dict, repo: str = "thing") -> Path:
        root = tmp_path / repo
        root.mkdir(parents=True, exist_ok=True)
        path = root / "papeete-actor.yaml"
        path.write_text(yaml.safe_dump(card, sort_keys=False))
        return path

    return _write


@pytest.fixture
def offer() -> dict:
    """One conformant offer. `rail` is a Papeete rail — the shipped reference profile's."""
    return {
        "id": "contract-deviation",
        "means": "the door for a shape that cannot express something true",
        "nature": "action",
        "rail": "contract-deviation",
        "completion": "a revision of the schema, or a refusal saying why the shape is right",
    }


@pytest.fixture
def publication() -> dict:
    return {
        "id": "the-contract",
        "means": "a version of the contract exists, and what moved in it",
        "shape": "none",
        "surface": "src/schemas/",
    }


@pytest.fixture
def release() -> dict:
    return {
        "id": "the-package",
        "means": "the gates and the contracts, as one pip-installable package",
        "versioning": "semver",
        "surface": "PyPI `the-package`",
        "announced_by": "the-contract",
    }


@pytest.fixture
def subscription() -> dict:
    return {
        "to": "UP.STREAM/their-publication",
        "notice": {"binding": "event-log", "cadence": "on demand", "position": "v1.0.0"},
        "then": {"outcome": "records", "intent": "I re-pin and re-run the join"},
    }


@pytest.fixture
def registry() -> dict:
    """A registry naming one adopted actor, one that owes a card, and one external artifact."""
    return {
        "repos": [
            {"repo": "example/upstream", "papeete_actor": "UP.STREAM",
             "card": "papeete-actor.yaml", "card_status": "adopted"},
            {"repo": "example/owes-a-card", "papeete_actor": "none",
             "card": "papeete-actor.yaml", "card_status": "none"},
            {"repo": "papeete-hub/kpack"},
        ]
    }


def errors_matching(rep, needle: str) -> list[str]:
    return [e for e in rep.errors if needle in e]
