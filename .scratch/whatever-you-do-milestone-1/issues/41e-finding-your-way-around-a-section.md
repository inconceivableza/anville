# 41e: Finding your way around a section

**What to build:** A participant always knows where they are in a section and how to get back: a section they have finished opens at its start, a section split into pages says which page they are on, every page has a way back to the hub at its top, and moving between pages or confirming a reading leaves them where they expect on the page.

**Blocked by:** 41b (The flow back to the hub and Section 1)

**Status:** ready-for-agent

**Sprint:** not yet decided

**Spec:** Hub, progress and gates; Engine: sections, tracks, gates, progress

- [ ] A completed section opens at its first page from the hub and the sidebar; a section in progress still opens at the page reached
- [ ] On a section split into pages, the way to the previous page reads "← Previous page", apart from "← Back to the hub", and each page says which it is ("Page 2 of 3")
- [ ] The invitations page has "← Back to the hub" at its top, as section pages do, and no participant page is without a way back
- [ ] Going on to a page, going back to one, and confirming a reading each land where the participant expects, not jumping to the top or part way down

**Context**

- Found at the 41b hand check (8 Oct): reopening "Before we begin" once complete landed on its last page, and its "← Back" went to the page before rather than to the hub. The original prototype never reopens onboarding as a whole: its hub cards open one screen, which returns to the hub on saving.
- The developer saw a jump in scroll position on some screen but could not say which. Start by reproducing it together. Places that move the page today: confirming a reading reloads at the reading's top, above its passages; a save without JavaScript reloads at the block saved; choosing or removing a coach reloads at the coach checklist, and its steps swap in place; issuing or revoking a link reloads at that person; "Continue →" and "← Back" land at the top of their page.
