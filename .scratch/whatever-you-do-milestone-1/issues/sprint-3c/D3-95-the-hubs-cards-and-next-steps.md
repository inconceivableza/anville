# 95: The hub's cards and next steps

**What to build:** The hub's side cards both say "Manage" and do not explain themselves, Section 1's next step still talks about reading passages, and it is not clear how to start *The shape of your life*. The cards say what a coach and trusted voices are for, with buttons saying what they do, "Your groups" goes, and Section 3 is plain to start. Wording is in the sprint 3c wording sheet's "Hub" table.

**Blocked by:** 94 (Walk with a coach on one screen, with no email address), D2; 87 (Six sections), A2; 89 (Status pills), B1

**Status:** claimed

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Implementation Decisions › Coach; Sprint 3c: the content owner's feedback

- [ ] The coach card and the Five trusted voices card read as the wording sheet's rows, with "Choose your coach" (then "See your coach") and "Invite people"; the voices card's button is shaped like the coach card's, but white
- [ ] Section 1's next step reads "Start with the ten-minute strengths evaluation.", and its part's lock note "Opens from {title}."
- [ ] "Your groups" no longer shows below the sections
- [ ] Section 3's page is laid out so its paragraphs, its PDF and its finish button read in order, and the hub's next step for it starts it with one button
- [ ] The hub and the sidebar take each side card and its status from one place, so they never disagree

**Carried from 87**

- [ ] Section 1's page has more room above its green button ("I've finished Section 1"), below the strengths evaluation's card (the stylesheet is in `frontend/`)
- The Five trusted voices card's sentence already reads as the wording sheet's row ("…beside your own strengths evaluation…")
