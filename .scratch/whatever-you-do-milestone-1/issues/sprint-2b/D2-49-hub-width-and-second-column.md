# 49: Hub width and second column

**What to build:** The hub takes the final prototype's layout: wide, with the next step and the sections on the left and hub side cards beside them, so sections no longer wrap in a thin column. Which sections are side cards, what the next step says and which photos appear all come from the pathway document.

**Blocked by:** D1-48 (FaithTech look and final tweaks)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress; The pathway document and versions

- [ ] The hub is laid out as the prototype's: its width, its two columns in its proportions, one column at phone width, and section rows that do not wrap
- [ ] A section the pathway document marks as a hub side card is drawn as a card in the second column, from its title, its authored sentence and its status, and is not listed with the other sections. Nothing on a card is written in a template
- [ ] The next step shows the section's title and time estimate, or the heading and sentence the section carries for when it is the next step, over the section's photo if it has one
- [ ] Photos are pathway content: files beside the document, named by a section, each with its credit. A setting in the document lists the credits on the credits page, on for now
- [ ] The header counts sections complete ("2 of 5 sections complete") in place of answers. There is no "Where you started" card

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3-nc-copy-copy.zip`, the hub view
- The hub's photos are the prototype's grass (the next step) and, for D3-50, the figure facing the sun (the wizard). Both are from Unsplash, whose licence needs no attribution; the credits are shown anyway, behind the setting
- New fields go into the schema and its linter. The faithful port takes none of them, and the drift test sets them aside
