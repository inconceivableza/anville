# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import hashlib
import json
import mimetypes
import re
from datetime import date
from typing import NamedTuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import apnumber
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.vary import vary_on_headers

from access.consent import consent_required
from access.models import name_shown_for
from engine.document import (
    BLOCK_TYPES,
    LONG_TEXT_MAX_LENGTH,
    SCALE_POINTS,
    AnswerRefused,
    UnknownBlock,
    answer_from_form,
    answerable_block,
    authored_text,
    checklist,
    text_for,
    unmet,
)
from engine.document.blocks import (
    COMPARISON_UNSORTED,
    CONTACTS,
    SENT_ALREADY,
    anchor_of,
    blocks_of,
    coach_brief,
    comparison_status,
    freeze_warning,
    landing_of,
    page_count,
    page_field,
    page_of,
    pages_of,
    saves_quietly,
    section_ended_by,
    section_of,
    signpost_shown,
    text_shown,
    warns_beside_the_press,
    way_on_named_by,
)
from engine.document.coach import (
    asked_in_a_sentence,
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
    coach_answer_from_form,
    coach_confirmed,
    coach_from_form,
    commitments,
)
from engine.document.contacts import (
    LIST_FULL,
    MAX_CONTACTS,
    can_add_row,
    contact_from_form,
    declined_sentence,
    needed,
    rows_of,
    voices_card,
    withdrawn_sentence,
)
from engine.document.aggregation import aggregate
from engine.document.gates import (
    clause_message,
    clauses_of,
    coach_answer,
    comparison_viewed,
    comparison_wait_message,
    links_issued_key,
    messages_after_a_press,
    opened_key,
)
from engine.document.scoring import score
from engine.hub import (
    COACH_WITHDREW,
    COMPARISON_READY_SENTENCE,
    COMPLETE,
    block_ids_fixed_on_completion,
    complete_sections,
    completes_with_its_evaluation,
    finish_waits,
    hub_for,
    is_locked,
    is_once_only_and_complete,
    open_blocks,
    page_reached,
    section_by_id,
    track_sections,
    with_coach_answer,
    HERO_VIDEO_CREDIT,
    WIZARD_PHOTOS,
    WizardStep,
    wizard_step,
)
from engine.document.observers import (
    link_lifetime,
    minimum_observers,
    privacy_notice,
    relationship_from_form,
    relationship_question,
)
from engine.document.letter import letter_shown, opens_on_from_form, seal_press, unsealed_letter
from engine.document.photos import credits_listed, listed, on_pexels, on_unsplash
from engine.models import (
    CollectionFrozen,
    Contact,
    Invitation,
    ObserverResponse,
    PathwayVersion,
    Publication,
    Response,
    Result,
    SealedLetter,
)
from engine import demo_shortcuts, reminders, scenario_loading, stay_in_touch
from engine.document.tie_break import pair_plan, reweigh
from engine.results import comparison_page, pair_page, results_page


class ParticipantState(NamedTuple):
    """✨ Everything stored for one participant: their response (None before their first answer), the pathway version
    it answers and that version's track sections, and its state: answers, sections completed, pages moved past by
    section, and the blocks whose answers are fixed."""

    response: Response | None
    version: PathwayVersion | None
    sections: list
    answers: dict
    completed: set
    moved_past: dict
    fixed: set

    def reached(self, section):
        """✨ The page of a section this participant has reached, or None while the section is locked, and for a once-only
        section once complete, never seen again (ticket 69). Every way into a section (its address, "Continue →",
        completion, an answer or a checklist step) is guarded by this."""
        if is_locked(section, self.completed, self.answers, self.sections, self.moved_past):
            return None
        if is_once_only_and_complete(section, self.completed):
            return None
        return page_reached(section, self.moved_past, self.answers, self.sections)

    def with_answers(self, answers):
        """✨ This state with `answers` in place of its own, and what is complete worked out again from them, since a part
        of a section is complete once its gate passes."""
        stored = self.response.completed_sections if self.response is not None else ()
        return self._replace(answers=answers, completed=complete_sections(self.sections, answers, stored))

    def stored_response(self, user):
        """✨ Their response, begun now if this is the first thing they store."""
        if self.response is not None:
            return self.response
        return Response.objects.get_or_create(participant=user, version=self.version)[0]


class Invite(NamedTuple):
    """✨ The way to invite people, beside the press on to the comparison on the comparison signpost alone (ticket 88,
    fix-3, fix-8, fix-10), offered before and after the minimum, the press greyed below it: the address of the Five
    trusted voices card's page, the phrase beside it (empty from the minimum), and whether the comparison is still
    waiting on answers."""

    href: str
    phrase: str
    waiting: bool = False


class Finish(NamedTuple):
    """✨ The finish a part's end offers when the part is the last thing in its section (ticket 88): that section's
    identifier, its finish button's label, whether it is complete already, and whether it completes itself as its
    evaluation ends (`completes_with_its_evaluation`, ticket 119), so that its label is a way on to the hub, not a
    press."""

    section_id: str
    label: str
    done: bool
    way_on: bool = False


@vary_on_headers("HX-Request")
def home(request):
    """✨ The public homepage (ticket 32a), the same for everyone; "Begin" leads to sign-up, or to the hub once
    signed in.

    Its "Stay in touch" form posts here (ticket 74): with htmx the section alone comes back to take the form's place,
    thanks or refusal, so there is no new page; without, the homepage comes back opened at the section, by the
    fragment in the form's action. A link to the form may name a choice to tick in it (ticket 111); with htmx, which
    asks for it to bring the form back in place of the thanks (sprint-3d-r1-fix-4), it is the section alone again, so
    the response varies with that header, or a cache could hand the section alone to a visit for the page."""
    if request.method == "POST":
        stay = stay_in_touch.subscribe(request.POST)
    else:
        stay = stay_in_touch.opened_with(request.GET)
    status = 400 if stay.refused else 200
    if _is_htmx(request):
        return render(request, "engine/stay_in_touch.html", {"stay": stay}, status=status)
    begin = reverse("hub") if request.user.is_authenticated else reverse("account_signup")
    return render(request, "engine/home.html", {"begin": begin, "stay": stay}, status=status)


# ✨ The photographs the stylesheet draws on the homepage and behind the hub's next step, and the two the homepage's
# steps 3 and 4 show (the notebook and the Bible, stand-ins for journalling until the final photos are picked; ticket
# 110), each a courtesy credit (ticket 101), linked to its photographer and its page as traced (sprint-3d-r1-fix-5).
# The credits page lists them after the pathway's own, after the video's and before the wizard's (`WIZARD_PHOTOS`),
# leaving out one listed already: a required credit always, a courtesy one while the document's setting for courtesy
# credits is on.
SITE_PHOTO_CREDITS = [
    on_unsplash(
        "Photograph of a church gathering with Bibles open",
        "Sincerely Media",
        "https://unsplash.com/@sincerelymedia",
        "https://unsplash.com/photos/woman-reading-book-dGxOgeXAXm8",
    ),
    on_unsplash(
        "Photograph of a figure facing the sun",
        "Andreas Rasmussen",
        "https://unsplash.com/@andreasdress",
        "https://unsplash.com/photos/woman-sitting-in-front-of-grassfield-VLYvYq4da-A",
    ),
    on_unsplash(
        "Photograph of a notebook, a pen and a cup of coffee",
        "Andres Molina",
        "https://unsplash.com/@nomadicfitlust",
        "https://unsplash.com/photos/a-cup-of-coffee-and-a-notebook-on-a-table-8CGOX7oSMbI",
    ),
    on_unsplash(
        "Photograph of a woman walking in a field at sunset",
        "Sasha Freemind",
        "https://unsplash.com/@sashafreemind",
        "https://unsplash.com/photos/woman-standing-on-grass-field-frq5Q6Ne9k4",
    ),
    on_unsplash(
        "Photograph of misty hills at sunrise",
        "Alexander Philipp",
        "https://unsplash.com/@alexphily",
        "https://unsplash.com/photos/golden-sunrise-over-misty-hills-and-distant-ocean-22-PF7Tkk7E",
    ),
    on_unsplash(
        "Photograph of two friends talking beside a lake",
        "Aarón Blanco Tejedor",
        "https://unsplash.com/@the_meaning_of_love",
        "https://unsplash.com/photos/man-in-black-jacket-standing-beside-body-of-water-during-sunset-aocUkMcxeqI",
    ),
    on_unsplash(
        "Photograph of hands shaping clay",
        "Alex Jones",
        "https://unsplash.com/@alexjones",
        "https://unsplash.com/photos/"
        "a-clay-stained-hand-of-a-potter-engaging-in-a-craft-work-of-pottery-or-molding-Tq4YjCa2BSc",
    ),
    on_unsplash(
        "Photograph of a carpenter planing wood",
        "Minh Đức",
        "https://unsplash.com/@meanduck",
        "https://unsplash.com/photos/craftsman-planing-wood-on-a-workbench-P4mxT-OgYho",
    ),
    on_unsplash(
        "Photograph of an open Bible on a jetty at sunrise",
        "Aaron Burden",
        "https://unsplash.com/@aaronburden",
        "https://unsplash.com/photos/book-on-top-of-table-and-body-of-water-535Npq1wFG8",
    ),
    on_unsplash(
        "Photograph of a woman in a summer dress looking out over a field of wheat",
        "Hannah Skelly",
        "https://unsplash.com/@ivelisseskelly",
        "https://unsplash.com/photos/woman-in-orange-dress-on-wheat-field-4aJ9VluXAgo",
    ),
    on_unsplash(
        "Photograph of a teacher standing before a classroom of pupils",
        "Quilia",
        "https://unsplash.com/@heyquilia",
        "https://unsplash.com/photos/students-in-classroom-with-teacher-presenting-zFSo6bnZJTw",
    ),
    on_pexels(
        "Photograph of a woman working in a rice paddy",
        "Nandhu Kumar",
        "https://www.pexels.com/@nandhukumar/",
        "https://www.pexels.com/photo/woman-working-on-rice-paddy-field-12883428/",
    ),
    on_unsplash(
        "Photograph of a chef chopping vegetables in a restaurant kitchen",
        "Pylyp Sukhenko",
        "https://unsplash.com/@novokayn",
        "https://unsplash.com/photos/chef-chopping-vegetables-in-restaurant-kitchen-y-XZf_TNRms",
    ),
    on_unsplash(
        "Photograph of a man and a child looking at a plant",
        "OPPO Find X5 Pro",
        "https://unsplash.com/@oppofindx5pro",
        "https://unsplash.com/photos/a-man-and-a-child-looking-at-a-plant-Nc-hc5g5yhw",
    ),
    on_unsplash(
        "Photograph of a mechanic working on a machine in a garage",
        "Kato Blackmore",
        "https://unsplash.com/@katoblackmore",
        "https://unsplash.com/photos/a-man-working-on-a-machine-in-a-garage-KhF58h0hTbc",
    ),
    on_unsplash(
        "Photograph of a doctor in blue scrubs",
        "Bruno Rodrigues",
        "https://unsplash.com/@naosouogagliasso",
        "https://unsplash.com/photos/man-in-blue-medical-scrubs-279xIHymPYY",
    ),
    on_unsplash(
        "Photograph of a builder in a hard hat on a building frame",
        "Josh Olalde",
        "https://unsplash.com/@josholalde",
        "https://unsplash.com/photos/construction-worker-in-hard-hat-on-building-frame-X1P1_EDNnok",
    ),
    on_unsplash(
        "Photograph of a grandmother peeling potatoes with her grandson",
        "CDC",
        "https://unsplash.com/@cdc",
        "https://unsplash.com/photos/"
        "woman-in-yellow-and-white-floral-button-up-shirt-holding-yellow-banana-E9BR0lNMiQE",
    ),
    on_unsplash(
        "Photograph of an artist holding a paint palette",
        "Vitaly Gariev",
        "https://unsplash.com/@silverkblack",
        "https://unsplash.com/photos/artist-holding-colorful-paint-palette-malUrSBj1v8",
    ),
    on_unsplash(
        "Photograph of a woman working at a laptop by a window",
        "Andrew Neel",
        "https://unsplash.com/@andrewtneel",
        "https://unsplash.com/photos/"
        "girl-wearing-grey-long-sleeved-shirt-using-macbook-pro-on-brown-wooden-table-ute2XAFQU2I",
    ),
    on_unsplash(
        "Photograph of a scientist in a white coat",
        "National Cancer Institute",
        "https://unsplash.com/@nci",
        "https://unsplash.com/photos/woman-in-white-robe-sitting-on-black-office-rolling-chair-uVnRa6mOLOM",
    ),
    on_unsplash(
        "Photograph of a fisherman holding a cormorant on a raft",
        "Willian Justen de Vasconcellos",
        "https://unsplash.com/@willianjusten",
        "https://unsplash.com/photos/fisherman-holding-a-cormorant-on-a-raft-BDO8psCMUFU",
    ),
    on_unsplash(
        "Photograph of a carer helping an elderly couple with colouring",
        "Age Cymru",
        "https://unsplash.com/@agecymru",
        "https://unsplash.com/photos/caregiver-assisting-elderly-couple-with-coloring-bSXk1lOp8T0",
    ),
]


def credits_page(request):
    """✨ The copyright notice of each translation the published pathway quotes, open to anyone, since the public
    homepage quotes scripture too. The publishers ask for their notices on the work's copyright page (ticket 39). After
    them, the credits of the pathway's photos that the document lists (ticket 49b), then the site's own, by the same
    rule: a required credit always, a courtesy one only while the document's setting is on (sprint-3d-r1-fix-5)."""
    version = Publication.current_version()
    translations = version.document.get("translations", {}) if version else {}
    photo_credits = credits_listed(version.document) if version else []
    site_credits = dict.fromkeys([HERO_VIDEO_CREDIT, *SITE_PHOTO_CREDITS, *(photo.credit for photo in WIZARD_PHOTOS)])
    courtesy = bool(version and version.document.get("show_courtesy_credits", False))
    shown = {
        "translations": translations.values(),
        "photo_credits": photo_credits,
        "site_photo_credits": [credit for credit in listed(site_credits, courtesy) if credit not in photo_credits],
    }
    return render(request, "engine/credits.html", shown)


def privacy(request):
    """✨ The privacy notice (ticket 100), open to anyone: visitors, observers and coaches have no account, and a
    participant reads it before consenting."""
    return render(request, "engine/privacy.html")


@login_required
@consent_required
def hub(request):
    """✨ Where the participant always starts: their track's sections, their status, and the next step."""
    state = _participant(request.user)
    if state.version is None:
        return render(request, "engine/hub.html", {})
    if not any(section["blocks"] for section in state.sections):
        return render(request, "engine/hub.html", {})  # ✨ no content is the empty state, never a fallback
    wizard = _wizard_due(state)
    if wizard is not None:
        return redirect(wizard)
    hub = _hub_of(state)
    coach = _coach_of(state.response, state.answers)
    coach_section = _coach_section_of(state.version.document)
    coach_page = _coach_page_of(state.version.document, hub)
    minimum = minimum_observers(state.version.document)
    waiting = hub.waiting_on_answers
    voices = _hub_voices(state, hub)
    side_cards = _side_cards(state, hub, voices)
    coach_wait = _coach_wait_panel(hub, state.response, coach, coach_page)
    comparison = _hub_comparison(state)
    return render(
        request,
        "engine/hub.html",
        {
            "title": text_for(state.version.document["title"], "participant"),
            "hub": hub,
            "photo": _photo_of(state.version.document, hub.next_step.id if hub.next_step else None),
            "coach_wait": coach_wait,
            "next_look": _next_look(hub, coach_wait),
            "side_cards": side_cards,
            "coach_card": _coach_card(coach, coach_section, coach_page),
            "voices": voices,
            "comparison": comparison,
            "comparison_next": _comparison_next(hub, comparison),
            "waiting_sentence": waiting.waiting_sentence(minimum) if waiting is not None else None,
            "waiting_way": _waiting_way(state.version.document, hub),
            "name": name_shown_for(state.response.participant) if state.response else None,
            # ✨ Demo only (ticket 113): the sections the hidden shortcut offers to open.
            "demo_shortcut": demo_shortcuts.offered(state.version.document, hub) if demo_shortcuts.tools_on() else [],
        },
    )


def _comparison_next(hub, comparison):
    """✨ The comparison as the hub's next step leads to it in place of "Waiting on answers" (sprint-3c-r3-fix-14): once
    the section waiting on answers, the one holding the comparison signpost, has the document's minimum in and the
    comparison is not yet viewed (its status "ready", as `comparison_status` has it, the minimum the comparison page's
    own), with the engine's sentence naming that section. None below the minimum, where the wait stands, never leading
    to an empty comparison; and wherever nothing waits on answers, or the comparison is shut with its section."""
    waiting = hub.waiting_on_answers
    if waiting is None or comparison is None or comparison["section"] != waiting.id:
        return None
    if comparison["status"] != "ready" or comparison["locked"]:
        return None
    return {**comparison, "sentence": COMPARISON_READY_SENTENCE.replace("{section}", waiting.called)}


def _waiting_way(document, hub):
    """✨ Where the hub's "Waiting on answers" panel leads, as {"label", "href"}: to the section waiting, by its title,
    at the page reached, while it is open (ticket 68); while it is locked by observers yet to answer, to the page of the
    contact list its opening condition names, by that list's section's title, where more people can be invited (ticket
    106), as the coach's wait leads to the coach page. None with no wait, or with that list's section locked too."""
    waiting = hub.waiting_on_answers
    if waiting is None:
        return None
    if not waiting.is_locked:
        return {"label": waiting.title, "href": page_url(waiting.id, waiting.page)}
    clauses = section_by_id(document, waiting.id)["opens_when"]["clauses"]
    asked = next(clause["block"] for clause in clauses if clause["type"] == "observers_answered")
    holding = section_of(document, asked)
    if any(state.id == holding["id"] and state.is_locked for state in hub.sections):
        return None
    href = page_url(holding["id"], page_of(holding, asked))
    return {"label": text_for(holding["title"], "participant"), "href": href}


def _next_look(hub, coach_wait):
    """✨ The class the hub's next-step panel takes, so the stylesheet can give each state its own photo (fix-8): the
    section's own while one is next, then one each for waiting on answers (trusted voices'), the coach's wait and
    nothing waiting. The panels' order is the template's."""
    if hub.next_step is not None:
        return f"look-section-{hub.next_step.id}"
    if hub.waiting_on_answers is not None:
        return "look-answers"
    return "look-coach" if coach_wait else "look-rest"


def _hub_comparison(state):
    """✨ The document's comparison signpost as the hub shows it, in a row and beside "Invite people" on the Five trusted
    voices card (ticket 67b): its status and press as its section's card has them (`_comparison_signpost_shown`), with
    its title, the section it is in and the part of that section holding its sort, after which its row is listed, or
    None where its sort is not in a part of that section, as in *Whatever You Do*'s Section 2, which lists it first
    (ticket 87), and whether the comparison is `locked`, shut with its section (fix-19), when nothing leads to it. None
    before there is a result, and for a pathway without one."""
    document = state.version.document
    for block in blocks_of(document):
        shown = _comparison_signpost_shown(state, block)
        if shown is not None:
            section, holding = section_of(document, block["id"]), section_of(document, block["sort"])
            return {
                **shown,
                "title": authored_text(block, "participant")["title"],
                "section": section["id"],
                "after": holding["id"] if holding.get("part_of") == section["id"] else None,
                "locked": _comparison_locked(state, block["sort"]),
            }
    return None


def _coach_section_of(document):
    """✨ The identifier of the section holding the document's coach checklist, or None for a document without one."""
    checklists = [block["id"] for block in blocks_of(document) if block["type"] == "coach_checklist"]
    return section_of(document, checklists[0])["id"] if checklists else None


def _side_cards(state, hub, voices):
    """✨ The hub's side cards, each with the status its card shows, for the hub and the sidebar alike, so the two never
    disagree (ticket 95): the coach's tagged with where the coach stands (ticket 51b), and Five trusted voices, as
    `_hub_voices` gives it, with its own tag while it is unlocked (ticket 51a)."""
    coach_section = _coach_section_of(state.version.document)
    # ✨ The coach is read only where a side card is theirs, so a page without that card never depends on the coach.
    on_a_card = any(card.id == coach_section for card in hub.side_cards())
    answer = _coach_standing(state.response, _coach_of(state.response, state.answers)) if on_a_card else None
    cards = []
    for card in hub.side_cards():
        if card.id == coach_section:
            card = with_coach_answer(card, answer)
        elif voices is not None and card.id == voices["section"]:
            card = card._replace(label=voices["tag"], tone=voices["tone"])
        cards.append(card)
    return cards


def _coach_card(coach, coach_section, coach_page):
    """✨ What the Walk with a coach card adds to a side card's own (ticket 65): {"section", "page", "chosen"}, its
    button leading to the `coach_page`, None while the card is locked, and whether a `coach` is chosen, which its
    button's words say (ticket 95)."""
    return {"section": coach_section, "page": coach_page, "chosen": coach is not None}


def _coach_wait_panel(hub, response, coach, coach_page):
    """✨ What the hub's next-step panel says in place of "Nothing is waiting for you right now" while nothing is next
    and a section waits on nothing but the coach's acceptance (ticket 65): {"heading", "sentence", "coach_page"}, by
    where the `coach` stands (`_coach_standing`), or None otherwise, or with no `coach_page` to lead to."""
    wait = hub.coach_wait
    if hub.next_step is not None or wait is None or not wait.only or coach_page is None:
        return None
    wording = wait.panel(_coach_standing(response, coach), coach["name"] if coach else "")
    return {**wording._asdict(), "coach_page": coach_page}


def _coach_standing(response, coach):
    """✨ The coach's answer, as `_coach_of` gives it; with no coach, `COACH_WITHDREW` while the response keeps that the
    last one withdrew their acceptance, saying nothing of who (ADR 0024), and otherwise None."""
    if coach is not None:
        return coach["answer"]
    return COACH_WITHDREW if response is not None and response.coach_withdrew else None


def _photo_of(document, section_id):
    """✨ The address of the photo the document names for the section by this identifier, or None for no section or one
    without a photo (ticket 49b)."""
    if section_id not in document.get("photos", {}):
        return None
    return reverse("photo", args=[section_id])


def _wizard_due(state):
    """✨ Where a participant is taken in place of the hub (ticket 50): the page they have reached of the first section
    the document marks as a wizard that they have not completed and can open, or None."""
    for section in state.sections:
        if _shows_as_wizard(state, section):
            reached = state.reached(section)
            if reached is not None:
                return page_url(section["id"], reached)
    return None


def _shows_as_wizard(state, section):
    """✨ Whether a section's pages are drawn as its wizard, without the hub's links or the sidebar: until it is
    complete. Once complete it is reread as any other section."""
    return bool(section.get("wizard")) and section["id"] not in state.completed


def _section_shown(request, state, section, shown, status=200):
    """✨ A page of a section as `_section_page` gives it, drawn as its wizard while it is one."""
    if _shows_as_wizard(state, section):
        step = wizard_step(state.sections, section, shown["page"]["number"])
        shown = {**shown, "step": step, "steps": step.numbers}
        return render(request, "engine/wizard.html", shown, status=status)
    return render(request, "engine/section.html", shown, status=status)


def _coach_page_of(document, hub):
    """✨ The address of the page of the document's coach checklist, at the checklist, or None for a document without
    one, whose hub then says nothing of a coach. None too while the participant's `hub` has its section locked, as a
    locked section's pages are never linked."""
    for block in blocks_of(document):
        if block["type"] == "coach_checklist":
            section = section_of(document, block["id"])
            if any(state.id == section["id"] and state.is_locked for state in hub.sections):
                return None
            return _block_address(document, block["id"])
    return None


def _block_address(document, block_id):
    """✨ The address of the page a block is on, at the block's anchor where it has one (`anchor_of`)."""
    section = section_of(document, block_id)
    address = page_url(section["id"], page_of(section, block_id))
    anchor = anchor_of(section, block_id)
    return f"{address}#{anchor}" if anchor else address


# ✨ What the comparison is called where no comparison signpost names it, as in the faithful port: the original
# prototype's heading for it.
COMPARISON_TITLE = "How others experience you"


def _comparison_title(document, sort_id):
    """✨ What the comparison of the sort `sort_id` is called, in the sidebar's link to it and as its own page's
    heading: the title of the comparison signpost pointing at it, as the hub's row names it (ticket 109;
    sprint-3d-r1-fix-1), or where no signpost does, the engine's own."""
    for block in blocks_of(document):
        if block["type"] == "comparison_signpost" and block["sort"] == sort_id:
            return authored_text(block, "participant")["title"]
    return COMPARISON_TITLE


def _comparison_title_for_coach(document, sort_id, name):
    """✨ What a coach's shared view calls the comparison of the sort `sort_id`: the title the participant's own page is
    headed with (`_comparison_title`), with the participant's `name` in place of "you", so "How others see you" reads
    "How others see Sam" and the engine's own "How others experience you" reads "How others experience Sam"
    (sprint-3d-r1-fix-2). A title that never says "you" is kept as written."""
    return re.sub(r"\byou\b", lambda _: name, _comparison_title(document, sort_id), flags=re.IGNORECASE)


def _quick_link_names(document, hub, scored):
    """✨ What the sidebar's links to the comparison of the `scored` block, to the invitations and to the coach page are
    called, as {"comparison", "invitations", "coach"}: what the hub calls each page they open, in the pathway's words
    (ticket 109), the title of the comparison signpost's row (`_comparison_title`) or of the side card holding the
    contact list or the coach checklist. Where the hub names no such page, as for a list or a checklist within a larger
    section, the engine's own."""
    names = {
        "comparison": _comparison_title(document, scored["id"]) if scored is not None else COMPARISON_TITLE,
        "invitations": "Invite others to assess you",
        "coach": "Your coach",
    }
    cards = {card.id: card.title for card in hub.side_cards()}
    for name, block_type in (("invitations", "contact_list"), ("coach", "coach_checklist")):
        held = [section_of(document, block["id"])["id"] for block in blocks_of(document) if block["type"] == block_type]
        if held and held[0] in cards:
            names[name] = cards[held[0]]
    return names


def participant_nav(request):
    """✨ The header and sidebar of every participant page (ticket 41a), as `engine/participant_header.html` needs them:
    the pathway's name, and unless the site switches it off, the sidebar. The sidebar lists what the hub lists, in its
    order (ticket 80): its sections, the comparison signpost's row and its side cards, from the hub's own derivation, so
    their statuses and locks are the hub's; a locked section carries no address, and neither does a page within it,
    such as the coach page. Below them are links, kept beside the entries as quick ways in (developer's call, 23 Oct):
    results and the comparison once there is a result, since before then they lead only back to the sort, the
    comparison only while it is open too (fix-19), the invitations, and the coach page, each named as the hub names the
    page it opens (`_quick_link_names`). `current` is the section whose page this is, if any."""
    state = _participant(request.user)
    if state.version is None:
        return {"title": None, "sidebar": None}
    document = state.version.document
    title = text_for(document["title"], "participant")
    if not settings.ANVILLE_SIDEBAR or not any(section["blocks"] for section in state.sections):
        return {"title": title, "sidebar": None}
    hub = _hub_of(state)
    links = []
    scored = _scored_block(document)
    names = _quick_link_names(document, hub, scored)
    if scored and Result.objects.filter(response=state.response, block_id=scored["id"]).exists():
        links.append(("Your results", reverse("results", args=[scored["id"]])))
        if not _comparison_locked(state, scored["id"]):
            links.append((names["comparison"], reverse("comparison", args=[scored["id"]])))
    links.append((names["invitations"], reverse("invitations")))
    coach_page = _coach_page_of(document, hub)
    if coach_page:
        links.append((names["coach"], coach_page))
    return {
        "title": title,
        "sidebar": {
            "outline": hub.outline(),
            "comparison": _hub_comparison(state),
            "side_cards": _side_cards(state, hub, _hub_voices(state, hub)),
            "current": _current_section(request, document),
            "links": [{"label": label, "href": href, "is_current": href == request.path} for label, href in links],
        },
    }


def _current_section(request, document):
    """✨ The identifier of the section whose page this is, or None. Every address naming a section is that section's,
    a refused "Continue →" or completion included; a coach checklist's step, without JavaScript, shows the page of the
    checklist's section."""
    match = request.resolver_match
    if match is None:
        return None
    if match.url_name == "coach_checklist":
        return section_of(document, match.kwargs["block_id"])["id"]
    return match.kwargs.get("section_id")


@login_required
@consent_required
def start(request):
    """✨ Where agreeing to consent leads. A participant with nothing saved goes straight to their first step,
    as the prototype goes from its account screen into onboarding; anyone who has begun goes to the hub."""
    state = _participant(request.user)
    if state.response is not None or state.version is None:
        return redirect("hub")
    next_step = _hub_of(state).next_step
    if next_step is None or not any(section["blocks"] for section in state.sections):
        return redirect("hub")  # ✨ the hub's empty state says there is nothing to begin
    return redirect("section", next_step.id)


@login_required
@consent_required
def section(request, section_id, page=1):
    """✨ One page of a section's blocks. A locked section, or a page not yet reached, is refused here, whatever the
    participant typed in the bar: a page ahead of the one reached leads back to that one."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    _page_or_404(section, page)
    if page > reached:
        return redirect(page_url(section_id, reached))
    sort_done = _sort_done_with(state, section)
    if sort_done is not None:
        return redirect("results", sort_done)
    # ✨ A link just issued, a coach's or an observer's, shown this once. Read only on a page holding a block that
    # lists people with their links (`lists_links`), whose address is the path the cookie was set for, so deleting it
    # here reaches it; the section's later pages sit under that path too when the block is on its first.
    shows_links = any(BLOCK_TYPES[block["type"]].lists_links for block in pages_of(section)[page - 1])
    issued = _issued_link(request) if shows_links else None
    demo = _demo_prefill(request, state.version.document)
    _open_letters_due(state, pages_of(section)[page - 1])
    drawn = _section_page(state, section, page, issued=issued, demo=demo, kept=_letter_dates(request))
    shown = _section_shown(request, state, section, drawn)
    if issued is not None:
        shown["Cache-Control"] = "no-store"
        shown.delete_cookie(ISSUED_COOKIE, path=request.path)
    return shown


def _sort_done_with(state, section):
    """✨ The identifier of the sort a section's page would only point past, or None: a part of a section holding its
    sort and nothing else, once the sort is in (fix-13). The page would show no more than a link to the results, so
    every way into it leads there instead; the results page itself goes on to any tie-break pair left, as "View my
    results →" does (ticket 61). A section with anything beside its sort is still shown, and so is a part whose
    section is not open, or a section that is no part: the results page's way back leads to such a section itself,
    and one that is no part keeps its own completion there."""
    if len(section["blocks"]) != 1:
        return None
    [block] = section["blocks"]
    if not BLOCK_TYPES[block["type"]].scored or block["id"] not in state.answers:
        return None
    return block["id"] if _section_this_is_part_of(state, section) else None



@login_required
@consent_required
@require_POST
def move_past_page(request, section_id, page):
    """✨ "Continue →" from one page of a section to the next, allowed exactly when the page offers it: once that page's
    clauses pass and nothing on the way to it (an unconfirmed reading, a held link) holds what follows. Re-checked here
    rather than trusted to the page. The last page has no way on but completing the section. Every answer on the page
    the press sends is stored first (`_page_answers_stored`)."""
    state = _participant(request.user, first_version=lambda: _version_sent(request))
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return _to_the_hub_when_locked(request)
    if _page_or_404(section, page) == page_count(section):
        raise Http404("The last page of a section is moved past by completing it.")
    if page > reached:
        return _go_to(request, page_url(section_id, reached))
    # ✨ Every answer on the page is sent with the press and stored first, as its own save would store it, so what was
    # chosen or typed since is kept whether or not the page then lets the participant on, without JavaScript too (ticket
    # 107's letter, then every answer: sprint-3d-r1-fix-6). One refused refuses the press, saying which.
    state, not_saved = _page_answers_stored(request, state, section, page)
    shown = _section_page(state, section, page)
    if not_saved or not shown["offers_way_on"] or shown["unmet"]:
        return _way_on_refused(request, state, section, {**shown, "not_saved": not_saved})

    state.stored_response(request.user).move_past_page(section_id, page)
    return _go_to(request, page_url(section_id, page + 1))


@login_required
@consent_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page. It is
    done from the section's last page, so a participant who has not reached it is sent to the page they have. A part of
    a section, or a hub side card, has no completion of its own: it is complete once its gate passes. Every answer on
    the last page the press sends is stored first, so the gate reads them (`_page_answers_stored`, sprint-3d-r1-fix-6),
    and a refusal lists only what is still missing."""
    state = _participant(request.user, first_version=lambda: _version_sent(request))
    section = _section_or_404(state.version, section_id)
    if _completes_itself(section):
        raise Http404("This section is complete once its gate passes, with no completion of its own.")
    reached = state.reached(section)
    if reached is None:
        return _to_the_hub_when_locked(request)
    last = page_count(section)
    if reached < last:
        return _go_to(request, page_url(section_id, reached))
    state, not_saved = _page_answers_stored(request, state, section, last)
    # ✨ The press that finishes a section holding a letter not yet sealed seals it too, until the date it chose (ticket
    # 104); a letter sealed already keeps its first date, whatever is sent.
    letter = unsealed_letter(section, _seals(state))
    chosen = request.POST.get("opens_on")
    opens_on, seal_refusal = opens_on_from_form(letter, chosen, timezone.localdate()) if letter else (None, None)
    if not_saved or unmet(section, state.answers) or seal_refusal:
        # ✨ The date the press sent comes back as sent, so a page drawn again without JavaScript keeps it.
        shown = _section_page(state, section, last, chosen=chosen)
        return _way_on_refused(request, state, section, {**shown, "seal_refusal": seal_refusal, "not_saved": not_saved})

    fixed_block_ids = block_ids_fixed_on_completion(section, state.answers)
    with transaction.atomic():
        participant_response = state.stored_response(request.user)
        participant_response.complete_section(section_id, fixed_block_ids=fixed_block_ids)
        if letter is not None:
            SealedLetter.seal(participant_response, letter["id"], opens_on)
    if letter is not None:
        _keep_letter_date(request, letter["id"], None)  # ✨ sealed, it keeps no date picked (sprint-3d-r1-fix-3)
        # ✨ Back to the letter, so the participant sees it sealed and until when, rather than only a tick on the hub.
        return _go_to(request, f"{page_url(section_id, page_of(section, letter['id']))}#{landing_of(letter)}")
    # ✨ Back to the hub, which points at the next step, as the prototype's `completePillar` goes (ticket 41b); a wizard
    # ✨ with a welcome by way of it first (sprint-3c-r3-fix-7).
    if section.get("wizard") and "welcome" in section:
        return _go_to(request, reverse("wizard_welcome", args=[section_id]))
    return _go_to(request, reverse("hub"))


# ✨ The date last picked for each letter not yet sealed, by its block, kept in the participant's session as it is
# changed, so the page that seals it offers it again after going back to the letter and on (sprint-3d-r1-fix-3). Never
# stored beyond the session: sealing takes only the date its own press sends.
LETTER_DATES_KEY = "letter_dates"


@login_required
@consent_required
@require_POST
def letter_date(request, block_id):
    """✨ The date a letter not yet sealed opens on, kept quietly as it is picked (sprint-3d-r1-fix-3): with JavaScript
    as its field changes; without, as "← Previous page" goes back from the page that seals it, sending the page's form
    (`back`), which this then leads on to. Anything but a date forgets the one kept, and a letter sealed keeps none.
    Going back stores every answer on the page sent with it too, as any press on a page does (sprint-3d-r1-fix-6), or,
    with one refused, draws the page again saying which, at its refusal."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "letter")
    section = section_of(state.version.document, block_id)
    last = page_count(section)
    if state.reached(section) != last:
        return _refused(request, NOT_OPEN, status=403)
    seals = _seals(state)
    _keep_letter_date(request, block["id"], None if block["id"] in seals else _date_sent(request))
    if "back" not in request.POST:
        return HttpResponse(status=204)
    state, not_saved = _page_answers_stored(request, state, section, last)
    if not_saved:
        return _answers_refused(request, state, section, last, not_saved)
    return _go_to(request, _previous_page(section, last, seals) or page_url(section["id"], last))


def _date_sent(request):
    """✨ The date a press sent for a letter to open on, as an ISO date, or None for anything but a date."""
    try:
        return date.fromisoformat(request.POST.get("opens_on") or "").isoformat()
    except ValueError:
        return None


def _letter_dates(request):
    """✨ The dates kept for the participant's letters not yet sealed, by block (`LETTER_DATES_KEY`)."""
    return request.session.get(LETTER_DATES_KEY, {})


def _keep_letter_date(request, block_id, picked):
    """✨ Keep `picked`, an ISO date, as the date last picked for the letter `block_id`, or forget it with None."""
    kept = {letter: day for letter, day in _letter_dates(request).items() if letter != block_id}
    request.session[LETTER_DATES_KEY] = {**kept, block_id: picked} if picked else kept


@login_required
@consent_required
def wizard_welcome(request, section_id):
    """✨ A wizard's welcome, as v3's "Welcome, Alex" (sprint-3c-r3-fix-7): once it is complete, its last step, all of
    its counter marked, leading on to the hub. Before then it leads to the wizard's page reached, and a wizard without
    a welcome, or a section that is not one, to the hub."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    if not section.get("wizard") or "welcome" not in section:
        return redirect("hub")
    if section_id not in state.completed:
        reached = state.reached(section)
        return redirect(page_url(section_id, reached) if reached is not None else "hub")
    welcome = section["welcome"]
    # ✨ The step after the last, so every mark of the counter is on and its photo is the next one, as v3's.
    last = wizard_step(state.sections, section, page_count(section))
    after = WizardStep(last.count + 1, last.count, welcome)
    shown = {
        "section": section,
        "welcome": welcome,
        "heading": welcome["heading"].replace("{name}", name_shown_for(request.user)),
        "step": after,
        "steps": after.numbers,
    }
    return render(request, "engine/wizard_welcome.html", shown)


def _to_the_hub_when_locked(request):
    """✨ A press on a section that is locked, or outside the track: to the hub, with htmx told to go there rather than
    draw the hub beneath the button (fix-2)."""
    return _go_to(request, reverse("hub")) if _is_htmx(request) else redirect("hub")


def _way_on_refused(request, state, section, shown):
    """✨ A refused "Continue →" or completion, nothing stored by it but the answers it sent (`not_saved` lists any of
    those refused): with htmx, only what sits beneath the button, for the page's `#gate-refusal`, so the page neither
    reloads nor moves (fix-2); without, the page again."""
    shown = {**shown, "refused": True}
    if _is_htmx(request):
        return render(request, "engine/gate_refusal.html", shown, status=400)
    return _section_shown(request, state, section, shown, status=400)


@login_required
@consent_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them. A section that
    completes itself was never theirs to take back, and a side card stays complete (ticket 52), as does a section its
    evaluation completed (ticket 119). Nor is a wizard's, which the hub never asks for again once given (ticket 50)."""
    state = _participant(request.user)
    if not _reopens(_section_or_404(state.version, section_id), state.sections):
        raise Http404("This section's completion is not taken back.")
    if state.response is not None:
        state.response.reopen_section(section_id)
    return _see_other("hub")


@login_required
@consent_required
@require_POST
def save_answer(request, block_id):
    """✨ Autosave: validate and store one block's answer against the participant's pathway version.

    A participant with a response answers its version. A first answer is recorded against the version
    the page was rendered from, so a version published while they were typing never captures it.
    """
    state = _participant(request.user, first_version=lambda: _published_version(request.POST.get("version")))
    if state.version is None:
        raise Http404("No published pathway version was named.")
    try:
        block = answerable_block(state.version.document, block_id)
    except UnknownBlock:
        raise Http404("This pathway version has no block by that identifier that takes an answer.")
    if BLOCK_TYPES[block["type"]].captures is CONTACTS:
        # ✨ Never the whole list at once, which from a page left open would drop whoever was added since (ticket 51a).
        raise Http404("A contact list keeps each person on their own, at its own address.")
    # ✨ A block a participant has not reached is as shut as the page that would have shown it, whether a
    # lock or an unconfirmed reading holds it. Otherwise they could fill it in without ever opening it, and
    # both would be decoration again, which is exactly the prototype's mistake.
    section = section_of(state.version.document, block_id)
    if is_once_only_and_complete(section, state.completed):
        # ✨ Never seen again once complete (ticket 69), so not refused on its page: there is none to go back to.
        return _go_to(request, reverse("hub"))
    if not _is_open(state, section, block):
        return _refused(request, NOT_OPEN, status=403)
    unstorable = _why_not_stored(state, block)
    if unstorable is not None:
        return _answer_refused(request, state, section, block_id, *unstorable)
    block_type = BLOCK_TYPES[block["type"]]
    try:
        value = answer_from_form(state.version.document, block, _answer_sent(request, block))
    except AnswerRefused as refused:
        return _answer_refused(request, state, section, block_id, str(refused), status=400)

    participant_response = state.stored_response(request.user)
    # ✨ The row is updated in place, so the answers read before are a step behind what is about to be stored.
    saved = state.with_answers({**state.answers, block_id: value})
    if block_type.scored:
        scores = score(state.version.document, value)
        try:
            participant_response.submit_sort(block_id, value, scores)
        except IntegrityError:
            # ✨ A sort sent from a page left open: the retake, at the foot of the results, is the way to sort again.
            refusal = "Your results are already in. To sort again, retake the strengths evaluation from your results."
            return _answer_refused(request, state, section, block_id, refusal, status=409)
        # ✨ A sort too close to call on one framework or both, and not flat, leads to the tie-break's pairs first.
        if pair_plan(state.version.document, scores):
            return _go_to(request, _with_demo_profile(request, reverse("tie_break", args=[block_id])))
        _participant(request.user)  # ✨ the evaluation has ended, so a section it ends completes now (ticket 119)
        return _to_results(request, block_id)
    if not participant_response.save_answer(block_id, value):
        # ✨ a completion fixed it after the check above, and the UPDATE saw that
        return _answer_refused(request, state, section, block_id, FIXED_REFUSAL, status=409)
    return _saved(request, saved, section, block_id)


def _why_not_stored(state, block):
    """✨ Why an answer to a block the participant has reached may not be stored now, as `(refusal, status)`, or None
    when it may."""
    if block["id"] in _seals(state):
        # ✨ Sealed, it is never changed, and the refusal, like the page, never carries it (ticket 104).
        return SEALED_REFUSAL, 409
    if block["id"] in state.fixed:
        # ✨ Refused here, not only disabled on the page, so a page left open from before completing cannot change it.
        return FIXED_REFUSAL, 409
    waiting = comparison_wait_message(block, state.answers)
    if waiting is not None:
        # ✨ Refused here, not only disabled on the page, so the reflection is written only once its comparison has been
        # seen (ADR 0019).
        return waiting, 403
    return None


def _answer_sent(request, block):
    """✨ What a form sent as one block's answer, every value under its name: its page's name for it (`page_field`), as
    its page's form and its own save with JavaScript send it (sprint-3d-r1-fix-6), or else `value`, as a form of its
    own sends it (a reading's confirmation, the sort)."""
    field = page_field(block)
    return request.POST.getlist(field if field in request.POST else "value")


@login_required
@consent_required
@require_POST
def save_page(request, section_id, page):
    """✨ A page's own Save, beside its way on, for a browser without JavaScript (sprint-3d-r1-fix-6): every answer on
    the page stored at once, as each saves on its own with JavaScript, then the page again at the Save; or, with any
    refused, the page drawn again at its refusal, saying which. The date a letter opens on, sent from the page that
    seals it, is kept as going back from that page keeps it (sprint-3d-r1-fix-3), so the page offers it again. A page
    shut, or not reached, is refused as an answer on it would be, on a page of its own (ticket 71); a once-only section
    complete leads to the hub (ticket 69)."""
    state = _participant(request.user, first_version=lambda: _version_sent(request))
    section = _section_or_404(state.version, section_id)
    _page_or_404(section, page)
    if is_once_only_and_complete(section, state.completed):
        return _go_to(request, reverse("hub"))
    reached = state.reached(section)
    if reached is None or page > reached:
        return _refused(request, NOT_OPEN, status=403)
    state, not_saved = _page_answers_stored(request, state, section, page)
    letter = unsealed_letter(section, _seals(state)) if page == page_count(section) else None
    if letter is not None and "opens_on" in request.POST:
        _keep_letter_date(request, letter["id"], _date_sent(request))
    if not_saved:
        return _answers_refused(request, state, section, page, not_saved)
    return _see_other(f"{page_url(section_id, page)}#completion")


def _version_sent(request):
    """✨ The pathway version a press on a page records a first answer against, as `save_answer` does: the published
    version the page was drawn from, which its form names, or else the one published now, for a press sending none."""
    return _published_version(request.POST.get("version")) or Publication.current_version()


def _answer_stored(request, state, section, block, sent):
    """✨ One answer sent with a press, `sent` its values, stored as the block's own save would store it, and refused for
    the same reasons, as `(value, refusal)`: the value stored and None, or None and why it was not."""
    if not _is_open(state, section, block):
        return None, NOT_OPEN
    unstorable = _why_not_stored(state, block)
    if unstorable is not None:
        return None, unstorable[0]
    try:
        value = answer_from_form(state.version.document, block, sent)
    except AnswerRefused as refused:
        return None, str(refused)
    if not state.stored_response(request.user).save_answer(block["id"], value):
        return None, FIXED_REFUSAL  # ✨ a completion fixed it after the check above, and the UPDATE saw that
    return value, None


def _page_answers_stored(request, state, section, page):
    """✨ Every answer on one page of a section that a press there sent (sprint-3d-r1-fix-6). The page's answers belong
    to its one form (`sent_with_its_page`), so its Save, its way on and the way back from a page that seals a letter all
    send them, and each is stored as its own save would store it, refused for the same reasons: without JavaScript,
    nothing chosen on the page is lost to a press, and none is refused silently. An answer not sent, as a rating with no
    point chosen or one fixed and so disabled, is left as it was.

    Returns `(state, not_saved)`: the state with what was stored in it, and each answer refused, in the page's order, as
    {"name", "refusal"}: its prompt, which names it on the press's refusal, and why."""
    stored, not_saved = {}, []
    for block in pages_of(section)[page - 1]:
        field = page_field(block)
        if not BLOCK_TYPES[block["type"]].sent_with_its_page or field not in request.POST:
            continue
        value, refusal = _answer_stored(request, state, section, block, request.POST.getlist(field))
        if refusal is None:
            stored[block["id"]] = value
        else:
            not_saved.append({"name": text_for(block["prompt"], "participant"), "refusal": refusal})
    if stored:
        state = state._replace(response=state.stored_response(request.user))
        state = state.with_answers({**state.answers, **stored})
    return state, not_saved


def _answers_refused(request, state, section, page, not_saved):
    """✨ A press on a page that is not a way on (its Save, or going back from the page that seals a letter) with answers
    refused: the page drawn again, those stored in it, opened at its refusal (`#refused`), which names each answer not
    saved and says why. Only without JavaScript, which saves each answer on its own."""
    shown = _section_page(state, section, page, chosen=request.POST.get("opens_on"), kept=_letter_dates(request))
    return _section_shown(request, state, section, {**shown, "not_saved": not_saved}, status=400)


def _answer_refused(request, state, section, block_id, refusal, status):
    """✨ An answer not saved, and why: with htmx, the status line beside it; without, its page again, the reason shown
    at the answer. A form submitted as a full page (Enter in an answer field does that) never lands the participant on
    the bare status line (fix-7)."""

    def its_page(status):
        shown = _section_page(state, section, page_of(section, block_id), kept=_letter_dates(request))
        _on_page(shown, block_id)["refusal"] = refusal
        return _section_shown(request, state, section, shown, status=status)

    return _refused(request, refusal, status, page=its_page)


@sensitive_post_parameters()
@login_required
@consent_required
@require_POST
def coach_checklist(request, block_id):
    """✨ One step of choosing a coach: from the intro to the questions, to an outcome, or back to the start; and
    saving the coach chosen, or removing them.

    Nothing from the checklist is stored or logged. The candidate's name and the answers so far travel only in the
    form, screen to screen, and the outcome is worked out again from what was posted, never taken from the button
    pressed. The answers are opinions about another person, including their faith (special category data under
    GDPR), and no later step reads them; `sensitive_post_parameters` keeps them out of error reports too. Saving
    keeps only the chosen coach's name, as a contact (ADR 0022), and only once the outcome allows it.
    """
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "coach_checklist")
    section = section_of(state.version.document, block_id)
    if not _is_open(state, section, block):
        return _refused(request, NOT_OPEN, status=403)
    to = request.POST.get("step")
    if to not in CHECKLIST_STEPS:
        return HttpResponseBadRequest("The coach checklist has no such step.")

    screen = _checklist_step(block, to, request.POST, _coach_kept(state.answers, block_id))
    kept = state.answers
    coach = None
    if to == "save" and screen["screen"] == "chosen":
        # ✨ Always a new contact, so the previous coach's link stops, with any answer given through it. Their link is
        # made in the same act, so nobody misses that step (ticket 51b).
        [coach] = state.stored_response(request.user).replace_contacts(block_id, [screen["coach"]], Contact.Role.COACH)
        link = _issue_link(request, coach)
        screen["coach"] = {**screen["coach"], "id": coach.pk}
        screen["issued"] = {"contact": coach.pk, "link": link}
        kept = {**kept, block_id: [screen["coach"]]}
    elif to == "remove" and state.response is not None:
        state.response.replace_contacts(block_id, [], Contact.Role.COACH)
        kept = {key: value for key, value in kept.items() if key != block_id}
    # ✨ A save the outcome does not allow is refused, though its screen (a stop, say) has nothing to add.
    refused = screen.get("refusal") or (to == "save" and screen["screen"] != "chosen")
    status = 400 if refused else 200
    stored = status == 200 and to in ("save", "remove")
    page = page_of(section, block_id)
    is_htmx = request.headers.get("HX-Request") == "true"
    if not is_htmx and stored:
        # ✨ Once stored, the checklist is behind: the page shows only the coach kept, so it is safe to go back to, with
        # the link just made, as issuing it leads back.
        if coach is not None:
            return _back_with_issued(request, coach, screen["issued"]["link"])
        return _see_other(_block_address(state.version.document, block_id))
    shown = _section_page(state.with_answers(kept), section, page)
    checklist_block = next(on_page for on_page in shown["section"]["blocks"] if on_page["id"] == block_id)
    checklist_block["checklist"] = _checklist_screen(checklist_block["text"], **screen)
    if is_htmx:
        # ✨ Keeping or removing a coach can change what the page's gate holds met (the coach's link issued), so its way
        # on comes too, as after an autosave; stepping through the checklist changes nothing stored, so it stays.
        context = {**shown, "block": checklist_block, "stored": stored}
        result = render(request, "engine/coach_checklist_result.html", context, status=status)
        if coach is not None:
            result["Cache-Control"] = "no-store"  # ✨ it holds the link, shown this once
        return result
    # ✨ Never a redirect without JavaScript while choosing: the answers would have to go in the address, where they
    # are logged. The page returned is the one the checklist is on.
    return render(request, "engine/section.html", shown, status=status)


# ✨ The buttons of the coach checklist: back to the intro keeping what was given, on to the questions, to see how
# it looks, "I'm still confident" past a second thought, starting again with someone else, saving the coach chosen,
# removing them, and keeping the coach already chosen after all.
CHECKLIST_STEPS = ("intro", "questions", "outcome", "confident", "restart", "save", "remove", "keep")


def _checklist_step(block, to, posted, coach_kept=None):
    """✨ Where a press of the checklist's button leads, from what its form held and the coach already kept (if any),
    as the screen's state. A coach saved, or kept after all, is "chosen", with the coach; an intro while a coach is
    kept says so."""
    questions = block["questions"]
    if to == "keep" and coach_kept:
        return {"screen": "chosen", "coach": coach_kept}
    if to == "remove":
        return {"screen": "intro"}
    if to in ("restart", "keep"):
        return {"screen": "intro", "kept": coach_kept}
    name, given = (posted.get("name") or "").strip(), checklist_answers(questions, posted)
    if to == "intro":
        return {"screen": "intro", "name": name, "answers": given, "kept": coach_kept}
    if to != "save":  # ✨ on the coach's details, the name is checked with their email, where it can be put right
        try:
            name = candidate_name_from_form(posted)
        except AnswerRefused as refused:
            return {"screen": "intro", "name": name, "answers": given, "refusal": str(refused), "kept": coach_kept}
    if to == "questions":
        return {"screen": "questions", "name": name, "answers": given}
    try:
        given = checklist_answers_from_form(questions, posted)
    except AnswerRefused as refused:
        return {"screen": "questions", "name": name, "answers": given, "refusal": str(refused)}
    outcome = checklist_outcome(questions, given)
    if outcome.verdict == "stop" or (outcome.verdict == "confirm" and to == "outcome"):
        return {"screen": outcome.verdict, "name": name, "answers": given, "outcome": outcome}
    # ✨ Going ahead: all Yes, or "I'm still confident" past a second thought.
    going_ahead = {"screen": "proceed", "name": name, "answers": given, "confident": bool(outcome.flagged)}
    if to != "save":
        return going_ahead
    try:
        return {"screen": "chosen", "coach": coach_from_form(posted)}
    except AnswerRefused as refused:
        return {**going_ahead, "confirmed": coach_confirmed(posted), "refusal": str(refused), "invalid": refused.field}


def _checklist_screen(
    text,
    screen="intro",
    name="",
    answers=None,
    outcome=None,
    refusal=None,
    confident=False,
    coach=None,
    confirmed=False,
    invalid=None,
    kept=None,
    issued=None,
):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters. On going ahead, whether
    the box was ticked, and which field a refusal is about; once chosen, the coach kept, with their link
    (`issued` is a link just issued, shown this once). On the intro while choosing again, `kept` is the coach who
    stays until another is saved."""
    answers = answers or {}
    # ✨ `asked` completes "Do you think <name>…" in one sentence; the flags keep the question as authored.
    questions = [
        {
            **question,
            "answer": answers.get(question["id"]),
            "asked": asked_in_a_sentence(question["question"]),
        }
        for question in text["questions"]
    ]
    flagged = set(outcome.flagged) if outcome else set()
    return {
        "screen": screen,
        "name": name,
        "answers": answers,
        "questions": questions,
        "count": apnumber(len(questions)),
        "flags": [question for question in questions if question["id"] in flagged],
        "critical_no": bool(outcome and outcome.critical_no),
        "confident": confident,
        "refusal": refusal,
        "coach": coach,
        "confirmed": confirmed,
        "invalid": invalid,
        "kept": kept,
        "link": _coach_link_state(coach["id"], issued) if screen == "chosen" and coach and "id" in coach else None,
    }


def _coach_kept(answers, block_id):
    """✨ The coach kept for a coach checklist, as {"name", "email", "id"}, or None: its answer is the one coach kept."""
    kept = answers.get(block_id)
    return kept[0] if kept else None


def _coach_link_state(contact_id, issued=None):
    """✨ The coach's link as the coach page shows it: the contact it is for, its invitation while it works, the coach's
    answer ("waiting" while a working link is unanswered, None with no link at all), whether the coach has said no by
    declining, and the link itself if it was just issued. An answer outlasts the link's expiry, but not its revoking:
    it belongs to the link it came through. A coach who withdraws their acceptance has no link to show: they are
    deleted as they withdraw (ADR 0024)."""
    invitation = Invitation.objects.filter(contact_id=contact_id).first()
    live = invitation if invitation is not None and invitation.works() else None
    answer = invitation.coach_answer if invitation is not None else None
    return {
        "contact_id": contact_id,
        "invitation": live,
        "answer": answer or ("waiting" if live else None),
        "said_no": answer == Invitation.CoachAnswer.DECLINED,
        "issued": issued["link"] if issued and issued["contact"] == contact_id else None,
    }


def _saved(request, state, section, block_id):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A block that opens what follows (a reading) lands at its confirmation, with what it opened beneath, rather than
    back at its top above what was just read (ticket 41e).

    With htmx, the status goes where the participant is looking, and the section's gate is brought up to date beside
    it, out of band: without the second part the button would stay as it was rendered, and someone who had just written
    enough to finish the section would have to reload before the engine would let them say so. htmx swaps everything
    but the gate into the status, so the templates' line breaks are trimmed: a quiet save's status must stay empty, or
    the row beneath a wizard's rating shows and moves the next statement down (fix-11).
    """
    page = page_of(section, block_id)
    block = next(block for block in section["blocks"] if block["id"] == block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(state, section, page)
        quietly = saves_quietly(state.version.document, section, block)
        status = render_to_string("engine/save_status.html", {**shown, "saves_quietly": quietly}, request).strip()
        gate = render_to_string("engine/completion.html", {**shown, "out_of_band": True}, request).strip()
        return HttpResponse(status + gate)
    return _see_other(f"{page_url(section['id'], page)}#{landing_of(block)}")


@login_required
@consent_required
def results(request, block_id):
    """✨ The participant's own stored result for a scored block, never recomputed and never anyone else's.

    Before there is a result, the participant is sent to the page of the block's section the sort is on. After, the
    page leads back to the section that one is a part of (ticket 41b), or else to the sort's own section, where it is
    completed.
    """
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    if _pairs_left(state.version.document, result):
        return redirect("tie_break", block_id)
    drawn = _results_drawn(state, result, block_id)
    context = {
        "drawn": drawn,
        "results": drawn["results"],
        "section": section,
        "finish": _results_finish(state, block_id),
        # ✨ How a refused finish comes back, as on a section's page (fix-2).
        "messages_after_a_press": messages_after_a_press(state.version.document),
    }
    return render(request, "engine/results.html", context)


def _results_finish(state, block_id):
    """✨ What the results page offers in place of "Compare with how others see you →", when its sort is the last
    thing in a part that is the last thing in its section, so the results are that section's end (ticket 88): the
    section's finish alone, as `_finish_of` gives it, the comparison and the way to invite people being the comparison
    signpost's, in the section after (fix-10). None otherwise, when the page offers the press on to the comparison."""
    document = state.version.document
    part = section_of(document, block_id)
    return _finish_of(state, part) if part["blocks"][-1]["id"] == block_id else None


def _invite(state):
    """✨ The way to invite people offered beside the press on to the comparison, wherever that press is offered
    (ticket 88, fix-3, fix-8), and on the comparison's own page while it waits (fix-16): Five trusted voices' page.
    Below the minimum it is `waiting` and its phrase says, while its card needs more links, how many answers are still
    needed, or else how many of the minimum have answered; the press is greyed then. From the minimum the
    phrase is empty. None for a pathway without that card or while it is locked, where the press is offered alone, as
    before."""
    answered, minimum = _answered(state.response), minimum_observers(state.version.document)
    hub = _hub_of(state)
    voices = _hub_voices(state, hub)
    if voices is None:
        return None
    if answered >= minimum:
        return Invite(page_url(voices["section"]), "")
    if voices["more_needed"]:
        # ✨ Answers still needed, not the voices card's links (29 Oct): one link out unanswered still needs three.
        still = minimum - answered
        phrase = f"Still need answers from {still} {'person who knows' if still == 1 else 'people who know'} you"
    else:
        phrase = comparison_status(answered, minimum, viewed=False)[1]
    return Invite(page_url(voices["section"]), phrase, waiting=True)


def _results_drawn(state, result, block_id):
    """✨ The participant's own results for a sort as both its results page and a `sort_results` block draw them
    (`engine/own_results.html`), or None while there are none to show: before the sort is in, or while tie-break pairs
    are left (ticket 57). Like the results page, it stores the re-weighted result the first time it is shown."""
    document = state.version.document
    if result is None or _pairs_left(document, result):
        return None
    scores = _scores_shown_storing_reweighted(document, result)
    name = name_shown_for(state.response.participant)
    return {"results": results_page(document, scores, state.answers[block_id], name), "block_id": block_id}


@login_required
@consent_required
@require_http_methods(["GET", "POST"])
def tie_break(request, block_id):
    """✨ The tie-break's next unanswered pair (ticket 30b), for a participant whose own sort left one framework or both
    too close to call; anyone else, or one who has answered or skipped every pair, goes on to their results. Answering stores the
    choice beside the sort's result, "Both are right" as given beside the skip (ticket 108), and comes back here for the
    next. Only the participant's own result is read, so an observer's sort never leads here."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    plan = pair_plan(state.version.document, result.scores)
    if request.method == "POST":
        try:
            place = int(request.POST.get("pair", ""))
        except ValueError:
            place = -1
        chosen = request.POST.get("chosen") or None
        # ✨ "Both are right" (ticket 108) chooses neither, as the skip does, and only where the version offers it.
        both = request.POST.get("both") == "true"
        offers_both = "both" in state.version.document.get("presentation", {}).get("tie_break", {})
        if (
            not 0 <= place < len(plan)
            or (chosen is not None and chosen not in plan[place]["constructs"])
            or (both and (chosen is not None or not offers_both))
        ):
            refusal = "That is not one of this pair’s answers."
            # ✨ Without JavaScript, the next pair again, saying why (fix-2); with every pair answered, a page of its own.
            left = len(result.tie_break_answers) < len(plan)
            page = (lambda status: _pair_shown(request, state, result, block_id, plan, status, refusal)) if left else None
            return _refused(request, refusal, status=400, page=page)
        # ✨ A pair already answered (a form sent twice, or from a stale tab) stores nothing; either way the next is shown.
        result.answer_pair(place, plan[place], chosen, both=both)
        _scores_shown_storing_reweighted(state.version.document, result)  # ✨ the last answer re-weights the result
        if not _pairs_left(state.version.document, result):
            _participant(request.user)  # ✨ the evaluation has ended, so a section it ends completes now (ticket 119)
        return _see_other(_with_demo_profile(request, reverse("tie_break", args=[block_id])))
    if len(result.tie_break_answers) >= len(plan):
        return redirect("results", block_id)
    return _pair_shown(request, state, result, block_id, plan)


def _pair_shown(request, state, result, block_id, plan, status=200, refusal=None):
    """✨ The tie-break's next unanswered pair, with `refusal`, a press refused without JavaScript, said above it."""
    shown = pair_page(state.version.document, plan, len(result.tie_break_answers))
    # ✨ Demo only (fix-23): after a demo profile's sort, its guide beside the pair.
    demo = _demo_prefill(request, state.version.document)
    context = {"pair": shown, "block_id": block_id, "demo": demo, "refusal": refusal}
    return render(request, "engine/tie_break.html", context, status=status)


def _signposted_pairs_left(state, block):
    """✨ For a section signpost, whether the section it leads to holds a sort that is in with tie-break pairs still to
    answer or skip: its evaluation has not ended, so the signpost keeps its own wording, its button leading through
    that section and the results on to the next pair, rather than saying it is finished (hand check of 18 Nov). False
    for any other block, and for a section with no sort or none in yet."""
    if block["type"] != "section_signpost" or state.response is None:
        return False
    document = state.version.document
    linked = section_by_id(document, block["section"]) or {"blocks": []}
    sort = next((other["id"] for other in linked["blocks"] if BLOCK_TYPES[other["type"]].scored), None)
    result = Result.objects.filter(response=state.response, block_id=sort).first() if sort else None
    return result is not None and _pairs_left(document, result)


def _pairs_left(document, result):
    """✨ Whether the participant still has tie-break pairs to answer or skip before their results (ticket 30b)."""
    return len(result.tie_break_answers) < len(pair_plan(document, result.scores))


def _scores_shown_storing_reweighted(document, result):
    """✨ The participant's result as their results page and comparison show it (ticket 30c): re-weighted by the
    tie-break's answers once every pair is answered or skipped, or else the sort's as scored. The re-weighted result
    is worked out and stored beside the sort's the first time it is needed, so this writes, on a GET too."""
    if result.reweighted is None and pair_plan(document, result.scores) and not _pairs_left(document, result):
        result.keep_reweighted(reweigh(document, result.scores, result.tie_break_answers))
    return result.shown


@login_required
@consent_required
def comparison(request, block_id):
    """✨ The participant's self-result beside the observer average (ADR 0005), open to anyone with a result, whatever
    sections they have done, save where a section holds a comparison signpost to the sort: the comparison is then that
    section's, refused while it is locked, as its pages are (fix-19). Below the minimum it shows how many have
    answered and no numbers; it never shows which person has answered, and single observers' percents only in the
    distribution strip, in ascending order. From the minimum, the numbers show only while answer collection is frozen
    (ADR 0017): before the press that looks, and again once withdrawals unfreeze collection, this address shows that
    press and its warning in their place, so loading it, from the menu or a typed address, never looks
    (sprint-3d-r1-fix-1)."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    if _comparison_locked(state, block_id):
        return redirect("hub")
    return _comparison_shown(request, state, result, section, block_id)


def _comparison_shown(request, state, result, section, block_id, status=200, share_refusal=None):
    """✨ The comparison page, from `_own_result`'s state, result and section, with `share_refusal`, a refused tick of the
    coach's box sent without JavaScript, said above the box (fix-2). Below the minimum, where the pathway has a Five
    trusted voices card, `invite` is the way to it, and the page waits on answers with it in place of its refusal
    (fix-16); otherwise None, and the refusal stands, as in the faithful port.

    From the minimum while answer collection is open (`ready`), `warning` is the freeze warning, which the page says
    beneath the press that looks, as Section 2's card does (ticket 106); where the document asks on a page of its own
    instead, as the faithful port does, the page is that one, "Before you look", unless a refused tick is to be said
    (sprint-3d-r1-fix-1)."""
    document = state.version.document
    scores = _scores_shown_storing_reweighted(document, result)
    shown = _comparison_of(state.response, scores, state.answers[block_id])
    warning = _freeze_warning(state.response, shown["observers"], shown["minimum"]) if shown["ready"] else None
    if warning and not warns_beside_the_press(document) and share_refusal is None:
        context = {"block_id": block_id, "warning": warning}
        return render(request, "engine/comparison_confirm.html", context, status=status)
    sort = next(block for block in blocks_of(document) if block["id"] == block_id)
    invite = _invite(state) if shown["frameworks"] is None else None
    context = {
        "heading": _comparison_title(document, block_id),
        "comparison": shown,
        "warning": warning,
        "invite": invite if invite and invite.waiting else None,
        "block_id": block_id,
        "coach": _coach_sharing(state.response, block_id),
        "brief": coach_brief(sort),
        "back": _section_holding_comparison_signpost(state, block_id) or section["back"],
        "onward": _reflection_after_comparison(state, block_id),
        "share_refusal": share_refusal,
    }
    return render(request, "engine/comparison.html", context, status=status)


@login_required
@consent_required
@require_POST
def share_with_coach(request, block_id):
    """✨ The comparison's "Give my coach access to my results and this comparison", ticked or not (ticket 27). Ticking is refused until the
    participant has visited their comparison and their coach has accepted through a link that still works; the consent
    is then kept on that link, so it goes with it (ADR 0011). Unticking withdraws it at once, whatever else holds.

    The box saves as it changes: with htmx, "Saved" and the line under it for the new state; without, the comparison
    again, at the box. A refusal without JavaScript is the comparison again, saying why (fix-2), or before there is a
    result, and so no comparison, a page of its own."""
    state, result, section = _own_result(request.user, block_id)
    if request.POST.get("share") != "on":
        Invitation.withdraw_results_from_coach(request.user)
    else:
        visited = result is not None and block_id in state.response.comparisons_visited
        if not (visited and Invitation.share_results_with_coach(state.response)):
            refusal = "Your coach can see this only once they have accepted and you have seen your comparison."

            def its_page(status):
                return _comparison_shown(request, state, result, section, block_id, status, share_refusal=refusal)

            return _refused(request, refusal, status=403, page=its_page if result is not None else None)
    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/coach_share_saved.html", {"coach": _coach_sharing(state.response, block_id)})
    return _see_other(f"{reverse('comparison', args=[block_id])}#coach-share")


def _comparison_of(response, scores, sort, role="participant", name=""):
    """✨ The comparison of one participant's result with their observers, as both they and their coach see it, worded
    for `role`, the coach's about the participant by `name` (ticket 118). The
    observers' answers are worked into it only while answer collection is frozen, which the participant's look does
    (ADR 0017): with the minimum in while it is open, it is `ready`, with a count and no numbers, as below the minimum,
    so neither they nor their coach can see what one more answer adds (sprint-3d-r1-fix-1)."""
    document = response.version.document
    assessments = ObserverResponse.assessments_for(response)
    if response.collection_frozen_at is not None:
        average = aggregate(document, assessments.assessments)
    else:
        average = {"observers": len(assessments.assessments), "frameworks": None}
    shown = comparison_page(document, scores, sort, average, role, name)
    shown["ready"] = response.collection_frozen_at is None and shown["observers"] >= shown["minimum"]
    # ✨ Below the minimum, or before the look, there is no comparison on the page to call illustrative.
    shown["illustrative"] = assessments.all_test_data and shown["frameworks"] is not None
    return shown


def _coach_sharing(response, block_id):
    """✨ The participant's coach as the comparison's consent needs them, or None when there is nothing to say: with
    `offer` "tick" once they accepted through a working link and the comparison was visited by its button; "expired"
    when they accepted but the link no longer works; "awaiting" while they have not answered or have no link yet. A
    coach who declined is offered nothing here: the coach page already says so. One who withdrew their acceptance is no
    coach at all, deleted as they withdrew (ADR 0024)."""
    coach = _coach_of(response)
    if coach is None:
        return None
    if coach["can_see"]:
        offer = "tick" if block_id in response.comparisons_visited else None
    elif coach["answer"] == Invitation.CoachAnswer.ACCEPTED:
        offer = "expired"
    elif coach["answer"] in ("waiting", None):
        offer = "awaiting"
    else:
        offer = None
    return {**coach, "offer": offer} if offer else None


def _coach_of(response, answers=None):
    """✨ The coach kept, as the hub and the comparison read them, or None: their name, the coach page, their answer as
    the coach page tells it, whether they can be shown the results (accepted through a working link) and whether they
    are. The answer is read from the `answers` the gate reads (the response's own, if not given), as a `coach_accepted`
    clause reads it, so the hub's wording and Section 4's lock never disagree (fix-2)."""
    coach = response.contacts.filter(role=Contact.Role.COACH).first() if response is not None else None
    if coach is None:
        return None
    if answers is None:
        answers = response.answers_with_contacts_and_visits()
    accepted = Invitation.accepted_coach_of(response)
    return {
        "name": coach.name,
        "coach_page": _listed_at(coach),
        "answer": coach_answer(answers, coach.block_id),
        "can_see": accepted is not None,
        "shared": accepted is not None and accepted.results_shared_at is not None,
    }


def _hub_voices(state, hub):
    """✨ The Five trusted voices card (ticket 51a): the hub's side card whose section holds a contact list, or None for
    a pathway without one, or while it is locked, when it is drawn as any other side card. What it shows is the contact
    list's `voices_card`; this reads what that needs, and the section's own page lists everyone."""
    document = state.version.document
    for block in blocks_of(document):
        if block["type"] != "contact_list":
            continue
        section_id = section_of(document, block["id"])["id"]
        card = next((side_card for side_card in hub.side_cards() if side_card.id == section_id), None)
        if card is None or card.is_locked:
            continue
        invited = state.answers.get(links_issued_key(block["id"]), 0)
        answered = _answered(state.response) if state.response else 0
        withdrew = state.response.observers_withdrew if state.response else 0
        declined = ObserverResponse.declined(state.response) if state.response else 0
        minimum = minimum_observers(document)
        frozen = _frozen(state.response)
        shown = voices_card(block, card, invited, answered, minimum, frozen, withdrew=withdrew, declined=declined)
        return {"section": section_id, **shown}
    return None


def _answered(response):
    """✨ How many observers' assessments of a participant's `response` are in and count toward the minimum, as every
    count on the way to the comparison reads it (`ObserverResponse.counted`)."""
    return ObserverResponse.counted(response)


def _freeze_warning(response, answered, minimum):
    """✨ The warning a press on to the comparison carries (`freeze_warning`) while it would freeze answer collection:
    with `answered`, the observer assessments in, at least the `minimum` and collection not yet frozen; None
    otherwise. Those who declined have replied too, and are waited on no longer (ticket 120)."""
    if response.collection_frozen_at is not None or answered < minimum:
        return None
    replied = answered + ObserverResponse.declined(response)
    return freeze_warning(replied, response.contacts.filter(role=Contact.Role.CONTACT).count())


@login_required
@consent_required
@require_POST
def visit_comparison(request, block_id):
    """✨ The results page's "Compare with how others see you →": record the visit Section 1's gate waits on, then go to
    the comparison. Recorded whatever the comparison will show, since the explanation below the minimum counts too
    (ticket 16c). Only this press counts, never loading the comparison's address, which a browser may do ahead of
    time (Chrome preloads from the address bar) without the participant ever seeing it.

    With at least the minimum number of observer assessments in, and collection not yet frozen, the press first asks:
    how many of the people invited have answered, and that once they look no more answers are added. Its button
    confirms, which freezes collection, then goes on as before (ticket 55). Below the minimum nothing is asked. Where
    the document puts that warning beside the press (`warns_beside_the_press`), the press is the look: it freezes
    collection and goes on with no page between (ticket 106).

    A press with the minimum in, confirmed or with collection already frozen, is also the view a comparison signpost's
    "Viewed" reads (ticket 67a), kept once withdrawals unfreeze collection. Only this press freezes, so only it shows
    the observers' numbers: the comparison's own address offers it while collection is open (sprint-3d-r1-fix-1)."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return _see_other(page_url(section["id"], section["page"]))
    if _comparison_locked(state, block_id):
        return _to_the_hub_when_locked(request)  # ✨ nothing recorded or frozen, as on the page itself (fix-19)
    response = state.response
    answered, minimum = _answered(response), minimum_observers(state.version.document)
    if response.collection_frozen_at is None and answered >= minimum:
        asks = not warns_beside_the_press(state.version.document)
        if asks and request.POST.get("confirmed") != "yes":
            context = {"block_id": block_id, "warning": _freeze_warning(response, answered, minimum)}
            # ✨ No `back`: the button leads to the hub, as a section's does, since the page is reached from the hub's
            # cards and the sidebar as well as from the results page (fix-21).
            return render(request, "engine/comparison_confirm.html", context)
    # ✨ The freeze is counted again under its lock: a withdrawal since may have left fewer than the minimum.
    response.look_at_comparison(block_id)
    return _see_other("comparison", block_id)


@login_required
@consent_required
@require_POST
def demo_shortcut(request):
    """✨ Demo only (ticket 113): the hub's hidden control, completing what the section chosen needs to open, and only
    that (`demo_shortcuts.open_section`), then back to the hub with no message. A section not offered now, as one
    opened since the hub was drawn, is left as it is. Off a development or demo system there is no such control, so it
    is a 404; something it can't make up without changing what the participant has is refused, keeping nothing."""
    if not demo_shortcuts.tools_on():
        raise Http404("There are no demo shortcuts here.")
    state = _participant(request.user)
    if state.version is None or _wizard_due(state) is not None:
        return _see_other("hub")  # ✨ the hub sends them on, as it would without the press
    section = _section_or_404(state.version, request.POST.get("section", ""))
    hub = _hub_of(state)
    if section["id"] in {offered.id for offered in demo_shortcuts.offered(state.version.document, hub)}:
        try:
            demo_shortcuts.open_section(state.stored_response(request.user), section["id"])
        except demo_shortcuts.CannotMakeUp:
            return _refused(request, DEMO_SHORTCUT_REFUSED, status=409)
    return _see_other("hub")


# ✨ What the hub's demo shortcut says when it can't open a section without changing what the participant has.
DEMO_SHORTCUT_REFUSED = "The demo shortcut can't open that section without changing what you've already done."


@login_required
@consent_required
@require_http_methods(["GET", "POST"])
def retake(request, block_id):
    """✨ The results page's quiet "Retake the strengths evaluation" asks first, saying what will be cleared, and warning
    that what the people invited sent will be deleted; only its button clears the participant's own sort and everything
    worked out from it (`Response.clear_sort`), then opens the sort afresh (29 Oct). The sections they finished stay
    finished. It is the same on every system, and offers no demo profile.

    Before any sort, on a development or demo system alone, the same address is where the sort page's hidden link leads,
    to load a demo profile (fix-21): one of `seed_tie_break`'s starting profiles, and how to answer its pairs, chosen
    apart (fix-25), as a combination that holds on this pathway, only for a participant the sort is open to. The sort
    then opens with the profile's cards placed and its sliders set, beside its guide to those answers, and nothing is
    stored until the participant sends it (fix-23). Off a demo system there is nothing here before a sort, so it is a
    404. A combination not offered, as none is with a sort in, is refused with its reason and nothing cleared."""
    state, result, section = _own_result(request.user, block_id)
    demo_profiles = result is None
    if demo_profiles and not demo_shortcuts.tools_on():
        raise Http404("There is no self-assessment to retake yet.")
    sort_page = page_url(section["id"], section["page"])
    document = state.version.document
    # ✨ Before any sort, only a participant the sort is open to may have one loaded for them (fix-21).
    if result is None and not _is_open(state, section_of(document, block_id), answerable_block(document, block_id)):
        return redirect(sort_page)
    # ✨ Worked out on every visit, so a combination that does not hold on this pathway is never offered (fix-21).
    offer = scenario_loading.offered(document) if demo_profiles else scenario_loading.Offered([], [], (), [])
    response = state.response

    def this_page(status=200, refusal=None):
        """✨ The page asking, with `refusal`, a choice refused without JavaScript, said above the choice (fix-2)."""
        context = {
            "block_id": block_id,
            "clearing": result is not None,
            "back": (
                {"title": "results", "href": reverse("results", args=[block_id])}
                if result is not None
                else {"title": "the sort", "href": sort_page}
            ),
            "sort_page": sort_page,
            "offer": offer,
            # ✨ None or 0 when nobody has sent anything, which leaves nothing to warn of. Every send, counting or not
            # (sprint-3d-r1-fix-1), and every decline (ticket 120), since the retake deletes them all and those people
            # are asked again.
            "answered": ObserverResponse.sent_count(response) if result is not None else None,
            "declined": ObserverResponse.declined(response) if result is not None else None,
            "tie_break": bool(result and result.tie_break_answers),
            "coach_shown": result is not None and bool((_coach_of(response) or {}).get("shared")),
            "refusal": refusal,
        }
        return render(request, "engine/retake.html", context, status=status)

    if request.method == "POST":
        profile = request.POST.get(scenario_loading.PROFILE_FIELD, MYSELF)
        answers = request.POST.get(scenario_loading.ANSWERS_FIELD) or None
        refusal = None if profile == MYSELF else scenario_loading.refusal(offer, profile, answers)
        if refusal is not None:
            # ✨ Without JavaScript, this page again, saying why, with nothing cleared (fix-2).
            return _refused(request, refusal, status=400, page=lambda status: this_page(status, refusal))
        if result is not None:
            response.clear_sort(block_id)
        if profile == MYSELF:
            return _see_other(sort_page)
        # ✨ Nothing stored: the sort starts from the profile, and the participant sends it themselves (fix-23).
        return _see_other(f"{sort_page}?{scenario_loading.demo_query(profile, answers)}")
    return this_page()


# ✨ No demo profile: what the retake's button sends, as it carries no choice (fix-21; 29 Oct).
MYSELF = "myself"

def _demo_prefill(request, document):
    """✨ Demo only (fix-23): the demo profile and answers the address names (fix-25), as `scenario_loading.prefill`
    gives them, or None: off a development or demo system, with no profile named, or with a combination not offered on
    this pathway."""
    profile = request.GET.get(scenario_loading.PROFILE_FIELD)
    if not profile or not demo_shortcuts.tools_on():
        return None
    return scenario_loading.prefill(document, profile, request.GET.get(scenario_loading.ANSWERS_FIELD) or None)


def _with_demo_profile(request, url):
    """✨ `url` naming the same demo profile and answers as this request's address, on a development or demo system
    (fix-23), so the pairs that follow a demo profile's sort show its guide too."""
    profile = request.GET.get(scenario_loading.PROFILE_FIELD)
    if not profile or not demo_shortcuts.tools_on():
        return url
    return f"{url}?{scenario_loading.demo_query(profile, request.GET.get(scenario_loading.ANSWERS_FIELD) or None)}"


def _own_result(user, block_id):
    """✨ The participant's state, their stored result for a scored block (None before they have one), and the section
    the sort is on with its page, and `back`, where the results and the comparison lead back to: the section that one
    is a part of, if it is one (ticket 41b), or else that section itself. A block that is not scored is a 404."""
    state = _participant(user)
    try:
        block = answerable_block(state.version.document, block_id) if state.version else None
    except UnknownBlock:
        block = None
    if block is None or not BLOCK_TYPES[block["type"]].scored:
        raise Http404("This pathway version has no scored block by that identifier.")
    section = section_of(state.version.document, block_id)
    result = Result.objects.filter(response=state.response, block_id=block_id).first()
    title, page = text_for(section["title"], "participant"), page_of(section, block_id)
    back = _section_this_is_part_of(state, section) or _way_back(section, page)
    return state, result, {"id": section["id"], "title": title, "page": page, "back": back}


@login_required
@consent_required
def download(request, block_id):
    """✨ A download block's file, served only to a participant who has reached the block, as a section's content is
    (ticket 40). The schema keeps the file's name to letters, digits and hyphens, so it cannot leave the folder."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "download")
    if not _is_open(state, section_of(state.version.document, block_id), block):
        return HttpResponseForbidden("This file opens once you reach it.")
    waiting = comparison_wait_message(block, state.answers)
    if waiting is not None:
        # ✨ Refused here, not only left off the page, as a reflection's save is (ADR 0019).
        return HttpResponseForbidden(waiting)
    path = settings.PATHWAY_FILES_DIR / block["file"]
    if not path.is_file():
        raise Http404("This pathway's file is not here.")
    return FileResponse(path.open("rb"), content_type="application/pdf", filename=block["file"])


@login_required
@consent_required
def photo(request, section_id):
    """✨ The photo the published pathway names for a section, a file beside the document (ticket 49b). Only a file the
    document names as a photo is served, and the schema keeps its name to letters, digits and hyphens, so it cannot
    leave the folder."""
    state = _participant(request.user)
    named = state.version.document.get("photos", {}).get(section_id) if state.version else None
    if named is None:
        raise Http404("This pathway has no photo for that section.")
    path = settings.PATHWAY_FILES_DIR / named["file"]
    if not path.is_file():
        raise Http404("This pathway's photo is not here.")
    return FileResponse(path.open("rb"), content_type=mimetypes.guess_type(path.name)[0])


@login_required
@consent_required
def invitations(request):
    """✨ The old address of the invitations page, which is now the contact list's own page (ticket 51a): the first
    contact list the participant has reached, or else the hub."""
    state = _participant(request.user)
    document = state.version.document if state.version else None
    for block in blocks_of(document) if document else ():
        if block["type"] == "contact_list" and _is_open(state, section_of(document, block["id"]), block):
            return redirect(_block_address(document, block["id"]))
    return redirect("hub")


@login_required
@consent_required
@require_POST
def contacts(request, block_id):
    """✨ Add one person to a contact list, and make their observer's link in the same act (ticket 51a), so nobody is
    listed without having had one. Then back to the list at them, which shows the link this once. Nobody else on the
    list is touched, so a page left open since someone else was added never drops them. Without JavaScript the press
    carries the whole list, and saves edits to people listed with it (fix-1, `_link_with_the_list`)."""
    state = _participant(request.user, first_version=lambda: _published_version(request.POST.get("version")))
    block = _block_of_type(state.version, block_id, "contact_list")
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    if _frozen(state.response):
        return _refuse_frozen(request, state, block)
    typed = [] if _is_htmx(request) else _typed_rows(request)
    if typed:
        return _link_with_the_list(request, state, block, typed)
    try:
        person = contact_from_form(*_typed_for_new(request))
    except AnswerRefused as refused:
        return _person_refused(request, state, block, refused)
    lifetime = link_lifetime(state.version.document)
    added = state.stored_response(request.user).add_contact(block_id, person, lifetime, MAX_CONTACTS)
    if added is None:
        return _person_refused(request, state, block, AnswerRefused(LIST_FULL))
    person, token = added
    link = _link_of(request, person, token)
    if _is_htmx(request):
        # ✨ In place of the row they were typed into, and nothing more: filling every row adds none, as "Add another
        # person" does that (ticket 70).
        state = _participant(request.user)
        rows = _contact_rows(block, state.answers, {"contact": person.pk, "link": link})
        added_row = _as_typed_in(request, block, next(row for row in rows if row["contact_id"] == person.pk))
        return _rows_sent_back(request, state, block, [added_row])
    return _back_with_issued(request, person, link)


def _link_with_the_list(request, state, block, typed):
    """✨ "Get link" pressed without JavaScript, the whole list sent with it (fix-1): the edits typed to people listed
    are saved, as their own Save would, and the person typed in the row pressed is added with their link, all or none.
    A refusal, theirs or an edit's, comes back in its row with every row as typed. Then back to the list at them, as
    ever, with what was typed in the other empty rows in the cookie that carries their link (ADR 0020).

    Too much typing to fit in that cookie, and the list's page is drawn here instead, with their link and every row as
    typed, never cached. A reload sends the press again, so the list's form carries a `press` (`_press_of`), and a press
    that already added that person (`_repeated_press`) adds nobody again: the page comes back with them listed."""
    pressed = request.POST.get("row", "")
    new = next((row for row in typed if row["person"] is None and str(row["number"]) == pressed), None)
    others = [row for row in typed if row["person"] is None and row is not new]
    repeated = _repeated_press(request, block, new)
    if repeated is not None:
        return _list_page(request, _participant(request.user), block, 200, kept=others)
    edits, refusals = _edits_of(state, block, typed)
    try:
        person = contact_from_form(new["name"] if new else "", new["email"] if new else "")
    except AnswerRefused as refused:
        if new is None:
            return _press_refused(request, state, block, typed, refusals, refusal=str(refused))
        refusals[new["number"]] = refused
    if refusals:
        return _press_refused(request, state, block, typed, refusals)
    with transaction.atomic():
        _save_edits(edits)
        added = state.stored_response(request.user).add_contact(
            block["id"], person, link_lifetime(state.version.document), MAX_CONTACTS
        )
        if added is None:
            transaction.set_rollback(True)
    if added is None:
        return _press_refused(request, state, block, typed, {}, refusal=LIST_FULL)
    person, token = added
    _remember_press(request, person)
    link = _link_of(request, person, token)
    kept = [{"name": row["name"], "email": row["email"]} for row in others]
    if len(json.dumps({"contact": person.pk, "link": link, "kept": kept})) <= ISSUED_COOKIE_MOST:
        return _back_with_issued(request, person, link, kept=kept)
    issued = {"contact": person.pk, "link": link}
    drawn = _list_page(request, _participant(request.user), block, 200, kept=others, issued=issued)
    drawn["Cache-Control"] = "no-store"
    return drawn


def _typed_rows(request):
    """✨ What a press of the list's one form sent from each of its rows, in order, as {"number", "person" (None for an
    empty row), "drawn", "name", "email"} (fix-1): none for a press that sent one person alone."""
    keys = ("number", "person", "drawn", "name", "email")
    return [
        {
            "number": int(number),
            "person": int(person) if person.isdigit() else None,
            "drawn": drawn,
            "name": name,
            "email": email,
        }
        for number, person, drawn, name, email in zip(*(request.POST.getlist(key) for key in keys))
        if number.isdigit()
    ]


def _typed_for_new(request):
    """✨ The name and email address typed for someone new: in the row whose "Get link" was pressed (`row`), among all
    the rows sent, or else the one person sent."""
    pressed = request.POST.get("row")
    typed = next((typed for typed in _typed_rows(request) if str(typed["number"]) == pressed), None)
    if typed is not None:
        return typed["name"], typed["email"]
    return request.POST.get("name"), request.POST.get("email")


def _drawn(name, email):
    """✨ A short fingerprint of a person as a row showed them, sent back with it, so a press saves only the rows
    changed since the page was drawn: a page left open never puts back what another tab has since saved (fix-1)."""
    return hashlib.sha256(f"{name}\0{email}".encode()).hexdigest()[:16]


def _edits_of(state, block, typed):
    """✨ The edits typed to people listed, sent with a press of the list's one form (fix-1), as ([(their identifier,
    what to save)], {row number: why it is refused}): only rows changed since the page was drawn, each checked as their
    own Save checks it. Someone taken off the list since is passed over."""
    changed = [row for row in typed if row["person"] is not None and _drawn(row["name"], row["email"]) != row["drawn"]]
    on_list = set(
        Contact.objects.filter(
            response=state.response,
            block_id=block["id"],
            role=Contact.Role.CONTACT,
            pk__in=[row["person"] for row in changed],
        ).values_list("pk", flat=True)
    )
    edits, refusals = [], {}
    for row in changed:
        if row["person"] not in on_list:
            continue
        try:
            edits.append((row["person"], contact_from_form(row["name"], row["email"])))
        except AnswerRefused as refused:
            refusals[row["number"]] = refused
    return edits, refusals


def _save_edits(edits):
    """✨ Save each edit from `_edits_of`, the person's link still working."""
    for contact_id, fields in edits:
        Contact.objects.filter(pk=contact_id).update(**fields)


def _saved_with_the_list(request, state, block, typed, asked=0, back=None):
    """✨ A press of the list's one form without JavaScript that adds nobody (fix-1): the edits typed to people listed
    saved, all or none, then the list's page drawn here, at least `asked` rows, with what was typed in the empty rows
    back in them, since it is kept nowhere. Sending it again saves the same again. With nothing typed in them, a
    redirect to `back`, if given, as Save made before: only empty rows are left behind."""
    edits, refusals = _edits_of(state, block, typed)
    if refusals:
        return _press_refused(request, state, block, typed, refusals)
    _save_edits(edits)
    state = _participant(request.user)
    kept = [row for row in typed if row["person"] is None]
    if back and not any(row["name"] or row["email"] for row in kept):
        return _see_other(back)
    return _list_page(request, state, block, 200, asked=asked, kept=kept)


def _press_refused(request, state, block, typed, refusals, refusal=None):
    """✨ The list's page again after a press of its one form was refused, nothing from it stored (fix-1): every row as
    typed, each refused one with why and the field at fault, or `refusal` on the list's own line."""
    kept = [
        {**row, "refusal": str(refusals[row["number"]]), "invalid": refusals[row["number"]].field}
        if row["number"] in refusals
        else row
        for row in typed
    ]
    return _list_page(request, state, block, 400, refusal=refusal, kept=kept)


# ✨ Where the session remembers which person each recent press of a contact list's form added, by its `press`, and
# how many it remembers: a press is one page drawn, so a handful covers any reload.
PRESSES_KEY = "contact_presses"
PRESSES_KEPT = 20


def _press_of(block, rows):
    """✨ What a contact list's form sends as `press`: a fingerprint of who it lists, so it changes as soon as a press
    adds anyone, and a press sent again by a reload is told from a new one (fix-1, `_repeated_press`). The same list
    draws the same page."""
    listed = ",".join(str(row["contact_id"]) for row in rows if row["contact_id"])
    return hashlib.sha256(f"{block['id']}:{listed}".encode()).hexdigest()[:16]


def _repeated_press(request, block, new):
    """✨ The person this press already added, if it is one sent again (a reload of the page it drew), or None: its
    `press` added them, and they are on this list still, as the row pressed has them (fix-1)."""
    added = request.session.get(PRESSES_KEY, {}).get(request.POST.get("press") or "")
    if added is None or new is None:
        return None
    try:
        person = contact_from_form(new["name"], new["email"])
    except AnswerRefused:
        return None
    return Contact.objects.filter(pk=added, block_id=block["id"], **person).first()


def _remember_press(request, person):
    """✨ Remember that this press added `person`, for `_repeated_press`: only identifiers, never their details."""
    press = request.POST.get("press")
    if not press:
        return
    presses = request.session.get(PRESSES_KEY, {})
    presses[press] = person.pk
    request.session[PRESSES_KEY] = dict(list(presses.items())[-PRESSES_KEPT:])


@login_required
@consent_required
@require_POST
def contact(request, block_id, contact_id):
    """✨ Change one person's name or email address, and theirs alone (ticket 51a), as the row saves on a change with
    JavaScript, or by its Save button without (fix-2). Their link keeps working. Another participant's contact, or one
    from another list, is a 404 that says nothing of whether it exists. Save without JavaScript sends the whole list,
    and saves every edit typed to it, the empty rows' typing coming back (fix-1, `_saved_with_the_list`)."""
    state, block, person = _listed_person(request, block_id, contact_id)
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    typed = [] if _is_htmx(request) else _typed_rows(request)
    if typed:
        return _saved_with_the_list(request, state, block, typed, back=_listed_at(person))
    try:
        changed = contact_from_form(request.POST.get("name"), request.POST.get("email"))
    except AnswerRefused as refused:
        return _person_refused(request, state, block, refused, contact_id=person.pk)
    Contact.objects.filter(pk=person.pk).update(**changed)
    if _is_htmx(request):
        state = _participant(request.user)
        return _rows_sent_back(request, state, block, [_listed_row(state, block, person.pk, saved=True)])
    return _see_other(_listed_at(person))


@login_required
@consent_required
def contact_removal(request, block_id, contact_id):
    """✨ Take one person off a contact list (ticket 13d), deleting them and their link; anything already sent through
    it stays (ADR 0007). Someone whose link still works is removed only once the participant has confirmed, having been
    told it will stop; opening this address, or pressing Remove for them, only asks. Then back to the list, or with
    JavaScript, their row alone: asking in it, then gone, an empty row in its place while the list still shows as many
    (fix-2)."""
    state, block, person = _listed_person(request, block_id, contact_id)
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    confirmed = request.method == "POST" and (
        request.POST.get("confirmed") == "yes" or person.live_invitation() is None
    )
    is_htmx = request.method == "POST" and _is_htmx(request)
    if not confirmed and is_htmx:
        return _rows_sent_back(request, state, block, [_listed_row(state, block, person.pk, confirming=True)])
    if not confirmed:
        back = {"title": "your list", "href": _listed_at(person)}
        context = {"person": person, "back": back, "has_live_link": person.live_invitation() is not None}
        return render(request, "engine/contact_removal.html", context)
    number = _listed_row(state, block, person.pk)["number"] if is_htmx else None
    person.delete()  # ✨ their invitation goes with them
    if is_htmx:
        state = _participant(request.user)
        held = len(state.answers.get(block_id) or [])
        if rows_of(block, held) < rows_of(block, held + 1):
            return _rows_sent_back(request, state, block, [])
        return _rows_sent_back(request, state, block, [_empty_row(block, number)])
    return _see_other(_block_address(state.version.document, block_id))


@login_required
@consent_required
@require_POST
def another_row(request, block_id):
    """✨ "Add another person" below a contact list's rows (ticket 70): one more empty row, storing nobody, since its
    "Get link" adds the person as any empty row's does. With JavaScript, that row alone, to go after the others, with
    the control again counting it, so nothing typed in any other row is touched; without, the list's page again
    showing one more row than the page it was pressed on (`rows`), with the edits typed to people listed saved and
    what was typed in each empty row back in it (fix-1, `_saved_with_the_list`). Refused, with nothing saved, once the
    list shows the most it may hold, and while answer collection is frozen, when nobody can be added."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "contact_list")
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    if _frozen(state.response):
        return _refuse_frozen(request, state, block)
    shown = rows_of(block, len(state.answers.get(block_id) or []), _posted_count(request, "rows"))
    if not can_add_row(shown):
        return _refused(
            request,
            LIST_FULL,
            status=400,
            page=lambda status: _list_page(request, state, block, status, LIST_FULL, kept=_typed_rows(request)),
        )
    number = shown + 1
    if _is_htmx(request):
        context = {
            "row": _empty_row(block, number),
            "block": {"id": block_id, "rows_shown": number, "adds_rows": can_add_row(number)},
            "pathway": {"version_id": state.version.pk},
        }
        return render(request, "engine/contact_row_added.html", context)
    return _saved_with_the_list(request, state, block, _typed_rows(request), asked=number)


def _listed_person(request, block_id, contact_id):
    """✨ The participant's state, a contact list block and one person on it, or a 404 that says nothing of whether
    another participant has a contact by that number, or this one on another list."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "contact_list")
    person = _own_contact_or_404(request.user, contact_id)
    if person.block_id != block_id or person.role != Contact.Role.CONTACT or person.response != state.response:
        raise Http404("You have no contact by that number on this list.")
    return state, block, person


def _list_shut(request, state, block):
    """✨ The refusal for a change to a contact list the participant has not reached, or None while it is open to change.
    A completion never fixes a contact list: only an agreement scale can be marked `fixed_once_complete`."""
    if not _is_open(state, section_of(state.version.document, block["id"]), block):
        return _refused(request, NOT_OPEN, status=403)
    return None


def _person_refused(request, state, block, refused, contact_id=None):
    """✨ The list's page again, saying why one person was not saved, with what was typed in their row (or, for someone
    new, the first empty one) and the field at fault marked, so nothing typed is lost. A press that sent the whole list
    without JavaScript is refused by `_press_refused` instead (fix-1)."""
    name, email = (request.POST.get("name"), request.POST.get("email")) if contact_id else _typed_for_new(request)
    typed = {
        "contact_id": contact_id,
        "name": name or "",
        "email": email or "",
        "refusal": str(refused),
        "invalid": refused.field,
    }
    if _is_htmx(request):
        # ✨ Their row alone, as typed, where they typed it (fix-2).
        rows = _contact_rows(block, state.answers, typed=typed)
        row = next((row for row in rows if row["contact_id"] == contact_id), None) or _empty_row(block, 0)
        row = _as_typed_in(request, block, {**row, **{key: typed[key] for key in typed if key != "contact_id"}})
        return _rows_sent_back(request, state, block, [row], status=400)
    # ✨ As many rows as the page they typed in had shown, so a row "Add another person" added is still there
    # (ticket 70).
    asked = _posted_count(request, "row")
    section = section_of(state.version.document, block["id"])
    rows_back = {block["id"]: {"typed": typed, "asked": asked}}
    shown = _section_page(state, section, page_of(section, block["id"]), rows_back=rows_back)
    on_page = _on_page(shown, block["id"])
    if not any(row.get("refusal") for row in on_page["rows"]):
        on_page["refusal"] = str(refused)
    return _section_shown(request, state, section, shown, status=400)


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _rows_sent_back(request, state, block, rows, status=200):
    """✨ Rows of a contact list alone, as one of its buttons sends them back with JavaScript, to take that row's place
    (fix-2): never the page, so typing not yet saved in another row is kept. Never cached, since a row may hold a link
    just issued."""
    shown_block = {
        "id": block["id"],
        "frozen": RESULTS_SEEN if _frozen(state.response) else None,
    }
    context = {"rows": rows, "block": shown_block, "pathway": {"version_id": state.version.pk}}
    sent = render(request, "engine/contact_rows.html", context, status=status)
    sent["Cache-Control"] = "no-store"
    return sent


def _listed_row(state, block, contact_id, issued=None, **marks):
    """✨ One person's row as the list shows it, with `issued`, their link just issued, and any `marks` (saved, or asking
    before they are removed)."""
    issued_for = {"contact": contact_id, "link": issued} if issued else None
    row = next(row for row in _contact_rows(block, state.answers, issued_for) if row["contact_id"] == contact_id)
    return {**row, **marks}


def _empty_row(block, number):
    """✨ An empty row of a contact list, for the next person, at its place."""
    return {
        "number": number,
        "is_needed": number <= needed(block),
        "contact_id": None,
        "name": "",
        "email": "",
        "invitation": None,
        "issued": None,
    }


def _as_typed_in(request, block, row):
    """✨ A row sent back for someone new, numbered as the empty row they were typed into, which it replaces: the list's
    page numbers them in order once it is next drawn."""
    posted = request.POST.get("row", "")
    if not posted.isdigit():
        return row
    number = int(posted)
    return {**row, "number": number, "is_needed": number <= needed(block)}


@login_required
@consent_required
@require_POST
def issue_invitation(request, contact_id):
    """✨ Issue, or reissue, one contact's link (one that was lost or has expired), then go back to where that person is
    listed, which shows it this once: only its hash is kept. An observer is listed on their contact list's page; the
    coach on the coach page, and their link leads to the coach's own page rather than an observer's.

    A redirect, so a reload of the page that follows never issues again. The link travels to that page in a short-lived
    signed cookie of the participant's own, not in the address (where the history would keep it) or the session (where
    the database would).

    While answer collection is frozen an observer's link is neither issued nor reissued; a coach's still is (ticket 55).
    """
    contact = _own_contact_or_404(request.user, contact_id)
    if contact.role == Contact.Role.CONTACT and _frozen(contact.response):
        state = _participant(request.user)
        return _refuse_frozen(request, state, _block_of_type(state.version, contact.block_id, "contact_list"))
    link = _issue_link(request, contact)
    if contact.role == Contact.Role.CONTACT and _is_htmx(request):
        return _person_row_sent_back(request, contact, issued=link)  # ✨ with the link in it (fix-2)
    return _back_with_issued(request, contact, link)


def _frozen(response):
    """✨ Whether a participant's answer collection is frozen (ticket 55), so nobody can be added or sent a new link."""
    return response is not None and response.collection_frozen_at is not None


def _refuse_frozen(request, state, block):
    """✨ Someone added, or an observer's link issued, while answer collection is frozen: with htmx, the short status;
    without, the list's page again, whose own line says why (ticket 71)."""
    return _refused(request, RESULTS_SEEN, status=403, page=lambda status: _list_page(request, state, block, status))


def _list_page(request, state, block, status, refusal=None, asked=0, kept=(), issued=None):
    """✨ The page a contact list is on, as it now stands, with `refusal`, if given, on the list's own line, at least
    `asked` rows, `kept`, what was typed in its rows, back in them, and `issued`, a link just issued (fix-1)."""
    section = section_of(state.version.document, block["id"])
    rows_back = {block["id"]: {"asked": asked, "kept": kept}}
    shown = _section_page(state, section, page_of(section, block["id"]), issued=issued, rows_back=rows_back)
    if refusal is not None:
        _on_page(shown, block["id"])["refusal"] = refusal
    return _section_shown(request, state, section, shown, status=status)


def _on_page(shown, block_id):
    """✨ One block of a page as `_section_page` gives it, to mark before it is drawn."""
    return next(block for block in shown["section"]["blocks"] if block["id"] == block_id)


def _posted_count(request, key):
    """✨ A count a form posted under `key`, such as how many rows its page showed, or 0 for none or anything else."""
    posted = request.POST.get(key, "")
    return int(posted) if posted.isdigit() else 0


def _refused(request, refusal, status, page=None):
    """✨ The one way a press is refused: with htmx, the short status line beside what was pressed; without, `page` (a
    callable drawing the page it was pressed on again, the refusal shown there, with the same status) or, with none,
    a page of its own in the participant's frame saying why, with the way back to the hub. A form submitted as a full
    page never lands the participant on the bare status line (fix-7, ticket 71)."""
    if _is_htmx(request):
        return render(request, "engine/save_status.html", {"refusal": refusal}, status=status)
    if page is not None:
        return page(status)
    return render(request, "engine/refused.html", {"refusal": refusal}, status=status)


# ✨ Why a press on something not reached is refused: a lock, an unconfirmed reading or a page not yet gone through.
# Refused with no `page` (an answer, a coach checklist step, a change to a contact list), so without htmx it is a page
# of its own saying why, since the page it was on is shut too (ticket 71).
NOT_OPEN = "This is not open yet."


# ✨ Why the participant can add nobody while answer collection is frozen: the Five trusted voices card's wording (ticket
# 51a), on the card, the list's page and any refusal.
RESULTS_SEEN = "You've seen your results, so no more answers are added."


def _issue_link(request, contact):
    """✨ Issue, or reissue, one contact's link, and return it, this once: an observer's or, for a coach, the coach's."""
    token = Invitation.issue(contact, link_lifetime(contact.response.version.document))
    return _link_of(request, contact, token)


def _link_of(request, contact, token):
    """✨ The link a contact's token is used at: the coach's own page for a coach, the observer's landing otherwise."""
    link_to = "coaching" if contact.role == Contact.Role.COACH else "observe"
    return request.build_absolute_uri(reverse(link_to, args=[token]))


def _back_with_issued(request, contact, link, kept=None):
    """✨ A redirect to where the contact is listed, carrying the link just issued for that page to show this once, and
    `kept`, what was typed in the list's other empty rows, for that page to put back in them (fix-1). That travels as
    the link does, in the participant's own cookie, so it is kept nowhere of ours (ADR 0020); a caller with more than
    fits (`ISSUED_COOKIE_MOST`) draws the page itself instead."""
    listed_at = _listed_at(contact)
    back = _see_other(listed_at)
    issued = {"contact": contact.pk, "link": link}
    if kept:
        issued["kept"] = kept
    back.set_signed_cookie(
        ISSUED_COOKIE,
        json.dumps(issued),
        salt=ISSUED_COOKIE,
        max_age=ISSUED_COOKIE_SECONDS,
        path=listed_at.partition("#")[0],  # ✨ that page alone reads it
        secure=request.is_secure(),
        httponly=True,
        samesite="Lax",
    )
    return back


# ✨ Where a link just issued waits for the page that shows it, and for how long at most.
ISSUED_COOKIE = "issued_link"
ISSUED_COOKIE_SECONDS = 60
# ✨ The most its contents may run to, as JSON: quoting can double them, and a browser drops a cookie past 4096 bytes,
# signature and attributes included.
ISSUED_COOKIE_MOST = 1800


def _issued_link(request):
    """✨ The link just issued, as {"contact", "link"}, or None: none was, or its cookie is stale or not ours."""
    signed = request.get_signed_cookie(ISSUED_COOKIE, default=None, salt=ISSUED_COOKIE, max_age=ISSUED_COOKIE_SECONDS)
    return json.loads(signed) if signed else None


@login_required
@consent_required
@require_POST
def revoke_invitation(request, contact_id):
    """✨ Stop one contact's link, and with a coach's, the answer given through it. Revoking one that is already gone
    does nothing. The page comes back at that person."""
    contact = _own_contact_or_404(request.user, contact_id)
    Invitation.objects.filter(contact=contact).delete()
    if contact.role == Contact.Role.CONTACT and _is_htmx(request):
        return _person_row_sent_back(request, contact)  # ✨ fix-2
    return _see_other(_listed_at(contact))


def _person_row_sent_back(request, contact, issued=None):
    """✨ An observer's row of their contact list alone, as it now stands, with `issued`, their link just issued."""
    state = _participant(request.user)
    block = _block_of_type(state.version, contact.block_id, "contact_list")
    return _rows_sent_back(request, state, block, [_listed_row(state, block, contact.pk, issued=issued)])


def _listed_at(contact):
    """✨ The address of the page a contact is listed on, at their place in it: the page of the contact list holding
    them, at their row, for an observer; the page of the coach checklist that chose them for a coach."""
    document = contact.response.version.document
    if contact.role == Contact.Role.COACH:
        return _block_address(document, contact.block_id)
    section = section_of(document, contact.block_id)
    return f"{page_url(section['id'], page_of(section, contact.block_id))}#person-{contact.pk}"


def observe(request, token):
    """✨ Where an observer's link leads: before it is claimed, the privacy notice and the way to start; after, word
    that it has been used. Opening it claims nothing. The observer's own link, claimed from it, leads to their page.
    A wrong, expired or revoked link gets one refusal, the same for all three, naming nobody.

    Observers have no account: nothing here reads or writes the signed-in user, if there is one.
    """
    invitation = Invitation.live(token)
    if invitation is None:
        expired = _expired_withdrawal(request, token, Contact.Role.CONTACT)
        if expired is not None:
            return expired
        return _observers_page(request, token, came_by_link=True)  # ✨ an observer's own link, or the refusal
    if invitation.claimed_at is not None:
        return render(request, "engine/link_used.html", status=410)
    frozen = NO_MORE_ANSWERS if invitation.contact.response.collection_frozen_at is not None else None
    return _landing(request, invitation, reverse("start_observing", args=[token]), frozen)


def _landing(request, invitation, action, frozen=None):
    """✨ The privacy notice and the button that claims, posting to `action`. Never cached, since it is reached by a
    secret."""
    document, name = _asked_by(invitation)
    shown = render(
        request,
        "engine/observer_landing.html",
        {"notice": privacy_notice(document, name), "name": name, "action": action, "frozen": frozen},
    )
    shown["Cache-Control"] = "no-store"
    return shown


@require_http_methods(["GET", "POST"])
def start_observing(request, token):
    """✨ The observer's "I'm answering for Sam": the claim. It takes them on to their own link, kept in a cookie too
    (`_claimed`); the participant's copy is used up. A second claim is told the link has been used, so whoever claimed
    first is noticed, not hidden.

    Only the claim sets the cookie, never a plain visit: this is a POST that carries a CSRF token, so no other site
    can put someone else's claim in an observer's browser by sending it to a link. Opening this address, by a reload
    or a bookmark, claims nothing and goes on to the link's own page (ticket 78).
    """
    if request.method == "GET":
        return redirect("observe", token)
    secret = Invitation.claim(token)
    if secret is None:
        if Invitation.live(token) is not None:
            return render(request, "engine/link_used.html", status=410)
        return _refuse_link(request)
    return _claimed(request, secret)


@require_http_methods(["GET", "POST"])
def fresh_link(request, signed):
    """✨ Where a reminder's button leads (ticket 43b, ADR 0016): the privacy notice and a button, as the observer's
    landing has. Opening it changes nothing, since mail filters open every link in a message; only the button's POST
    gives the observer a fresh link of their own, already claimed, in place of the one they were sent, and takes them
    into the observer assessment. It works again until they have sent; a tampered address, or one whose link is dead,
    reissued or frozen, or whose participant's consent is withdrawn, gets the dead-link refusal."""
    pk = reminders.invitation_to_answer(signed)
    invitation = Invitation.answerable(pk) if pk is not None else None
    if invitation is None:
        return _refuse_link(request)
    if request.method == "GET":
        return _landing(request, invitation, reverse("fresh_link", args=[signed]))
    secret = Invitation.claim_afresh(invitation.pk)
    if secret is None:
        return _refuse_link(request)
    return _claimed(request, secret)


def _claimed(request, secret):
    """✨ On to the observer's own link, just claimed, leaving it in a cookie too. From the claim on it is the page they
    are on, so it is there to bookmark, before they send and after (29 Oct). It sits in the browser's history, as any
    page does: someone else at that browser could already reach the page by the cookie, and the page never shows what
    was sent."""
    invitation = Invitation.claimed_by(secret)
    shown = redirect("observe", secret)
    if invitation is not None:
        shown.set_cookie(
            OBSERVER_COOKIE,
            secret,
            expires=invitation.expires_at,
            path=reverse("observer"),
            secure=request.is_secure(),
            httponly=True,
            samesite="Lax",
        )
    return shown


def observer(request):
    """✨ On to the observer's own link, by the cookie their claim left, so their page has the one address (29 Oct)."""
    secret = request.COOKIES.get(OBSERVER_COOKIE)
    if Invitation.claimed_by(secret) is not None:
        return redirect("observe", secret)
    return _observers_page(request, secret)


def coaching(request, token):
    """✨ Where the coach's link leads: who asked them, and the commitments to accept or decline; once answered, their
    answer. A wrong, expired or revoked link, or an observer's, gets the observers' one refusal, naming nobody.

    The coach has no account and claims nothing (spec, Coach): nothing here reads or writes the signed-in user.
    """
    invitation = Invitation.live(token, role=Contact.Role.COACH)
    if invitation is None:
        expired = _expired_withdrawal(request, token, Contact.Role.COACH)
        return expired if expired is not None else _refuse_link(request)
    return _coach_page(request, invitation, token)


@sensitive_post_parameters()
@require_POST
def answer_coaching(request, token):
    """✨ The coach accepting or declining, once per link. Accepting needs every commitment ticked; declining is always
    open. Only the answer is kept, never which boxes were ticked: one affirms the coach's own faith, special category
    data about them, and `sensitive_post_parameters` keeps the boxes out of error reports too."""
    invitation = Invitation.live(token, role=Contact.Role.COACH)
    if invitation is None:
        return _refuse_link(request)
    if invitation.coach_answer is not None:
        return _coach_page(request, invitation, token, refusal=ANSWERED_ALREADY, status=409)
    block = _coach_block(invitation)
    try:
        answer = coach_answer_from_form(block["questions"], request.POST)
    except AnswerRefused as refused:
        ticked = set(request.POST.getlist("commitment"))
        return _coach_page(request, invitation, token, refusal=str(refused), ticked=ticked, status=400)
    if not Invitation.answer_as_coach(token, answer):
        # ✨ Answered, revoked or expired since it was read above: read again, so the page says which.
        invitation = Invitation.live(token, role=Contact.Role.COACH)
        if invitation is None:
            return _refuse_link(request)
        return _coach_page(request, invitation, token, refusal=ANSWERED_ALREADY, status=409)
    messages.add_message(request, messages.INFO, "answered", extra_tags=JUST_ANSWERED)
    return _see_other("coaching", token)


@require_http_methods(["GET", "POST"])
def coach_withdrawal(request, token):
    """✨ The coach withdrawing their acceptance (ADR 0024), as an observer withdraws (ticket 15b): opening the page only
    asks, and its button deletes the coach, acceptance, name and link, leaving the participant told only that their
    coach withdrew. Only a working link that accepted can, whether or not the participant's consent stands; any other
    gets the one refusal, naming nobody.

    Before the acceptance goes, whatever it opened is recorded as opened (`_withdraw`).

    An expired link that accepted still withdraws (29 Oct), on the expired link's page (`_expired_withdrawal`)."""
    invitation = Invitation.withdrawable_by_coach(token)
    if invitation is None:
        expired = _expired_withdrawal(request, token, Contact.Role.COACH, withdraws=request.method == "POST")
        return expired if expired is not None else _refuse_link(request)
    _, name = _asked_by(invitation)
    if request.method == "POST":
        if not _withdraw(invitation, token):
            return _refuse_link(request)
        shown = render(request, "engine/coach_withdrawal.html", {"name": name, "withdrawn": True})
    else:
        action = reverse("coach_withdrawal", args=[token])
        shown = render(request, "engine/coach_withdrawal.html", {"name": name, "action": action})
    shown["Cache-Control"] = "no-store"
    return shown


ANSWERED_ALREADY = "You've already answered."

# ✨ Marks the page a coach's answer leads to, so its thanks is said once and not on every later visit (ticket 25a).
JUST_ANSWERED = "coach-just-answered"


def _just_answered(request):
    """✨ Whether this page is the one the coach's answer led to. Reading the flash messages uses them all up, so any
    other is put back for the page it was meant for."""
    others = []
    found = False
    for message in messages.get_messages(request):
        if message.extra_tags == JUST_ANSWERED:
            found = True
        else:
            others.append(message)
    for message in others:
        messages.add_message(request, message.level, message.message, extra_tags=message.extra_tags)
    return found


def _coach_page(request, invitation, token, refusal=None, ticked=(), status=200):
    """✨ The coach's page for a live coach's link: the participant's name, the authored invitation, each commitment
    with its note as a box (`ticked` as last sent, on a refusal), or once answered, what follows the answer: thanks
    only on the page their accepting led to, and while the participant shares their results, the sort's brief with them
    (ticket 25a). Never cached, since it is reached by a secret."""
    document, name = _asked_by(invitation)
    shared = _shared_with_coach(invitation, name)
    scored = _scored_block(document)
    text = authored_text(_coach_block(invitation), "participant")
    named = {field: text.get(field, "").replace("{name}", name) for field in COACH_TEXT_FIELDS}
    promises = [
        {"id": question["id"], "commitment": question["commitment"], "note": question.get("coach_note", "")}
        for question in commitments(text["questions"])
    ]
    context = {
        "name": name,
        "text": named,
        "commitments": promises,
        "count": apnumber(len(promises)),
        "ticked": ticked,
        "answer": invitation.coach_answer,
        "refusal": refusal,
        "token": token,
        "shared": shared,
        "brief": coach_brief(scored) if shared and scored else None,
        "briefed": bool(scored and coach_brief(scored)),  # ✨ so "What happens next" promises a guide only if one comes
        "just_accepted": _just_answered(request),
    }
    shown = render(request, "engine/coach_link.html", context, status=status)
    shown["Cache-Control"] = "no-store"
    return shown


# ✨ The authored passages of the coach's page, each naming the participant as {name}.
COACH_TEXT_FIELDS = ("coach_invitation", "coach_accepted", "coach_declined")


def _shared_with_coach(invitation, name):
    """✨ The participant's results and comparison, as they see them but worded about them by `name`, as the observer's
    pages are (ticket 118), for a coach who accepted through this link and whom they are happy to show; otherwise None.
    Read afresh on every visit, so a withdrawal shows at once (ticket 27). Nothing else of the participant's is read:
    only the stored result, the sort it was scored from and the observers' assessments, through the same suppression
    as the participant's own comparison."""
    if invitation.coach_answer != Invitation.CoachAnswer.ACCEPTED or invitation.results_shared_at is None:
        return None
    participant_response = invitation.contact.response
    document = participant_response.version.document
    scored = _scored_block(document)
    result = Result.objects.filter(response=participant_response, block_id=scored["id"]).first() if scored else None
    if result is None:
        return None
    sort = participant_response.answers[scored["id"]]
    scores = _scores_shown_storing_reweighted(document, result)
    return {
        "results": results_page(document, scores, sort, name, role="coach"),
        "comparison": _comparison_of(participant_response, scores, sort, role="coach", name=name),
        "comparison_heading": _comparison_title_for_coach(document, scored["id"], name),
    }


def _coach_block(invitation):
    """✨ The coach checklist that chose the coach a link is for, in the participant's pathway version."""
    document = invitation.contact.response.version.document
    return next(block for block in blocks_of(document) if block["id"] == invitation.contact.block_id)


@require_POST
def send_assessment(request, token=None):
    """✨ The observer sending their observer assessment, once, with the secret they claimed: from their own link
    (`token`), or else from the cookie. It counts at once, and nothing of it is ever shown back. The participant's copy
    of the link is not a secret, so it is refused here as any wrong link is. Then back to the page it was sent from,
    which now says thank you. One with every card in "Haven't seen this" is kept as a decline (ticket 120), however it
    was sent, though the sort asks first.

    A second send from the same secret is refused, and the first stands. A reissued link is a new claim, so its observer
    may send one too, and both count (ADR 0007).
    """
    if token is None:
        secret, back = request.COOKIES.get(OBSERVER_COOKIE), reverse("observer")
    else:
        secret, back = token, reverse("observe", args=[token])
    invitation = Invitation.claimed_by(secret)
    if invitation is None:
        return _refuse_link(request)
    document, _ = _asked_by(invitation)
    scored = _scored_block(document)
    if scored is None:
        raise Http404("This pathway has no assessment for observers.")
    try:
        assessment = answer_from_form(document, scored, request.POST.get("value"), role="observer")
        relationship = relationship_from_form(document, request.POST.get("relationship"))
    except AnswerRefused as refused:
        return render(request, "engine/save_status.html", {"refusal": str(refused)}, status=400)
    try:
        sent = ObserverResponse.send(invitation.contact.response, secret, assessment, relationship=relationship)
    except IntegrityError:
        return render(request, "engine/save_status.html", {"refusal": SENT_ALREADY}, status=409)
    except CollectionFrozen:
        return render(request, "engine/save_status.html", {"refusal": NO_MORE_ANSWERS}, status=409)
    if sent is None:
        # ✨ The observer withdrew through another page while this send was on its way.
        return _refuse_link(request)
    return _go_to(request, back)


@require_http_methods(["GET", "POST"])
def withdrawal(request, token=None):
    """✨ The observer withdrawing, with the secret they claimed: from their own link (`token`), or else from the cookie
    (ticket 15b). Opening the page asks and deletes nothing; only its button's POST deletes what they sent, found by
    the hash of that secret, and ends their link. The participant's copy of the link is not a secret, and a link that
    has stopped working claims nothing, so both are refused as any wrong link is: after that, the privacy notice tells
    the observer to ask the people who run the service. A participant's withdrawn consent closes every other page of
    the observer's, never this one (ticket 45).

    An own link that has expired, once its observer sent answers, still withdraws (29 Oct), on the expired link's page
    (`_expired_withdrawal`); the cookie alone never reaches it.
    """
    secret = request.COOKIES.get(OBSERVER_COOKIE) if token is None else token
    invitation = Invitation.claimed_by(secret, for_withdrawal=True)
    if invitation is None:
        expired = _expired_withdrawal(request, token, Contact.Role.CONTACT, withdraws=request.method == "POST")
        return expired if expired is not None else _refuse_link(request)
    _, name = _asked_by(invitation)
    action = reverse("withdrawal") if token is None else reverse("withdrawal_by_link", args=[token])
    if request.method == "POST":
        _withdraw(invitation, secret)
        shown = render(request, "engine/withdrawal.html", {"name": name, "withdrawn": True})
        shown.delete_cookie(OBSERVER_COOKIE, path=reverse("observer"))
    else:
        shown = render(request, "engine/withdrawal.html", {"name": name, "action": action})
    shown["Cache-Control"] = "no-store"
    return shown


@csrf_exempt
@require_http_methods(["GET", "POST"])
def stop_reminders(request, signed):
    """✨ Where a reminder's stop link leads (ticket 43a): opening it only asks, and only a POST stops this participant's
    reminders to that person, from the page's button or as a mail provider's one-click `List-Unsubscribe` (RFC 8058).
    It works while the contact exists, whatever has happened to their link, and looks the same throughout; a tampered or
    removed one gets the dead-link refusal.

    Exempt from CSRF, since a one-click POST comes from the mail provider with no token: the signed address is the only
    authority, so a forged POST would need it anyway, and all it can do is stop reminders."""
    contact = reminders.contact_to_stop(signed)
    if contact is None:
        return _refuse_link(request)
    name = name_shown_for(contact.response.participant)
    if request.method == "POST":
        reminders.stop_reminders(contact)
        shown = render(request, "engine/stop_reminders.html", {"name": name, "stopped": True})
    else:
        action = reverse("stop_reminders", args=[signed])
        shown = render(request, "engine/stop_reminders.html", {"name": name, "action": action})
    shown["Cache-Control"] = "no-store"
    return shown


# ✨ What an observer is told while answer collection is frozen (ticket 55).
NO_MORE_ANSWERS = "No more answers are being taken."


# ✨ Where an observer's own secret is kept, so the observer's pages know them without a link or an account. It
# holds one claim: claiming a second link, for someone else, replaces the first, whose own link still works.
OBSERVER_COOKIE = "observer"


def _observers_page(request, secret, came_by_link=False):
    """✨ The observer's page for the invitation a secret claimed, or the refusal if there is none: the observer
    assessment until it is sent, then thanks, worded for a decline where they saw nothing (ticket 120). While answer
    collection is frozen, one who has not sent is told no more answers are being taken, and offered no assessment
    (ticket 55). An observer who `came_by_link` rather than by the cookie is at their own link, which the page offers
    to copy, and sends the assessment through it. Never cached, since it is reached by a secret.

    Demo only (ticket 113): the sort offers the participant's demo profiles, hidden until revealed, and starts from the
    one the address names (`_observer_demo_prefill`)."""
    invitation = Invitation.claimed_by(secret)
    if invitation is None:
        return _refuse_link(request)
    document, name = _asked_by(invitation)
    scored = _scored_block(document)
    sent = ObserverResponse.sent_with(secret)
    declined = sent and ObserverResponse.declined_with(secret)
    frozen = not sent and invitation.contact.response.collection_frozen_at is not None
    assessment = None
    if scored and not sent and not frozen:
        assessment = {
            "id": scored["id"],
            "widget": BLOCK_TYPES[scored["type"]].widget(document, "observer", name),
            "action": reverse("send_assessment_by_link", args=[secret]) if came_by_link else reverse("send_assessment"),
            "relationship": relationship_question(document, name),
            "demo_profiles": scenario_loading.offered(document).profiles if demo_shortcuts.tools_on() else [],
        }
        placed = _observer_demo_prefill(request, document)
        if placed is not None:
            # ✨ Each card already where the profile places it, so the widget opens at "All sorted" (`placed` in sort.js).
            assessment["widget"] = {**assessment["widget"], "placed": placed}
    withdraw_at = reverse("withdrawal_by_link", args=[secret]) if came_by_link else reverse("withdrawal")
    context = {
        "name": name,
        "own_link": request.build_absolute_uri(reverse("observe", args=[secret])) if came_by_link else None,
        "assessment": assessment,
        "sent": sent,
        "declined": declined,
        "frozen": NO_MORE_ANSWERS if frozen else None,
        "withdraw_at": withdraw_at,
    }
    shown = render(request, "engine/observer.html", context)
    shown["Cache-Control"] = "no-store"
    return shown


def _observer_demo_prefill(request, document):
    """✨ Demo only (ticket 113): the observer version of the demo profile the address names, as
    `scenario_loading.observer_sort` gives it, for an observer's sort to start from, storing nothing until they send it;
    or None: off a development or demo system, with no profile named, or with one not offered on this pathway."""
    profile = request.GET.get(scenario_loading.PROFILE_FIELD)
    if not profile or not demo_shortcuts.tools_on():
        return None
    return scenario_loading.observer_sort(document, profile)


def _scored_block(document):
    """✨ The document's scored block, whose assessment observers make about the participant so it can be set beside
    the participant's own, or None for a document without one."""
    return next((block for block in blocks_of(document) if BLOCK_TYPES[block["type"]].scored), None)


def _refuse_link(request):
    """✨ The one refusal for a wrong, expired or revoked link, or an observer's own link or cookie that no longer
    works: the same for all, naming nobody."""
    return render(request, "engine/link_refused.html", status=404)


# ✨ How an expired link that can still withdraw is found, by the role of the person it was for, and the address its
# page posts to: a coach's link once it accepted, an observer's own link once they sent answers through it (ADR 0026).
EXPIRED_WITHDRAWALS = {
    Contact.Role.COACH: (Invitation.expired_acceptance, "coach_withdrawal"),
    Contact.Role.CONTACT: (Invitation.expired_claim, "withdrawal_by_link"),
}


def _expired_withdrawal(request, token, role, *, withdraws=False):
    """✨ The one way through an expired link that can still withdraw, a coach's or an observer's as `role` says
    (`EXPIRED_WITHDRAWALS`): its page, asking, with a button posting to the withdrawal by that link; or, when
    `withdraws`, what was shared through it withdrawn (`_withdraw`) and word that it is done. None for a token that is
    no such link, which each caller answers its own way."""
    find, withdrawal = EXPIRED_WITHDRAWALS[role]
    expired = find(token)
    if expired is None:
        return None
    if not withdraws:
        return _expired_link(request, expired, reverse(withdrawal, args=[token]))
    if not _withdraw(expired, token):
        return _refuse_link(request)
    return _expired_link(request, withdrawn=True)


def _withdraw(invitation, secret):
    """✨ Withdraw what the person holding `secret` shared through `invitation`, its link working or expired, and say
    whether it is done. A coach's acceptance goes once whatever it opened is recorded as opened, as the participant's
    next page would have recorded it, so a section it opened stays open however soon the coach withdraws (ADR 0019,
    ADR 0024); False if the link never accepted. An observer's answers go, and it is done even when an earlier press
    left nothing to withdraw."""
    if invitation.contact.role == Contact.Role.COACH:
        _store_completions_and_openings(invitation.contact.response)
        return Invitation.withdraw_as_coach(secret)
    ObserverResponse.withdraw(secret)
    return True


def _expired_link(request, expired=None, action=None, *, withdrawn=False):
    """✨ An observer's own link or an accepting coach's once it has expired (29 Oct): saying so, with a quiet way to
    withdraw what they shared, posting to `action`; or, `withdrawn`, word that it is done. It names the participant
    the `expired` invitation was for, as the link did while it worked, so whoever holds it learns nothing new, and gives
    its own address to come back to (the developer's 29 Oct hand check). Never cached, since it is reached by a
    secret."""
    context = {"action": action, "withdrawn": withdrawn, "here": request.build_absolute_uri()}
    if expired is not None:
        context["name"] = _asked_by(expired)[1]
        context["coach"] = expired.contact.role == Contact.Role.COACH
    shown = render(request, "engine/link_expired.html", context, status=200 if withdrawn else 410)
    shown["Cache-Control"] = "no-store"
    return shown


def _asked_by(invitation):
    """✨ The pathway document an invitation belongs to, and the display name of the participant who asked."""
    participant_response = invitation.contact.response
    return participant_response.version.document, name_shown_for(participant_response.participant)


def _own_contact_or_404(user, contact_id):
    """✨ One of this participant's own contacts, their coach included, or a 404 that says nothing about whether anyone
    else has a contact by that number."""
    contact = Contact.objects.select_related("response__version").filter(pk=contact_id, response__participant=user).first()
    if contact is None:
        raise Http404("You have no contact by that number.")
    return contact


def page_url(section_id, page=1):
    """✨ The address of one page of a section. The first is the section's own address, with no page number.
    Templates reach it as the `page_url` tag (`engine/templatetags/section_pages.py`)."""
    if page == 1:
        return reverse("section", args=[section_id])
    return reverse("section_page", args=[section_id, page])


def _see_other(where, *args):
    """✨ After a POST, the browser should GET the page it lands on rather than repeat the POST."""
    response = redirect(where, *args)
    response.status_code = 303
    return response


def _to_results(request, block_id):
    """✨ A scored answer's next page is its result."""
    return _go_to(request, reverse("results", args=[block_id]))


def _go_to(request, where):
    """✨ After an assessment is sent, the page it leads to. htmx is told to go there rather than swap anything in."""
    if request.headers.get("HX-Request") == "true":
        return HttpResponse(headers={"HX-Redirect": where})
    return _see_other(where)


def _hub_of(state, answers=None):
    """✨ The participant's hub as `hub_for` works it out from their state, with `answers` in place of their stored ones
    where a page has newer, and the pathway's minimum number of observer answers, which a lock note may say."""
    return hub_for(
        state.sections,
        state.answers if answers is None else answers,
        state.completed,
        moved_past=state.moved_past,
        minimum=minimum_observers(state.version.document),
    )


def _participant(user, first_version=Publication.current_version):
    """✨ Everything stored for this participant, as a `ParticipantState`.

    A participant without a response yet reads `first_version()`: by default the published version, so what they
    see is what their first answer will be recorded against.

    Not only a read: it stores the completion of each hub side card whose gate now passes, the first time it is seen,
    on any request, a GET included (ticket 52).
    """
    participant_response = Response.in_progress(user)
    if participant_response is None:
        version = first_version()
        sections = track_sections(version.document) if version else []
        return ParticipantState(None, version, sections, {}, complete_sections(sections, {}, ()), {}, set())
    sections, answers, completed, moved_past = _store_completions_and_openings(participant_response)
    return ParticipantState(
        response=participant_response,
        version=participant_response.version,
        sections=sections,
        answers=answers,
        completed=completed,
        moved_past=moved_past,
        fixed=set(participant_response.fixed_answers),
    )


def _store_completions_and_openings(participant_response):
    """✨ Store each hub side card's completion, the completion of each section its evaluation's end completes (ticket
    119), and each opened section's opening the first time any is seen, and return the response's track sections, the
    answers the gate reads, the sections complete and the pages moved past, those included."""
    sections = track_sections(participant_response.version.document)
    answers = participant_response.answers_with_contacts_and_visits()
    # ✨ A part of a section, or a hub side card, is complete once its gate passes, so locks and the hub count it without
    # a completion.
    completed = complete_sections(sections, answers, participant_response.completed_sections)
    moved_past = participant_response.moved_past_by_section()
    # ✨ Likewise a section that completes itself as its evaluation ends, the first time it is seen to have (ticket 119),
    # before the side cards and openings that may wait on it.
    if _complete_those_ended_by_their_evaluation(participant_response, sections, answers, completed, moved_past):
        completed = complete_sections(sections, answers, participant_response.completed_sections)
    # ✨ A side card's completion is stored the first time it is seen, so it stays complete once its links expire or are revoked, or
    # its people are taken off the list, and never locks again what it opened (ticket 52).
    stored = participant_response.completed_sections
    for section in sections:
        if "side_card" in section and section["id"] in completed and section["id"] not in stored:
            participant_response.complete_section(section["id"])
    # ✨ Likewise the first time a section with opening conditions is open, so it stays open once the coach's link is
    # revoked or reissued, or the coach changed (ADR 0019).
    for section in sections:
        if (
            "opens_when" in section
            and opened_key(section["id"]) not in answers
            and not is_locked(section, completed, answers, sections, moved_past)
        ):
            participant_response.open_section(section["id"])
            answers[opened_key(section["id"])] = True
    return sections, answers, completed, moved_past


def _complete_those_ended_by_their_evaluation(participant_response, sections, answers, completed, moved_past):
    """✨ Store the completion of each section that completes itself as its evaluation ends (ticket 119,
    `completes_with_its_evaluation`) and has not been stored yet, once that evaluation has ended: the sort in, and every
    tie-break pair answered or skipped. It is re-checked as the participant's own press is (`complete_section`): open
    and reached to its last page, its parts done and its gate met. Stored, never worked out on the fly, so a retake,
    which clears the sort, leaves it complete (ADR 0025). Whether any was stored; the response's completions are read
    again if so."""
    waiting = [
        (section, sort_id)
        for section in sections
        if (sort_id := completes_with_its_evaluation(section, sections)) is not None
        and section["id"] not in participant_response.completed_sections
    ]
    document = participant_response.version.document
    stored = False
    for section, sort_id in waiting:
        if (
            is_locked(section, completed, answers, sections, moved_past)
            or page_reached(section, moved_past, answers, sections) < page_count(section)
            or finish_waits(section, sections, completed)
            or unmet(section, answers)
        ):
            continue
        result = Result.objects.filter(response=participant_response, block_id=sort_id).first()
        if result is None or _pairs_left(document, result):
            continue
        participant_response.complete_section(
            section["id"], fixed_block_ids=block_ids_fixed_on_completion(section, answers)
        )
        stored = True
    if stored:
        participant_response.refresh_from_db(fields=["completed_sections", "fixed_answers", "updated_at"])
    return stored


def _is_open(state, section, block):
    """✨ Whether a participant has reached a block: its section is not locked, its page has been reached, and no
    unconfirmed reading or held link above it holds it shut."""
    reached = state.reached(section)
    if reached is None:
        return False
    blocks, _ = open_blocks(section, state.answers, state.sections, up_to_page=reached)
    return block in blocks


def _page_or_404(section, page):
    if not 1 <= page <= page_count(section):
        raise Http404("This section has no page by that number.")
    return page


FIXED_REFUSAL = "This answer was fixed when you completed this section."
SEALED_REFUSAL = "Your letter was sealed when you finished this section, so it can no longer be changed."


def _seals(state):
    """✨ The participant's sealed letters, by block (ticket 104)."""
    if state.response is None:
        return {}
    return {sealed.block_id: sealed for sealed in state.response.sealed_letters.all()}


def _open_letters_due(state, page_blocks):
    """✨ Record the first time a sealed letter on this page is opened on or after its date (ticket 104)."""
    seals = _seals(state)
    for block in page_blocks:
        sealed = seals.get(block["id"])
        if sealed is not None and sealed.opened_at is None and sealed.is_open():
            sealed.open()


def _letter_of(block, seals):
    """✨ For a letter block, where it stands, as `letter_shown` gives it (ticket 104); None for any other block."""
    sealed = seals.get(block["id"])
    return letter_shown(block, sealed.opens_on if sealed else None, timezone.localdate())


def _block_of_type(version, block_id, block_type):
    """✨ The version's block by that identifier, provided it is of that type; otherwise a 404."""
    for block in blocks_of(version.document) if version else ():
        if block["id"] == block_id and block["type"] == block_type:
            return block
    raise Http404(f"This pathway version has no {block_type} by that identifier.")


def _section_or_404(version, section_id):
    section = section_by_id(version.document, section_id) if version else None
    if section is None:
        raise Http404("This pathway version has no section by that identifier.")
    return section


def _section_page(state, section, page=1, issued=None, demo=None, rows_back=None, chosen=None, kept=None):
    """✨ One page of a section as its template needs it. Every page but the last ends in "Continue →", held by that
    page's own clauses; the last ends in the section's completion, held by the whole gate. `issued` is a link just
    issued, a coach's or an observer's, which the page shows this once beside the person it is for. `demo` is a demo
    profile, from `_demo_prefill`, that a sort not yet in starts from (fix-23). `rows_back` is how a contact list's
    rows come back from a press without JavaScript, by its identifier, as `_contact_rows` takes it (ticket 70,
    fix-1). `chosen` is the date a refused press to seal a letter sent, offered again in place of the default (ticket
    104); `kept` the dates last picked for the participant's letters, by block, as their session keeps them, each
    offered while its letter still accepts it (`_letter_dates`, sprint-3d-r1-fix-3)."""
    rows_back = rows_back or {}
    version, answers, fixed = state.version, state.answers, state.fixed
    opened, activity_open = open_blocks(section, answers, state.sections, up_to_page=page)
    on_page = {block["id"] for block in pages_of(section)[page - 1]}
    blocks = [block for block in opened if block["id"] in on_page]
    is_last = page == page_count(section)
    # ✨ A sort leads only to its results, as in the prototype, so completing is not offered beside it until it
    # is in. The linter makes its section's gate require it, so the server refuses completion before then too.
    sort_pending = any(BLOCK_TYPES[block["type"]].scored and block["id"] not in answers for block in blocks)
    # ✨ Nor is it offered in a section whose work is all in its parts until they are done (ticket 106).
    parts_pending = is_last and finish_waits(section, state.sections, state.completed)
    # ✨ A link shows the section it leads to exactly as the hub would: its title, its status and whether it is open.
    hub = _hub_of(state, answers)
    links = _requirement_links(state, section, page)
    gate_checklist = [(message, met, links.get(message)) for message, met in checklist(section, answers, page=page)]
    states = {other.id: other for other in hub.sections}
    seals = _seals(state)
    letter = unsealed_letter(section, seals) if is_last else None
    press = seal_press(letter, timezone.localdate(), chosen, (kept or {}).get(letter["id"])) if letter else None
    named = None if is_last else way_on_named_by(pages_of(section)[page - 1], seals)
    # ✨ How many observers declined, read only for a page that holds a contact list, the one place it is said.
    lists = state.response is not None and any(block["type"] == "contact_list" for block in blocks)
    declined = ObserverResponse.declined(state.response) if lists else 0
    return {
        # ✨ Where "← Back" at the top leads: the section this is a part of, or else the hub.
        "back": _section_this_is_part_of(state, section),
        "page": {
            "number": page,
            "count": page_count(section),
            "is_last": is_last,
            # ✨ The press's own label where the block it is for gives one, as the letter's "Save my letter and continue
            # →" (ticket 107), or None for "Continue →".
            "way_on_label": _way_on_label(named),
            # ✨ Whether the page has its own Save, shown without JavaScript beside its way on (sprint-3d-r1-fix-6):
            # while any answer on it can be sent with its form, or while it seals the letter, whose date the Save keeps
            # (sprint-3d-r1-fix-3). Drawn before the seal, the Save is the form's first button, the one Enter in the
            # date presses, so Enter there never seals the letter, even on a page with no other answer (code review of
            # 23 Nov); with JavaScript, main.js then cancels it.
            "saves": press is not None or any(_sent_with_its_page(state, block, seals) for block in blocks),
            "previous": _previous_page(section, page, seals),
        },
        "pathway": {
            "version_id": version.pk,
            "scale_points": SCALE_POINTS,
            "long_text_max_length": LONG_TEXT_MAX_LENGTH,
        },
        "section": {
            "id": section["id"],
            "title": text_for(section["title"], "participant"),
            # ✨ While it holds a letter not yet sealed, the press that finishes it says it seals it (ticket 104).
            "complete_label": press["label"] if press else _complete_label(section),
            # ✨ The line above the finish, such as when to come back and press it (ticket 106), or None.
            "complete_note": text_for(section["complete_note"], "participant") if "complete_note" in section else None,
            "is_part": "part_of" in section,
            # ✨ On a part's last page, the finish of the section it is the last thing in, if it is (ticket 88).
            "finish": _finish_of(state, section) if is_last else None,
            "is_side_card": "side_card" in section,
            "reopens": _reopens(section, state.sections),
            # ✨ Completed as its evaluation ends, with no press, its label then a way on to the hub (ticket 119).
            "completes_with_evaluation": completes_with_its_evaluation(section, state.sections) is not None,
            "blocks": [
                _block_for_participant(
                    version.document,
                    block,
                    answers,
                    fixed,
                    states,
                    issued,
                    _frozen(state.response),
                    drawn=_sort_results_drawn(state, block),
                    demo=demo,
                    comparison=_comparison_signpost_shown(state, block),
                    pairs_left=_signposted_pairs_left(state, block),
                    rows_back=rows_back.get(block["id"]),
                    coach_withdrew=state.response is not None and state.response.coach_withdrew,
                    observers_withdrew=state.response.observers_withdrew if state.response is not None else 0,
                    observers_declined=declined,
                    saves_quietly=saves_quietly(version.document, section, block),
                    letter=_letter_of(block, seals),
                )
                for block in blocks
            ],
        },
        # ✨ The date the press that finishes the section seals its letter until, while it holds one not yet sealed, and
        # the letter's block, whose date is kept as it is picked (sprint-3d-r1-fix-3).
        "seal": {**press, "letter": letter["id"]} if press else None,
        "is_complete": section["id"] in state.completed,
        # ✨ Demo only (fix-21): a sort not yet in offers a hidden "Load a demo profile (demo only)", where one holds.
        "demo_profile": (
            sort_pending and demo_shortcuts.tools_on() and bool(scenario_loading.offered(version.document).profiles)
        ),
        # ✨ Over the whole section, since the ratings it fixed may be on an earlier page than its completion.
        "holds_fixed_answers": any(block["id"] in fixed for block in section["blocks"]),
        # ✨ The way on, "Continue →" or completion. Going on from a page is refused on exactly these and `unmet`.
        "offers_way_on": activity_open and not sort_pending and not parts_pending,
        # ✨ What the checklist marks unmet: on the last page, where completing checks it, the whole gate.
        "unmet": [message for message, met, _ in gate_checklist if not met],
        "checklist": gate_checklist,
        # ✨ Where the document asks for it (ticket 83), the checklist only once a press is refused, and unmet alone.
        "messages_after_a_press": messages_after_a_press(version.document),
    }


def _way_on_label(block):
    """✨ The label of the press leading on from a page, from the block it is for (`way_on_named_by`): its
    `continue_label`, or None for "Continue →", as where the press is for no block (ticket 107)."""
    if block is None or "continue_label" not in block:
        return None
    return text_for(block["continue_label"], "participant")


def _sent_with_its_page(state, block, seals):
    """✨ Whether a block shown on a page has an answer its page's form sends (sprint-3d-r1-fix-6): an ordinary answer
    (`sent_with_its_page`) that can still be changed there, so not fixed, not a sealed letter and not waiting on the
    comparison, each of which the page draws with nothing to send."""
    if not BLOCK_TYPES[block["type"]].sent_with_its_page:
        return False
    if block["id"] in state.fixed or block["id"] in seals:
        return False
    return comparison_wait_message(block, state.answers) is None


def _previous_page(section, page, sealed_ids):
    """✨ Where "← Previous page" leads: the page before, at its way on, the press that left it (ticket 41e), or at the
    block that press was for, so going back to the letter lands on it (ticket 107). None on the first page."""
    if page == 1:
        return None
    named = way_on_named_by(pages_of(section)[page - 2], sealed_ids)
    anchor = f"block-{named['id']}" if named else "completion"
    return f"{page_url(section['id'], page - 1)}#{anchor}"


def _completes_itself(section):
    """✨ Whether a section is complete once its gate passes, with no completion of its own to press: a part of a section
    (ticket 41b), or a hub side card (ticket 52)."""
    return "part_of" in section or "side_card" in section


def _reopens(section, sections):
    """✨ Whether the participant can take back a section's completion: not one that completes itself, nor one its
    evaluation completes (ticket 119), which would complete again at once, nor a wizard, which once complete is never
    asked for again (ticket 50)."""
    return (
        not _completes_itself(section)
        and completes_with_its_evaluation(section, sections) is None
        and not section.get("wizard")
    )


def _section_this_is_part_of(state, section):
    """✨ The section a part of a section belongs to, as its ways back name it: {"title", "href"}, at the page of it the
    participant has reached. None for a section that is not a part, or whose section is outside the track or locked."""
    parent_section = section_by_id(state.version.document, section["part_of"]) if "part_of" in section else None
    reached = state.reached(parent_section) if parent_section else None
    if reached is None:
        return None
    return _way_back(parent_section, reached)


def _section_holding_comparison_signpost(state, sort_id):
    """✨ Where the comparison of a sort leads back to (ticket 96): the open section in the track holding a comparison
    signpost to it, as its ways back name it, {"title", "href"}, at the page reached. None where no section holds one,
    as in the faithful port, when the comparison leads back as its results do; the comparison is never shown while the
    section holding one is locked (fix-19)."""
    held = _open_section_holding_comparison_signpost(state, sort_id)
    if held is None:
        return None
    section, reached = held
    return _way_back(section, reached)


def _way_back(section, page):
    """✨ A way back to a page of a section, as a back button names it: {"title", "href"}."""
    return {"title": text_for(section["title"], "participant"), "href": page_url(section["id"], page)}


def _sections_holding_comparison_signpost(state, sort_id):
    """✨ The sections in the track holding a comparison signpost to the sort."""
    return [
        section
        for section in state.sections
        if any(block["type"] == "comparison_signpost" and block["sort"] == sort_id for block in section["blocks"])
    ]


def _open_section_holding_comparison_signpost(state, sort_id):
    """✨ The open section holding a comparison signpost to the sort, and the page reached, or None."""
    for section in _sections_holding_comparison_signpost(state, sort_id):
        reached = state.reached(section)
        if reached is not None:
            return section, reached
    return None


def _comparison_locked(state, sort_id):
    """✨ Whether the comparison of a sort is shut (fix-19): a section in the track holds a comparison signpost to it, as
    *Whatever You Do*'s Section 2 does, making the comparison that section's, and none of them is open. Never where no
    section holds one, as in the faithful port, whose comparison is open to anyone with a result."""
    holding = _sections_holding_comparison_signpost(state, sort_id)
    return bool(holding) and _open_section_holding_comparison_signpost(state, sort_id) is None


def _reflection_after_comparison(state, sort_id):
    """✨ Where the comparison's last button leads (fix-18): the section holding its signpost, at the field that waits on
    the comparison (the block carrying `after_comparison` for the sort), as {"label", "href"}, the address anchored at
    that field, and on to the workbook where that field is a download, as *Whatever You Do*'s first workbook is. None
    where no section holds one, as in the faithful port, or where it has no such field, when the page's top back button
    is offered again in its place."""
    held = _open_section_holding_comparison_signpost(state, sort_id)
    if held is None:
        return None
    section = held[0]
    for block in section["blocks"]:
        if block.get("after_comparison", {}).get("sort") == sort_id and page_of(section, block["id"]) is not None:
            return {
                "label": BLOCK_TYPES[block["type"]].onward_label,
                "href": f"{page_url(section['id'], page_of(section, block['id']))}#{landing_of(block)}",
            }
    return None


def _finish_of(state, part):
    """✨ The finish a part's end offers when the part is the last thing in its section (ticket 88), as a `Finish`;
    once its section is complete, the end offers nothing in its place, the way back at the
    page's top being the only one (ticket 96), save where its evaluation completed it, when its label is the way on to
    the hub's next step (ticket 119). None for a part that ends nothing, or whose section the participant
    has not reached. Pressing it is that section's own completion, so its gate refuses it exactly as it refuses the
    section's own button."""
    ended = section_ended_by(state.version.document, part)
    if ended is None or state.reached(ended) is None:
        return None
    way_on = completes_with_its_evaluation(ended, state.sections) is not None
    return Finish(ended["id"], _complete_label(ended), ended["id"] in state.completed, way_on)


def _complete_label(section):
    """✨ The wording of the button that completes the section: its own, or else "Mark complete"."""
    return text_for(section.get("complete_label", "Mark complete"), "participant")


def _requirement_links(state, section, page):
    """✨ Where each of a section's requirements met on another page is met, by its message (ticket 41b): a coach's link
    on the coach page, people's links on the invitations page. One whose page is not open yet is left out, and so is one
    met in this section itself, as on a hub side card (ticket 52). One met on another page of this section, as the
    letter is on the page before its seal, leads to its block there (ticket 107)."""
    document = state.version.document
    links = {}
    for clause in clauses_of(section):
        on_page = page_of(section, clause["block"])
        if on_page is not None and on_page != page:
            links.setdefault(clause_message(clause), _block_address(document, clause["block"]))
        if clause["type"] != "links_issued":
            continue
        block = next(block for block in blocks_of(document) if block["id"] == clause["block"])
        if section_of(document, block["id"])["id"] == section["id"]:
            continue
        if not _is_open(state, section_of(document, block["id"]), block):
            continue
        is_coach = block["type"] == "coach_checklist"
        links[clause_message(clause)] = (
            _block_address(document, block["id"]) if is_coach else reverse("invitations")
        )
    return links


def _published_version(posted):
    """✨ The pathway version a form names, provided it has been published; otherwise None."""
    if not (posted or "").isdigit():
        return None
    return PathwayVersion.objects.filter(pk=int(posted), publications__isnull=False).distinct().first()


def _sort_results_drawn(state, block):
    """✨ For a `sort_results` block, its sort's results as `_results_drawn` gives them, or None; None for any other."""
    if block["type"] != "sort_results":
        return None
    result = Result.objects.filter(response=state.response, block_id=block["sort"]).first()
    return _results_drawn(state, result, block["sort"])


def _comparison_signpost_shown(state, block):
    """✨ For a `comparison_signpost` block, its sort and where the way to that sort's comparison stands, as
    `comparison_status` words it, once there is a result; None before, and for any other block (ticket 67a). Below the
    minimum, where `_invite` marks the way to invite people `waiting`, the status says its phrase (fix-3), and the press
    is greyed (fix-8). Between a retake and the new sort, it is `unsorted`: the press greyed and its line leading back
    to the sort (29 Oct), in `COMPARISON_UNSORTED`'s words. That is while the sort's section, or the one it is part
    of, stays finished, as a retake leaves it; before the first sort it cannot be. Where the document puts the freeze
    warning beside the press, `warning` is that warning while a press would freeze answer collection, or None; and
    `signpost` is the address of the signpost on its page, where a hub row or sidebar entry with no room for the
    warning leads meanwhile (ticket 106)."""
    if block["type"] != "comparison_signpost":
        return None
    sort = block["sort"]
    if not Result.objects.filter(response=state.response, block_id=sort).exists():
        section = section_of(state.version.document, sort)
        if not {section["id"], section.get("part_of")} & set(state.completed):
            return None
        link, rest = COMPARISON_UNSORTED
        return {
            "sort": sort,
            "status": "waiting",
            "label": f"{link} {rest}".removesuffix("."),
            "invite": _invite(state),
            "unsorted": page_url(section["id"], page_of(section, sort)),
            "unsorted_line": {"link": link, "rest": rest},
        }
    document = state.version.document
    answered, minimum = _answered(state.response), minimum_observers(document)
    viewed = comparison_viewed(state.answers, sort)
    status, label = comparison_status(answered, minimum, viewed)
    invite = _invite(state)
    shown = invite.phrase if invite and invite.waiting else label
    warning = _freeze_warning(state.response, answered, minimum) if warns_beside_the_press(document) else None
    return {
        "sort": sort,
        "status": status,
        "label": shown,
        "invite": invite,
        "warning": warning,
        "signpost": _block_address(document, block["id"]),
    }


def _block_for_participant(
    document,
    block,
    answers,
    fixed,
    states,
    issued=None,
    frozen=False,
    drawn=None,
    demo=None,
    comparison=None,
    pairs_left=False,
    rows_back=None,
    coach_withdrew=False,
    observers_withdrew=0,
    observers_declined=0,
    saves_quietly=False,
    letter=None,
):
    """✨ One block as its template needs it. `states` are the track's sections as the hub sees them, keyed by
    identifier; a signpost to a section outside the participant's track has no state and shows nothing. `issued` is a
    link just issued, a coach's or an observer's. While answer collection is `frozen`, a contact list says why it adds
    nobody (ticket 55); otherwise it offers "Add another person" until it shows the most rows it may (ticket 70). Its
    rows come back from a press without JavaScript as `rows_back` gives them (fix-1). `drawn` is a `sort_results`
    block's results, from `_sort_results_drawn`, and `comparison` a `comparison_signpost`'s status, from
    `_comparison_signpost_shown`. A section signpost whose section's sort has `pairs_left`, from
    `_signposted_pairs_left`, is not yet finished. A sort not yet in starts from `demo`, a demo profile, with its guide
    beside it (fix-23). A coach checklist opens saying the coach withdrew while the response keeps that they did
    (`coach_withdrew`, ADR 0024). A contact list says how many observers withdrew, naming nobody
    (`observers_withdrew`), and how many declined (`observers_declined`, ticket 120). One that `saves_quietly` says
    nothing on a save (`blocks.saves_quietly`). A letter stands as `letter` says (`letter_shown`), and while it is
    sealed its answer is left out, so nothing on the page can carry it (ticket 104)."""
    rows = _contact_rows(block, answers, issued, **(rows_back or {})) if block["type"] == "contact_list" else None
    widget = BLOCK_TYPES[block["type"]].widget
    shown_widget = widget(document, "participant", "") if widget else None  # ✨ the participant's wording names no one
    if demo is not None and BLOCK_TYPES[block["type"]].scored and block["id"] not in answers:
        # ✨ Each item already in its bucket at its value, so the widget opens at "All sorted" (`placed` in sort.js).
        shown_widget = {**shown_widget, "placed": demo.sort}
    else:
        demo = None
    text = text_shown(document, block, "participant")
    is_checklist = block["type"] == "coach_checklist"
    link = states.get(block["section"]) if block["type"] == "section_signpost" else None
    results = None
    if link is not None:
        linked = section_by_id(document, block["section"])
        text, sort = signpost_shown(block, text, linked, link.status == COMPLETE and not pairs_left, "participant")
        results = reverse("results", args=[sort]) if sort else None
    return {
        "rows": rows,
        "rows_shown": len(rows) if rows is not None else None,
        "adds_rows": rows is not None and not frozen and can_add_row(len(rows)),
        "press": _press_of(block, rows) if rows is not None else None,
        "checklist": (
            _opening_checklist(text, _coach_kept(answers, block["id"]), issued, coach_withdrew)
            if is_checklist
            else None
        ),
        "id": block["id"],
        # ✨ The name its page's form sends its answer under, every answer on a page being sent at once
        # (sprint-3d-r1-fix-6).
        "field": page_field(block),
        "landing": landing_of(block),  # ✨ where saving it without JavaScript comes back to
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": text,
        "answer": None if letter is not None and letter["state"] == "sealed" else answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": shown_widget,
        "demo": demo,
        "link": link,
        "results": results,  # ✨ where a section signpost's button leads instead, once its section is done (ticket 61)
        "frozen": RESULTS_SEEN if frozen and block["type"] == "contact_list" else None,
        "withdrawn": withdrawn_sentence(observers_withdrew) if block["type"] == "contact_list" else None,
        "declined": declined_sentence(observers_declined) if block["type"] == "contact_list" else None,
        "drawn": drawn,
        "comparison": comparison,
        # ✨ While it waits on the comparison, its authored message, and it is drawn disabled (ticket 68).
        "waiting": comparison_wait_message(block, answers),
        "saves_quietly": saves_quietly,
        "letter": letter,
    }


def _opening_checklist(text, kept, issued=None, coach_withdrew=False):
    """✨ A coach checklist as a page opens it: the coach kept, if one was chosen, with their link; with none, that the
    last coach withdrew, while the response keeps it (ADR 0024); and otherwise its intro, empty, since nothing from an
    earlier visit to the checklist itself was kept."""
    if kept:
        return _checklist_screen(text, screen="chosen", coach=kept, issued=issued)
    if coach_withdrew:
        return _checklist_screen(text, screen="withdrawn")
    return _checklist_screen(text)


def _contact_rows(block, answers, issued=None, typed=None, asked=0, kept=()):
    """✨ A contact list's rows: each person on it in order, with their invitation while their link works and the link
    itself if it was just issued (`issued`, shown this once), then empty rows for the next people, as many as `asked`
    for in all if that is more (ticket 70). Each row is marked needed or optional by its place. `typed` is a person
    whose save was refused, shown as typed in their row, or for someone new in the first empty one, with why and the
    field at fault. `kept` is what was typed in the rows of the page pressed without JavaScript, any refusal with it,
    or else what the link just issued brought back: a person's in their row, and the empty rows' in order, each in the
    next empty row, with a row for each (fix-1). Each person's row carries `drawn`, their fingerprint as stored."""
    people = answers.get(block["id"]) or []
    if not kept and issued and any(person["id"] == issued["contact"] for person in people):
        kept = issued.get("kept", ())
    for_people = {typed_in["person"]: typed_in for typed_in in kept if typed_in.get("person") is not None}
    for_new = [typed_in for typed_in in kept if typed_in.get("person") is None]
    links = Invitation.objects.filter(contact_id__in=[person["id"] for person in people], expires_at__gt=timezone.now())
    working = {invitation.contact_id: invitation for invitation in links}
    rows = []
    for number in range(1, rows_of(block, len(people), max(asked, len(people) + len(for_new))) + 1):
        person = people[number - 1] if number <= len(people) else {"name": "", "email": "", "id": None}
        just_issued = issued and issued["contact"] == person["id"]
        rows.append(
            {
                "number": number,
                "is_needed": number <= needed(block),
                "contact_id": person["id"],
                "name": person["name"],
                "email": person["email"],
                "invitation": working.get(person["id"]),
                "issued": issued["link"] if just_issued else None,
                "drawn": _drawn(person["name"], person["email"]) if person["id"] else "",
            }
        )
    empty = (row for row in rows if row["contact_id"] is None)
    pairs = [(row, for_people[row["contact_id"]]) for row in rows if row["contact_id"] in for_people]
    for row, typed_in in [*pairs, *zip(empty, for_new)]:
        row.update(name=typed_in["name"], email=typed_in["email"])
        row.update({mark: typed_in[mark] for mark in ("refusal", "invalid") if mark in typed_in})
    if typed is not None:
        row = next((row for row in rows if row["contact_id"] == typed["contact_id"]), None)
        if row is not None:  # ✨ a full list has no empty row: its refusal is the list's own
            row.update(name=typed["name"], email=typed["email"], refusal=typed["refusal"], invalid=typed["invalid"])
    return rows
