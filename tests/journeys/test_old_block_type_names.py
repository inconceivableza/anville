# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ The section link and comparison link block types became the section signpost and the comparison signpost
(ticket 75). A pathway version is never edited, so one stored under the old names keeps them in its row, and the engine
reads them as the new ones. A document being loaded may use only the new names."""

import json

import pytest
from django.core.management import CommandError
from django.db.models import TextField
from django.db.models.functions import Cast

from engine.document import content_hash
from engine.document.blocks import COMPARISON_STATUSES
from engine.models import PathwayVersion, Publication
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)
from tests.journeys.test_whatever_you_do import (
    people_answer,
    press_compare,
    reflection_stored,
    save_the_reflection,
    section_1,
    section_2,
    the_pathway,
    to_the_reflection,
)

OLD_NAMES = {"section_signpost": "section_link", "comparison_signpost": "comparison_link"}
VIEWED = COMPARISON_STATUSES["viewed"]


def under_the_old_names(document):
    """✨ The document as it was stored before the rename, each signpost under its old block type name."""
    for section in document["content"]["sections"]:
        for block in section["blocks"]:
            block["type"] = OLD_NAMES.get(block["type"], block["type"])
    return document


def old_name_paths(document):
    """✨ Where in the document each block under an old name sits, as the linter's paths name it."""
    return [
        f"/content/sections/{s}/blocks/{b}/type"
        for s, section in enumerate(document["content"]["sections"])
        for b, block in enumerate(section["blocks"])
        if block["type"] in OLD_NAMES.values()
    ]


def types_in(document):
    return {block["type"] for section in document["content"]["sections"] for block in section["blocks"]}


def store(document):
    """✨ Stored and published as a version loaded before the rename was, past the loader, which now refuses it."""
    version = PathwayVersion.objects.create(document=document, content_hash=content_hash(document))
    Publication.objects.create(version=version)
    return version


def stored_row():
    """✨ The document exactly as the database holds it, read as text so nothing on the way out changes it."""
    raw = PathwayVersion.objects.annotate(raw=Cast("document", TextField())).values_list("raw", flat=True).get()
    return json.loads(raw)


@pytest.fixture
def participant(signed_in_client):  # noqa: F811
    store(under_the_old_names(the_pathway()))
    return signed_in_client


@pytest.mark.django_db
def test_a_version_stored_under_the_old_names_reads_with_the_new_ones_and_its_row_is_never_rewritten():
    stored = under_the_old_names(the_pathway())
    store(stored)

    read = PathwayVersion.objects.get().document

    assert set(OLD_NAMES) <= types_in(read)
    assert not types_in(read) & set(OLD_NAMES.values())
    assert stored_row() == stored
    assert PathwayVersion.objects.get().content_hash == content_hash(stored)


@pytest.mark.django_db
def test_a_participant_on_a_version_stored_under_the_old_names_finds_both_signposts_as_before(participant):
    client = to_the_reflection(participant)

    assert "View my results →" in section_1(client)
    assert "0 of 3 answered" in section_2(client)  # ✨ the comparison signpost is Section 2's (ticket 87)
    assert VIEWED not in client.get("/hub/").content.decode()
    assert save_the_reflection(client).status_code == 403

    people_answer(client)
    assert press_compare(client).status_code == 303

    assert VIEWED in section_2(client)
    assert VIEWED in client.get("/hub/").content.decode()
    assert save_the_reflection(client).status_code < 400
    assert reflection_stored()


@pytest.mark.django_db
def test_loading_a_document_under_the_old_names_is_refused_at_each_block_that_uses_one(load_pathway):
    document = under_the_old_names(the_pathway())

    with pytest.raises(CommandError) as refused:
        load_pathway(document)

    assert old_name_paths(document)
    for path in old_name_paths(document):
        assert path in str(refused.value)
    assert not PathwayVersion.objects.exists()
