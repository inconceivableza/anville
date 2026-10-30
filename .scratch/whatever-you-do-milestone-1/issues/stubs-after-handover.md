# Ticket stubs left at the handover

> ✨ Drafted with AI assistance, 30 Oct 2026. Stubs, not tickets: no agreed tests, no status line, not grilled. Turn each into a ticket (`docs/agents/issue-tracker.md`) before building it.

## 1. Demo profiles for observers

The sort page's hidden "Load a demo profile (demo only)" link (`data-demo-reveal`, held Alt, or a long press on the title on a phone; `sort_assessment.html`, `main.js`) has no equivalent on the observer's sort (`observer.html`, `_observers_page` in `engine/views.py`). Add one: a hidden choice of profile that opens the observer's sort with its cards placed (`placed` in the widget, as `_block_for_participant` does with `scenario_loading.prefill(...).sort`). Observers answer no pairs, so the "how to answer the pairs" choice is not needed. Only where `_demo_tools_on()`; nothing is stored until the observer sends it.

## 2. Hub: complete every section up to a chosen one (demo only)

A hidden control on the hub, revealed as above, that completes every section before a chosen one, for a demo walk-through. It has to make up what each gate needs: the wizard's answers, a sort, a coach who has accepted, three observers with links (no emails are sent), and each section's completion. The test helpers already walk this path (`through_to_section_3`, `coach_accepts`, `through_to_the_letter` in `tests/journeys/test_whatever_you_do.py`); `seed_tie_break` shows how a demo-only write is guarded. Open questions: whether the made-up observers also send assessments, and whether it may run on a participant who has started.

## 3. The demo notice asks for an @example.com address

The demo notice should tell people to sign up with an `@example.com` email address. The thin strip's wording is in `engine/templates/engine/demo_strip.html` ("Use made-up details, not your own."); the full notice's wording is the `ANVILLE_DEMO_NOTICE` setting, so it changes in the deployment's values, not in code. Record the new wording in the content owner's wording-changes document.

## 4. Five trusted voices: we don't email them

On the Five trusted voices side card, one brief, quiet line saying no email is sent to the people added: the participant contacts each themselves and shares their link. Suggested: "We don't email them: send each person their link yourself." Record it in the wording-changes document.
