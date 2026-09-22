"""✨ The second validation pass: cross-references the JSON Schema cannot express.

Runs only on a document that has already passed the schema, so it relies on the document's shape.
"""

from engine.document.problem import Problem


def lint(document):
    identifiers = list(_identifiers(document))
    construct_ids = _ids_of("construct", identifiers)
    return [
        *_duplicates(identifiers),
        *_missing_sections(document, _ids_of("section", identifiers)),
        *_missing_blocks(document, _ids_of("block", identifiers)),
        *_missing_constructs(document, construct_ids),
        *_loads_per_framework(document, construct_ids),
    ]


def _identifiers(document):
    """Every identifier the document declares, as (kind, identifier, path)."""
    for s, section in enumerate(document["content"]["sections"]):
        yield "section", section["id"], f"/content/sections/{s}/id"
        for b, block in enumerate(section["blocks"]):
            yield "block", block["id"], f"/content/sections/{s}/blocks/{b}/id"
    instrument = document.get("instrument", {})
    for b, bucket in enumerate(instrument.get("buckets", [])):
        yield "bucket", bucket["id"], f"/instrument/buckets/{b}/id"
    for i, item in enumerate(instrument.get("items", [])):
        yield "item", item["id"], f"/instrument/items/{i}/id"
    for f, framework in enumerate(document.get("measurement", {}).get("frameworks", [])):
        yield "framework", framework["id"], f"/measurement/frameworks/{f}/id"
        for c, construct in enumerate(framework["constructs"]):
            yield "construct", construct["id"], f"/measurement/frameworks/{f}/constructs/{c}/id"


def _ids_of(kind, identifiers):
    return {identifier for k, identifier, _ in identifiers if k == kind}


def _duplicates(identifiers):
    first_use = {}
    for kind, identifier, path in identifiers:
        if (kind, identifier) in first_use:
            yield Problem(
                path,
                f"The {kind} identifier '{identifier}' is already used at {first_use[kind, identifier]}.",
            )
        else:
            first_use[kind, identifier] = path


def _missing_sections(document, section_ids):
    for s, section in enumerate(document["content"]["sections"]):
        for r, required in enumerate(section.get("requires", [])):
            if required not in section_ids:
                yield Problem(f"/content/sections/{s}/requires/{r}", f"There is no section '{required}' in this pathway.")


def _missing_blocks(document, block_ids):
    for s, section in enumerate(document["content"]["sections"]):
        for c, clause in enumerate(section.get("gate", {}).get("clauses", [])):
            if clause["block"] not in block_ids:
                yield Problem(
                    f"/content/sections/{s}/gate/clauses/{c}/block",
                    f"There is no block '{clause['block']}' in this pathway.",
                )


def _missing_constructs(document, construct_ids):
    for i, item in enumerate(document.get("instrument", {}).get("items", [])):
        for n, construct in enumerate(item["loads"]):
            if construct not in construct_ids:
                yield Problem(f"/instrument/items/{i}/loads/{n}", f"There is no construct '{construct}' in this pathway.")
    for c, description in enumerate(document.get("presentation", {}).get("constructs", [])):
        if description["construct"] not in construct_ids:
            yield Problem(
                f"/presentation/constructs/{c}/construct",
                f"There is no construct '{description['construct']}' in this pathway.",
            )


def _loads_per_framework(document, construct_ids):
    frameworks = document.get("measurement", {}).get("frameworks", [])
    for i, item in enumerate(document.get("instrument", {}).get("items", [])):
        if not set(item["loads"]) <= construct_ids:
            continue  # the unknown construct is the problem worth reporting, already done above
        for framework in frameworks:
            in_framework = {construct["id"] for construct in framework["constructs"]}
            count = sum(1 for construct in item["loads"] if construct in in_framework)
            if count != 1:
                found = "no construct" if count == 0 else f"{count} constructs"
                yield Problem(
                    f"/instrument/items/{i}/loads",
                    f"Item '{item['id']}' loads onto {found} in '{framework['id']}'; it must load onto exactly one.",
                )
