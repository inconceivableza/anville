# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

"""✨ Demo shortcuts (ticket 113), offered only on a development or demo system (`tools_on`), for showing the app without
walking every step by hand: the hub's hidden control, which completes what a chosen section needs to open
(`open_section`), and the made-up address the homepage and the sign-up page suggest (`example_address`). An observer's
sort starts from a demo profile through `scenario_loading.observer_sort`.

The control makes up only what a real participant would have, through the models' own steps, so every rule and lock
still applies and it never makes a state the app can't reach: the participant's sort, as the `just-leading` demo
profile, with its pairs answered; a coach, "Alex (demo)", who accepts through their own link; and people, "Demo voice 1"
to "3", with no email address, so no reminder can go, who claim their links and send observer versions of demo profiles.
Text a section's own gate needs is "(demo answer)", and a rating the middle of the scale. Everything it makes up is
marked as test data, as `seed_tie_break`'s is. It never makes up consent, age or a wizard's answers (Before we begin),
which the hub can't be reached without. On a participant who has started it only adds what is missing: no answer,
observer or coach is changed or removed, and nothing goes backwards.
"""

import json
import random

from django.conf import settings
from django.db import transaction

from engine import scenario_loading
from engine.document import AnswerRefused, answer_from_form
from engine.document.blocks import BLOCK_TYPES, SCALE_POINT, SCALE_POINTS, TEXT, blocks_of
from engine.document.contacts import MAX_CONTACTS
from engine.document.gates import (
    clause_passes,
    clauses_of,
    has_content,
    links_issued_key,
    opened_key,
    unmet,
    waits_on_comparison,
)
from engine.document.observers import link_lifetime, minimum_observers
from engine.document.scoring import score
from engine.document.tie_break import reweigh
from engine.hub import (
    block_ids_fixed_on_completion,
    complete_sections,
    finish_waits,
    is_locked,
    section_by_id,
    track_sections,
)
from engine.models import CollectionFrozen, Contact, Invitation, ObserverResponse, Response, Result
from engine.tie_break_scenarios import DoesNotFit, ScenarioDoesNotHold, seeding

# ✨ The participant's made-up sort, a demo profile and how its pairs are answered: one gift just leading, kept on top.
PARTICIPANT_PROFILE = ("just-leading", "leader")
COACH = {"name": "Alex (demo)", "email": ""}
# ✨ Each made-up person's name, numbered from 1, and the demo profile each sends the observer version of, in turn.
VOICE = "Demo voice {number}"
VOICE_PROFILES = ("flat", "tied-both", "tied-apest")
DEMO_ANSWER = "(demo answer)"
MIDDLE_OF_THE_SCALE = SCALE_POINTS[(len(SCALE_POINTS) - 1) // 2]

# ✨ First names from varied backgrounds, one of which a made-up address begins with.
EXAMPLE_NAMES = (
    "amara", "bilal", "chen", "dmitri", "esther", "farah", "giovanni", "hana", "ifeoma", "jamal",
    "kiri", "lucia", "mateo", "nadia", "olu", "rhys", "siobhan", "tomasz", "yuki", "zainab",
)  # fmt: skip


def tools_on():
    """✨ Whether this is a development or demo system, where tools that write made-up data or take back a participant's
    answers are offered: DEBUG on, or a demo notice set, as for `seed_tie_break` (fix-15). A production deployment has
    neither."""
    return bool(settings.DEBUG or settings.ANVILLE_DEMO_NOTICE)


def example_address():
    """✨ A made-up address to sign up to a demo with, at the reserved example.com, which no mail is sent to: one of
    `EXAMPLE_NAMES` and two digits from 10 to 99, chosen afresh each time."""
    return f"{random.choice(EXAMPLE_NAMES)}{random.randint(10, 99)}@example.com"


def offered(document, hub):
    """✨ The sections the hub's control offers to open, as the participant's `hub` lists them: each not yet open,
    leaving out the side cards, which open with Before we begin. None on a pathway the participant's made-up sort does
    not hold on, as the demo profiles are made for Whatever You Do."""
    locked = [entry.section for entry in hub.outline() if entry.section.is_locked]
    if not locked or scenario_loading.prefill(document, *PARTICIPANT_PROFILE) is None:
        return []
    return locked


class CannotMakeUp(Exception):
    """✨ Something a section needs that the control can't make up: it isn't one of the things it makes up, or making it
    would change what the participant already has."""


def open_section(response, section_id):
    """✨ Complete what the section `section_id` needs to open, and only that, on the participant's `response`: each
    section it requires, with what that needs first, then its own opening conditions, and the response marked as test
    data. Together or not at all: CannotMakeUp, keeping nothing, where something can't be made up."""
    with transaction.atomic():
        shortcut = _Shortcut(response)
        section = section_by_id(shortcut.document, section_id)
        shortcut.open(section)
        if shortcut.is_locked(section):
            raise CannotMakeUp(f"{section_id} is still locked.")
        Response.objects.filter(pk=response.pk).update(is_test_data=True)


class _Shortcut:
    """✨ One press of the control: the participant's response and its pathway, and each link made during it, by
    contact, so the person it was made for answers through it, since only its hash is kept."""

    def __init__(self, response):
        self.response = response
        self.document = response.version.document
        self.sections = track_sections(self.document)
        self.tokens = {}

    def progress(self):
        """✨ The answers the gate reads and the sections complete, read afresh after each step, as the hub reads
        them."""
        self.response.refresh_from_db()
        answers = self.response.answers_with_contacts_and_visits()
        return answers, complete_sections(self.sections, answers, self.response.completed_sections)

    def is_locked(self, section):
        answers, completed = self.progress()
        return is_locked(section, completed, answers, self.sections, self.response.moved_past_by_section())

    def open(self, section):
        """✨ Each section `section` requires complete, then each of its opening conditions that fails made to pass,
        unless it has opened before."""
        for required in section.get("requires", []):
            self.complete(section_by_id(self.document, required))
        if has_content(self.progress()[0].get(opened_key(section["id"]))):
            return
        for clause in section.get("opens_when", {}).get("clauses", []):
            if not clause_passes(clause, self.progress()[0]):
                self.make(clause)

    def complete(self, section):
        """✨ `section` complete: opened, the clauses of its gate and its parts' made to pass, the look given to any
        block of it waiting on the comparison, then finished, as the participant's press does. A part or a hub side
        card, with no finish of its own, is complete once its gate passes. Never a wizard, such as Before we begin."""
        if section["id"] in self.progress()[1]:
            return
        if section.get("wizard"):
            raise CannotMakeUp(f"{section['id']} is a wizard, whose answers are never made up.")
        self.open(section)
        parts = [other for other in self.sections if other.get("part_of") == section["id"]]
        for each in (section, *parts):
            for clause in clauses_of(each):
                if not clause_passes(clause, self.progress()[0]):
                    self.make(clause)
        for block in section["blocks"]:
            if waits_on_comparison(block, self.progress()[0]):
                self.look(block["after_comparison"]["sort"])
        answers, completed = self.progress()
        if self.is_locked(section) or unmet(section, answers) or finish_waits(section, self.sections, completed):
            raise CannotMakeUp(f"{section['id']} can't be finished.")
        if "part_of" not in section and "side_card" not in section:
            self.response.complete_section(section["id"], block_ids_fixed_on_completion(section, answers))

    def make(self, clause):
        """✨ One failing clause of a gate or an opening condition made to pass, by what a participant would have done
        or been sent."""
        block = next(block for block in blocks_of(self.document) if block["id"] == clause["block"])
        if clause["type"] in ("has_answer", "min_text_length"):
            self.answer(block)
        elif clause["type"] == "links_issued" and block["type"] == "coach_checklist":
            self.coach_link(block)
        elif clause["type"] == "links_issued":
            for _ in range(clause["min"] - (self.progress()[0].get(links_issued_key(block["id"])) or 0)):
                self.voice(block)
        elif clause["type"] == "coach_accepted":
            self.coach_accepts(block)
        elif clause["type"] == "observers_answered":
            self.people_answer(block)
        else:
            raise CannotMakeUp(f"A {clause['type']} clause isn't made up.")

    def answer(self, block):
        """✨ An answer to `block`, which has none: the participant's sort, "(demo answer)" for text, or the middle of
        the scale for a rating. One given already, if too short for its clause, is never changed."""
        if has_content(self.progress()[0].get(block["id"])):
            raise CannotMakeUp(f"{block['id']} has an answer that would have to change.")
        block_type = BLOCK_TYPES[block["type"]]
        if block_type.scored:
            self.sort(block)
        elif block_type.captures in (TEXT, SCALE_POINT):
            made_up = DEMO_ANSWER if block_type.captures is TEXT else MIDDLE_OF_THE_SCALE
            if not self.response.save_answer(block["id"], made_up):
                raise CannotMakeUp(f"{block['id']} is fixed.")
        else:
            raise CannotMakeUp(f"A {block['type']} answer isn't made up.")

    def sort(self, block):
        """✨ The participant's sort, `PARTICIPANT_PROFILE`'s, checked and scored as theirs is when sent, then each of
        its pairs answered as the profile's guide says and the result re-weighted, as the tie-break's page stores
        them."""
        try:
            seeded = seeding(self.document, *PARTICIPANT_PROFILE)
            value = answer_from_form(self.document, block, json.dumps(seeded.sort))
        except (DoesNotFit, ScenarioDoesNotHold, AnswerRefused) as problem:
            raise CannotMakeUp(str(problem)) from problem
        scores = score(self.document, value)
        self.response.submit_sort(block["id"], value, scores)
        result = Result.objects.get(response=self.response, block_id=block["id"])
        for place, (pair, chosen) in enumerate(seeded.questions):
            result.answer_pair(place, pair, chosen)
        if seeded.questions:
            result.keep_reweighted(reweigh(self.document, scores, result.tie_break_answers))

    def coach(self, block):
        """✨ The coach the checklist `block` chose, or "Alex (demo)" saved in their place where there is none, as the
        checklist saves one."""
        coach = self.response.contacts.filter(block_id=block["id"], role=Contact.Role.COACH).first()
        if coach is None:
            [coach] = self.response.replace_contacts(block["id"], [COACH], Contact.Role.COACH)
        return coach

    def link(self, contact):
        """✨ A link made for `contact`, in place of any they had, as the participant makes one."""
        self.tokens[contact.pk] = Invitation.issue(contact, link_lifetime(self.document))
        return self.tokens[contact.pk]

    def coach_link(self, block):
        """✨ A working link for the coach, who has none. Making one again where an expired one was accepted would take
        that acceptance back, so that can't be made up."""
        coach = self.coach(block)
        expired = Invitation.objects.filter(contact=coach).first()
        if expired is not None and expired.coach_answer == Invitation.CoachAnswer.ACCEPTED:
            raise CannotMakeUp("The coach's acceptance would be taken back.")
        self.link(coach)

    def coach_accepts(self, block):
        """✨ The coach accepting through their own link: one made during this press, or else one made again, as the
        participant would make it for them."""
        coach = self.coach(block)
        token = self.tokens.get(coach.pk) or self.link(coach)
        if not Invitation.answer_as_coach(token, Invitation.CoachAnswer.ACCEPTED):
            raise CannotMakeUp("The coach's link took no answer.")

    def voices(self, block):
        """✨ The made-up people on the list `block`, in its order: those with no email address, which a participant
        can't leave out."""
        held = self.response.contacts.filter(block_id=block["id"], role=Contact.Role.CONTACT, email="")
        return list(held.order_by("position"))

    def voice(self, block):
        """✨ A made-up person added to the list `block` with their link, as the participant adds one: "Demo voice" with
        the next number, and no email address, so no reminder can go."""
        person = {"name": VOICE.format(number=len(self.voices(block)) + 1), "email": ""}
        added = self.response.add_contact(block["id"], person, link_lifetime(self.document), MAX_CONTACTS)
        if added is None:
            raise CannotMakeUp("The list is full.")
        contact, token = added
        self.tokens[contact.pk] = token
        return contact

    def people_answer(self, block):
        """✨ Observer assessments sent until the minimum count, by made-up people on the list `block` who have not sent,
        then by new ones; nobody else's is ever sent for them."""
        waiting = [voice for voice in self.voices(block) if voice.sent_at is None]
        for _ in range(minimum_observers(self.document) - ObserverResponse.counted(self.response)):
            self.send_as(waiting.pop(0) if waiting else self.voice(block), block)

    def send_as(self, voice, block):
        """✨ A made-up person's observer assessment, the observer version of their turn's demo profile, sent as test
        data through their link claimed as an observer claims theirs."""
        profile = VOICE_PROFILES[[each.pk for each in self.voices(block)].index(voice.pk) % len(VOICE_PROFILES)]
        scored = next(each for each in blocks_of(self.document) if BLOCK_TYPES[each["type"]].scored)
        sort = scenario_loading.observer_sort(self.document, profile)
        secret = Invitation.claim(self.tokens.get(voice.pk) or self.link(voice))
        try:
            assessment = answer_from_form(self.document, scored, json.dumps(sort), role="observer")
            sent = ObserverResponse.send(self.response, secret, assessment, is_test_data=True) if secret else None
        except (AnswerRefused, CollectionFrozen) as problem:
            raise CannotMakeUp("A made-up person's assessment wasn't taken.") from problem
        if sent is None:
            raise CannotMakeUp("A made-up person's link wasn't claimed.")

    def look(self, sort_id):
        """✨ The look at the sort's comparison, as the participant's press records it (`look_at_comparison`), with the
        minimum in to make it a view: made-up people answering on the pathway's contact list first where too few
        have."""
        if not Result.objects.filter(response=self.response, block_id=sort_id).exists():
            raise CannotMakeUp("There is no sort to compare.")
        if ObserverResponse.counted(self.response) < minimum_observers(self.document):
            lists = [block for block in blocks_of(self.document) if block["type"] == "contact_list"]
            if not lists:
                raise CannotMakeUp("There is nobody to ask.")
            self.people_answer(lists[0])
        self.response.look_at_comparison(sort_id)
