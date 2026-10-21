# 65: The hub while Section 3 waits, and Manage on both cards

**What to build:** While Section 3 waits on the coach and nothing else is open, the hub's next-step panel says what it is waiting for and leads to the coach page, rather than "Nothing is waiting for you right now". The Walk with a coach card gets a Manage button like Five trusted voices', and a line saying what Section 3 waits on; both cards' Manage buttons are made small so the cards grow as little as possible.

**Blocked by:** A1-64 (Opening conditions and the coach's acceptance)

**Status:** claimed

**Sprint:** 3a (from 20 Oct)

**Spec:** Engine: sections, tracks, gates, progress; Implementation Decisions › Coach

- [x] With nothing next and Section 3 locked only by the coach, the panel reads "Waiting on your coach to respond" / "Section 3 opens once {coach} has accepted." while a working link is unanswered, with a "Your coach" button to the coach page
- [x] After a decline it reads "{coach} has said no" / "Choose someone else to walk with you. Section 3 opens once they accept."; with no working link, "Choose a coach" / "Section 3 opens once your coach has accepted."; each with the same button
- [ ] The Walk with a coach card shows "Manage", leading to the coach page, in every state once unlocked
- [ ] While Section 3 waits on the coach, the card's line reads "Section 3 opens once your coach accepts", or after a decline "Choose another coach to open Section 3"; otherwise no line
- [ ] Both cards' Manage buttons are the small pill, at phone width too

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the hub's side cards, for the button's look
