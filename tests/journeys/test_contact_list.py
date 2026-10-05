"""✨ A contact list: people who know the participant, a name and an email per row, kept as records of their own.

The rows are people other than the participant, so they are stored as contacts (which later become observers'
invitations, ticket 13) rather than among the participant's answers. The gate still reads them as the block's
answer, so a section can ask for none or at least an authored number.
"""

import re

import pytest

from engine.models import Contact, Response
from tests.documents import pathway_document
from tests.journeys.pages import gate_checklist, version_on
from tests.journeys.test_answers import shown
from tests.journeys.test_hub import signed_in_client  # noqa: F401  (a fixture, used by name)

ONBOARDING = "onboarding"
ADD_TWO = "Add at least two people, or leave the list empty to do this later."


def with_a_contact_list(**fields):
    """✨ The test pathway with a contact list at the foot of onboarding, whose gate asks for none or at least two."""
    document = pathway_document()
    onboarding = document["content"]["sections"][0]
    onboarding["blocks"].append({"id": "contacts", "type": "contact_list", "min_rows": 2, **fields})
    onboarding["gate"] = {
        "clauses": [
            {"type": "entry_count", "block": "contacts", "min": 2, "allow_none": True, "message": ADD_TWO},
        ]
    }
    return document


@pytest.fixture
def participant(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_contact_list())
    return signed_in_client


def rows_shown(page):
    """✨ Each row of the contact list as the participant sees it, as (name, email)."""
    form = re.search(r'<form id="block-contacts".*?</form>', page, re.S).group(0)

    def values(field):
        inputs = re.findall(rf'<input[^>]*\bname="{field}"[^>]*>', form)
        return [re.search(r'value="([^"]*)"', tag).group(1) if 'value="' in tag else "" for tag in inputs]

    return list(zip(values("name"), values("email"), strict=True))


def save_contacts(client, *rows, **extra):
    """✨ Save the whole list as the browser does, one name and one email per row, in order."""
    form = {
        "name": [name for name, _ in rows],
        "email": [email for _, email in rows],
        "version": version_on(shown(client, ONBOARDING)),
        **extra,
    }
    return client.post("/answers/contacts/", form, HTTP_HX_REQUEST="true")


def stored():
    return [(contact.name, contact.email) for contact in Contact.objects.order_by("position")]


JO, PRIYA, CHRIS = ("Jo", "jo@example.com"), ("Priya", "priya@example.com"), ("Chris", "chris@example.com")
BLANK = ("", "")


# What the participant sees


@pytest.mark.django_db
def test_the_list_opens_with_as_many_empty_rows_as_the_author_asks_for(participant):
    assert rows_shown(shown(participant, ONBOARDING)) == [BLANK, BLANK]


@pytest.mark.django_db
def test_without_an_authored_number_the_list_opens_with_five_rows(signed_in_client, load_pathway):  # noqa: F811
    document = with_a_contact_list()
    del document["content"]["sections"][0]["blocks"][-1]["min_rows"]
    load_pathway(document)

    assert rows_shown(shown(signed_in_client, ONBOARDING)) == [BLANK] * 5


@pytest.mark.django_db
def test_each_row_asks_for_a_first_name_and_an_email_address_as_the_prototype_does(participant):
    page = shown(participant, ONBOARDING)

    assert re.search(r'<input[^>]*type="text"[^>]*name="name"[^>]*placeholder="First name"', page)
    assert re.search(r'<input[^>]*type="email"[^>]*name="email"[^>]*placeholder="Email address"', page)
    assert "+ Add another person" in page


# Saving


@pytest.mark.django_db
def test_the_list_is_saved_as_contacts_in_the_order_written_and_acknowledged(participant):
    saved = save_contacts(participant, JO, PRIYA)

    assert saved.status_code == 200
    assert "Saved" in saved.content.decode()
    assert stored() == [JO, PRIYA]
    assert {contact.role for contact in Contact.objects.all()} == {Contact.Role.CONTACT}


@pytest.mark.django_db
def test_contacts_are_kept_apart_from_the_participants_answers(participant):
    save_contacts(participant, JO, PRIYA)

    response = Response.objects.get()
    assert "contacts" not in response.answers
    assert {contact.response for contact in Contact.objects.all()} == {response}
    assert {contact.block_id for contact in Contact.objects.all()} == {"contacts"}


@pytest.mark.django_db
def test_empty_rows_are_left_out_and_space_around_each_entry_is_trimmed(participant):
    save_contacts(participant, BLANK, ("  Jo ", " jo@example.com  "), ("   ", "  "), PRIYA)

    assert stored() == [JO, PRIYA]


@pytest.mark.django_db
def test_saving_again_replaces_the_list_so_a_person_taken_off_it_is_not_kept(participant):
    save_contacts(participant, JO, PRIYA, CHRIS)

    save_contacts(participant, JO, BLANK, CHRIS)

    assert stored() == [JO, CHRIS]


@pytest.mark.django_db
def test_emptying_every_row_keeps_no_contacts(participant):
    save_contacts(participant, JO, PRIYA)

    assert save_contacts(participant, BLANK, BLANK).status_code == 200
    assert stored() == []


@pytest.mark.django_db
def test_saved_contacts_survive_a_reload(participant):
    save_contacts(participant, JO, PRIYA, CHRIS)

    assert rows_shown(shown(participant, ONBOARDING)) == [JO, PRIYA, CHRIS]


@pytest.mark.django_db
def test_fewer_contacts_than_the_authored_number_are_shown_above_empty_rows(signed_in_client, load_pathway):  # noqa: F811
    load_pathway(with_a_contact_list(min_rows=4))
    save_contacts(signed_in_client, JO)

    assert rows_shown(shown(signed_in_client, ONBOARDING)) == [JO, BLANK, BLANK, BLANK]


# Refusals


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["priya@", "priya", "priya@example", "priya example.com", "@example.com"])
def test_an_email_address_that_is_not_one_is_refused_naming_its_row_and_nothing_changes(participant, email):
    """✨ Checked as Django checks an email field, not the prototype's "has an @ past the first character"."""
    save_contacts(participant, JO)

    refused = save_contacts(participant, JO, ("Priya", email))

    assert refused.status_code == 400
    assert "Check the email address in row 2." in refused.content.decode()
    assert stored() == [JO]


@pytest.mark.django_db
@pytest.mark.parametrize("row", [("Priya", ""), ("", "priya@example.com")])
def test_a_row_with_only_a_name_or_only_an_email_is_refused_naming_its_row(participant, row):
    refused = save_contacts(participant, JO, BLANK, row)

    assert refused.status_code == 400
    assert "Add both a name and an email address in row 3." in refused.content.decode()
    assert stored() == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row, refusal",
    [
        (("P" * 151, "priya@example.com"), "The name in row 1 is too long."),
        (("Priya", "p" * 243 + "@example.com"), "Check the email address in row 1."),
    ],
)
def test_a_name_or_email_too_long_to_keep_is_refused_naming_its_row(participant, row, refusal):
    refused = save_contacts(participant, row)

    assert refused.status_code == 400
    assert refusal in refused.content.decode()
    assert stored() == []


def marked_invalid(refused):
    """✨ The row and field a refusal says is at fault, which main.js marks in the list, or None."""
    marked = re.search(r'data-invalid-row="(\d+)" data-invalid-field="(\w+)"', refused.content.decode())
    return (int(marked.group(1)), marked.group(2)) if marked else None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rows, at_fault",
    [
        ((JO, ("Priya", "priya")), (2, "email")),
        ((JO, BLANK, ("Chris", "")), (3, "email")),
        ((("", "jo@example.com"),), (1, "name")),
        ((("J" * 151, "jo@example.com"),), (1, "name")),
    ],
)
def test_a_refusal_says_which_field_is_at_fault_so_the_page_can_mark_it(participant, rows, at_fault):
    assert marked_invalid(save_contacts(participant, *rows)) == at_fault


@pytest.mark.django_db
def test_a_refusal_about_the_whole_list_marks_no_field(participant):
    people = [(f"Person {number}", f"person{number}@example.com") for number in range(51)]

    assert marked_invalid(save_contacts(participant, *people)) is None


@pytest.mark.django_db
def test_the_browser_leaves_checking_the_email_addresses_to_the_server(participant):
    """✨ With its own check on, the browser stops an address without an "@" before htmx sends it, silently, so
    the participant is never told which row is wrong. The server's refusal names the row instead."""
    page = shown(participant, ONBOARDING)

    assert re.search(r'<form id="block-contacts"[^>]*\snovalidate[\s>]', page)


@pytest.mark.django_db
def test_a_list_of_more_than_fifty_people_is_refused(participant):
    people = [(f"Person {number}", f"person{number}@example.com") for number in range(51)]

    refused = save_contacts(participant, *people)

    assert refused.status_code == 400
    assert "Add no more than 50 people." in refused.content.decode()
    assert stored() == []


# Adding another row


@pytest.mark.django_db
def test_add_another_without_javascript_saves_the_list_and_comes_back_with_one_more_row(participant):
    """✨ With JavaScript the row is added in the page. Without it, the button submits the form with one more
    row asked for, and the page comes back showing it."""
    added = participant.post(
        "/answers/contacts/",
        {"name": ["Jo", "Priya"], "email": ["jo@example.com", "priya@example.com"], "rows": "3",
         "version": version_on(shown(participant, ONBOARDING))},
    )

    assert added.status_code == 303
    assert added.url == "/sections/onboarding/?rows=3#block-contacts"
    assert stored() == [JO, PRIYA]
    assert rows_shown(participant.get(added.url).content.decode()) == [JO, PRIYA, BLANK]


@pytest.mark.django_db
def test_rows_asked_for_in_the_address_are_capped_at_fifty(participant):
    assert len(rows_shown(participant.get("/sections/onboarding/?rows=1000").content.decode())) == 50


# The gate and progress


@pytest.mark.django_db
def test_the_section_can_be_completed_with_no_contacts_at_all(participant):
    assert participant.post(f"/sections/{ONBOARDING}/complete/").status_code == 303


@pytest.mark.django_db
def test_once_anyone_is_added_the_authored_number_is_needed_to_complete(participant):
    save_contacts(participant, JO)

    refused = participant.post(f"/sections/{ONBOARDING}/complete/")

    assert refused.status_code == 400
    assert gate_checklist(refused.content.decode()) == {ADD_TWO: False}
    save_contacts(participant, JO, PRIYA)
    assert participant.post(f"/sections/{ONBOARDING}/complete/").status_code == 303


@pytest.mark.django_db
def test_the_gate_keeps_up_with_each_save(participant):
    saved = save_contacts(participant, JO)

    assert gate_checklist(saved.content.decode()) == {ADD_TWO: False}
    assert gate_checklist(save_contacts(participant, JO, PRIYA).content.decode()) == {ADD_TWO: True}


@pytest.mark.django_db
def test_a_contact_list_counts_towards_progress_once_anyone_is_on_it(participant):
    assert "0 of 3 answered" in participant.get("/hub/").content.decode()  # ✨ the test pathway's two, and this

    save_contacts(participant, JO)

    assert "1 of 3 answered" in participant.get("/hub/").content.decode()


@pytest.mark.django_db
def test_a_contact_list_in_a_locked_section_refuses_the_list(signed_in_client, load_pathway):  # noqa: F811
    document = with_a_contact_list()
    onboarding, calling = document["content"]["sections"]
    calling["blocks"].append(onboarding["blocks"].pop())
    del onboarding["gate"]
    load_pathway(document)

    refused = signed_in_client.post(
        "/answers/contacts/",
        {"name": ["Jo"], "email": ["jo@example.com"], "version": version_on(shown(signed_in_client, ONBOARDING))},
        HTTP_HX_REQUEST="true",
    )

    assert refused.status_code == 403
    assert stored() == []
