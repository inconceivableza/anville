# 83: Messages only after a press, and Before we begin's "Log out"

**What to build:** Pages greet participants with errors before they have done anything, and some buttons grey out. One rule, everywhere: a gate's message or a refusal shows only after a press it refused, and no button is disabled to stop a press. Before we begin's "Exit", which only goes back to the homepage still signed in, becomes "Log out" (carried from 26 through 54).

**Blocked by:** 85 (The new words), A1A

**Status:** resolved

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Sprint 3c: the content owner's feedback; Participants, access and consent (ADR 0004)

- [x] No page shows a gate's message or a refusal line on arrival: Before we begin's "Choose what's bringing you to the course to continue." and "Answer all five to continue", "Add at least 3 people.", "Choose a coach and send them their link." and a section's "Complete the…" prompts each show only once a press is refused, by what is missing
- [x] No button is greyed out or disabled to stop a press: choosing a reason and pressing "Continue →" at once moves to the next page
- [x] "Get link" is an outline button until its row has a name, then green; without JavaScript it is always green
- [x] The five opening questions show no "Saved" note after each answer
- [x] Before we begin's "Exit" reads "Log out", and pressing it signs the participant out and lands on the homepage, signed out; all of it works with JavaScript off
