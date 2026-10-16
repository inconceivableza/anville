# 50: Before we begin as a wizard

**What to build:** A new participant goes straight into Before we begin, shown as a wizard of two pages, what brings them and then the five opening ratings, and lands on the hub when it is done. As merged from the `hackathon-ui` branch in A0-48, the wizard is a page of its own with four steps, keeping what it learns on the account; this makes the wizard the section itself, read from the pathway document. The coach and contacts pages leave Before we begin, to become the two hub side cards Walk with a coach and Five trusted voices.

**Blocked by:** A2-49b (Next step wording and photos)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Onboarding; Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] A section the pathway document marks as a wizard is where a participant who has not completed it is taken instead of the hub, shown page by page without the hub's links or the sidebar, in the prototype's layout with the section's photo beside it
- [ ] Before we begin is a wizard of these two pages, the reason and then the five ratings, and no more: the hackathon's working-style and reminder steps go. Completing it lands on the hub, which shows it complete and never asks for it again
- [ ] The account holds nothing from the wizard: a migration takes out the four fields the hackathon added (reason, way of working, reminder, onboarding completed), which have already run on staging
- [ ] Walk with a coach and Five trusted voices are hub side card sections, holding the coach checklist and the contact list as they work today. Answers already given in them are kept
- [ ] Once complete, Before we begin is listed in the hub and can be reread, with its ratings fixed. A participant who had completed it before this change is not sent through the wizard again, and one part-way through it lands on the wizard page they had reached

**Carried from 49a**

- A section gets `"side_card": {"sentence": …}` to be drawn as a card; the hub's own Five trusted voices and Walk with a mentor cards, written in the template, stay until 51a and 51b, so once these sections are side cards both show at once until then
- A side card can still be the hub's next step, the first section neither complete nor locked, so where the side cards sit in the document decides whether one is; and the sidebar lists no side card, since it shares the hub's list

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the onboarding view, for layout only; its four steps are not the content
- Because the hackathon's wizard is separate from the section, the hub then asked for Before we begin again; its newest commit stops the wizard sticking on its first step. Making the wizard the section removes both
- A later pathway may want the hub not to list a wizard at all; not this ticket
- Answers are keyed by block, so moving a block to another section keeps its answer
- The hackathon's "way of working" (guided online or paper workbook) set nothing beyond the account. A track is chosen by a choice block in onboarding (spec, Engine: sections, tracks, gates, progress), and *Whatever You Do* has one track, whose Workbook is the paper part; choosing a track (user story 14) stays with the offline track, ticket 23
