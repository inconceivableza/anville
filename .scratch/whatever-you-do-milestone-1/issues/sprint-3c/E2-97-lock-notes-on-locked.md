# 97: Lock notes on "Locked"

**What to build:** A locked section's note sits as a line under it on the hub, adding clutter. "Locked" becomes a small button that shows its note on hover, keyboard focus or a tap, on the hub and in the sidebar.

**Blocked by:** 96 (A back button at the top of every participant page), E1; 89 (Status pills), B1

**Status:** resolved

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Sprint 3c: the content owner's feedback; Engine: sections, tracks, gates, progress

- [x] On the hub and in the sidebar, a locked section's "Locked" is a small button, and its note no longer shows as a line under the section
- [x] The note shows on hover, on keyboard focus and on a tap, and goes on moving away or tapping elsewhere, without JavaScript too
- [x] Screen readers hear the note as the button's description
- [x] With JavaScript, Escape closes an open note through the handler that already closes the sidebar, not a listener of its own
- [x] At phone width the note stays within the screen
