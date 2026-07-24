"""papeete-actor check — the cross-card join. ECO.GOV's standing nonconformity, closed.

Everything here needs EVERY card at once, which is exactly why none of it lives in the per-card
gate. Walk the registry, read each papeete-actor.yaml, and join publications against subscriptions and
dependencies:

    dangling-subscription       nobody publishes that id
    unsubscribed-publication    information no one pulls — dead output, or a missing consumer
    unschematised-publication   a publication with records and no shape
    unpinned-scripted-sub       a then.run over a state-transfer binding on a floating ref
    undeclared-consumption      NOT COMPUTED — by construction. The evidence is in consumer code,
                                not in cards. Detection is a heuristic plus the honesty rule, and
                                a heuristic finding is a prompt to declare, never a verdict.

The join is only as true as the cards are. Six of seven were v0 when this was written, and a v0
card cannot express `dependencies` at all — so the report says how much of the ecosystem it
actually covered rather than implying it covered all of it.
"""
from pathlib import Path

import yaml

from .cards import CONTRACT, FLOATING, registry_classes, resolve_source
from .report import Report
from .schemas import load


def _load(path: Path):
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        return None


def _actor_id(card: dict) -> str | None:
    """The ecosystem-layer id. ONE KEY: `papeete_actor:` (ADR-PA-0013, ADR-PA-0015).

    `actor:` IS NOT READ AS A FALLBACK, and its removal is not a deletion. From the rename until
    2026-07-23 both keys were read, because the join ran over a mixed ecosystem: six cards were
    still at actor-card/v0 and only their own pairs could migrate them. All six did, so the
    tolerance now describes nothing — and a tolerance kept past its occasion is how a transitional
    shape becomes the permanent one.

    IT IS REPLACED BY A LOUD FAILURE, NOT BY SILENCE, because silence here is the worse bug. A card
    whose id does not resolve is not skipped: it still joins under its REPO NAME, so its
    publications index as `banking-tech/X` while every consumer writes `BNK.TECH/X`. The join then
    reports a DANGLING-SUBSCRIPTION against each one — a confident, precise, wrong answer, which is
    exactly what this tool exists to prevent. So `run` REFUSES a card carrying the retired key
    rather than quietly resolving it to None.
    """
    return card.get("papeete_actor")


def run(workspace: Path, registry_path: Path) -> Report:
    """workspace: the directory holding the sibling repos. registry_path: ecosystem/registry.yaml."""
    rep = Report()
    reg = _load(registry_path)
    if not reg:
        rep.errors.append(f"{registry_path}: missing or unparseable — the join has no index to walk")
        return rep

    schema = load("papeete-actor-card")
    classes = registry_classes(reg)

    cards: dict[str, dict] = {}     # repo dir name -> card
    unmigrated: list[str] = []
    for entry in reg.get("repos", []):
        repo = entry.get("repo") or ""
        if not repo or "<" in repo or not entry.get("card"):
            continue
        org, name = repo.split("/", 1) if "/" in repo else ("", repo)
        # THE ECOSYSTEM SPANS TWO ORGS, so a flat sibling layout is not enough. `--workspace` may
        # point at one org's directory (repos are siblings) or at the parent holding both (repos
        # are under <org>/). Try both, and the parent's parent, so the same command works from
        # either. Before ADR-ECO-0019 no papeete-hub repo held a card and only the flat shape was
        # ever exercised.
        candidates = [workspace / name, workspace / org / name, workspace.parent / org / name]
        path = next((c / entry["card"] for c in candidates if (c / entry["card"]).exists()), None)
        if path is None:
            if entry.get("card_status") != "none":
                rep.notes.append(
                    f"{repo}: card_status '{entry.get('card_status')}' but no card found "
                    f"(looked in {', '.join(str(c) for c in candidates)})"
                )
            continue
        card = _load(path)
        if not isinstance(card, dict):
            rep.errors.append(f"{path}: does not parse")
            continue
        # THE RETIRED KEY IS A HARD ERROR, not a fallback (ADR-PA-0015). See `_actor_id`: resolving
        # it to None instead would leave the card in the join under its repo name and turn every
        # `<id>/<publication>` subscription against it into a false DANGLING-SUBSCRIPTION.
        if "actor" in card:
            rep.errors.append(
                f"{path}: declares the retired key `actor:` — renamed `papeete_actor:` by "
                f"ADR-PA-0013. The transitional fallback that read both was removed once every "
                f"card had migrated (ADR-PA-0015). Rename the key; until then this card's id "
                f"cannot be resolved and the join would report false dangling subscriptions."
            )
            continue
        cards[name] = card
        if card.get("card") != CONTRACT:
            unmigrated.append(name)

    if not cards:
        rep.errors.append(f"{workspace}: no cards found — the sibling repos are not checked out here")
        return rep

    # ── the index of what is published, keyed as consumers write it ──────
    published: dict[str, str] = {}
    for name, card in cards.items():
        actor = _actor_id(card)
        for pub in (card.get("publications") or []):
            for key in {actor, name}:
                if key and key != "none":
                    published[f"{key}/{pub['id']}"] = name

    # ── dangling subscriptions ───────────────────────────────────────────
    subscribed: set[str] = set()
    for name, card in cards.items():
        for sub in (card.get("subscriptions") or []):
            to = str(sub.get("to", ""))
            if to in published:
                subscribed.add(to)
                continue
            source = resolve_source(to, classes)
            kind = classes.get(source)
            if kind == "external":
                rep.notes.append(f"{name}: '{to}' is EXTERNAL — outside the actor set, never dangling")
            elif "/" not in to:
                rep.notes.append(f"{name}: subscription '{to}' names no publication id — not joinable")
            else:
                rep.warns.append(
                    f"DANGLING-SUBSCRIPTION  {name} -> '{to}'"
                    + (f" (source '{source}' owes a card)" if kind == "dangling" else "")
                )

    # ── unsubscribed publications ────────────────────────────────────────
    for key, owner in sorted(published.items()):
        # A publication is reachable under either of its two keys; only report the pair once.
        actor = _actor_id(cards[owner])
        aliases = {f"{k}/{key.split('/', 1)[1]}" for k in {actor, owner} if k and k != "none"}
        if aliases & subscribed:
            continue
        if key.startswith(f"{owner}/") and actor and actor != "none":
            continue                                   # report under the actor id, not twice
        rep.warns.append(f"UNSUBSCRIBED-PUBLICATION  {key}  (owner: {owner})")

    # ── the two v1 classes, per card ─────────────────────────────────────
    for name, card in cards.items():
        if card.get("card") != CONTRACT:
            continue
        root = workspace / name
        refs = {str(d.get("id")): str(d.get("ref")) for d in (card.get("dependencies") or [])}
        for pub in (card.get("publications") or []):
            log = root / "events" / str(pub.get("id", ""))
            records = [p for p in log.glob("*.yaml") if p.name != "schema.yaml"] if log.is_dir() else []
            if records and pub.get("shape") in (None, "none"):
                rep.warns.append(f"UNSCHEMATISED-PUBLICATION  {name}/{pub['id']}  ({len(records)} records)")
        reference = schema["the_pin_rule"]["bindings"]["reference"]
        for sub in (card.get("subscriptions") or []):
            then, notice = sub.get("then") or {}, sub.get("notice") or {}
            if "run" not in then or notice.get("binding") in reference:
                continue
            source = resolve_source(sub.get("to", ""), refs)
            if refs.get(source, "none") in FLOATING:
                rep.warns.append(f"UNPINNED-SCRIPTED-SUBSCRIPTION  {name} -> '{sub.get('to')}'")

    covered = len(cards) - len(unmigrated)
    distinct = sum(len(c.get("publications") or []) for c in cards.values())
    rep.oks.append(
        f"joined {len(cards)} card(s): {distinct} publications, {covered} at {CONTRACT}"
    )
    if unmigrated:
        rep.notes.append(
            f"{len(unmigrated)} card(s) still at v0 ({', '.join(sorted(unmigrated))}) — they cannot "
            f"express `dependencies`, so the two v1 classes were not computed for them"
        )
    rep.notes.append(
        "undeclared-consumption is NOT computed — the evidence is in consumer code, not in cards"
    )
    return rep
