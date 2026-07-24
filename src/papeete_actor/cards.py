"""The papeete-actor-card/v1 gate — one card against the contract.

WHAT THIS IS NOT. It does not run the cross-card join (papeete_actor.check). The classes that need every
card at once — dangling subscription, unsubscribed publication, undeclared consumption — are not
decidable from one file. This validates the half a schema can carry.

A v0 CARD IS UNMIGRATED, NOT NON-CONFORMANT. ECO.GOV cannot place a card in another repo; adoption
and migration are each pair's own act, so a v0 card warns and does not fail.
"""
from pathlib import Path

import yaml

from . import profile
from . import registry as _registry
from .report import Report
from .schemas import load

CONTRACT = "papeete-actor-card/v1"
FLOATING = {"main", "master", "HEAD", "none", "None"}


def registry_classes(reg: dict) -> dict[str, str]:
    """Map every id the registry knows to `actor` | `dangling` | `external`.

    KEPT AS THE NAME CONSUMERS ALREADY IMPORT; the rule itself now lives in `registry.classes`,
    which reads `classification` out of ecosystem-registry/v0 instead of restating it. It was
    stated here in Python and nowhere in a contract — so a consumer could satisfy every published
    shape and still not know how its own registry would be read (ADR-PA-0017).

    The rule is unchanged, and it is worth keeping its reason next to the name: it is KEYED ON
    card_status, NOT on `papeete_actor:`. reliever-implementation carries `papeete_actor: none`
    (no BNK.* context id) and yet its card is adopted; settler carries `papeete_actor: none` and
    ADR-PA-0009 §1 ruled it an actor that owes one. Keying on the id calls both external and
    silences the very defect the class exists to surface.
    """
    return _registry.classes(reg)


def resolve_source(to: str, known) -> str:
    """The source id a subscription's `to` names.

    THREE shapes share one field, and the separator is ambiguous in all of them because a source id
    may itself contain a slash:

        BNK.KNOW/meta-model                     <actor>/<publication>      -> BNK.KNOW
        papeete-hub/kpack                       a whole artifact, no publication id
                                                                           -> papeete-hub/kpack
        papeete-hub/papeete-actor/<publication> <repo-path>/<publication>  -> papeete-hub/papeete-actor

    So: take the LONGEST prefix that is a known id, and fall back to the first segment when none is.

    Naively splitting on the first slash breaks the second and third shapes — it yields the org,
    which resolves to nothing. That reported papeete-hub/kpack as a dangling subscription in both
    repos holding it, when ADR-ECO-0014 §2 exists precisely so it is reported as external. The
    third shape appeared when ECO.GOV began consuming a contract from a repo-path source
    (ADR-ECO-0019) and this function reported `papeete-hub` as an undeclared dependency.
    """
    to = str(to)
    parts = to.split("/")
    for cut in range(len(parts), 0, -1):
        candidate = "/".join(parts[:cut])
        if candidate in known:
            return candidate
    return parts[0]


def _require(d: dict, keys, where: str, rep: Report) -> None:
    for k in keys:
        if k not in d:
            rep.errors.append(f"{where}: missing required key '{k}'")


def _unknown(d: dict, spec: dict, where: str, rep: Report) -> None:
    """Keys the schema does not name. A NOTE, never an error.

    v0 enumerated nothing, so authors invented — `authority`, `caveat` and `outbox` appear across
    three cards, each expressing something `status`/`surface`/`means` already covers. Honest
    content in an ad-hoc field is how a shape stops being a shape. Reporting rather than rejecting
    keeps a card able to say a true thing it has no slot for; the note is the prompt to fold it in,
    or to widen the contract on purpose.
    """
    allowed = set(spec.get("required", [])) | set(spec.get("optional", []))
    for k in sorted(set(d) - allowed):
        rep.notes.append(f"{where}: '{k}' is not named by the schema — fold it in, or widen the contract")


def lint(path: Path | str, schema: dict | None = None, registry: dict | None = None,
         prof: dict | None = None) -> Report:
    """One card against papeete-actor-card/v1.

    `path` IS COERCED, and every parameter after it stays optional. This is the one function in
    the package another package imports — papeete-actor-simple calls `lint(path)` positionally
    and merges the Report into its own, because the card contract is consumed there and never
    re-authored (ADR-PAS-0004). `profile.load` already took `Path | str`; this taking only `Path`
    was an asymmetry between two loaders a consumer reaches the same way.
    """
    path = Path(path)
    schema = schema or load("papeete-actor-card")
    prof = profile.load() if prof is None else prof
    rep = Report()

    try:
        card = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        rep.errors.append(f"{path}: does not parse: {e}")
        return rep
    if not isinstance(card, dict):
        rep.errors.append(f"{path}: not a mapping")
        return rep

    if card.get("card") != CONTRACT:
        rep.warns.append(f"{path}: declares '{card.get('card')}' — UNMIGRATED, not checked against {CONTRACT}")
        return rep

    # The retired sections. Half a migration is worse than none: a reader cannot tell which half
    # is authoritative.
    for gone, why in (("requests", "renamed 'offers'"), ("requests_out", "removed — routing lives in §6")):
        if gone in card:
            rep.errors.append(f"{path}: '{gone}' survives a v1 card — {why}")

    _require(card, schema["identity"]["required"], str(path), rep)
    _require(card, schema["remainder"]["required"], str(path), rep)

    # ── offers ───────────────────────────────────────────────────────────
    if card.get("offers") is None:
        rep.errors.append(f"{path}: missing 'offers' (use [] — an actor nobody addresses is conformant)")
    for i, off in enumerate(card.get("offers") or []):
        where = f"{path}: offers[{i}] '{off.get('id', '?')}'"
        _require(off, schema["offers"]["required"], where, rep)
        _unknown(off, schema["offers"], where, rep)
        # `nature` is the contract's; `rail` is the deployment's (ADR-PA-0016). A profile that
        # declares no rails leaves the field required and its values unconstrained.
        enums = dict(schema["offers"]["enums"])
        rails = profile.rails(prof)
        if rails:
            enums["rail"] = rails
        for fld, allowed in enums.items():
            if fld in off and off[fld] not in allowed:
                rep.errors.append(f"{where}: {fld}='{off[fld]}' not in {allowed}")

    # ── publications ─────────────────────────────────────────────────────
    if card.get("publications") is None:
        rep.errors.append(f"{path}: missing 'publications' (use [] — ADR-ECO-0014 §3)")
    for i, pub in enumerate(card.get("publications") or []):
        where = f"{path}: publications[{i}] '{pub.get('id', '?')}'"
        _require(pub, schema["publications"]["required"], where, rep)
        _unknown(pub, schema["publications"], where, rep)
        if "what" in pub:
            rep.errors.append(f"{where}: 'what' is renamed 'means' in v1")
        shape = pub.get("shape")
        if shape and shape != "none":
            if not (path.parent / shape).exists():
                rep.errors.append(f"{where}: shape '{shape}' does not resolve")
        elif shape == "none":
            # The obligation binds at FIRST RECORD, not at declaration — a schema for a fact never
            # emitted could only be imagined. So `shape: none` is legal only while the log is empty.
            log = path.parent / "events" / str(pub.get("id", ""))
            records = [p for p in log.glob("*.yaml") if p.name != "schema.yaml"] if log.is_dir() else []
            if records:
                rep.errors.append(
                    f"{where}: shape: none but {len(records)} record(s) exist — the obligation "
                    f"binds at first record (publication/v2 `binds_at`)"
                )
            else:
                rep.notes.append(f"{where}: shape: none — log empty, obligation binds at first record")

    # ── releases ─────────────────────────────────────────────────────────
    # THE STATE HALF of what an actor produces. A release is versioned and actionable; a
    # publication is a point in time. The stream fields — `at`, `supersedes`, `backfilled` — mean
    # nothing applied to an artefact, which is why the two are separate sections rather than one
    # with a flag.
    if card.get("releases") is None:
        rep.errors.append(f"{path}: missing 'releases' (use [] — an actor may ship no artefacts, ADR-PA-0009 §3)")
    pub_ids = {p.get("id") for p in (card.get("publications") or []) if isinstance(p, dict)}
    for i, rel in enumerate(card.get("releases") or []):
        where = f"{path}: releases[{i}] '{rel.get('id', '?')}'"
        _require(rel, schema["releases"]["required"], where, rep)
        _unknown(rel, schema["releases"], where, rep)
        # CUTTING THE RELEASE IS EMITTING THE FACT. The announcing publication is this actor's own,
        # never someone else's — so the join is intra-card and decidable here rather than in check.
        announced = rel.get("announced_by")
        if announced is not None and announced not in pub_ids:
            rep.errors.append(
                f"{where}: announced_by '{announced}' is not a publication on this card — an "
                f"artefact that ships with no fact is invisible to every consumer that pins it "
                f"(papeete-actor-card/v1 `conformance.unannounced_release`)"
            )

    # ── dependencies ─────────────────────────────────────────────────────
    if card.get("dependencies") is None:
        rep.errors.append(f"{path}: missing 'dependencies'")
    dep_refs: dict[str, str] = {}
    classes = registry_classes(registry) if registry else {}
    for i, dep in enumerate(card.get("dependencies") or []):
        where = f"{path}: dependencies[{i}] '{dep.get('id', '?')}'"
        _require(dep, schema["dependencies"]["required"], where, rep)
        _unknown(dep, schema["dependencies"], where, rep)
        if "external" in dep:
            rep.errors.append(f"{where}: 'external' is retired — externality derives from the registry")
        if dep.get("id"):
            dep_refs[str(dep["id"])] = str(dep.get("ref"))
            if classes:
                kind = classes.get(str(dep["id"]))
                if kind is None:
                    rep.errors.append(f"{where}: resolves nowhere in registry.yaml")
                elif kind == "external":
                    rep.notes.append(f"{where}: EXTERNAL — outside the actor set, never dangling")
                elif kind == "dangling":
                    rep.notes.append(f"{where}: an ACTOR THAT OWES A CARD (card_status: none) — dangling, not external")

    # ── subscriptions ────────────────────────────────────────────────────
    if card.get("subscriptions") is None:
        rep.errors.append(f"{path}: missing 'subscriptions'")
    sub_spec = schema["subscriptions"]
    pin_rule = schema["the_pin_rule"]
    for i, sub in enumerate(card.get("subscriptions") or []):
        where = f"{path}: subscriptions[{i}] '{sub.get('to', '?')}'"
        _require(sub, sub_spec["required"], where, rep)
        _unknown(sub, sub_spec, where, rep)
        if "how" in sub:
            rep.errors.append(f"{where}: 'how' is replaced by 'notice:' + 'then:' in v1")
        if "pin" in sub:
            rep.errors.append(f"{where}: 'pin' moves to dependencies[].ref in v1")

        notice = sub.get("notice") or {}
        if notice:
            _require(notice, sub_spec["notice"]["required"], f"{where}.notice", rep)

        then = sub.get("then") or {}
        if not then:
            continue
        _require(then, sub_spec["then"]["required"], f"{where}.then", rep)
        if not any(k in then for k in sub_spec["then"]["at_least_one_of"]):
            rep.errors.append(
                f"{where}.then: needs at least one of {sub_spec['then']['at_least_one_of']} — "
                f"a subscription that reacts to nothing is undeclared consumption wearing a declaration"
            )
        allowed = sub_spec["then"]["enums"]["outcome"]
        if then.get("outcome") is not None and then["outcome"] not in allowed:
            rep.errors.append(f"{where}.then: outcome='{then['outcome']}' not in {allowed}")

        # THE PIN RULE. A scripted consumer that BUILDS ON upstream content breaks silently on
        # drift. One that OBSERVES the difference must not pin: a drift-guard comparing a pin
        # against itself is tautologically green — the identity-vs-freshness bug two cards in this
        # ecosystem already report against themselves.
        if "run" in then:
            binding = notice.get("binding")
            if binding in pin_rule["bindings"]["reference"]:
                rep.notes.append(f"{where}.then: run: over reference binding '{binding}' — exempt; a pin would blind it")
            else:
                source = resolve_source(sub.get("to", ""), dep_refs)
                ref = dep_refs.get(source)
                if ref is None:
                    rep.errors.append(f"{where}.then: declares run: but '{source}' is not in dependencies")
                elif ref in FLOATING:
                    rep.errors.append(
                        f"{where}.then: run: over state-transfer binding '{binding}' against floating "
                        f"ref '{ref}' — must pin (papeete-actor-card/v1 `the_pin_rule`)"
                    )

    if not rep.errors:
        rep.oks.append(f"{path} conforms to {CONTRACT}")
    return rep
