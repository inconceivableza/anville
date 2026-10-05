# 32a: Homepage, copied from the prototype

**What to build:** A public front page at the site's root, copied from the original prototype's homepage as it is, with its moving-forest hero, so someone who scans a QR code at FaithTech understands what Whatever You Do is without being told. Its "How it works" is replaced by the content owner's newer section. The page is static in the app's templates; making it generated from content is ticket 32b.

**Blocked by:** None (can start immediately)

**See also:** `Prototypes for reference/original-prototype.html` (the homepage, `id="homepage"`) and `Prototypes for reference/how-it-works-homepagesection.html` (the new "How it works", without its "Notes for implementation"); the hero video is `Prototypes for reference/hero.mp4`.

**Status:** ready-for-agent

**Sprint:** 2a (ends 8 Oct, before FaithTech)

**Spec:** Out of Scope; Delivery and hosting; Legalities are parked, not forgotten

- [ ] The page is at `/` for everyone, signed in or not, and "Begin" leads to sign-up, or to the hub if already signed in; the hub moves to `/hub/`, and signing in lands there
- [ ] It keeps the hero (with the forest video, muted and looping, and a still frame for when video does not play), About, the new How it works, Impact and the footer's verse and copyright, copied word for word except that "anonymously" is left out of step 1; it leaves out Churches and the church leaders' page, Articles (the blog), Newsletter, Team, Go further (spiritual directors), Donate, Contact, and the footer's Privacy Policy and Terms links. The navigation menu lists only what remains
- [ ] In How it works, steps 2–4 are greyed in their mockups and each labelled "In the workbook"; their text and times stay readable
- [ ] Nothing loads from a third party: no tracking, and the fonts and video are served by the app
- [ ] The page reads well on a phone

**Context**

- Copy is copied as is, but for "anonymously", which promises more than the app gives (the participant knows whom they invited). These lines also promise more than the app does today, for the content owner to change: "answer six questions in your own words" and "20 min Written questions" (31a and 31b are deferred), "Five people who know you well" (onboarding asks for two), "we send them what they need before each conversation" (nothing is sent), and "3 conversations" (the workbook has conversations two to four)
- The prototype has no still frame for the video (its `hero-poster.jpg` is missing); take one from the video
- A privacy notice and a contact address are needed before real use; neither exists yet
- Fonts stay off third-party servers for the same GDPR reason as ticket 03; most visitors will arrive from a QR code on a phone
