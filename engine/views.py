# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

import json
import mimetypes
from typing import NamedTuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.humanize.templatetags.humanize import apnumber
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST

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
    CONTACTS,
    blocks_of,
    coach_brief,
    comparison_status,
    landing_of,
    link_shown,
    page_count,
    page_of,
    pages_of,
    section_of,
    translation_shown,
)
from engine.document.coach import (
    candidate_name_from_form,
    checklist_answers,
    checklist_answers_from_form,
    checklist_outcome,
    coach_answer_from_form,
    coach_details_as_typed,
    coach_from_form,
    commitments,
)
from engine.document.contacts import (
    LIST_FULL,
    MAX_CONTACTS,
    can_add_row,
    contact_from_form,
    needed,
    rows_of,
    voices_card,
)
from engine.document.aggregation import aggregate
from engine.document.gates import clauses_of, links_issued_key, opened_key, waits_on_comparison
from engine.document.scoring import score
from engine.hub import (
    COMPLETE,
    block_ids_fixed_on_completion,
    complete_sections,
    hub_for,
    is_locked,
    open_blocks,
    page_reached,
    section_by_id,
    track_sections,
    with_coach_answer,
)
from engine.document.observers import (
    link_lifetime,
    minimum_observers,
    privacy_notice,
    relationship_from_form,
    relationship_question,
)
from engine.document.photos import credits_listed
from engine.models import (
    CollectionFrozen,
    Contact,
    Invitation,
    ObserverResponse,
    PathwayVersion,
    Publication,
    Response,
    Result,
)
from engine import reminders, scenario_loading
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
        """✨ The page of a section this participant has reached, or None while the section is locked. Every way into
        a section (its address, "Continue →", completion, an answer or a checklist step) is guarded by this."""
        if is_locked(section, self.completed, self.answers, self.sections, self.moved_past):
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


def home(request):
    """✨ The public homepage (ticket 32a), the same for everyone; "Begin" leads to sign-up, or to the hub once
    signed in."""
    begin = reverse("hub") if request.user.is_authenticated else reverse("account_signup")
    return render(request, "engine/home.html", {"begin": begin})


def credits_page(request):
    """✨ The copyright notice of each translation the published pathway quotes, open to anyone, since the public
    homepage quotes scripture too. The publishers ask for their notices on the work's copyright page (ticket 39). After
    them, the credits of the pathway's photos that the document lists (ticket 49b)."""
    version = Publication.current_version()
    translations = version.document.get("translations", {}) if version else {}
    photo_credits = credits_listed(version.document) if version else []
    return render(
        request, "engine/credits.html", {"translations": translations.values(), "photo_credits": photo_credits}
    )


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
    hub = hub_for(state.sections, state.answers, state.completed, moved_past=state.moved_past)
    coach = _coach_of(state.response)
    return render(
        request,
        "engine/hub.html",
        {
            "title": text_for(state.version.document["title"], "participant"),
            "hub": hub,
            "photo": _photo_of(state.version.document, hub.next_step.id if hub.next_step else None),
            "coach_wait": _coach_wait_panel(state, hub, coach),
            "side_cards": _side_cards(state, hub, coach),
            "coach_card": _coach_card(state, hub, coach),
            "voices": _hub_voices(state, hub),
            "minimum": minimum_observers(state.version.document),
            "name": name_shown_for(state.response.participant) if state.response else None,
        },
    )


def _coach_section_of(document):
    """✨ The identifier of the section holding the document's coach checklist, or None for a document without one."""
    checklists = [block["id"] for block in blocks_of(document) if block["type"] == "coach_checklist"]
    return section_of(document, checklists[0])["id"] if checklists else None


def _side_cards(state, hub, coach):
    """✨ The hub's side cards, the coach's section's tagged with where the `coach` stands (ticket 51b)."""
    coach_section = _coach_section_of(state.version.document)
    return [
        with_coach_answer(card, coach["answer"] if coach else None) if card.id == coach_section else card
        for card in hub.side_cards()
    ]


def _coach_card(state, hub, coach):
    """✨ What the Walk with a coach card adds to a side card's own (ticket 65): {"section", "manage", "line"}, its
    "Manage" leading to the coach page, None while the card is locked, and its line while a section waits on the
    `coach` at all, None otherwise."""
    wait = hub.coach_wait
    return {
        "section": _coach_section_of(state.version.document),
        "manage": _coach_page_of(state.version.document, hub),
        "line": wait.line(coach["answer"] if coach else None) if wait is not None else None,
    }


def _coach_wait_panel(state, hub, coach):
    """✨ What the hub's next-step panel says in place of "Nothing is waiting for you right now" while nothing is next
    and a section waits on nothing but the coach's acceptance (ticket 65): {"heading", "sentence", "coach_page"}, by
    the `coach`'s answer, or None otherwise, or with no coach page to lead to."""
    wait = hub.coach_wait
    coach_page = _coach_page_of(state.version.document, hub)
    if hub.next_step is not None or wait is None or not wait.only or coach_page is None:
        return None
    wording = wait.panel(coach["answer"] if coach else None, coach["name"] if coach else "")
    return {**wording._asdict(), "coach_page": coach_page}


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
        steps = range(1, shown["page"]["count"] + 1)
        shown = {**shown, "photo": _photo_of(state.version.document, section["id"]), "steps": steps}
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
    """✨ The address of the page a block is on, at the block."""
    section = section_of(document, block_id)
    return f"{page_url(section['id'], page_of(section, block_id))}#block-{block_id}"


def participant_nav(request):
    """✨ The header and sidebar of every participant page (ticket 41a), as `engine/participant_header.html` needs them:
    the pathway's name, and unless the site switches it off, the sidebar. The sidebar's sections are the hub's own, so
    their statuses and locks are the hub's; a locked section carries no address, and neither does a page within it,
    such as the coach page. Results and the comparison are listed once there is a result, since before then they lead
    only back to the sort. `current` is the section whose page this is, if any."""
    state = _participant(request.user)
    if state.version is None:
        return {"title": None, "sidebar": None}
    document = state.version.document
    title = text_for(document["title"], "participant")
    if not settings.ANVILLE_SIDEBAR or not any(section["blocks"] for section in state.sections):
        return {"title": title, "sidebar": None}
    hub = hub_for(state.sections, state.answers, state.completed, moved_past=state.moved_past)
    links = []
    scored = _scored_block(document)
    if scored and Result.objects.filter(response=state.response, block_id=scored["id"]).exists():
        links += [
            ("Your results", reverse("results", args=[scored["id"]])),
            ("How others experience you", reverse("comparison", args=[scored["id"]])),
        ]
    links.append(("Invite others to assess you", reverse("invitations")))
    coach_page = _coach_page_of(document, hub)
    if coach_page:
        links.append(("Your coach", coach_page))
    return {
        "title": title,
        "sidebar": {
            "outline": hub.outline(),
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
    next_step = hub_for(state.sections, state.answers, state.completed).next_step
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
    # ✨ A link just issued, a coach's or an observer's, shown this once. Read only on a page holding a coach checklist or
    # a contact list, whose address is the path the cookie was set for, so deleting it here reaches it; the section's
    # later pages sit under that path too when the block is on its first.
    shows_links = any(block["type"] in LISTED_WITH_LINKS for block in pages_of(section)[page - 1])
    issued = _issued_link(request) if shows_links else None
    demo = _demo_prefill(request, state.version.document)
    shown_page = _section_page(state, section, page, issued=issued, demo=demo, asked_rows=_asked_rows(request))
    shown = _section_shown(request, state, section, shown_page)
    if issued is not None:
        shown["Cache-Control"] = "no-store"
        shown.delete_cookie(ISSUED_COOKIE, path=request.path)
    return shown


def _asked_rows(request):
    """✨ How many rows each contact list on a page was asked to show by "Add another person" without JavaScript
    (ticket 70), by its identifier, from the address that press leads to: `?rows-<block>=<rows>`."""
    prefix = "rows-"
    return {
        key.removeprefix(prefix): int(value)
        for key, value in request.GET.items()
        if key.startswith(prefix) and value.isdigit()
    }


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


# ✨ The blocks whose people are listed with their links: a coach checklist's coach, and a contact list's people.
LISTED_WITH_LINKS = ("coach_checklist", "contact_list")


@login_required
@consent_required
@require_POST
def move_past_page(request, section_id, page):
    """✨ "Continue →" from one page of a section to the next, allowed exactly when the page offers it: once that page's
    clauses pass and nothing on the way to it (an unconfirmed reading, a held link) holds what follows. Re-checked here
    rather than trusted to the page. The last page has no way on but completing the section."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    if _page_or_404(section, page) == page_count(section):
        raise Http404("The last page of a section is moved past by completing it.")
    if page > reached:
        return _see_other(page_url(section_id, reached))
    shown = _section_page(state, section, page)
    if not shown["offers_way_on"] or shown["unmet"]:
        return _section_shown(request, state, section, {**shown, "refused": True}, status=400)

    state.stored_response(request.user).move_past_page(section_id, page)
    return _see_other(page_url(section_id, page + 1))


@login_required
@consent_required
@require_POST
def complete_section(request, section_id):
    """✨ The participant's own act of finishing a section, re-checked here rather than trusted to the page. It is
    done from the section's last page, so a participant who has not reached it is sent to the page they have. A part of
    a section, or a hub side card, has no completion of its own: it is complete once its gate passes."""
    state = _participant(request.user)
    section = _section_or_404(state.version, section_id)
    if _completes_itself(section):
        raise Http404("This section is complete once its gate passes, with no completion of its own.")
    reached = state.reached(section)
    if reached is None:
        return redirect("hub")
    last = page_count(section)
    if reached < last:
        return _see_other(page_url(section_id, reached))
    if unmet(section, state.answers):
        shown = _section_page(state, section, last)
        return _section_shown(request, state, section, {**shown, "refused": True}, status=400)

    fixed_block_ids = block_ids_fixed_on_completion(section, state.answers)
    state.stored_response(request.user).complete_section(section_id, fixed_block_ids=fixed_block_ids)
    # ✨ Back to the hub, which points at the next step, as the prototype's `completePillar` goes (ticket 41b).
    return _see_other("hub")


@login_required
@consent_required
@require_POST
def reopen_section(request, section_id):
    """✨ The participant taking back their own completion. Their answers stay exactly as they left them. A section that
    completes itself was never theirs to take back, and a side card stays complete (ticket 52). Nor is a wizard's, which
    the hub never asks for again once given (ticket 50)."""
    state = _participant(request.user)
    if not _reopens(_section_or_404(state.version, section_id)):
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
    if not _is_open(state, section, block):
        return _refuse_shut(request)
    if block_id in state.fixed:
        # ✨ Refused here, not only disabled on the page, so a page left open from before completing cannot change it.
        return _answer_refused(request, state, section, block_id, FIXED_REFUSAL, status=409)
    if waits_on_comparison(block, state.answers):
        # ✨ Refused here, not only disabled on the page, so the reflection is written only once its comparison has been
        # seen (ADR 0019).
        refusal = text_for(block["after_comparison"]["message"], "participant")
        return _answer_refused(request, state, section, block_id, refusal, status=403)
    block_type = BLOCK_TYPES[block["type"]]
    try:
        value = answer_from_form(state.version.document, block, request.POST.get("value"))
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
            refusal = "Your results are already in. Retaking the sort is not offered yet."
            return _answer_refused(request, state, section, block_id, refusal, status=409)
        # ✨ A sort too close to call on one framework or both, and not flat, leads to the tie-break's pairs first.
        if pair_plan(state.version.document, scores):
            return _go_to(request, _with_demo_profile(request, reverse("tie_break", args=[block_id])))
        return _to_results(request, block_id)
    if not participant_response.save_answer(block_id, value):
        # ✨ a completion fixed it after the check above, and the UPDATE saw that
        return _answer_refused(request, state, section, block_id, FIXED_REFUSAL, status=409)
    return _saved(request, saved, section, block_id)


def _answer_refused(request, state, section, block_id, refusal, status):
    """✨ An answer not saved, and why: with htmx, the status line beside it; without, its page again, the reason shown
    at the answer. A form submitted as a full page (Enter in an answer field does that) never lands the participant on
    the bare status line (fix-7)."""

    def its_page(status):
        shown = _section_page(state, section, page_of(section, block_id))
        on_page = next(block for block in shown["section"]["blocks"] if block["id"] == block_id)
        on_page["refusal"] = refusal
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
    keeps only the chosen coach's name and email address, as a contact, and only once the outcome allows it.
    """
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "coach_checklist")
    section = section_of(state.version.document, block_id)
    if not _is_open(state, section, block):
        return _refuse_shut(request)
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
        return _see_other(f"{page_url(section['id'], page)}#block-{block_id}")
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
        return {**going_ahead, **coach_details_as_typed(posted), "refusal": str(refused), "invalid": refused.field}


def _checklist_screen(
    text,
    screen="intro",
    name="",
    answers=None,
    outcome=None,
    refusal=None,
    confident=False,
    coach=None,
    email="",
    confirmed=False,
    invalid=None,
    kept=None,
    issued=None,
):
    """✨ One screen of the coach checklist as its template needs it: the questions with any answers given, and on
    a second thought or a stop, each answer that was not Yes with why that question matters. On going ahead, the
    coach's details as typed, and which of them a refusal is about; once chosen, the coach kept, with their link
    (`issued` is a link just issued, shown this once). On the intro while choosing again, `kept` is the coach who
    stays until another is saved."""
    answers = answers or {}
    questions = [{**question, "answer": answers.get(question["id"])} for question in text["questions"]]
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
        "email": email,
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
    answer ("waiting" while a working link is unanswered, None with no link at all), and the link itself if it was
    just issued. An answer outlasts the link's expiry, but not its revoking: it belongs to the link it came through."""
    invitation = Invitation.objects.filter(contact_id=contact_id).first()
    live = invitation if invitation is not None and invitation.works() else None
    answer = invitation.coach_answer if invitation is not None else None
    return {
        "contact_id": contact_id,
        "invitation": live,
        "answer": answer or ("waiting" if live else None),
        "issued": issued["link"] if issued and issued["contact"] == contact_id else None,
    }


def _saved(request, state, section, block_id):
    """✨ What a stored answer sends back: with htmx, the status and its page's gate; without, its page again.

    A block that opens what follows (a reading) lands at its confirmation, with what it opened beneath, rather than
    back at its top above what was just read (ticket 41e).
    """
    page = page_of(section, block_id)
    if request.headers.get("HX-Request") == "true":
        shown = _section_page(state, section, page)
        return render(request, "engine/save_result.html", shown)
    block = next(block for block in section["blocks"] if block["id"] == block_id)
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
    context = {"drawn": drawn, "results": drawn["results"], "section": section, "retake": _demo_tools_on()}
    return render(request, "engine/results.html", context)


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
    choice beside the sort's result and comes back here for the next. Only the participant's own result is read, so an
    observer's sort never leads here."""
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
        if not 0 <= place < len(plan) or (chosen is not None and chosen not in plan[place]["constructs"]):
            refusal = "That is not one of this pair’s answers."
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=400)
        # ✨ A pair already answered (a form sent twice, or from a stale tab) stores nothing; either way the next is shown.
        result.answer_pair(place, plan[place], chosen)
        _scores_shown_storing_reweighted(state.version.document, result)  # ✨ the last answer re-weights the result
        return _see_other(_with_demo_profile(request, reverse("tie_break", args=[block_id])))
    place = len(result.tie_break_answers)
    if place >= len(plan):
        return redirect("results", block_id)
    shown = pair_page(state.version.document, plan, place)
    # ✨ Demo only (fix-23): after a demo profile's sort, its guide beside the pair.
    demo = _demo_prefill(request, state.version.document)
    return render(request, "engine/tie_break.html", {"pair": shown, "block_id": block_id, "demo": demo})


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
    """✨ The participant's self-result beside the observer average (ADR 0005), reached from the results page and, like
    it, open to anyone with a result, whatever sections they have done. Below the minimum it shows how many have
    answered and no numbers; it never shows which person has answered, and single observers' percents only in the
    distribution strip, in ascending order."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return redirect(page_url(section["id"], section["page"]))
    scores = _scores_shown_storing_reweighted(state.version.document, result)
    shown = _comparison_of(state.response, scores, state.answers[block_id])
    sort = next(block for block in blocks_of(state.response.version.document) if block["id"] == block_id)
    context = {
        "comparison": shown,
        "block_id": block_id,
        "coach": _coach_sharing(state.response, block_id),
        "brief": coach_brief(sort),
        "back": section["back"],
    }
    return render(request, "engine/comparison.html", context)


@login_required
@consent_required
@require_POST
def share_with_coach(request, block_id):
    """✨ The comparison's "Give my coach access to my results and this comparison", ticked or not (ticket 27). Ticking is refused until the
    participant has visited their comparison and their coach has accepted through a link that still works; the consent
    is then kept on that link, so it goes with it (ADR 0011). Unticking withdraws it at once, whatever else holds.

    The box saves as it changes: with htmx, "Saved" and the line under it for the new state; without, the comparison
    again, at the box."""
    state, result, _ = _own_result(request.user, block_id)
    if request.POST.get("share") != "on":
        Invitation.withdraw_results_from_coach(request.user)
    else:
        visited = result is not None and block_id in state.response.comparisons_visited
        if not (visited and Invitation.share_results_with_coach(state.response)):
            refusal = "Your coach can see this only once they have accepted and you have seen your comparison."
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=403)
    if request.headers.get("HX-Request") == "true":
        return render(request, "engine/coach_share_saved.html", {"coach": _coach_sharing(state.response, block_id)})
    return _see_other(f"{reverse('comparison', args=[block_id])}#coach-share")


def _comparison_of(response, scores, sort):
    """✨ The comparison of one participant's result with their observers, as both they and their coach see it."""
    document = response.version.document
    assessments = ObserverResponse.assessments_for(response)
    shown = comparison_page(document, scores, sort, aggregate(document, assessments.assessments))
    # ✨ Below the minimum there is no comparison on the page to call illustrative.
    shown["illustrative"] = assessments.all_test_data and shown["frameworks"] is not None
    return shown


def _coach_sharing(response, block_id):
    """✨ The participant's coach as the comparison's consent needs them, or None when there is nothing to say: with
    `offer` "tick" once they accepted through a working link and the comparison was visited by its button; "expired"
    when they accepted but the link no longer works; "awaiting" while they have not answered or have no link yet. A
    coach who declined is offered nothing here: the coach page already says so."""
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


def _coach_of(response):
    """✨ The coach kept, as the hub and the comparison read them, or None: their name, the coach page, their answer as
    the coach page tells it, whether they can be shown the results (accepted through a working link) and whether they
    are."""
    coach = response.contacts.filter(role=Contact.Role.COACH).first() if response is not None else None
    if coach is None:
        return None
    accepted = Invitation.accepted_coach_of(response)
    return {
        "name": coach.name,
        "coach_page": _listed_at(coach),
        "answer": _coach_link_state(coach.pk)["answer"],
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
        answered = len(ObserverResponse.assessments_for(state.response).assessments) if state.response else 0
        shown = voices_card(block, card, invited, answered, minimum_observers(document), frozen=_frozen(state.response))
        return {"section": section_id, **shown}
    return None


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
    confirms, which freezes collection, then goes on as before (ticket 55). Below the minimum nothing is asked.

    A press with the minimum in, confirmed or with collection already frozen, is also the view a comparison link's
    "Viewed" reads (ticket 67a), kept once withdrawals unfreeze collection."""
    state, result, section = _own_result(request.user, block_id)
    if result is None:
        return _see_other(page_url(section["id"], section["page"]))
    response = state.response
    answered = len(ObserverResponse.assessments_for(response).assessments)
    viewed = answered >= minimum_observers(state.version.document)
    if response.collection_frozen_at is None and viewed:
        if request.POST.get("confirmed") != "yes":
            invited = response.contacts.filter(role=Contact.Role.CONTACT).count()
            context = {"block_id": block_id, "answered": answered, "invited": invited, "everyone": answered >= invited}
            return render(request, "engine/comparison_confirm.html", context)
        # ✨ Counted again under the freeze's lock: a withdrawal since may have left fewer than the minimum.
        viewed = response.freeze_collection()
    response.visit_comparison(block_id, viewed=viewed)
    return _see_other("comparison", block_id)


def _demo_tools_on():
    """✨ Whether this is a development or demo system, where tools that write made-up data or take back a
    participant's answers are offered: DEBUG on, or a demo notice set, as for `seed_tie_break` (fix-15). A production
    deployment has neither."""
    return bool(settings.DEBUG or settings.ANVILLE_DEMO_NOTICE)


@login_required
@consent_required
@require_http_methods(["GET", "POST"])
def retake(request, block_id):
    """✨ Demo only (fix-19): the results page's quiet "Retake the assessment (demo only)" asks first, saying what will
    be cleared; only its button clears the participant's own sort and everything worked out from it, then opens the
    sort afresh. Off a development or demo system it is a 404.

    It also offers a demo profile (fix-21): one of `seed_tie_break`'s starting profiles, and how to answer its pairs,
    chosen apart (fix-25), as a combination that holds on this pathway. Once the old sort is cleared, the sort opens
    with the profile's cards placed and its sliders set, beside its guide to those answers, and nothing is stored until
    the participant sends it (fix-23). Before any sort, from the sort page's hidden link, the same choice clears
    nothing, and only for a participant the sort is open to. A combination not offered is refused with its reason and
    nothing cleared.

    A section completed whose gate needed the sort is no longer complete, so the hub never shows it complete beside an
    assessment not started; the participant's other answers in it stay, and completing it again needs the new sort."""
    if not _demo_tools_on():
        raise Http404("Retaking the assessment is offered only on a development or demo system.")
    state, result, section = _own_result(request.user, block_id)
    sort_page = page_url(section["id"], section["page"])
    document = state.version.document
    # ✨ Before any sort, only a participant the sort is open to may have one loaded for them (fix-21).
    if result is None and not _is_open(state, section_of(document, block_id), answerable_block(document, block_id)):
        return redirect(sort_page)
    # ✨ Worked out on every visit, so a combination that does not hold on this pathway is never offered (fix-21).
    offer = scenario_loading.offered(document)
    response = state.response
    reopened = []
    if result is not None:
        reopened = [
            shown
            for shown in state.sections
            if shown["id"] in response.completed_sections
            and _reopens(shown)
            and any(clause["block"] == block_id for clause in clauses_of(shown))
        ]
    if request.method == "POST":
        profile = request.POST.get(scenario_loading.PROFILE_FIELD, MYSELF)
        answers = request.POST.get(scenario_loading.ANSWERS_FIELD) or None
        refusal = None if profile == MYSELF else scenario_loading.refusal(offer, profile, answers)
        if refusal is not None:
            return render(request, "engine/save_status.html", {"refusal": refusal}, status=400)
        if result is not None:
            response.clear_sort(block_id, reopened=[shown["id"] for shown in reopened])
        if profile == MYSELF:
            return _see_other(sort_page)
        # ✨ Nothing stored: the sort starts from the profile, and the participant sends it themselves (fix-23).
        return _see_other(f"{sort_page}?{scenario_loading.demo_query(profile, answers)}")
    context = {
        "block_id": block_id,
        "clearing": result is not None,
        "sort_page": sort_page,
        "offer": offer,
        "myself": MYSELF,
        "reopened": [text_for(shown["title"], "participant") for shown in reopened],
        "tie_break": bool(result and result.tie_break_answers),
        "frozen": result is not None and response.collection_frozen_at is not None,
        "coach_shown": result is not None and bool((_coach_of(response) or {}).get("shared")),
    }
    return render(request, "engine/retake.html", context)


# ✨ The retake page's "Sort the cards myself", as its choice sends it (fix-21).
MYSELF = "myself"

def _demo_prefill(request, document):
    """✨ Demo only (fix-23): the demo profile and answers the address names (fix-25), as `scenario_loading.prefill`
    gives them, or None: off a development or demo system, with no profile named, or with a combination not offered on
    this pathway."""
    profile = request.GET.get(scenario_loading.PROFILE_FIELD)
    if not profile or not _demo_tools_on():
        return None
    return scenario_loading.prefill(document, profile, request.GET.get(scenario_loading.ANSWERS_FIELD) or None)


def _with_demo_profile(request, url):
    """✨ `url` naming the same demo profile and answers as this request's address, on a development or demo system
    (fix-23), so the pairs that follow a demo profile's sort show its guide too."""
    profile = request.GET.get(scenario_loading.PROFILE_FIELD)
    if not profile or not _demo_tools_on():
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
    back = _section_this_is_part_of(state, section) or {"title": title, "href": page_url(section["id"], page)}
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
    list is touched, so a page left open since someone else was added never drops them."""
    state = _participant(request.user, first_version=lambda: _published_version(request.POST.get("version")))
    block = _block_of_type(state.version, block_id, "contact_list")
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    if _frozen(state.response):
        return _refuse_frozen(request, state, block)
    try:
        person = contact_from_form(request.POST.get("name"), request.POST.get("email"))
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


@login_required
@consent_required
@require_POST
def contact(request, block_id, contact_id):
    """✨ Change one person's name or email address, and theirs alone (ticket 51a), as the row saves on a change with
    JavaScript, or by its Save button without (fix-2). Their link keeps working. Another participant's contact, or one
    from another list, is a 404 that says nothing of whether it exists."""
    state, block, person = _listed_person(request, block_id, contact_id)
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
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
        context = {"person": person, "back": _listed_at(person), "has_live_link": person.live_invitation() is not None}
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
    showing one more row than the page it was pressed on (`rows`), each person in theirs. Refused once the list shows
    the most it may hold, and while answer collection is frozen, when nobody can be added."""
    state = _participant(request.user)
    block = _block_of_type(state.version, block_id, "contact_list")
    shut = _list_shut(request, state, block)
    if shut is not None:
        return shut
    if _frozen(state.response):
        return _refuse_frozen(request, state, block)
    posted = request.POST.get("rows", "")
    shown = rows_of(block, len(state.answers.get(block_id) or []), int(posted) if posted.isdigit() else 0)
    if not can_add_row(shown):
        return _refused(
            request, LIST_FULL, status=400, page=lambda status: _list_page(request, state, block, status, LIST_FULL)
        )
    number = shown + 1
    if _is_htmx(request):
        context = {
            "row": _empty_row(block, number),
            "block": {"id": block_id, "rows_shown": number, "adds_rows": can_add_row(number)},
            "pathway": {"version_id": state.version.pk},
        }
        return render(request, "engine/contact_row_added.html", context)
    section = section_of(state.version.document, block_id)
    page = page_url(section["id"], page_of(section, block_id))
    return _see_other(f"{page}?rows-{block_id}={number}#{block_id}-row-{number}")


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
        return _refuse_shut(request)
    return None


def _person_refused(request, state, block, refused, contact_id=None):
    """✨ The list's page again, saying why one person was not saved, with what was typed in their row (or, for someone
    new, the first empty one) and the field at fault marked, so nothing typed is lost."""
    typed = {
        "contact_id": contact_id,
        "name": request.POST.get("name", ""),
        "email": request.POST.get("email", ""),
        "refusal": str(refused),
        "invalid": refused.field,
    }
    if _is_htmx(request):
        # ✨ Their row alone, as typed, where they typed it (fix-2).
        rows = _contact_rows(block, state.answers, typed=typed)
        row = next((row for row in rows if row["contact_id"] == contact_id), None) or _empty_row(block, 0)
        row = _as_typed_in(request, block, {**row, **{key: typed[key] for key in typed if key != "contact_id"}})
        return _rows_sent_back(request, state, block, [row], status=400)
    section = section_of(state.version.document, block["id"])
    shown = _section_page(state, section, page_of(section, block["id"]))
    on_page = next(shown_block for shown_block in shown["section"]["blocks"] if shown_block["id"] == block["id"])
    # ✨ As many rows as the page they typed in had shown, so a row "Add another person" added is still there
    # (ticket 70).
    posted = request.POST.get("row", "")
    on_page["rows"] = _contact_rows(block, state.answers, typed=typed, asked=int(posted) if posted.isdigit() else 0)
    if not any(row.get("refusal") for row in on_page["rows"]):
        on_page["refusal"] = typed["refusal"]
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


def _list_page(request, state, block, status, refusal=None):
    """✨ The page a contact list is on, as it now stands, with `refusal`, if given, on the list's own line."""
    section = section_of(state.version.document, block["id"])
    shown = _section_page(state, section, page_of(section, block["id"]))
    if refusal is not None:
        on_page = next(shown_block for shown_block in shown["section"]["blocks"] if shown_block["id"] == block["id"])
        on_page["refusal"] = refusal
    return _section_shown(request, state, section, shown, status=status)


def _refuse_shut(request):
    """✨ A press on something the participant has not reached (an answer, a coach checklist step, a change to a contact
    list): with htmx, the short status line beside it; without, a page saying why, since the page it was on is shut
    too (ticket 71)."""
    return _refused(request, NOT_OPEN, status=403)


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


def _back_with_issued(request, contact, link):
    """✨ A redirect to where the contact is listed, carrying the link just issued for that page to show this once."""
    listed_at = _listed_at(contact)
    back = _see_other(listed_at)
    back.set_signed_cookie(
        ISSUED_COOKIE,
        json.dumps({"contact": contact.pk, "link": link}),
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


@require_POST
def start_observing(request, token):
    """✨ The observer's "I'm answering for Sam": the claim. Their own link is shown this once, straight back rather
    than by redirect so it never sits in the history, and kept in a cookie so they need not follow it; the
    participant's copy is used up. A second claim is told the link has been used, so whoever claimed first is
    noticed, not hidden.

    Only the claim sets the cookie, never a plain visit: this is a POST that carries a CSRF token, so no other site
    can put someone else's claim in an observer's browser by sending it to a link.
    """
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
    """✨ The observer's page for a link just claimed, showing their own link this once and leaving it in a cookie."""
    invitation = Invitation.claimed_by(secret)
    own_link = request.build_absolute_uri(reverse("observe", args=[secret]))
    shown = _observers_page(request, secret, own_link=own_link)
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
    """✨ The observer's own page, reached by the cookie their claim left."""
    return _observers_page(request, request.COOKIES.get(OBSERVER_COOKIE))


def coaching(request, token):
    """✨ Where the coach's link leads: who asked them, and the commitments to accept or decline; once answered, their
    answer. A wrong, expired or revoked link, or an observer's, gets the observers' one refusal, naming nobody.

    The coach has no account and claims nothing (spec, Coach): nothing here reads or writes the signed-in user.
    """
    invitation = Invitation.live(token, role=Contact.Role.COACH)
    if invitation is None:
        return _refuse_link(request)
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
    """✨ The participant's results and comparison, as they see them, for a coach who accepted through this link and
    whom they are happy to show; otherwise None. Read afresh on every visit, so a withdrawal shows at once (ticket 27).
    Nothing else of the participant's is read: only the stored result, the sort it was scored from and the observers'
    assessments, through the same suppression as the participant's own comparison."""
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
        "results": results_page(document, scores, sort, name),
        "comparison": _comparison_of(participant_response, scores, sort),
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
    which now says thank you.

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
        refusal = "Your assessment has already been sent."
        return render(request, "engine/save_status.html", {"refusal": refusal}, status=409)
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
    """
    secret = request.COOKIES.get(OBSERVER_COOKIE) if token is None else token
    invitation = Invitation.claimed_by(secret, for_withdrawal=True)
    if invitation is None:
        return _refuse_link(request)
    _, name = _asked_by(invitation)
    action = reverse("withdrawal") if token is None else reverse("withdrawal_by_link", args=[token])
    if request.method == "POST":
        ObserverResponse.withdraw(secret)
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


def _observers_page(request, secret, own_link=None, came_by_link=False):
    """✨ The observer's page for the invitation a secret claimed, or the refusal if there is none: the observer
    assessment until it is sent, then thanks. While answer collection is frozen, one who has not sent is told no more
    answers are being taken, and offered no assessment (ticket 55). `own_link` is their link, shown only as they claim
    it. An observer who `came_by_link` rather than by the cookie sends the assessment through that link. Never cached,
    since it is reached by a secret."""
    invitation = Invitation.claimed_by(secret)
    if invitation is None:
        return _refuse_link(request)
    document, name = _asked_by(invitation)
    scored = _scored_block(document)
    sent = ObserverResponse.sent_with(secret)
    frozen = not sent and invitation.contact.response.collection_frozen_at is not None
    assessment = None
    if scored and not sent and not frozen:
        assessment = {
            "id": scored["id"],
            "widget": BLOCK_TYPES[scored["type"]].widget(document, "observer", name),
            "action": reverse("send_assessment_by_link", args=[secret]) if came_by_link else reverse("send_assessment"),
            "relationship": relationship_question(document, name),
        }
    withdraw_at = reverse("withdrawal_by_link", args=[secret]) if came_by_link else reverse("withdrawal")
    context = {
        "name": name,
        "own_link": own_link,
        "assessment": assessment,
        "sent": sent,
        "frozen": NO_MORE_ANSWERS if frozen else None,
        "withdraw_at": withdraw_at,
    }
    shown = render(request, "engine/observer.html", context)
    shown["Cache-Control"] = "no-store"
    return shown


def _scored_block(document):
    """✨ The document's scored block, whose assessment observers make about the participant so it can be set beside
    the participant's own, or None for a document without one."""
    return next((block for block in blocks_of(document) if BLOCK_TYPES[block["type"]].scored), None)


def _refuse_link(request):
    """✨ The one refusal for a wrong, expired or revoked link, or an observer's own link or cookie that no longer
    works: the same for all, naming nobody."""
    return render(request, "engine/link_refused.html", status=404)


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
    """✨ The address of one page of a section. The first is the section's own address, as before it had pages.
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
    sections = track_sections(participant_response.version.document)
    answers = participant_response.answers_with_contacts_and_visits()
    # ✨ A part of a section, or a hub side card, is complete once its gate passes, so locks and the hub count it without
    # a completion.
    completed = complete_sections(sections, answers, participant_response.completed_sections)
    # ✨ A side card's completion is stored the first time it is seen, so it stays complete once its links expire or are revoked, or
    # its people are taken off the list, and never locks again what it opened (ticket 52).
    stored = participant_response.completed_sections
    for section in sections:
        if "side_card" in section and section["id"] in completed and section["id"] not in stored:
            participant_response.complete_section(section["id"])
    # ✨ Likewise the first time a section with opening conditions is open, so it stays open once the coach's link is
    # revoked or reissued, or the coach changed (ADR 0019).
    moved_past = participant_response.moved_past_by_section()
    for section in sections:
        if (
            "opens_when" in section
            and opened_key(section["id"]) not in answers
            and not is_locked(section, completed, answers, sections, moved_past)
        ):
            participant_response.open_section(section["id"])
            answers[opened_key(section["id"])] = True
    return ParticipantState(
        response=participant_response,
        version=participant_response.version,
        sections=sections,
        answers=answers,
        completed=completed,
        moved_past=moved_past,
        fixed=set(participant_response.fixed_answers),
    )


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


def _section_page(state, section, page=1, issued=None, demo=None, asked_rows=None):
    """✨ One page of a section as its template needs it. Every page but the last ends in "Continue →", held by that
    page's own clauses; the last ends in the section's completion, held by the whole gate. `issued` is a link just
    issued, a coach's or an observer's, which the page shows this once beside the person it is for. `demo` is a demo
    profile, from `_demo_prefill`, that a sort not yet in starts from (fix-23). `asked_rows` is how many rows each
    contact list was asked to show, by its identifier, from `_asked_rows` (ticket 70)."""
    asked_rows = asked_rows or {}
    version, answers, fixed = state.version, state.answers, state.fixed
    opened, activity_open = open_blocks(section, answers, state.sections, up_to_page=page)
    on_page = {block["id"] for block in pages_of(section)[page - 1]}
    blocks = [block for block in opened if block["id"] in on_page]
    is_last = page == page_count(section)
    # ✨ A sort leads only to its results, as in the prototype, so completing is not offered beside it until it
    # is in. The linter makes its section's gate require it, so the server refuses completion before then too.
    sort_pending = any(BLOCK_TYPES[block["type"]].scored and block["id"] not in answers for block in blocks)
    # ✨ A link shows the section it leads to exactly as the hub would: its title, its status and whether it is open.
    hub = hub_for(state.sections, answers, state.completed, moved_past=state.moved_past)
    links = _requirement_links(state, section)
    gate_checklist = [(message, met, links.get(message)) for message, met in checklist(section, answers, page=page)]
    states = {other.id: other for other in hub.sections}
    return {
        # ✨ Where "← Back" at the top leads: the section this is a part of, or else the hub.
        "back": _section_this_is_part_of(state, section),
        "page": {
            "number": page,
            "count": page_count(section),
            "is_last": is_last,
        },
        "pathway": {
            "version_id": version.pk,
            "scale_points": SCALE_POINTS,
            "long_text_max_length": LONG_TEXT_MAX_LENGTH,
        },
        "section": {
            "id": section["id"],
            "title": text_for(section["title"], "participant"),
            "estimate": states[section["id"]].estimate,
            "complete_label": text_for(section.get("complete_label", "Mark complete"), "participant"),
            "is_part": "part_of" in section,
            "is_side_card": "side_card" in section,
            "reopens": _reopens(section),
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
                    comparison=_comparison_link_shown(state, block),
                    asked_rows=asked_rows.get(block["id"], 0),
                )
                for block in blocks
            ],
        },
        "is_complete": section["id"] in state.completed,
        # ✨ Demo only (fix-21): a sort not yet in offers a hidden "Load a demo profile (demo only)", where one holds.
        "demo_profile": sort_pending and _demo_tools_on() and bool(scenario_loading.offered(version.document).profiles),
        # ✨ Over the whole section, since the ratings it fixed may be on an earlier page than its completion.
        "holds_fixed_answers": any(block["id"] in fixed for block in section["blocks"]),
        # ✨ The way on, "Continue →" or completion. Going on from a page is refused on exactly these and `unmet`.
        "offers_way_on": activity_open and not sort_pending,
        # ✨ What the checklist marks unmet: on the last page, where completing checks it, the whole gate.
        "unmet": [message for message, met, _ in gate_checklist if not met],
        "checklist": gate_checklist,
    }


def _completes_itself(section):
    """✨ Whether a section is complete once its gate passes, with no completion of its own to press: a part of a section
    (ticket 41b), or a hub side card (ticket 52)."""
    return "part_of" in section or "side_card" in section


def _reopens(section):
    """✨ Whether the participant can take back a section's completion: not one that completes itself, nor a wizard,
    which once complete is never asked for again (ticket 50)."""
    return not _completes_itself(section) and not section.get("wizard")


def _section_this_is_part_of(state, section):
    """✨ The section a part of a section belongs to, as its ways back name it: {"title", "href"}, at the page of it the
    participant has reached. None for a section that is not a part, or whose section is outside the track or locked."""
    parent_section = section_by_id(state.version.document, section["part_of"]) if "part_of" in section else None
    reached = state.reached(parent_section) if parent_section else None
    if reached is None:
        return None
    return {"title": text_for(parent_section["title"], "participant"), "href": page_url(parent_section["id"], reached)}


def _requirement_links(state, section):
    """✨ Where each of a section's requirements met on another page is met, by its message (ticket 41b): a coach's link
    on the coach page, people's links on the invitations page. One whose page is not open yet is left out, and so is one
    met in this section itself, as on a hub side card (ticket 52)."""
    document = state.version.document
    links = {}
    for clause in clauses_of(section):
        if clause["type"] != "links_issued":
            continue
        block = next(block for block in blocks_of(document) if block["id"] == clause["block"])
        if section_of(document, block["id"])["id"] == section["id"]:
            continue
        if not _is_open(state, section_of(document, block["id"]), block):
            continue
        is_coach = block["type"] == "coach_checklist"
        links[text_for(clause["message"], "participant")] = (
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


def _comparison_link_shown(state, block):
    """✨ For a `comparison_link` block, its sort and where the way to that sort's comparison stands, as
    `comparison_status` words it, once there is a result; None before, and for any other block (ticket 67a)."""
    if block["type"] != "comparison_link":
        return None
    sort = block["sort"]
    if not Result.objects.filter(response=state.response, block_id=sort).exists():
        return None
    answered = len(ObserverResponse.assessments_for(state.response).assessments)
    viewed = sort in state.response.comparisons_viewed
    status, label = comparison_status(answered, minimum_observers(state.version.document), viewed)
    return {"sort": sort, "status": status, "label": label}


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
    asked_rows=0,
):
    """✨ One block as its template needs it. `states` are the track's sections as the hub sees them, keyed by
    identifier; a link to a section outside the participant's track has no state and shows nothing. `issued` is a
    link just issued, a coach's or an observer's. While answer collection is `frozen`, a contact list says why it adds
    nobody (ticket 55); otherwise it offers "Add another person" until it shows the most rows it may, at least
    `asked_rows` of them (ticket 70). `drawn` is a `sort_results` block's results, from `_sort_results_drawn`, and
    `comparison` a `comparison_link`'s status, from `_comparison_link_shown`. A sort not yet in starts from `demo`, a
    demo profile, with its guide beside it (fix-23)."""
    rows = _contact_rows(block, answers, issued, asked=asked_rows) if block["type"] == "contact_list" else None
    widget = BLOCK_TYPES[block["type"]].widget
    shown_widget = widget(document, "participant", "") if widget else None  # ✨ the participant's wording names no one
    if demo is not None and BLOCK_TYPES[block["type"]].scored and block["id"] not in answers:
        # ✨ Each item already in its bucket at its value, so the widget opens at "All sorted" (`placed` in sort.js).
        shown_widget = {**shown_widget, "placed": demo.sort}
    else:
        demo = None
    text = authored_text(block, "participant")
    if block["type"] == "scripture_reading":
        for passage, shown in zip(block["passages"], text["passages"]):
            shown["translation"] = translation_shown(document, passage)
    is_checklist = block["type"] == "coach_checklist"
    link = states.get(block["section"]) if block["type"] == "section_link" else None
    results = None
    if link is not None:
        linked = section_by_id(document, block["section"])
        text, sort = link_shown(block, text, linked, link.status == COMPLETE, "participant")
        results = reverse("results", args=[sort]) if sort else None
    return {
        "rows": rows,
        "rows_shown": len(rows) if rows is not None else None,
        "adds_rows": rows is not None and not frozen and can_add_row(len(rows)),
        "checklist": _opening_checklist(text, _coach_kept(answers, block["id"]), issued) if is_checklist else None,
        "id": block["id"],
        "landing": landing_of(block),  # ✨ where saving it without JavaScript comes back to
        "type": block["type"],
        "template": f"engine/blocks/{block['type']}.html",
        "variant": block.get("variant", "plain"),
        "text": text,
        "answer": answers.get(block["id"]),
        "is_fixed": block["id"] in fixed,
        "widget": shown_widget,
        "demo": demo,
        "link": link,
        "results": results,  # ✨ where a section link's button leads instead, once its section is complete (ticket 61)
        "frozen": RESULTS_SEEN if frozen and block["type"] == "contact_list" else None,
        "drawn": drawn,
        "comparison": comparison,
        # ✨ While it waits on the comparison, its authored message, and it is drawn disabled (ticket 68).
        "waiting": text_for(block["after_comparison"]["message"], "participant")
        if waits_on_comparison(block, answers)
        else None,
    }


def _opening_checklist(text, kept, issued=None):
    """✨ A coach checklist as a page opens it: the coach kept, if one was chosen, with their link, and otherwise its
    intro, empty, since nothing from an earlier visit to the checklist itself was kept."""
    if kept:
        return _checklist_screen(text, screen="chosen", coach=kept, issued=issued)
    return _checklist_screen(text)


def _contact_rows(block, answers, issued=None, typed=None, asked=0):
    """✨ A contact list's rows: each person on it in order, with their invitation while their link works and the link
    itself if it was just issued (`issued`, shown this once), then empty rows for the next people, as many as `asked`
    for in all if that is more (ticket 70). Each row is marked needed or optional by its place. `typed` is a person
    whose save was refused, shown as typed in their row, or for someone new in the first empty one, with why and the
    field at fault."""
    people = answers.get(block["id"]) or []
    links = Invitation.objects.filter(contact_id__in=[person["id"] for person in people], expires_at__gt=timezone.now())
    working = {invitation.contact_id: invitation for invitation in links}
    rows = []
    for number in range(1, rows_of(block, len(people), asked) + 1):
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
            }
        )
    if typed is not None:
        row = next((row for row in rows if row["contact_id"] == typed["contact_id"]), None)
        if row is not None:  # ✨ a full list has no empty row: its refusal is the list's own
            row.update(name=typed["name"], email=typed["email"], refusal=typed["refusal"], invalid=typed["invalid"])
    return rows
