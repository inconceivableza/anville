# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

import pytest
from django.core.management import CommandError, call_command
from django.db import DatabaseError, transaction

from engine.document import content_hash
from engine.models import PathwayVersion
from tests.documents import pathway_document


@pytest.mark.django_db
def test_loading_a_document_creates_a_pathway_version_with_its_content_hash(load_pathway):
    document = pathway_document()

    output = load_pathway(document)

    [version] = PathwayVersion.objects.all()
    assert version.document == document
    assert version.content_hash == content_hash(document)
    assert f"Loaded pathway version {version.pk}" in output


@pytest.mark.django_db
def test_loading_the_same_content_again_creates_no_duplicate_even_when_the_file_is_reformatted(load_pathway):
    load_pathway(pathway_document())

    output = load_pathway(pathway_document(), indent=4)

    [version] = PathwayVersion.objects.all()
    assert f"already pathway version {version.pk}" in output


@pytest.mark.django_db
def test_an_invalid_document_is_refused_with_the_paths_of_its_problems_and_nothing_is_stored(load_pathway):
    document = pathway_document()
    document["content"]["sections"][1]["gate"]["clauses"][0]["block"] = "missing"

    with pytest.raises(CommandError) as refused:
        load_pathway(document)

    assert "/content/sections/1/gate/clauses/0/block: There is no block 'missing' in this pathway." in str(refused.value)
    assert not PathwayVersion.objects.exists()


@pytest.mark.django_db
def test_a_file_that_is_not_json_is_refused(tmp_path):
    path = tmp_path / "pathway.json"
    path.write_text("{ not json")

    with pytest.raises(CommandError, match="is not valid JSON"):
        call_command("load_pathway", str(path))

    assert not PathwayVersion.objects.exists()


@pytest.mark.django_db
def test_a_stored_pathway_version_cannot_be_modified_even_bypassing_the_application(load_pathway):
    document = pathway_document()
    load_pathway(document)
    version = PathwayVersion.objects.get()

    version.document["title"] = "Tampered"
    with pytest.raises(DatabaseError), transaction.atomic():
        version.save()
    with pytest.raises(DatabaseError), transaction.atomic():
        PathwayVersion.objects.update(document={"format": 1})

    assert PathwayVersion.objects.get().document == document


@pytest.mark.django_db
def test_a_stored_pathway_version_cannot_be_deleted_even_if_it_was_never_published():
    document = pathway_document()
    PathwayVersion.objects.create(document=document, content_hash=content_hash(document))

    with pytest.raises(DatabaseError), transaction.atomic():
        PathwayVersion.objects.all().delete()

    assert PathwayVersion.objects.count() == 1
