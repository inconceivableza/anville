# 53c: New look for the observer's, coach's and account pages

**What to build:** The pages observers, coaches and visitors see are brought into the look A0-48 set, so the whole app reads as one. The stylesheet merged from the `hackathon-ui` branch already restyles every page, so this goes page by page and tidies what looks wrong. No page gets a new layout beyond the homepage's, which the prototype has. The participant's pages are 53b.

**Blocked by:** C1A-53a (One set of styles); C1B-46 (The demo notice on every page); B2B-55 (Answer collection freezes once results are viewed)

**Status:** resolved

**Sprint:** 2b (continued from 19 Oct)

**Spec:** Feedback from others; Operating and demonstrating

- [x] The observer's pages: the landing page, the thank-you, withdrawal, and the page a dead or frozen link shows
- [x] The coach's page, with the results and comparison it shows
- [x] Sign-up, sign-in, consent and the other account pages
- [x] Google sign-in's own pages (confirming, cancelled and the error page) say what allauth's stock English says, in our wording as well as our look
- [x] The homepage, keeping the words the hackathon took from the prototype, v3's where its earlier copy differs, and with nothing on it that is not yet true (a newsletter, donations, a contact address that does not exist)
- [x] Every one of these pages is readable at phone width, and none is left in the old look

**Context**

- Split from ticket 53 on 15 Oct. These pages stay plain cream: the deep brown frame is for the signed-in participant's pages only (53b; the developer's call, 19 Oct)
- Google sign-in's wording: from the sprint 2b end report's open questions, the developer's call, 19 Oct
- The observer's card sort and fine-tuning are 53b's, since the participant's share them
- The pages password reset and Google sign-in add (E1A-28a, E1B-28b) are built in this look whichever lands first
