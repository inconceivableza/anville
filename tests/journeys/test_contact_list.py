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


def another_row_form(page):
    """✨ The list's "Add another person" (ticket 70), as (where it posts, its fields), or None while it is not offered."""
    found = re.search(r'<form(?=[^>]*class="contact-more")[^>]*\baction="([^"]+)"[^>]*>(.*?)</form>', page, re.S)
    if not found:
        return None
    return found.group(1), dict(re.findall(r'<input[^>]*\bname="([^"]+)"[^>]*\bvalue="([^"]*)"', found.group(2)))


def add_another_row(client, section=ONBOARDING, page=None, htmx=False):
    """✨ Press "Add another person" on the page given or as it is now; `htmx` as the page's JavaScript sends it."""
    action, fields = another_row_form(page or shown(client, section))
    return client.post(action, fields, **(HTMX if htmx else {}))


def add_person(client, person, section=ONBOARDING, page=None, htmx=False):
    """✨ Add one person as the participant does, in the list's first empty row, on the page given or as it is now,
    first pressing "Add another person" if every row is filled; `htmx` as the page's JavaScript sends it."""
    page = page or shown(client, section)
    if not any("name" in fields and not fields["name"] for _, fields in forms_of(page)):
        page = client.get(add_another_row(client, section, page).url).content.decode()
    action, fields = next(form for form in forms_of(page) if "name" in form[1] and not form[1]["name"])
    name, email = person
    return client.post(action, {**fields, "name": name, "email": email}, **(HTMX if htmx else {}))


def save_person(client, name, changed, section=ONBOARDING, page=None, htmx=False):
    """✨ Change the named person's row and save it, on the page given (one left open, say) or as it is now; `htmx` as
    the row's autosave sends it."""
    action, fields = next(form for form in forms_of(page or shown(client, section)) if form[1].get("name") == name)
    new_name, new_email = changed
    return client.post(action, {**fields, "name": new_name, "email": new_email}, **(HTMX if htmx else {}))


# ✨ What htmx adds to every request it sends.
HTMX = {"HTTP_HX_REQUEST": "true"}


def save_contacts(client, *rows, section=ONBOARDING):
    """✨ Add each person in turn, as the participant does, each with their link; an empty row is passed over."""
    added = None
    for row in rows:
        if row != BLANK:
            added = add_person(client, row, section)
    return added


def action_in_row(client, name, pattern, section=ONBOARDING):
    """✨ Where a button in the named person's row posts, on the list's page as it is now."""
    rows = re.findall(r'<li class="contact-row".*?</li>', shown(client, section), re.S)
    row = next(row for row in rows if f'value="{name}"' in row)
    found = re.search(rf'action="({pattern})"', row)
    assert found, f"no {pattern} for {name} on the contact list's page"
    return found.group(1)


def removal_action(client, name, section=ONBOARDING):
    """✨ Where the named person's Remove button posts."""
    return action_in_row(client, name, r"/contacts/[\w-]+/\d+/remove/", section)


def confirmation_of(page):
    """✨ The form that confirms a removal on the page given, as (where it posts, its fields), or None if it asks
    nothing."""
    for action, form in re.findall(r'<form[^>]*\baction="([^"]+/remove/)"[^>]*>(.*?)</form>', page, re.S):
        fields = dict(re.findall(r'<input[^>]*\bname="([^"]+)"[^>]*\bvalue="([^"]*)"', form))
        if "confirmed" in fields:
            return action, fields
    return None


def take_off_the_list(client, name, section=ONBOARDING):
    """✨ Take the named person off the list as the participant does: press their Remove button, then, if the page asks
    first, confirm. Returns the last response."""
    pressed = client.post(removal_action(client, name, section))
    asked = confirmation_of(pressed.content.decode()) if pressed.status_code == 200 else None
    if asked is None:
        return pressed
    action, fields = asked
    return client.post(action, fields)


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
def test_once_every_row_is_filled_no_more_appear_until_another_is_asked_for(participant):
    """✨ "Add another person" is always offered below the rows instead (ticket 70)."""
    save_contacts(participant, JO, PRIYA)
    page = shown(participant, ONBOARDING)

    assert rows_shown(page) == [JO, PRIYA]
    assert another_row_form(page)


# More than the rows ask for (ticket 70)


@pytest.mark.django_db
def test_without_javascript_add_another_person_adds_one_empty_row_keeping_everyone_in_theirs(participant):
    save_contacts(participant, JO, PRIYA)

    added = add_another_row(participant)

    assert added.status_code == 303
    assert rows_shown(participant.get(added.url).content.decode()) == [JO, PRIYA, BLANK]
    assert stored() == [JO, PRIYA]


@pytest.mark.django_db
def test_with_javascript_add_another_person_sends_back_one_empty_row_to_go_after_the_others(participant):
    save_contacts(participant, JO, PRIYA)
    page = shown(participant, ONBOARDING)
    form = re.search(r'<form[^>]*class="contact-more"[^>]*>', page).group()
    rows_list = re.search(r'<ol[^>]*class="contact-rows"[^>]*>', page).group()

    sent = add_another_row(participant, page=page, htmx=True)

    assert sent.status_code == 200
    assert rows_sent_back(sent) == [None]
    assert 'hx-swap="beforeend"' in form
    assert re.search(r'hx-target="#([\w-]+)"', form).group(1) == re.search(r'id="([\w-]+)"', rows_list).group(1)
    assert stored() == [JO, PRIYA]


@pytest.mark.django_db
def test_at_the_most_a_list_holds_another_row_is_not_offered_and_one_asked_for_is_refused(participant):
    add_person(participant, JO)
    left_open = shown(participant, ONBOARDING)
    fifty = [{"name": f"Person {number}", "email": f"person{number}@example.com"} for number in range(50)]
    Response.objects.get().replace_contacts("contacts", fifty, Contact.Role.CONTACT)  # ✨ quicker than 50 requests

    assert another_row_form(shown(participant, ONBOARDING)) is None
    refused = add_another_row(participant, page=left_open)

    assert refused.status_code == 400
    assert "Add no more than 50 people." in refused.content.decode()
    assert Contact.objects.count() == 50


@pytest.mark.django_db
@pytest.mark.parametrize("htmx", [False, True])
def test_a_row_added_with_add_another_person_stores_nobody_until_its_get_link(participant, htmx):
    save_contacts(participant, JO, PRIYA)

    added = add_another_row(participant, htmx=htmx)
    page = added.content.decode() if htmx else participant.get(added.url).content.decode()
    row = re.findall(r'<li class="contact-row".*?</li>', page, re.S)[-1]

    assert stored() == [JO, PRIYA]
    assert "hx-trigger" not in row
    assert re.search(r"<button[^>]*>\s*Get link\s*</button>", row)
    action = re.search(r'<form[^>]*\baction="([^"]+)"', row).group(1)
    fields = dict(re.findall(r'<input[^>]*\bname="([^"]+)"[^>]*\bvalue="([^"]*)"', row))
    assert participant.post(action, {**fields, "name": CHRIS[0], "email": CHRIS[1]}).status_code == 303
    assert stored() == [JO, PRIYA, CHRIS]


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

    assert rows_shown(shown(participant, ONBOARDING)) == [JO, PRIYA, CHRIS]


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


# Saving as it changes, a row at a time (fix-2)


def row_of(page, name):
    """✨ The named person's row on a page."""
    rows = re.findall(r'<li class="contact-row".*?</li>', page, re.S)
    return next(row for row in rows if f'value="{name}"' in row)


def rows_sent_back(response):
    """✨ The rows a response holds, by who is in them (None for an empty row), asserting it holds nothing else."""
    body = response.content.decode()
    assert "<html" not in body and 'id="block-contacts"' not in body, "the whole page came back, not a row"
    rows = re.findall(r'<li class="contact-row".*?</li>', body, re.S)
    assert body.count("<li") == len(rows)
    return [re.search(r'name="name"[^>]*value="([^"]*)"', row).group(1) or None for row in rows]


@pytest.mark.django_db
def test_a_change_to_someone_listed_is_saved_as_it_changes_with_no_save_button_to_press(participant):
    add_person(participant, JO)
    row = row_of(shown(participant, ONBOARDING), "Jo")

    assert re.search(r'<form class="contact-person"[^>]*hx-trigger="input delay:\d+ms, change\b', row)
    assert all("save-fallback" in button for button in re.findall(r"<button[^>]*>\s*Save\s*</button>", row))
    saved = save_person(participant, "Jo", ("Joanne", "joanne@example.com"), htmx=True)

    assert saved.status_code == 200
    assert stored() == [("Joanne", "joanne@example.com")]


@pytest.mark.django_db
def test_an_invalid_email_is_refused_in_that_row_alone_and_changes_nothing(participant):
    save_contacts(participant, JO, PRIYA)

    refused = save_person(participant, "Jo", ("Jo", "jo@"), htmx=True)

    assert refused.status_code == 400
    assert "Check the email address." in refused.content.decode()
    assert rows_sent_back(refused) == ["Jo"]
    assert stored() == [JO, PRIYA]


@pytest.mark.django_db
def test_a_new_row_stores_nobody_until_get_link_is_pressed(participant):
    page = shown(participant, ONBOARDING)
    empty = re.findall(r'<li class="contact-row".*?</li>', page, re.S)[0]

    assert "hx-trigger" not in empty
    assert re.search(r"<button[^>]*>\s*Get link\s*</button>", empty)
    assert stored() == []
    assert add_person(participant, JO, page=page, htmx=True).status_code == 200
    assert stored() == [JO]


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["save", "get link", "reissue", "revoke", "remove"])
def test_each_action_with_javascript_sends_back_its_own_row_alone(participant, action):
    """✨ So typing not yet saved in any other row is never lost (fix-2)."""
    save_contacts(participant, JO, PRIYA)

    if action == "save":
        sent = save_person(participant, "Jo", ("Joanne", "jo@example.com"), htmx=True)
        assert rows_sent_back(sent) == ["Joanne"]
    elif action == "get link":
        sent = add_person(participant, CHRIS, htmx=True)
        assert rows_sent_back(sent) == ["Chris"]  # ✨ in a row "Add another person" added (ticket 70)
        assert link_shown(sent.content.decode())
    elif action in ("reissue", "revoke"):
        path = r"/invitations/\d+/issue/" if action == "reissue" else r"/invitations/\d+/revoke/"
        sent = participant.post(action_in_row(participant, "Jo", path), **HTMX)
        assert rows_sent_back(sent) == ["Jo"]
    else:
        asked = participant.post(removal_action(participant, "Jo"), **HTMX)
        assert rows_sent_back(asked) == ["Jo"]
        assert stored() == [JO, PRIYA]
        action_to_confirm, fields = confirmation_of(asked.content.decode())
        sent = participant.post(action_to_confirm, fields, **HTMX)
        assert stored() == [PRIYA]
        assert rows_sent_back(sent) in ([], [None])
    assert sent.status_code == 200


# Taking someone off the list (ticket 13d)


@pytest.mark.django_db
def test_removing_a_person_deletes_them_and_their_link_which_is_then_refused_as_a_dead_one(participant):
    jos_link = link_shown(participant.get(add_person(participant, JO).url).content.decode())
    add_person(participant, PRIYA)

    removed = take_off_the_list(participant, "Jo")

    assert removed.status_code == 303
    assert stored() == [PRIYA]
    assert Invitation.objects.count() == 1
    assert Client().get(jos_link).status_code == 404


@pytest.mark.django_db
def test_removing_someone_whose_link_is_live_asks_first(participant):
    add_person(participant, JO)

    pressed = participant.post(removal_action(participant, "Jo"))

    assert pressed.status_code == 200
    assert confirmation_of(pressed.content.decode())
    assert stored() == [JO]


@pytest.mark.django_db
def test_someone_whose_link_no_longer_works_is_removed_without_asking(participant):
    add_person(participant, JO)
    participant.post(action_in_row(participant, "Jo", r"/invitations/\d+/revoke/"))

    pressed = participant.post(removal_action(participant, "Jo"))

    assert pressed.status_code == 303
    assert stored() == []


@pytest.mark.django_db
def test_opening_the_removal_address_removes_nobody(participant):
    add_person(participant, JO)
    action = removal_action(participant, "Jo")

    participant.get(action)
    participant.get(action, {"confirmed": "yes"})

    assert stored() == [JO]
    assert Invitation.objects.count() == 1


@pytest.mark.django_db
def test_another_participants_contact_cannot_be_removed(participant):
    add_person(participant, JO)
    action = removal_action(participant, "Jo")

    someone_else = a_fresh_participant(participant, "someone@example.com")

    assert someone_else.post(action, {"confirmed": "yes"}).status_code == 404
    assert stored() == [JO]
    assert Invitation.objects.count() == 1


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
