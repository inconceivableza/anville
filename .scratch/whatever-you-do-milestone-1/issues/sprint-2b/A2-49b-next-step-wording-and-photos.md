# 49b: Next step wording and photos

**What to build:** The hub's next step says what the pathway document authors for it, over the section's photo, as the final prototype's does. The hub merged from the `hackathon-ui` branch in A0-48 writes its next step and its photo in the template; this moves both into the pathway document, with the photos' credits.

**Blocked by:** A1-49a (Hub layout and side cards)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** Hub, progress and gates; The pathway document and versions

- [x] The next step shows the section's title and time estimate, or the heading and sentence the section carries for when it is the next step
- [x] The next step is drawn over the section's photo where it has one, and reads as well without one where it has none
- [x] Photos are pathway content: files beside the document, named by a section. Each photo's credit is one of three: required by its licence, a courtesy its licence does not ask for, or marked by the author as needing none (public domain, or the author's own)
- [x] The credits page always lists required credits, lists courtesy credits only while a setting in the document is on (on for now), and lists nothing for a photo marked as needing none. The linter refuses a photo that says none of the three
- [x] Nothing in the next step is written in a template

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the hub view's next step
- The hub's photos are the prototype's grass (the next step) and, for A3-50, the figure facing the sun (the wizard). Both are from Unsplash, whose licence needs no attribution, so both are courtesy credits, shown while the setting is on. The setting can never hide a credit a licence requires (developer's call, 15 Oct)
- Split from ticket 49 on 15 Oct; 49a holds the layout and the side cards
- New fields go into the schema and its linter. The faithful port takes none of them, and the drift test sets them aside
