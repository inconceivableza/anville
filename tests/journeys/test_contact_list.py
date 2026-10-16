# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../../LICENSE.md

"""✨ A contact list: people who know the participant, a name and an email each, kept as records of their own.

The people are other than the participant, so they are stored as contacts (each with an observer's link, ticket 13)
rather than among the participant's answers. The gate still reads them as the block's answer, so a section can ask for
none or at least an authored number. Each person is added, with their link, or changed on their own, so saving one
never touches anyone else (ticket 51a).
"""

import re

import pytest
from django.test import Client

from engine.models import Contact, Invitation, Response
from tests.documents import pathway_document
from tests.journeys.pages import gate_checklist, version_on
from tests.journeys.test_answers import shown
from tests.journeys.test_hub import a_fresh_participant, signed_in_client  # noqa: F401  (fixtures, used by name)

ONBOARDING = "onboarding"
VOICES = "voices"
ADD_TWO = "Add at least two people, or leave the list empty to do this later."


def with_a_contact_list(**fields):
    """✨ The test pathway with a contact list at the foot of onboarding, whose gate asks for none or at least two."""
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"].append({"id": "contacts", "type": "contact_list", "needed": 2, "optional": 0, **fields})
    onboarding["gate"] = {
        "clauses": [
            {"type": "entry_count", "block": "contacts", "min": 2, "allow_none": True, "message": ADD_TWO},
        ]
    }
    return document


def with_trusted_voices(document=None, **fields):
    """✨ The test pathway with a side card after onboarding holding the contact list, three people needed and two
    more optional, as Five trusted voices is (ticket 51a), and complete once three of them have links (ticket 52)."""
    document = document or pathway_document()
    document["content"]["sections"].append(
        {
            "id": VOICES,
            "title": "Five trusted voices",
            "requires": ["onboarding"],
            "side_card": {"sentence": "Invite people who know you well."},
            "blocks": [{"id": "contacts", "type": "contact_list", "needed": 3, "optional": 2, **fields}],
            "gate": {
                "clauses": [{"type": "links_issued", "block": "contacts", "min": 3, "message": "Add three people."}]
            },
        }
    )
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_contact_list())
    return signed_in_client


@pytest.fixture
def voices(signed_in_client, load_pathway):  # noqa: F811
    """✨ A participant with Before we begin complete, on whose hub Five trusted voices is a side card."""
    load_pathway(with_trusted_voices())
    assert signed_in_client.post(f"/sections/{ONBOARDING}/complete/").status_code == 303
    return signed_in_client


def the_list(page):
    found = re.search(r'<div id="block-contacts".*?</ol>', page, re.S)
    assert found, "no contact list on this page"
    return found.group(0)


def forms_of(page):
    """✨ Each form of the list, as (where it posts, its fields as the page fills them)."""
    forms = []
    for action, form in re.findall(r'<form[^>]*\baction="([^"]+)"[^>]*>(.*?)</form>', the_list(page), re.S):
        fields = {}
        for tag in re.findall(r"<input[^>]*>", form):
            name = re.search(r'\bname="([^"]+)"', tag)
            if name:
                value = re.search(r'\bvalue="([^"]*)"', tag)
                fields[name.group(1)] = value.group(1) if value else ""
        forms.append((action, fields))
    return forms


def rows_shown(page):
    """✨ Each row of the contact list as the participant sees it, as (name, email)."""
    return [
        (fields["name"], fields["email"]) for _, fields in forms_of(page) if "name" in fields and "email" in fields
    ]


def add_person(client, person, section=ONBOARDING, page=None):
    """✨ Add one person as the participant does, in the list's first empty row, on the page given or as it is now."""
    action, fields = next(
        form for form in forms_of(page or shown(client, section)) if "name" in form[1] and not form[1]["name"]
    )
    name, email = person
    return client.post(action, {**fields, "name": name, "email": email})


def save_person(client, name, changed, section=ONBOARDING, page=None):
    """✨ Change the named person's row and save it, on the page given (one left open, say) or as it is now."""
    action, fields = next(form for form in forms_of(page or shown(client, section)) if form[1].get("name") == name)
    new_name, new_email = changed
    return client.post(action, {**fields, "name": new_name, "email": new_email})


def save_contacts(client, *rows, section=ONBOARDING):
    """✨ Add each person in turn, as the participant does, each with their link; an empty row is passed over."""
    added = None
    for row in rows:
        if row != BLANK:
            added = add_person(client, row, section)
    return added


def take_off_the_list(name):
    """✨ Delete a contact as taking them off the list does. The page's way to do it is ticket 13d's."""
    Contact.objects.filter(name=name).delete()


def stored():
    return [(contact.name, contact.email) for contact in Contact.objects.order_by("position")]


JO, PRIYA, CHRIS = ("Jo", "jo@example.com"), ("Priya", "priya@example.com"), ("Chris", "chris@example.com")
BLANK = ("", "")


def link_shown(page):
    found = re.search(r"http://testserver(/observe/[A-Za-z0-9_-]+/)", page)
    return found.group(1) if found else None


# What the participant sees


@pytest.mark.django_db
def test_the_list_opens_with_as_many_empty_rows_as_the_author_asks_for(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_contact_list(needed=3, optional=2))

    assert rows_shown(shown(signed_in_client, ONBOARDING)) == [BLANK] * 5


@pytest.mark.django_db
def test_without_authored_numbers_the_list_opens_with_five_rows(signed_in_client, load_pathway):  # noqa: F811
    document = with_a_contact_list()
    for field in ("needed", "optional"):
        del document["content"]["sections"][0]["blocks"][-1][field]
    load_pathway(document)

    assert rows_shown(shown(signed_in_client, ONBOARDING)) == [BLANK] * 5


@pytest.mark.django_db
def test_each_row_asks_for_a_first_name_and_an_email_address_as_the_prototype_does(participant):
    page = shown(participant, ONBOARDING)

    assert re.search(r'<input[^>]*type="text"[^>]*name="name"[^>]*placeholder="First name"', page)
    assert re.search(r'<input[^>]*type="email"[^>]*name="email"[^>]*placeholder="Email address"', page)


@pytest.mark.django_db
def test_once_every_row_is_filled_one_more_is_offered(participant):
    save_contacts(participant, JO, PRIYA)

    assert rows_shown(shown(participant, ONBOARDING)) == [JO, PRIYA, BLANK]


# Adding and saving


@pytest.mark.django_db
def test_people_are_kept_as_contacts_in_the_order_added_apart_from_the_participants_answers(participant):
    save_contacts(participant, JO, PRIYA)

    assert stored() == [JO, PRIYA]
    response = Response.objects.get()
    assert "contacts" not in response.answers
    assert {(contact.response, contact.block_id, contact.role) for contact in Contact.objects.all()} == {
        (response, "contacts", Contact.Role.CONTACT)
    }


@pytest.mark.django_db
def test_adding_a_person_makes_their_link_in_the_same_act_and_shows_it_to_copy(participant):
    added = add_person(participant, JO)

    assert added.status_code == 303
    page = participant.get(added.url).content.decode()
    link = link_shown(page)
    assert link
    assert Client().get(link).status_code == 200
    assert not Contact.objects.filter(invitation__isnull=True).exists()


@pytest.mark.django_db
def test_nobody_is_listed_without_having_had_a_link(participant):
    save_contacts(participant, JO, PRIYA, CHRIS)

    assert Invitation.objects.count() == Contact.objects.count() == 3


@pytest.mark.django_db
def test_space_around_each_entry_is_trimmed(participant):
    add_person(participant, ("  Jo ", " jo@example.com  "))

    assert stored() == [JO]


@pytest.mark.django_db
def test_saved_contacts_survive_a_reload(participant):
    save_contacts(participant, JO, PRIYA, CHRIS)

    assert rows_shown(shown(participant, ONBOARDING)) == [JO, PRIYA, CHRIS, BLANK]


@pytest.mark.django_db
def test_saving_one_person_leaves_everyone_else_unchanged_even_from_a_page_left_open(participant):
    """✨ Ticket 13a's bug: a page open since before someone was added saved its whole list, which dropped them."""
    add_person(participant, JO)
    left_open = shown(participant, ONBOARDING)
    priyas_link = link_shown(participant.get(add_person(participant, PRIYA).url).content.decode())

    saved = save_person(participant, "Jo", ("Joanne", "joanne@example.com"), page=left_open)

    assert saved.status_code == 303
    assert stored() == [("Joanne", "joanne@example.com"), PRIYA]
    assert Client().get(priyas_link).status_code == 200


@pytest.mark.django_db
def test_changing_a_persons_details_keeps_their_link_working(participant):
    jos_link = link_shown(participant.get(add_person(participant, JO).url).content.decode())

    save_person(participant, "Jo", ("Joanne", "joanne@example.com"))

    assert stored() == [("Joanne", "joanne@example.com")]
    assert Client().get(jos_link).status_code == 200


@pytest.mark.django_db
def test_another_participants_contact_cannot_be_changed(participant):
    add_person(participant, JO)
    left_open = shown(participant, ONBOARDING)

    someone_else = a_fresh_participant(participant, "someone@example.com")

    assert save_person(someone_else, "Jo", PRIYA, page=left_open).status_code == 404
    assert stored() == [JO]


# Refusals


@pytest.mark.django_db
@pytest.mark.parametrize("person", [("Priya", ""), ("", "priya@example.com")])
def test_a_person_needs_a_name_and_an_email_address(participant, person):
    refused = add_person(participant, person)

    assert refused.status_code == 400
    assert "Add both a name and an email address." in refused.content.decode()
    assert stored() == []


@pytest.mark.django_db
@pytest.mark.parametrize("changed", [("Jo", ""), ("", "jo@example.com")])
def test_a_person_saved_without_a_name_or_an_email_address_is_refused_and_unchanged(participant, changed):
    add_person(participant, JO)

    refused = save_person(participant, "Jo", changed)

    assert refused.status_code == 400
    assert "Add both a name and an email address." in refused.content.decode()
    assert stored() == [JO]


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["priya@", "priya", "priya@example", "priya example.com", "@example.com"])
def test_an_email_address_that_is_not_one_is_refused(participant, email):
    """✨ Checked as Django checks an email field, not the prototype's "has an @ past the first character"."""
    refused = add_person(participant, ("Priya", email))

    assert refused.status_code == 400
    assert "Check the email address." in refused.content.decode()
    assert stored() == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "person, refusal",
    [
        (("P" * 151, "priya@example.com"), "The name is too long."),
        (("Priya", "p" * 243 + "@example.com"), "Check the email address."),
    ],
)
def test_a_name_or_email_too_long_to_keep_is_refused(participant, person, refusal):
    refused = add_person(participant, person)

    assert refused.status_code == 400
    assert refusal in refused.content.decode()
    assert stored() == []


@pytest.mark.django_db
@pytest.mark.parametrize("person, at_fault", [(("Priya", "priya@"), "email"), (("", "priya@example.com"), "name")])
def test_a_refusal_comes_back_as_typed_with_the_field_at_fault_marked(participant, person, at_fault):
    refused = add_person(participant, person).content.decode()

    assert ("Priya" if person[0] else "", person[1]) in rows_shown(refused)
    assert re.search(rf'<input[^>]*name="{at_fault}"[^>]*aria-invalid="true"', refused)


@pytest.mark.django_db
def test_the_browser_leaves_checking_the_email_addresses_to_the_server(participant):
    """✨ With its own check on, the browser stops an address without an "@" before it is sent, so the server's
    refusal, which says what is wrong, is never seen."""
    add_person(participant, JO)
    forms = re.findall(r'<form class="contact-person"[^>]*>', the_list(shown(participant, ONBOARDING)))

    assert forms and all(re.search(r"\snovalidate[\s>]", form) for form in forms)


@pytest.mark.django_db
def test_a_fifty_first_person_is_refused(participant):
    add_person(participant, JO)
    fifty = [{"name": f"Person {number}", "email": f"person{number}@example.com"} for number in range(50)]
    Response.objects.get().replace_contacts("contacts", fifty, Contact.Role.CONTACT)  # ✨ quicker than 50 requests

    refused = participant.post("/contacts/contacts/", {"name": "Priya", "email": "priya@example.com"})

    assert refused.status_code == 400
    assert "Add no more than 50 people." in refused.content.decode()
    assert Contact.objects.count() == 50


# The gate and progress


@pytest.mark.django_db
def test_the_section_can_be_completed_with_no_contacts_at_all(participant):
    assert participant.post(f"/sections/{ONBOARDING}/complete/").status_code == 303


@pytest.mark.django_db
def test_once_anyone_is_added_the_authored_number_is_needed_to_complete(participant):
    add_person(participant, JO)

    refused = participant.post(f"/sections/{ONBOARDING}/complete/")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {ADD_TWO: False}
    add_person(participant, PRIYA)
    assert participant.post(f"/sections/{ONBOARDING}/complete/").status_code == 303


@pytest.mark.django_db
def test_a_contact_list_in_a_locked_section_refuses_anyone_added(signed_in_client, load_pathway):  # noqa: F811
    document = with_a_contact_list()
    onboarding, calling = document["content"]["sections"]
    calling["blocks"].append(onboarding["blocks"].pop())
    del onboarding["gate"]
    load_pathway(document)

    refused = signed_in_client.post(
        "/contacts/contacts/",
        {"name": "Jo", "email": "jo@example.com", "version": version_on(shown(signed_in_client, ONBOARDING))},
    )

    assert refused.status_code == 403
    assert stored() == []


# Five trusted voices, a side card of its own


@pytest.mark.django_db
def test_people_can_be_added_and_changed_once_before_we_begin_is_complete(voices):
    add_person(voices, JO, VOICES)
    save_person(voices, "Jo", ("Joanne", "joanne@example.com"), VOICES)
    add_person(voices, PRIYA, VOICES)

    assert stored() == [("Joanne", "joanne@example.com"), PRIYA]


@pytest.mark.django_db
def test_the_old_invitations_address_is_the_lists_own_page(voices):
    went = voices.get("/invitations/")

    assert went.status_code == 302
    assert went.url == f"/sections/{VOICES}/#block-contacts"
