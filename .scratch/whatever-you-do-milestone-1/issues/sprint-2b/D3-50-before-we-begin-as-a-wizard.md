# 50: Before we begin as a wizard

**What to build:** A new participant goes straight into Before we begin, shown as a wizard of two pages, what brings them and then the five opening ratings, and lands on the hub when it is done. On the `hackathon-ui` branch the wizard is a page of its own with four steps, keeping what it learns on the account; this makes the wizard the section itself, read from the pathway document. The coach and contacts pages leave Before we begin, to become the two hub side cards Walk with a coach and Five trusted voices.

**Blocked by:** D2-49 (Hub width and second column)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Onboarding; Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] A section the pathway document marks as a wizard is where a participant who has not completed it is taken instead of the hub, shown page by page without the hub's links or the sidebar, in the prototype's layout with the section's photo beside it
- [ ] Before we begin is a wizard of these two pages, the reason and then the five ratings, and no more: the branch's working-style and reminder steps go. Completing it lands on the hub, which shows it complete and never asks for it again
- [ ] The account holds nothing from the wizard: a migration takes out the four fields the branch added (reason, way of working, reminder, onboarding completed), which have already run on staging
- [ ] Walk with a coach and Five trusted voices are hub side card sections, holding the coach checklist and the contact list as they work today. Answers already given in them are kept
- [ ] Once complete, Before we begin is listed in the hub and can be reread, with its ratings fixed

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3-nc-copy-copy.zip`, the onboarding view, for layout only; its four steps are not the content
- Because the branch's wizard is separate from the section, the hub then asked for Before we begin again; its newest commit stops the wizard sticking on its first step. Making the wizard the section removes both
- A later pathway may want the hub not to list a wizard at all; not this ticket
- Answers are keyed by block, so moving a block to another section keeps its answer. Check what a participant already part-way through the earlier pathway version sees
