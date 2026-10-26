# 94: Walk with a coach on one screen, with no email address

**What to build:** Choosing a coach asks for their name twice and an email address nobody uses, across two screens, and then leaves the participant with no clear way on. The coach is a name alone (ADR 0022): the checklist's verdict card makes the link, and "You've chosen {name}" shows it with a way back to the hub, on the same page. Its wording is in the sprint 3c wording sheet's "Walk with a coach" and "Five trusted voices and links".

**Blocked by:** 82 (Where pages land), D1; 83 (Messages only after a press, and Before we begin's "Log out"), C1

**Status:** ready-for-agent

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Implementation Decisions › Coach

- [ ] Nothing asks for or shows a coach's email address, and the coach's link page says only the name is kept
- [ ] After the checklist, the verdict card ("{name} sounds like the right person") carries the agreement tick and the button that makes the link; pressing it shows "You've chosen {name}" with the link and a "Back to the hub" button, with no details screen between
- [ ] The second thought reads as the wording sheet gives it, and the checklist's copy uses one size and style for each kind of text
- [ ] The link dialog and its button say "Make a new link", for the coach and for observers alike, as the wording sheet gives it
- [ ] All of it works without JavaScript and at phone width
