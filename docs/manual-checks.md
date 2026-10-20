# Manual checks

> ✨ Written with AI assistance.

The tests stop at HTTP: nothing here runs a browser, so anything JavaScript, CSS or assistive technology does is checked by hand. This list says what to check and how. It is also the starting point if browser tests are added later. Add to it whenever a change does something in the browser that a test cannot see.

Run `npm run build` in `frontend/` first, so the browser gets the current JavaScript and CSS.

## How to check

| What | How, in Chrome (Firefox and Safari have equivalents) |
|---|---|
| Without JavaScript | DevTools, then ⌘⇧P, "Disable JavaScript", and reload. Turn it back on the same way. |
| Keyboard only | Put the mouse aside. Tab and Shift-Tab move between controls; Space or Enter presses a button; the arrow keys move a slider. The focused control should always be visible. |
| Screen reader | On macOS, VoiceOver: ⌘F5 turns it on and off, and Control-Option with the arrow keys reads through the page. Listen for what is announced when something changes without the page reloading. |
| Reduced motion | DevTools, the ⋮ menu, More tools, Rendering, then "Emulate CSS media feature prefers-reduced-motion: reduce". |
| Phone width | DevTools' device toolbar (⌘⇧M), at a width around 375px. |

## Buttons and colours (every page, beside a build from before the styles were tidied)

- With the sprint's previous build open in a second window, the homepage, hub, onboarding wizard, a section page with its way on, the coach checklist, results, comparison, invitations, consent, the account pages and the organisation pages look the same, at a wide screen and at phone width: the same colours, and each button the same size, colour and place.
- Expected differences, and only these: a button that was a link ("Go to your pathway", "← Previous page", "← Back to the hub", "Invite people who know you →") has no underline; an outlined button on the page's cream shows the cream through it, where it had a paler fill, and darkens a touch on hover, where it turned cream; and the wizard's "Continue" is in the page's typeface.
- A full-width button ("Mark complete", "I agree", "Join") has its words centred; a pill that spans a hub card ("Manage", the next step's "Begin") keeps its words at the left, as before.
- Keyboard only: each button and pill, the homepage's included, shows a dark green ring when Tab reaches it.
- With a mouse, the homepage's, hub's and wizard's pills lean towards the pointer as before; a button on any other page stays still.
- Without JavaScript, the Copy buttons on the invitations, coach and organisation pages are still hidden.
- A disabled "Mark complete" is grey with muted words, and the pointer shows it can't be pressed.
- Phone width: the header's "Your pathway" and "Sign out", and the save row's "Save", are the small size and fit on one line.

## The homepage (`/`, signed out and signed in)

- Side by side with the prototype's homepage (`Prototypes for reference/original-prototype.html`) and its newer "How it works" (`how-it-works-homepagesection.html`), the words match. The only differences: "anonymously" is gone from step 1, the Churches, Writing, Newsletter, Team, Go further, Donate and Contact sections are gone, and so are the footer's Privacy Policy and Terms links.
- The forest video plays muted and loops, with no sound and no controls. With the video blocked (DevTools, Network, right-click `hero.mp4`, "Block request URL", then reload), the still frame shows in its place.
- Reduced motion, and without JavaScript: the still frame shows from the start and the forest never moves, not even for a moment.
- In "How it works", steps 2–4 have greyed mockups, each labelled "In the workbook"; their words and times are as easy to read as step 1's.
- The round menu button stays visible over the video and over the white and pale sections below it. It opens a panel listing About, How it works and Impact only, and each link scrolls to its section and closes the panel.
- Without JavaScript, the menu still opens and its links still scroll.
- Keyboard only: Tab reaches the menu button first, Enter opens it, and the focus ring shows on it and on each link.
- DevTools, Network, reload: every request goes to this site (no Google Fonts, nothing else).
- With `ANVILLE_DEMO_NOTICE` set in `.env` (as every staging environment has it), the amber "Demo" notice sits under "Begin →" over the video, easy to read at phone width and on a wide screen, and at the top of the sign-up and sign-in pages. With it unset, neither shows.
- On a wide screen, About's text is centred in a narrower column than How it works' steps, and Impact is centred beneath them.
- Phone width: the headline fits without sideways scrolling, step 4's four-column roadmap is still legible, the Begin buttons are easy to tap, each step's mockup sits above its words, and the impact figures stay beside their text.
- Signed out, both "Begin →" buttons open sign-up; signed in, both open the hub. Signing in, and agreeing to consent, both land on the hub, not the homepage.

## The demo notice beyond the homepage (ticket 46; `ANVILLE_DEMO_NOTICE` set in `.env`)

- The hub, an observer's link before starting, and the coach's link show the full amber "Demo" notice at the top of the page, as the sign-up page does, and no thin strip.
- Every other page (a section, results, the comparison, invitations, credits, the observer's own page after starting) shows a thin amber strip at the very top, "DEMO Use made-up details, not your own.", and not the full notice.
- Phone width: the strip stays on one or two lines, easy to read, and covers nothing: the header and the page's first lines sit below it, not under it.
- With it unset, no page shows either.

## Sign up

- "I am 18 or over" sits beside its checkbox, as "Remember me" does on sign in.
- Submitting with it unticked: the browser stops the form and points at the box. Without JavaScript the same happens, since the check is the browser's own `required`.
- Keyboard only: Tab reaches the box and Space ticks it.
- "First name" comes first, with "e.g. Ed" as its placeholder, and the browser offers nothing saved for it.
- With `ANVILLE_ENROLMENT_REQUIRED=false` there is no enrolment code field; with it left out, the field sits after the email.

## Google sign-in (ticket 28b; needs a development OAuth client, `deploy/README.md`, "Set up Google sign-in", step 8)

- With neither `ANVILLE_GOOGLE_CLIENT_ID` nor `ANVILLE_GOOGLE_CLIENT_SECRET` in `.env`, or only one, sign in and sign up look exactly as before: no "or", no Google button.
- With both set and `runserver` restarted, sign in and sign up each end with "or" and an outlined "Continue with Google" across the form's width, at a wide screen and at phone width.
- Pressing it goes straight to Google's account chooser, with no Anville page asking again first. Cancelling there comes back to an Anville page, not an error.
- A Google account new to Anville comes back to a sign-up form with its email filled in, asking for the first name, the enrolment code (where asked for) and "I am 18 or over", and no password. Leaving the box unticked stops the form as on the email sign-up.
- Once signed up, the hub sends it to the consent page first. Signing out and pressing "Continue with Google" again signs straight in to the hub.
- An address that already has an email-and-password account is refused on that form, and no second account is made.

## Password reset (sign in's "Forgot your password?")

- Sign in shows "Forgot your password?" under the password field, and it opens the reset page, styled like sign in, with the demo notice when that is set.
- Asking for a reset of your own account's address: the page says an email is on its way. Locally, with no `EMAIL_URL`, the email is printed in the `runserver` terminal; open its link in the same browser. Setting a new password there, then signing in with it, reaches the hub; the old password is refused.
- Asking for a reset of an address with no account shows the very same page, and nothing is printed in the terminal.
- On staging, the reset email reaches a mailbox you own and carries the test-system disclaimer at its top and the mark on its subject.
- Opening the same link a second time says it is no longer valid.
- Phone width: the reset pages and the new-password page fit without sideways scrolling, and their buttons are easy to tap.

## Consent

- After signing up, and at a first sign-in, the consent page comes before the hub.
- Agreeing as a new participant opens onboarding, with the reason drop-down first, not the hub (in Whatever You Do, as the wizard, with no way to the hub until it is done).
- "I agree" and "I do not agree" are stacked with a gap between them and look like equal choices: neither is hidden, greyed out or smaller.
- "I do not agree" says nothing will be stored, and "Read the text again" goes back to the page.
- Without JavaScript, both buttons work: the page is a plain form.
- Keyboard only: Tab reaches both buttons in order, and Enter presses the focused one.
- Phone width: the text wraps and the buttons fill the width.
- "Your consent" sits quietly at the foot of the hub, including on the empty "Nothing to begin yet" hub.
- Once agreed, "Go to your pathway" and "Withdraw my consent" look alike in size, stacked as the first two buttons were.
- With a section open in one tab, withdraw in another, then type in the first tab: the page goes to the consent page rather than showing "Saved" or an error.
- With an observer's link and the coach's link open in a private window, withdraw: both now show the same refusal as a wrong link, naming nobody, also at phone width. The observer's "withdraw" page still opens. Agree again: both links work as before.

## The header and the pathway sidebar (every participant page)

- The hub, each section page, results, the comparison and invitations have the header: "Your pathway" on the left, the pathway's name (leading to the hub), and "Sign out" on the right. The coach's page and the observer's pages have none of it, even in the participant's own signed-in browser.
- "Your pathway" opens a panel down the left listing the hub's sections with their status chips; the section you are in is highlighted, and a locked section is greyed and not a link. Below them: invitations, the coach page once Section 1 is open, and results and the comparison once the sort is in. Pressing "Your pathway" again closes it.
- Without JavaScript, the panel opens and closes just the same.
- Keyboard only: Tab reaches "Your pathway", Enter or Space opens it, and Tab then moves through its links, with the focus ring showing on each.
- Screen reader: "Your pathway" is announced as collapsed or expanded, and the step you are on as the current page.
- Phone width: the header fits on one line or wraps tidily, the panel fills most of the width without sideways scrolling, and a long list scrolls inside the panel.
- Phone width (ticket 53b): every section in the panel that isn't locked is a link, and so are invitations, the coach page, results and the comparison below them; none is missing, as they were on a phone before. On the homepage, the menu still hides its links at phone width as before.
- "Sign out" lands on the homepage, signed out.
- The footer's "Credits" shows the header while signed in, and the plain page once signed out.
- With `ANVILLE_SIDEBAR=false` in `.env` and the server restarted, "Your pathway" is gone; the pathway's name and "Sign out" remain.

## The hub's layout (the hub, beside the prototype's: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html#hub`)

- The page is deep brown, and the hub, header included, is cream with rounded corners, inset a thin brown border from every edge. "Credits" sits below it on the brown, easy to read.
- On a wide screen the hub is about as wide as the prototype's: the next step and the sections in a wide left column, and the coach and trusted voices cards in a narrower right one, in the prototype's proportions. No section's title wraps that would fit on one line in the prototype.
- Section 1 shows "01", Sections 2–4 "02", "03" and "04", and Section 5 "05", each in small grey type to the left of the title; Before we begin shows no number, and its title lines up with the others. The Strengths assessment, within Section 1, shows no number.
- The header says "1 of 9 sections complete" once Before we begin is done, and counts up as sections, and the Strengths assessment, are completed. There is no "Where you started" card, even once the sort is in.
- "Your consent · Your groups" sits below the hub, lined up with its left edge.
- Phone width: one column, the cards below the sections; the brown border still shows, and nothing scrolls sideways.
- Walk with a coach and Five trusted voices, side cards since ticket 50, show in the right column as cards with their title, sentence and status, and not in the list or "Your pathway"; each title leads to its page. The old "Walk with a mentor" card is gone (ticket 51b), and so is the hub's own "Five trusted voices" card (ticket 51a).
- Walk with a coach's tag (ticket 51b): "Locked" before Before we begin is done, then "Not started"; once Sam is saved, "Link issued"; after Sam accepts or declines on the link, "Accepted" or "Declined"; reissuing the link goes back to "Link issued"; revoking it, "Not started". Its sentence is "When you're ready, ask someone to walk this with you.", with no briefing pack. At phone width the tag fits beside the title.
- Five trusted voices (ticket 51a) is a dark card, as the prototype's, with no names and no name box: "Not started" before anyone is added; with one person, "2 more needed" and "You'll see how others see you once 3 people have answered."; with three, "Complete" (ticket 52), as the section completes once three people have links. "Invited" counts people with a working link (revoking one counts down) and "Answered" counts assessments sent (starting from a link does not count), each "n / 5". "Manage" and the title lead to the section's page. Once the section is complete the tag says "Complete" and never asks for more people. Phone width: the meters fill the card.

## The participant's pages in the hub's look (ticket 53b; each page signed in, at a wide screen and at about 375px)

On every page below, check:
- The page is deep brown, as the hub is. The header and the page sit on cream with rounded corners, inset a thin brown border from every edge, and "Credits" is below them on the brown, easy to read. With `ANVILLE_DEMO_NOTICE` set, the thin amber strip is the top of the cream, its top corners rounded, and the header follows straight on beneath it.
- The cream runs across the whole width of the frame, but the page's words keep the narrow column they had, centred. On a phone the words sit about 16px in from the cream's edges, and nothing scrolls sideways.
- The page's title is in the heading face, light and large, as the hub's "Welcome" is; a title that wraps breaks into lines of similar length.
- The hub itself looks exactly as it did before this ticket. That includes its wide layout and its "Welcome, …" heading.

Page by page:
- **A section page** (Section 1, then a paged section such as Before we begin opened from the hub): "← Back to the hub", the title, "Page 1 of 2" where it has pages, then "Whole section: …" and each activity's "This part: …" in small grey capitals, as the hub's "1 of 9 sections complete" is. The scripture reading, the 1–10 scales, the long-text questions and the contact list are the same cards as before, on the cream.
- **The gate:** under "Mark complete" (or "Continue →"), each requirement still waiting is a pale box with a grey bar on its left; each one met is plain, with a green tick and bar. "← Previous page" sits beside the way on as before.
- **Section 1's Strengths assessment card:** its status ("Not started", "Complete" …) is a small rounded tag in grey capitals, as the hub's tags are. Once the assessment is done, "View my results →" leads to the results as before (ticket 61).
- **The Workbook's pages** (Sections 2, 3 and 4, on paper): "Download Section 2 (PDF)" and "I've finished Section 2" are in the same look as Section 1's buttons; the same for 3 and 4.
- **Walk with a coach and Five trusted voices** (the hub's side cards, opened): what each waits on is listed as the gate's pale boxes are, with no "Mark complete".
- **The hub's locked sections:** a locked section's row shows its title in grey and what opens it ("Opens once you've finished …") in grey beneath it, as before; a locked side card's title is grey and not a link.
- **The card sort and fine-tuning** (Section 1's assessment): the thin progress bar, the card and the five buckets, "↩ Undo last", the all-sorted screen with its counts, and the sliders look as they did. They now sit on the cream inside the frame. At phone width the buckets stack one above another and nothing scrolls sideways, even as a card flies off. The observer's sort, in a private window, looks the same but stays plain cream, with no frame.
- **The tie-break's pairs** (a participant tied on a framework): the pairs sit centred in the frame, and each option fills the column. At phone width the options are easy to tap.
- **Results:** each framework is a card. Each construct's name sits on the left and its standing on the right, with a gap between them even at phone width, where a long name wraps rather than running into its standing. Every drawing, the generalist's box and a framework's tie-break box are as D5-59b left them, each construct in its standing's colour (fix-16). "Compare with how others see you →" is centred below.
- **"Before you look"** (the freeze warning): its pale green box, then "Compare with how others see you →", centred.
- **The comparison:** the illustrative note is amber with its right-hand corners rounded. "You" is green and "Others" blue as before. The largest gaps and the questions to reflect on are cards, and "← Return to …" is at the foot. At phone width each construct stacks: its name, then the drawing, then the words.
- **Removing a contact** (without JavaScript, a person's "Remove" on the contact list): framed like the rest, with its form and buttons as before.
- **Credits:** signed in, framed with the header; signed out, plain cream with no frame and no header.
- **Not framed:** the wizard (Before we begin as new), the observer's pages, the coach's link, sign in, sign up, consent, and the organisations pages (Your groups, Your organisations, leaving a group, replacing a join link, and "This page is for admins") all stay plain cream, with no brown frame (their look is checked below, ticket 53c).

## The observer's, coach's and account pages in the new look (ticket 53c; each at a wide screen and at about 375px)

On every page below, check:
- The page is plain cream from edge to edge: no brown frame, no header. "Credits" is at the foot.
- The page's title is in the heading face, light and large, as a participant page's title is (ticket 53b); a title that wraps breaks into lines of similar length.
- On a phone the words sit about 16px in from the edges, the buttons fill the width and are easy to tap, and nothing scrolls sideways.

The observer's pages (an observer's link, in a private window):
- **The landing page:** "You've been invited" as the title, the privacy notice in its pale green box, then "I'm answering for …  →". With `ANVILLE_DEMO_NOTICE` set, the full amber notice is above the title.
- **The observer's own page:** "Answering for …" as the title, the link to bookmark in its box with "Copy", then the relationship drop-down and the sort as before.
- **The thank-you** (after sending): a card with "Thank you" in the heading face, then its sentence, then "Withdraw my answers" a line below it, not touching it.
- **Withdrawal:** "Withdraw your answers" as the title; a card with its sentence and, with room above it, the button. After pressing it, "Your answers have been withdrawn" in the heading face, then its sentence.
- **A dead link** (a wrong, expired or revoked link), **a used one** (the landing page's link again, after starting from it) and **a frozen one** (answer collection frozen, ticket 55): the first two are a title and a sentence; the frozen landing page and own page show the card with its heading in the heading face.
- **Stop reminders** (a reminder's stop link): the title, then a card with the sentence and, with room above it, the button; once pressed, "Reminders stopped" in the heading face.
- **An error page** (`/no-such-page/` with `DEBUG` off): the title, the message, then "Go to the homepage" a clear gap below it.

The coach's page (the coach's link, in a private window):
- Before answering: "… has asked you to be their coach" as the title, then the card of commitments, "What you'd be agreeing to" at the size of the participant's coach checklist headings, not as large as the title.
- Accepted ("Thank you — … will be told", or later "You're …'s coach") and declined ("That's a good answer"): the green or amber box with its heading at that same card size.
- Once shared: the guide, then "…'s results" and "How others experience …" as titles the size of the participant's results title, with the results and comparison beneath as the participant's own pages draw them, and at phone width the comparison stacks as theirs does.

The account pages (signed out unless said):
- **Sign in, sign up, password reset** (and its email's new-password page): the title, the line beneath it, the form in its pale box, the button across it.
- **Sign out** (`/accounts/logout/` opened directly): the question, then "Sign Out" alone, with no empty box round it.
- **Consent:** "Before you begin" as the title; "What is stored", "Who sees what" and "Your choice" smaller than it, each with room above. "I agree" and "I do not agree" as before. **Consent not given:** "Read the text again", then "Sign out" a line below it, not touching it.
- **Joining a group** (`/join/<token>/`): "Join …?" as the title, what the admins see, "Join", then "Not now, go to your pathway" a line below. "You're already in this group" and "This link no longer works" are a title with their button or sentence.

The organisations pages (signed in; these keep the participant header, the one difference from the checks above):
- **Your groups** (from the hub's foot): plain cream with the header and no brown frame; "Your groups" as the title, then each group's name, its organisation, what its admins see and "Leave this group". With none, "You're not in any groups."
- **Leaving a group** ("Leave this group"): "Leave …?" as the title, its sentence, then "Leave this group" and "Stay in this group" across the width, one beneath the other.
- **Your organisations** (signed in as an admin, from the hub's foot): "Your organisations" as the title, each organisation's groups with their join links, and the "New group" form as before.
- **Replacing a join link** (an admin's "Replace link" under a group): "Replace the join link for …?" as the title, its sentence, then "Replace link" and "Keep this link" as leaving's buttons are.
- **This page is for admins** (`/organisations/` opened directly, signed in as someone who is not an admin): the title, its sentence, then "Go to your pathway".
- At about 375px, each of these: the header fits, the words sit about 16px in from the edges, the buttons fill the width, and nothing scrolls sideways.

Google sign-in's own pages (needs the Google client pair, as above):
- **Finishing a sign-up:** "Sign up with Google", then "You're signing up with your Google account. One last step: please fill in this form.", the form, and "Sign up". Not "You are about to use your Google account to login to example.com".
- **Going on to Google** (`/accounts/google/login/` opened directly): "Sign in with Google", "You're about to sign in with your Google account.", then "Continue" alone, with no empty box round it.
- **Cancelled** (cancel at Google's account chooser): "Sign-in cancelled", then "You cancelled signing in with your Google account. If you didn't mean to, you can sign in again.", "sign in" leading to sign in.
- **Failed** (`/accounts/3rdparty/login/error/` opened directly): "Signing in with Google didn't work", then "Something went wrong while signing you in with your Google account. You can try again.", "try again" leading to sign in.

The homepage (`/`):
- The headline is "Everyone has a purpose. Do you know yours?", as v3's is; so is the heading of the callings carousel near the foot.
- Beneath the hero, "Whatever You Do is a pathway for discerning your purpose." then a row of small cream pills: Scripture, Strengths assessment, Peer feedback, Coach oversight, Workbook. At phone width they wrap onto two or three centred lines.
- Nothing offers what does not exist yet: no newsletter card, no "Get in touch" card or email address, no "Support our work" section or donation, and no "Ask us about coaching", "Talk to us" or "Ask about supporting the work". The coach band in "How it works" is its icon and sentence alone, and the churches section ends with its three points.
- "Ideas to explore" keeps its three pieces of writing, and the story from a parent follows it.

## Before we begin as a wizard (ticket 50; load the pathway again first, then sign up as someone new)

- After consent, Before we begin opens as the wizard, beside the photo of the figure facing the sun (as the prototype's onboarding view): no header, no "Your pathway", no link to the hub; "Step 1 of 2" with two bars at the top. Page 1 is the reason alone; "Continue →" leads to page 2, the five ratings, with "← Previous page" beside the way on.
- Going to `/hub/` part-way lands on the page reached. The last "Continue →" lands on the hub, Before we begin listed as complete, and the hub never sends you back. Its entry opens it as an ordinary section page, header and sidebar included, the ratings fixed.
- `/credits/` lists "Photograph of a figure facing the sun from Unsplash.".
- Phone width: the photo sits above the page, the ratings fit without scrolling sideways.
- The photo is as tall as the window on both pages, at a wide screen and at a tall one (over 900px high): no bare dark strip beneath it, whether at the top of the ratings or scrolled to their end, and the photo the same size and crop on page 2 as on page 1, never zoomed. At about 375px it sits above the page as before (fix-10).
- Pressing Enter in an answer (with a rating's point focused, chosen or not, or in the reason drop-down) does nothing: the page stays as it was, never "Not saved. No answer was sent." on a page of its own (fix-7).

## The hub's next step and its photo (load the pathway again first; ticket 49b)

- Once Section 1 is next: "Start with your gifts." and "Take the ten-minute strengths assessment and read three short passages on gifts.", over the grass photo, shaded so the words read clearly, the panel taller, as the prototype's. "Begin" leads into Section 1.
- `/credits/` lists "Photograph of grass from Unsplash." under "Photographs", after the scripture notices.
- Phone width: the photo fills the panel without stretching, and the words stay readable.

## Back to the hub and Section 1 (ticket 41b)

- Completing onboarding, and later Section 1, lands on the hub with the next step's card highlighted.
- Before Section 1's reading is confirmed, the Strengths assessment shows "Locked" and is not a link, on the hub and in "Your pathway", and the hub says "Opens from How you've been designed, once you've read the passages."; typing `/sections/strengths/` lands on the hub. Once the reading is confirmed, it opens.
- On the hub, the Strengths assessment sits inside Section 1's card, indented and quieter, on a line of its own; in "Your pathway" it is indented under Section 1. Both read well at phone width.
- A screen reader announces the Strengths assessment as a list nested within Section 1's entry.
- Before the sort, the Strengths assessment's page starts with "← Back to How you've been designed" and has no "Mark complete". Once the sort is in, its chip reads "Complete" on the hub, in the sidebar and on Section 1's card.
- Once the sort is in, opening the Strengths assessment from the hub, from "Your pathway", or by typing `/sections/strengths/` opens your results (or, with tie-break pairs still to answer, the next pair); the page saying only "Your sort is in. See your results" never shows. Same in both pathways.
- The results page's "← Back to How you've been designed" and the comparison's closing "← Return to How you've been designed" both land on Section 1.
- On the hub, Section 1 and Section 5 read "How you've been designed" and "A letter to your future self", with no "Section 1: " or "Section 5: " before them, beside their "01" and "05".
- In a pathway whose Section 1 asks for the coach's or the observers' links (Whatever You Do no longer does, ticket 52), those requirements beneath "Mark complete" are links, to the coach page and the invitations page; once met, each is ticked and plain.

## Autosaved answers (long text, 1–10 scale, single select)

- Typing or choosing shows "Saved"; changing the answer again clears it; a slow save shows "Saving…".
- With the server stopped, a save says "Not saved. Check your connection, then try again."
- A refused answer shows its reason where "Saved" would be.
- Near the 20,000-character limit, the text box says how many characters are left.
- Without JavaScript, a Save button appears and saves the answer. With JavaScript it is hidden.
- Without JavaScript, pressing Save (or Enter) on a 1–10 scale with no point chosen comes back to the same page, "Not saved. No answer was sent." beside the button. With JavaScript, Enter in an answer never reloads the page (fix-7).
- Screen reader: "Saved" and a refusal are announced.
- Ghost text (Section 1's reflection, the letter): it shows in grey in the empty box, is readable against the background, and disappears as you type. A screen reader names the box by its prompt, not by the ghost text.
- The reason in onboarding: it looks like the prototype's account-screen drop-down (a small dark caret at the right, not the browser's arrow), and is amber while "Select..." is showing, turning white once a reason is chosen, with or without JavaScript. The drop-down shows "Select..." until a reason is chosen, and choosing one shows "Saved" with no button press. Going back to "Select..." shows "Saved", turns the drop-down amber again, and unticks "Choose what's bringing you to the course" beneath the button; a reload still shows "Select...". Keyboard only: Tab reaches it, and the arrow keys change it (each change saves). It fills the card's width at phone width.

## The contact list ("Who knows you best?")

- In Whatever You Do it is the Five trusted voices side card's page (in the faithful port, onboarding's last page, reached by "Continue →" from the ratings): a numbered row per person, "First name" narrower than "Email address", the first three marked "Needed" and the next two "Optional" (in the faithful port, five "Needed"). The intro no longer says "anonymous".
- "Get link" on an empty row comes back with that person listed and their link in a dialog, with Copy; once all five rows are filled a sixth empty one appears. A change to a person saves when the field is left, changing only them, and their link keeps working.
- A bad address (`jo`, `jo@`, `jo@example`) or a missing name or email comes back with "Not saved." and why in that row, as typed, the field at fault red. The browser does not stop it first.
- Two tabs: open the page in both, add Priya in one, then in the other (not reloaded) change Jo's email and save. Priya is still listed, and her link still opens "You've been invited".
- After Before we begin is complete, people can still be added and changed. `/invitations/` opens this page.
- Phone width: each row's fields stack, nothing scrolls sideways.
- Screen reader: each field is read as "Person 1, first name" and so on; the row numbers themselves are not read; a marked field is announced as invalid.
- Phone width: each row's name and email stack beneath its number, full width.

## The coach's details (Whatever You Do's coach page)

- Going ahead (all Yes, or "I'm still confident — ask Sam"): beneath the gold box come "Their name" (already holding the first name typed on the intro), "Their email (optional)", the tick "I've spoken to this person and they're happy to receive a link from me about coaching me through this course.", a full-width "Save Sam as your coach", then "Choose someone else". The two boxes look like the intro's name box; the tick sits beside its words, not above them.
- Saving with the box unticked says "Tick the box to confirm you've spoken to them." beneath the tick, with the name and email kept as typed; a bad address (`sam`, `sam@`, `sam@example`) says "Check their email address." and the email box turns red. Nothing is saved either way. An empty email box saves (ticket 51b).
- Saving shows "You've chosen Sam" with their email (none if left empty), Sam's link shown once to copy (see "The coach's link"), "Choose someone else" and "Remove", without reloading the page. A reload, or coming back through the hub, shows the same, without the link.
- "Choose someone else" starts the checklist again, with "Sam stays your coach until you save someone else." and "Keep Sam" beneath its "Continue →". Enter in the name box goes on to the questions, not "Keep Sam". On the questions, with an answer chosen, Enter goes on like "Continue →", never back to the intro, and "Back" still shows on the left, at phone width too (fix-12). "Keep Sam" goes back to "You've chosen Sam" (or "Sam is your coach" once they have accepted). A reload before saving anyone new still shows the coach saved before. "Remove" goes back to the intro, and a reload shows the intro.
- Without JavaScript: saving and "Remove" come back to the coach page at the checklist; a refused save comes back as the whole coach page with its reason.
- Screen reader: the refusal is announced; a refused field is announced as invalid when Tab reaches it.
- Phone width: the details and buttons fill the card's width.

## The coach's link (ticket 13c)

- Saving Sam (ticket 51b) leads straight to "You've chosen Sam", saying the next step is to ask them properly, with the link shown once beneath, "Copy", "Waiting for Sam to answer. The link works until …", "Reissue link" and "Revoke link", without reloading the page; the link box has focus. "Copy" says "Copied". A reload shows no link, only the status. After "Revoke link" the button reads "Get a link for Sam", which shows a new link the same way.
- With Before we begin complete (and later, Section 1 too), saving a coach and "Reissue link" still work.
- Enter in the link box does nothing: the link stays the same and still works (with and without JavaScript).
- Without JavaScript: saving Sam, "Get a link for Sam", "Reissue link" and "Revoke link" each come back to the coach page at the checklist, the link shown once after issuing.
- In a private window, the link shows "participant has asked you to be their coach" (the participant's display name), the two authored paragraphs, "What you'd be agreeing to" and the six promises, each with its note in smaller type and a box to its left; the box or its words tick it. The line on what is kept sits above "Accept →" and "I can't commit to all of this".
- "Accept →" with a box unticked says "Tick all six to accept…" with the boxes as they were. All six ticked: "Thank you — participant will be told" and the authored line; a reload says "You're participant's coach" in its place (ticket 25a), and never shows the boxes again.
- "I can't commit to all of this" (any boxes ticked): "That's a good answer" and the two authored paragraphs.
- Back on the coach page after an accept: "Sam is your coach" in the gold card, with "Sam has accepted." After a decline, the card turns amber: "Sam isn't able to be your coach", choosing someone else or carrying on without a coach, "Choose someone else" as the primary button. Neither says which boxes were ticked.
- Saving another coach, or "Remove", then opening Sam's old link: "This link does not work". So too a revoked link, and Sam's link at `/observe/…` in place of `/coaching/…`.
- Keyboard only: Tab reaches each box, then Accept, then decline; Space ticks a box.
- Phone width: the promises wrap beside their boxes; the buttons fill the card's width.

## The coach sees the results and comparison (ticket 27)

- After accepting, the coach's link shows "What happens next" in a pale box within the gold card, "Sam finishes the strengths assessment and sends it to you. You'll get the results, how others rate the same strengths, and a short guide to that conversation — what it's for, what to ask, what to watch for. They'll appear on this page, so keep the link." It promises no email.
- On the comparison, with Sam chosen but not yet accepted: "Once Sam accepts being your coach…" with "Your coach page →", in a card at the top, just under "How others experience you", and no box. Once Sam has accepted, in that card at the top: "Give my coach access to my results and this comparison", unticked, and beneath it, lined up under the label's words, "Sam will see your results and the comparison below, which may update if more people answer.", the same however many have answered; no Save button. The tick looks like the coach details' "I've spoken to this person…" tick: same size, normal weight, a gap between box and words, the box level with the first line. Opening the comparison by its typed address, without pressing "Compare with how others see you →" first, shows no box and no empty panel. After Sam declines, the comparison says nothing of Sam. Once Sam's accepted link expires (in the Django shell, set that `Invitation`'s `expires_at` to the past), the comparison says the link has expired.
- Ticking saves at once: "Saved" at the card's foot, as autosaved answers show it, and the line becomes "Sam can see your results and the comparison below, which may update if more people answer. Untick to stop sharing." without a reload. Unticking saves at once too and turns the line back. With the network off (devtools, Offline), ticking says "Not saved. Check your connection, then try again." Without JavaScript, a "Save" button shows and does the same, coming back to the box. In a private window Sam's link now shows, below the gold card and in place of "What happens next", "participant's results", a line saying the participant is happy for them to see this, the results as the participant sees them (item scores included), then "How others experience participant" and the comparison, whose own sentences say "participant" where the participant's say "you", and whose single-person icon VoiceOver reads as "participant: Leading" where the participant hears "You: Leading" (the pathway's authored headings, gaps and questions still say "you"). Below the minimum: "Not enough answers yet" with the count, and no "Invite people who know you →".
- The coach's page has no form, button or link that changes anything of the participant's.
- Unticking and saving, then reloading Sam's link: "What happens next" again, and no results.
- Phone width: the shared results and comparison on Sam's link fit as on the participant's own pages.
- As an observer, in a private window: the privacy notice says the participant may also show what they see to a trusted third party (load the pathway again first).

## The coach's guide (ticket 25a; load the pathway again first)

- The comparison, reached by "Compare with how others see you →", with Sam chosen: in the coach card at the top, beneath the "Once Sam accepts…" line, or once Sam has accepted beneath the tick and its line, a pale green panel, closed, "🧭 Session 1 – Their gifts – coach guidance" with "Tap to see what your coach is asked to do." beneath and a ▾ on the right. Clicking it, or Enter or Space on it, opens it (▴): "PURPOSE" and "SUGGESTED LENGTH" in small green capitals, each over its line; "QUESTIONS TO ASK", four bullets; "WHAT TO LOOK OUT FOR", two; then a white box with a red left edge, "AVOID" in red over its sentence. No "Sent with this" and no placeholder note. Clicking again closes it. Without JavaScript it opens and closes the same. Ticking and unticking the consent leaves the panel as it was.
- With no coach chosen, the comparison has no coach card and no guide. Section 1 itself shows no guide.
- Sam's link, in a private window, before answering and after declining: no guide. Accepting lands on "Thank you — participant will be told"; a reload, or opening the link again later, says "You're participant's coach" in its place, with the same authored line beneath. No guide yet. Once the participant ticks "Give my coach access…", a reload shows the guide below the gold card, already open, with its title as a heading and no ▾, then "participant's results"; once they untick, both go.
- Phone width: the panel's title and subtitle wrap beside the 🧭, the ▾ stays at the right, and the bullets wrap within the panel, on the comparison and on Sam's link.
- The faithful port's comparison has no guide.

## The gate and "Mark complete"

- The button fills the width of the page, in every section, apart from "← Previous page" beside it on a page after the first. Onboarding's reads "Continue →"; every other section's reads "Mark complete".
- Completing onboarding opens Section 1, not the hub. Completing the last open section returns to the hub.

- Every requirement is listed below the button, a met one ticked (✓) and quieter, an unmet one with a dot. As you type, an item changes between the two in place: scrolled to the very bottom of the page, nothing moves.
- Screen reader: a met item is read as "Done: …", and the tick and dot are not read.
- A refused completion ("This section was not marked complete…") also shows below the button.

## Pages within a section (onboarding)

- Onboarding plays as two pages: in Whatever You Do, the wizard's (the reason; the five ratings), and in the faithful port, the reason and four ratings, then "Who knows you best?". In the faithful port each page is headed by the section's title, with "Page 1 of 2" quietly beneath it. A section of one page, such as Section 1, says nothing of pages.
- Every page but the last ends in "Continue →" (the full width on the first page), disabled until that page's own requirements are met, which are listed beneath it as the gate's are. The last page ends in onboarding's own "Continue →", which completes it.
- "Continue →" goes to the next page, at its top. Pressing it on a page with a requirement unmet (re-enable the button in DevTools) comes back with "This page is not finished yet." beneath it.
- "← Previous page", a secondary button, sits on the left of the way on, level with it, as "Back" sits beside "Continue →" in the coach checklist; the way on takes the rest of the row, and the checklist sits beneath both. It is on every page but the first and goes to the page before, with its answers as left, landing at that page's "Continue →" rather than its top. The first page has none. On a page whose way on is not offered yet (behind an unconfirmed reading), it sits on its own.
- On the coach page, each checklist screen ("Continue →" to "About Sam", then on to the outcome, "Back", "Choose someone else"): if the top of the checklist had scrolled out of view, the new screen opens at its heading, not part way down; if it was in view, nothing moves. Keyboard focus is on the new screen's heading, so Tab goes on from there. The same screen sent back stays put, focus included: "Continue →" on "About Sam" with an answer missing shows its refusal beside the button, still in view; so do "Get a link for Sam", "Reissue link" and "Revoke link".
- Going back and clearing the reason, then going forward again: the last page's checklist also lists "Choose what's bringing you to the course…" unticked, and completing is refused with it.
- Typing `/sections/onboarding/pages/2/` before reaching it lands on the page reached. The hub's "Carry on" and onboarding's entry lead to the page reached, not the first. Once onboarding is complete, its hub entry and its sidebar entry open it at page 1, and "← Back to the hub" at the top of every page goes to the hub.
- Refreshing any page keeps you on it. (A refused "Continue →" is the exception, as a refused completion is: the browser offers to send the form again.)
- Without JavaScript: "Continue →" and "← Previous page" both work, and the coach checklist's buttons come back to the coach page, not the first.
- Keyboard only: after the page's fields, Tab reaches "← Previous page", then "Continue →".
- Screen reader: each page's heading is read on arrival, then "Page 2 of 3"; "← Previous page" is read as a link. A new coach checklist screen reads its heading.
- Phone width: "← Previous page" and "Continue →" share a row at 375px; at 320px "Continue →" drops to its own line beneath, still full width.

## Fixed ratings (after completing onboarding, or Section 5)

- The chosen point keeps its colour; the other points don't react to hover, and nothing looks clickable.
- "Fixed when you completed this section." shows under each fixed rating, and there is no Save button, with or without JavaScript.
- Keyboard only: Tab moves past the fixed ratings rather than into them.
- Screen reader: a fixed rating is read as its prompt with the chosen point, and announced as unavailable (dimmed).
- A page left open from before completing, in another tab: choosing a new point says "Not saved. This answer was fixed when you completed this section."

## Time estimates (the hub, each section, Section 5's two activities)

- On the hub, each entry's estimate is quieter than its title: at the right-hand end of the title's line on a wide screen, lined up down the page, and on a line of its own under the title at phone width. A locked entry's note sits beneath.
- Once something in a section is answered (the sort submitted, one onboarding rating), its estimate has gone from its hub entry and its page.
- Section 5's "This part: …" above its two activities stays after answering.
- On a section page the estimate sits under the heading as "Whole section: …"; in Section 5, "This part: …" also sits above the letter's task and above the closing ratings' introduction, and reads as belonging to what follows it. The two labels at the top of Section 5 read as different things.
- Phone width: a long title wraps, and its estimate stays on the line beneath it.

## A link to another section (Section 1's Strengths assessment card)

- The card reads as a way somewhere else: the Strengths assessment's title, the text, the "Open Strengths Assessment →" button, then its status chip on a line of its own, coloured as on the hub.
- Before the sort is in, nothing follows the card: no reflection and no "Mark complete". After the sort, coming back to Section 1 shows the reflection.
- Keyboard only: Tab reaches the button, its focus is visible, and Enter opens the Strengths assessment.
- Screen reader: Tab to the button. It is a link styled as a button, since it goes to another page, so VoiceOver reads "Open Strengths Assessment, right arrow, link" and tells you how to follow it. Control-Option-Right arrow then reads the status.
- Phone width: the card's text and button wrap, and the status chip stays a small pill the width of its words rather than stretching across the card.
- Once the sort is in, back on Section 1 the card reads "You've completed the assessment. You can review your results any time." in place of "Sort your strengths into buckets…", and the button reads "View my results →". Clicking it opens your results page (or, with tie-break pairs still to answer, the next pair), never the assessment's start page. The status chip reads "Complete". Same in both pathways.
- Phone width: the finished sentence and the "View my results →" button wrap within the card.

## Sections 2–4 on paper (after Section 1, with a coach's link and three people's links made)

- The hub lists onboarding, Section 1, the Strengths assessment, "The shape of your life", "Putting your calling into words", "Growth plan" and Section 5, and no "The Workbook".
- Section 1 completes with the sort in and the reflection written, without visiting the comparison and with nobody invited; its checklist lists only the assessment and the reflections.
- With Section 1 complete and nobody invited, Section 2's entry says "Opens once you've finished Walk with a coach and Five trusted voices."; once the coach is saved, "Opens once you've finished Five trusted voices."; once three people are added, it opens. With a participant started after the pathway was loaded again (B1A-66): Section 2 opens with the sort in and both cards complete while Section 1 is still unfinished; before the sort, with nothing else done, its entry says "Opens once you've finished Strengths assessment, Walk with a coach and Five trusted voices." Section 3's entry then says "Opens once you've finished How you've been designed and The shape of your life.", and once Section 2 alone is finished, "Opens once you've finished How you've been designed." Phone width: the longer note wraps within its entry.
- Walk with a coach's and Five trusted voices' pages have no "Mark complete" and no "Mark as not complete". Until complete, each lists what it waits on ("Choose a coach and send them their link.", "Add at least 3 people.") as plain text, not a link; once complete, nothing below the list. The header's count goes up as each completes.
- Five trusted voices stays "Complete" after revoking one person's link (and Section 2 stays open). Phone width: Section 2's lock note wraps within its entry.
- While Section 2 is the next step, the hub's next step shows its title and "About 30–40 minutes". Section 3's entry says "Opens once you've finished The shape of your life.", and Section 4's "Opens once you've finished Putting your calling into words.".
- In each of Sections 2, 3 and 4, "Download Section 2 (PDF)" (3, 4) opens that section's PDF in the browser's own viewer, not a blank page or a download of an HTML error, and saving it keeps the name `whatever-you-do-workbook-section-2.pdf` (3, 4). Its text reads plainly, with no mention of a draft.
- "I've finished Section 2" leads to the hub with Section 3 open as the next step; the same for 3 and then 4, after which Section 5 opens.
- Keyboard only: Tab reaches the button and Enter opens the PDF; Tab then reaches "I've finished Section 2".
- Phone width: the button wraps rather than running off the screen, and the PDF opens in the phone's viewer.

## Scripture and the credits page (Section 1's reading, the homepage, `/credits/`)

- Section 1's passages show their references with no "(ESV)"; the homepage footer reads "Colossians 3:23 (NIV)".
- Scrolled down to "I have read these" and pressing it: the page comes back with "I have read these ✓" near the top of the window and what it opened beneath, not at the reading's heading above the passages.
- "Credits" sits at the foot of every page, the homepage's among its footer links, and leads to the credits page, signed in or not. It shows the ESV notice beginning "Unless otherwise indicated", then the NIV notice "marked NIV", each under its translation's name and word for word, with "®", "©" and "&" intact. Signed in, "← Back to the hub" is at its top; signed out, it is not.
- Whenever a passage is added or changed, compare its text with the publisher's word for word (for example the ESVUK or NIVUK on Bible Gateway): any cut is marked "…" or by its reference ("7a").
- Phone width: the notices wrap, and the footer link stays clear of the page's last block.

## The sort

- The cards come in a different order on each visit. The counter reads "1/36" and counts up.
- A thin gold progress bar runs across the top of the sort, empty at the start. It grows a step with each card, only ever goes back on an undo, is at 80% on "All 36 sorted!" and stays there on fine-tuning. Without JavaScript it is not shown. VoiceOver passes over it.
- Each bucket button places the card, the card flies (left for the weaker buckets, right for the stronger, down for the middle one), and the bucket's count goes up.
- Undo goes back one card at a time, all the way to the first, and is disabled when there is nothing to undo. Undoing the last card by keyboard moves focus to the "Sort your strengths" heading rather than losing it. It also works on the "All 36 sorted!" screen.
- Continuing is offered only once all 36 are sorted.
- The step labels read "Step 1 of 2 — Sort" and "Step 2 of 2 — Fine-tune".
- Fine-tuning groups the items under their buckets, strongest first, leaves out any empty bucket, and starts each slider at its bucket's seed (85, 65, 45, 25, 10 in Whatever You Do).
- Submitting without touching a slider still gives a complete result.
- "See my results" goes to the results page, and cannot be pressed twice while it is sending.
- After a sort is in, the section shows a link to the results instead of the sort. Submitting a second sort from another tab that still shows the sort says "Your results are already in…", not a connection error.
- Without JavaScript, the sort's place says it needs JavaScript.
- Keyboard only: the whole sort and fine-tune can be done. Focus stays on the bucket button just pressed, and moves to the new heading when the screen changes.
- Screen reader: each new card is announced ("Card 2 of 36: …"), and each slider is read with its item's text.
- Reduced motion: cards change without flying.
- Phone width: the bucket buttons stack, and a flying card never makes the page scroll sideways.

## Results

- Each construct reads as variant F (`prototype/result-bars`, `?variant=F`) did, without its ratio: its name and persona on the left, its standing on the right in its colour ("Leading", "Strong", "Present" or "Less used"), and beneath, a line across the full width with a dashed tick at an even share and the construct's dot, joined to the tick by a short line in the same colour. No percent anywhere on the page. The line has a short solid tick at each end and the dashed tick exactly in the middle, on every row and on the comparison too: the line runs from 0 to twice an even share (about 33% for six constructs), so a dot right of the middle is above an even share. A construct more than twice an even share sits at the right-hand end with a small arrow just past it in its colour, on this page and the comparison (the observers' arrow goes with their dot while the spread is ticked, and each person past the end gets one in its lane). No real sort is likely to reach it, so to see it set a stored share past the end in the dev database: `python manage.py shell -c "from engine.models import Result; r = Result.objects.latest('id'); r.scores['frameworks'][0]['constructs'][0]['percent'] = 40; r.save()"` makes the newest result's strongest APEST(d) construct 40%. The description, "Show item scores" (values unchanged) and the disclaimer are still there.
- On both frameworks, each dot, its line and its standing share the standing's colour: Leading dark green, Strong green, Present light green, Less used orange, so constructs with the same standing match whatever their order (fix-16).
- Phone width: each row's line still spans the width, the standing stays on one line beside the name, and no dot is cut off at either end.
- A screen reader reads each construct's name, persona and standing, and passes over the drawing.
- The generalist (Whatever You Do, a fresh participant): sorting every card into the same bucket and sending without moving a slider leaves both profiles level, and the results page opens with a hint box under the title, "You’re a generalist" in small capitals above its sentence, before the APEST(d) profile. A participant whose sort has clear leaders sees no such box, and neither does their coach's link. At phone width the box fits without the page scrolling sideways.
- The tie-break's pairs (Whatever You Do, a fresh participant): sort so that two APEST(d) roles come out level and PEP has a clear leader; sending leads to "Which is more true of you?" with a quiet label above it, two statement cards and "Neither fits — skip". Leave after one pair and open the results from the hub: you return to the next pair. After the last you reach your results. At phone width the cards stack full width without sideways scrolling.
- Tied on both, not flat (ticket 59a; load the pathway again first, then a fresh participant): sort so that two APEST(d) roles and two PEP energies each come out nearly level at the top, with a few cards in "Definitely not me" so something reads "Less used". Sending leads to the pairs, never the generalist box: the quiet label changes between "Your role among people" and "How you work" from one pair to the next. After the last pair the results show no generalist box.
- No results in Section 1 (Whatever You Do; load the pathway again first): before the sort, after it while a tie-break pair is left, and once the results are in, Section 1 shows nothing below the Strengths assessment's card but the gifts reflection: no results, no generalist or tie-break box, no "Compare with how others see you →". Once they are in, the card's "View my results →" opens them, and "Compare with how others see you →" is under them there, as before. Same at phone width.
- The re-weighted results: finish those pairs choosing the second-ranked role each time; the "Your APEST(d) Profile" card has a "Separated" box saying the top changed, that role now listed first, its dot only a little right of the one it passed, which keeps much the same standing as before (fix-22), and the comparison lists it first too. With a second fresh participant, choose one role in the first round and the other in the second: the box reads "Genuinely balanced" and names no leader. With a third, skip every pair: the box reads "Skipped" and the roles stay where the sort put them (ticket 59b). A coach given the results sees the same order but no box. At phone width the box sits inside the card without sideways scrolling.
- Both frameworks re-weighted and drawn unrounded (ticket 59b; load the pathway again first, then a fresh participant): sort as for "Tied on both, not flat", then choose one APEST(d) role in both its rounds and skip both PEP pairs. The "Your APEST(d) Profile" card has a "Separated" box and the "Your Professional Energy Profile (PEP)" card a "Skipped" box, each speaking only of its own profile, and no generalist box. Two roles that would round to the same percent sit a little apart on their lines, never on the same spot: on the results page, on the comparison (the observers' dot and, with the spread ticked, each observer's too) and on a coach's link. On each of those, the one further right is listed above the other, so no shorter line is ever above a longer one. At phone width the boxes sit inside their cards without sideways scrolling.
- The generalist's sentence (Whatever You Do): the hint box says both profiles are flat, every result "Present" or "Strong", and never that the top results are too close to call.
- A generalist after the pairs (fix-2; load the pathway again first, then a fresh participant): sort so that one APEST(d) role only just reads "Leading" with another just behind it, every other role and every PEP energy "Present" or "Strong". Choose one of the two in the first round and the other in the second. The "Your APEST(d) Profile" card has a "Genuinely balanced" box, both roles now read "Strong", and the results open with the generalist's box, its sentence saying both profiles are flat "even after your answers to “Which is more true of you?”". Choosing the same role in both rounds instead gives a "Separated" box and no generalist box. A coach given the results sees neither box. At phone width the box fits without sideways scrolling.
- Seeding the sorts for these checks (fix-15; load the pathway again first): rather than sorting by hand, `python manage.py seed_tie_break --profile <profile> --answers <answers>` makes a fresh participant with the sort already sent, and prints the sign-in details, a link that opens the first pair once signed in, which statement to choose (or skip) for each pair, and what the results should then show. Each run makes a new participant. The starting profile and how to answer the pairs are chosen apart (fix-25): `--profile` is `tied-apest`, `tied-pep`, `tied-both`, `just-leading` or `flat`; `--answers` is `leader`, `behind`, `one-each-way`, `skip`, or, with `tied-both` only, `separate-apest-skip-pep` or `separate-pep-skip-apest`. `flat` takes no `--answers` and every other profile needs one. `--profile flat --answers skip`, `--profile tied-apest --answers separate-apest-skip-pep` and `--profile tied-both` alone each stop with an error saying why, and make no participant. Which pair for which check:
  - The generalist, and the generalist's sentence: `--profile flat`.
  - The tie-break's pairs: `--profile tied-apest` (two APEST(d) roles level, PEP clear) with any answers; `--profile tied-pep` for two PEP energies level and APEST(d) clear, where every pair's quiet label reads "How you work".
  - Tied on both, not flat: `--profile tied-both` with any answers.
  - The re-weighted results: `--profile tied-apest --answers behind` for the "Separated" box with the top changed (Evangelist now first and Deacon second, both still "Leading", where Deacon used to drop to "Present"), `--answers leader` for "Separated" with the same top, `--answers one-each-way` for "Genuinely balanced", `--profile tied-both --answers skip` for "Skipped" (on both frameworks). With `--profile tied-pep`, the box is under the PEP profile instead, and the APEST(d) profile has none.
  - Both frameworks re-weighted: `--profile tied-both --answers separate-apest-skip-pep`; `--answers separate-pep-skip-apest` gives the "Separated" box under the PEP profile and "Skipped" under the APEST(d) profile.
  - A generalist after the pairs: `--profile just-leading --answers one-each-way`; `--answers leader` instead for the "Separated" box and no generalist box.
- The tie-break boxes name the roles and energies (fix-26; load the pathway again first, then a fresh participant for each, seeded or sorted by hand as above). Each box keeps its heading and its sentence names the constructs as the profile's labels do, except that deacon is "Deacon" with a capital, as everywhere text names it (fix-27):
  - A new leader ("Separated"): "Evangelist now sits on top, in place of Deacon, after your answers to “Which is more true of you?”." for `seed_tie_break --profile tied-apest --answers behind`; whichever role is chosen, the first name is the one now listed first and the second the one that led after the sort.
  - The same leader ("Separated"): choose the sort's leader in every pair; the box reads "<leader> stays on top, still ahead of <next>, after your answers to “Which is more true of you?”.", the second name the one listed just below it.
  - A circle ("Genuinely balanced"): "Your answers went in a circle — each option beat one and lost to another. That’s a real result rather than an error: <names> sit equally in you.", naming the tied roles in the order listed, "A and B" for two, "A, B and C" for more.
  - Level ("Genuinely balanced"): "<names> came out level after your answers to “Which is more true of you?”. That’s a real result rather than an error: they sit equally in you." (fix-28: reads the same for two or more, e.g. "Evangelist and Deacon came out level…")
  - Every pair skipped ("Skipped", on each framework skipped): "You skipped every “Which is more true of you?” pair here, so <names> stay as your sort placed them."
  - With both frameworks re-weighted, each box names only its own profile's constructs. A coach given the results, and the comparison, show no box. At phone width a longer sentence still wraps inside its card without sideways scrolling.

## The comparison (the results page's "Compare with how others see you →")

- Seed with `python manage.py seed_observers` and sign in as the participant it prints, with the banner saying the comparison is illustrative. Each construct is laid out as variant F (`prototype/result-bars`, `?variant=F`) did: the name on the left in a narrow column, any persona ("The Philosopher") on its own line beneath it and never wrapping, the line in the middle with a dashed tick at an even share, a green dot for you and a blue dot for the others, the stretch between them shaded grey, and on the right "You: Leading" in green, "Others: Strong" in blue, then in small grey "Others place this higher", "Others place this lower" or "Much the same". No agreement words until the spread is ticked (below). Over and above F, a green single-person icon sits just above your dot and a blue group icon just below the others', each centred on its dot, so where the dots overlap (a construct reading "Much the same") both icons still show in full. Only green and blue, in both frameworks. No "You / Others (average)" legend, and no percent anywhere on the page. The tick lines up down a framework's rows.
- With one or two observers (`seed_observers --observers 2`): "Not enough answers yet", "2 of 3 have answered so far", no percent anywhere and no banner. "Invite people who know you →" leads to the invitations page.
- "← Back to results" returns to the results page.
- In the faithful port, Section 1, with the sort in and the reflection written, before any visit: the checklist lists "View the 'Compare with how others see you' results to continue." unticked, between the assessment and the reflections, and "Mark complete" stays disabled. Find the way there from Section 1 alone (the Strengths card, then its results link, then "Compare with how others see you →"). With no observers, that page is "Not enough answers yet"; back in Section 1 the item is ticked and the section completes. Whatever You Do's Section 1 no longer asks for the visit (ticket 52).
- "Compare with how others see you →" is now a button in a form: it looks and sits as it did, works without JavaScript and by keyboard, and VoiceOver reads it as a button. In the faithful port, opening the comparison by typing its address shows it but leaves Section 1's item unticked.
- Phone width (under 600px): each construct stacks, the name, then the line full width with neither icon cut off at either end, then the words, then (while ticked) the agreement; the page never scrolls sideways.
- VoiceOver reads each construct as its name, then "You: Leading", "Others: Strong" and the "Others place this…" words, and skips the drawing. It reads the spread's tick as a checkbox, ticked or not.
- Below both frameworks, "🔍 Biggest Gaps" lists five cards, largest first, each naming its framework. A gap of five or more has a green "Others rate higher (+n)" or red "You rate higher (+n)" badge and its matching description; a smaller one reads "A modest gap…", and a gap of nothing has no badge. The badge's points are the only number on the page, until the content owner decides whether they stay (ticket 38).
- The gaps and agreement from unrounded shares (fix-1; `seed_observers`, as above): within one framework, a construct whose grey stretch is wider is never listed below one whose stretch is narrower. A construct reading "Much the same" beside its drawing never has a gap card with a badge's description: its card, if listed, reads "A modest gap…", even where its badge says "(+5)", which a gap just under five rounds to. No badge ever reads "(+0)": a gap too small to show as a whole number has no badge. With the spread ticked, the agreement words follow how far apart each construct's dots sit: dots close together read "Strong agreement", and a construct whose dots spread wider never reads as agreeing more than one whose dots sit closer.
- The words agree with the standings (fix-11; `seed_observers`, as above): no construct reads "Much the same" unless its "You:" and "Others:" standings are the same word. Where they differ, the words follow the standings even when the dots are close: "You: Strong", "Others: Less used" reads "Others place this lower", and "You: Present", "Others: Strong" reads "Others place this higher". Its gap card, if listed, can still read "A modest gap…", as the largest gaps are unchanged. Two dots on the same standing and close together still read "Much the same".
- "💬 Questions to sit with" follows with four gold-edged prompts, and its introduction says "coach".
- Phone width: a gap card's badge wraps under the construct's name instead of running off the card.
- At the foot of each profile card, under a thin rule, one tick, "Show how the 3 responses were spread", unticked, the same size and green tick as "Give my coach access…". Ticking it (mouse, or Tab then Space), with JavaScript on or off, does it for every construct in that card at once, the other card unchanged: each construct's blue dot, group icon and grey gap give way to a small blue dot per person, your dot and icon staying, and "Strong agreement", "Some variation" or "Divided views" appears in the observers' blue under that construct's line, centred where the group icon stood a moment before (set against the nearer side instead when the icon was near either end, never cut off), the same size at any window width. People at the same place as each other, or as you, never cover one another: the later ones drop into a lane just below the line, and however many share a place, the lanes squeeze closer together to stay inside the drawing, never over the agreement words or the next construct. Ticking and unticking move nothing: the card stays the same height and the tick stays where it is, as the room for the agreement line is kept while it is hidden. Unticking puts everything back. Ticking saves nothing: a reload shows it unticked. VoiceOver, while it is ticked, also reads "Each person's place, lowest first:" and their standings under each construct, which never show on screen. With two observers there is no comparison at all.

## Inviting observers (the contact list's page, from the hub's Five trusted voices card)

- Issuing a link shows it under that person's name, in a read-only field with Copy. Copy puts the whole link on the clipboard and reads "Copied"; pasting it in a private window opens "You've been invited".
- Without JavaScript, there is no Copy button, and the link in the field can be selected and copied by hand.
- With enough people listed that the page scrolls: with JavaScript, issuing, reissuing or revoking a lower person's link changes only their row, and the page does not move; the new link is focused. Without JavaScript, the page comes back opened at that person, not at the top.
- Reloading the page after issuing no longer shows the link (only its hash is kept), asks nothing about resending a form, and issues nothing new (the link from before still opens "You've been invited"), and the person shows "Link works until …" with "Reissue link" and "Revoke link".
- Going Back in the browser after issuing does not bring the link back from the cache.
- Phone width: the link field and Copy stay on one line without the page scrolling sideways.
- The observer's landing (a link opened in a private window): the notice's paragraphs, then "I'm answering for …" naming the participant, with nothing asked before it. Pressing it shows "Bookmark this link, it's yours" with Copy, as on the invitations page; reloading, or Back then Forward, does not bring the link back.
- After starting, the link as sent says "This link has already been used", in that window and in another; the bookmarked link, and `/observe/` in the same window, still reach "Answering for …". In a different browser, the bookmarked link reaches it too, but `/observe/` there says "This link does not work" (only starting sets the cookie). Reissuing from the invitations page stops them all.
- Signed in as the participant in the same browser, opening and starting their own link changes nothing on their hub or sections.
- Each listed person has "Remove", quieter than "Get link". For someone whose link works it opens "Remove Jo?" (in a dialog with JavaScript), saying the link will stop, with "Remove Jo" and "Keep Jo" stacked and alike in size; "Keep Jo" goes back to Jo's row with nothing changed. "Remove Jo" comes back to the list without Jo, the others unchanged, and Jo's link in a private window says "This link does not work". After revoking someone's link, "Remove" takes them off at once. Same with JavaScript off; at phone width the row's buttons wrap without the page scrolling sideways.

## The observer's assessment (after starting from a link, in a private window)

- The sort widget runs as the participant's does, about them: "Sort …'s strengths", "Choose the bucket that fits … best", buckets "Definitely not …" and "Not really …", the four reworded items ("outlast them", "different from theirs", "matters to them", "they could explain it"), "How strong is each one in …?", sliders from "Not …" to "Real strength", and "Send my assessment →", in the observer's own voice. Nothing speaks as the participant: no "Not me", "outlast you" or "your strengths".
- Sending shows "Thank you" in place of the widget, without a reload, and nothing of the assessment sent. Reloading, the bookmarked link, and `/observe/` all show the thanks, never the widget.
- From the bookmarked link in a different browser (no cookie), the assessment can be sent too, and the page it lands on is that link's.
- With the widget open in two tabs, sending from the second says "Your assessment has already been sent." beneath its button, not a connection error.
- The participant's own sort widget still reads in the first person, with "See my results →".
- Above the sort (load the pathway again first), "Your relationship to …" names the participant, with "Select..." then Family member, Close friend, Colleague / work contact, Church family / leader, Mentor / teacher and Other. It stays put while the cards are sorted and fine-tuned, and leaving it on "Select..." still sends. At phone width the label and box fit without a sideways scroll.
- After sending, the thanks carries a "Withdraw my answers" link, and nothing else is on the page: no sort, no relationship box, no "[Not built yet…]" line. From `/observe/` and from the bookmarked link alike.
- "Withdraw my answers" opens a page saying what withdrawing does, with a "Withdraw my answers" button; opening it, reloading it or going Back changes nothing. Pressing the button says "Your answers have been withdrawn". Then `/observe/` and the bookmarked link both say "This link does not work", and as the participant the invitations page shows the person as before. At phone width the button fills the width.
- Sending before fine-tuning (load the pathway again first): on "All 36 sorted!", under the bucket counts, "You can send your assessment now, or fine-tune how strong each one is in … first." and, side by side, "Send my assessment →" as the filled pill and "Continue to fine-tuning →" as the outlined one, with no slider to scroll past. Pressing send shows the thanks; the comparison (once three have answered) treats it as a sort sent with every slider untouched. Continuing still leads to the sliders and their "Send my assessment →". Undo still works from that screen. Keyboard: Tab reaches both buttons. Phone width: the two buttons stack, each whole, with no sideways scroll.
- The participant's own "All 36 sorted!" shows only "Continue to fine-tuning →", as before, with no send button and no sentence about sending.

## Answer collection freezes (after `migrate`; three observers answered, at least one more person invited)

- On the results page, "Compare with how others see you →" opens "Before you look": "3 of the 4 people you invited have answered…" and the same button again. "← Back to results" changes nothing; pressing the button opens the comparison. With everyone invited answered (or after `seed_observers`), it reads "Everyone you invited has answered. Once you look, you can't add anyone else." Below three answered, the press goes straight to "Not enough answers yet", as before.
- Once looked: the hub's Five trusted voices card reads "Complete" with "You've seen your results, so no more answers are added." The list's page says the same and why, has no empty row and no "Issue link" or "Reissue link"; names can still be saved, and "Revoke link" still works. The coach page still issues and reissues the coach's link.
- In a private window, an unanswered person's link shows the notice then "No more answers are being taken." with no button; their own link, if they had started, shows the same in place of the sort.
- An observer who answered withdraws: with two left, the comparison is "Not enough answers yet" again, the list offers its empty row and links again, and the next press asks again.
- The notice (load the pathway again first) ends with withdrawing at any time, through the link or by asking the people who run the service, and says no new answers are added once the participant has looked.
- Phone width: "Before you look" and the frozen notes fit with no sideways scroll.

## Observer reminders (after `migrate` and loading the pathway again; a person added at an address not at `example.com`)

- Move every link's clock back eight days with `python manage.py shell -c "from datetime import timedelta; from django.db.models import F; from engine.models import Invitation; Invitation.objects.update(issued_at=F('issued_at') - timedelta(days=8))"`, then run `python manage.py send_reminders`: it says "Sent 1 reminder." and the email printed above it reads "How do you see <name>'s strengths?", names the participant and the day the link stops working, asks for the link the participant sent, says where the name and email came from, and ends with "Stop reminders about <name>" and its link. Run it again: "Sent 0 reminders."
- Open the stop link in a private window: "Stop reminders about <name>" with a "Stop reminders" button; opening it stops nothing. Press it: "Reminders stopped". Move the clocks back another week and run the command: nothing is sent to that person.
- The participant's hub and list's page look the same before and after. The observers' notice ends with the reminders sentence.
- Phone width: the stop page fits with no sideways scroll.

## A fresh link from a reminder (load the pathway again; send a reminder as above)

- The printed email has a plain-text part with "Answer for <name> →" and its link, and an HTML part with that as a link and "How we handle your details" beside it, both to the same `/reminders/answer/…/` address.
- Open that address in a private window: the observers' privacy notice and "I'm answering for <name> →". Opening it changes nothing: the participant's copy of the link still opens its landing page.
- Press the button: the observer's page, showing their own link once, with the assessment. The participant's copy now gets the dead-link page; the participant's list's page looks the same as before.
- Press it again from another window: a new own link, and the first one is dead. After sending, the address gets the dead-link page. Phone width: no sideways scroll.

## Organisations and groups in the operator's admin (`/admin/`, as a superuser)

- The index has an "Organisations and groups" section with Groups, Memberships, Organisations and Permissions, apart from "Authentication and Authorization"'s own Groups.
- Adding an organisation shows a Permissions row under its name: typing part of an email in Holder finds the account, and saving with a capability makes the organisation and its first organisation admin in one go. The permission then lists the organisation and no group.
- Adding a group to it, with a type of Cohort or Team, shows its join token read-only once saved, and the same Permissions rows, plus Memberships where a participant can be found by email. Adding the same participant twice is refused with a message on the form, not an error page.
- On the Permissions list, adding one with both an organisation and a group, or neither, is refused with a message on the form.

## Your groups (the hub's "Your groups", after adding the participant to two groups in the admin)

- "Your groups" sits on the same line as "Your consent" at the foot of the hub, including on the empty "Nothing to begin yet" hub, and looks as quiet.
- The page has the header, as the hub does. Each group shows its name as a heading, its organisation under it, the sentence on what its admins see, and "Leave this group". No admin's name appears anywhere.
- "Leave this group" opens a page asking "Leave Autumn cohort?" (the group's own name), with "Leave this group" and "Stay in this group" stacked and alike in size. "Stay in this group" goes back with nothing changed; "Leave this group" comes back to "Your groups" without that group, and reloading asks nothing about resending a form.
- Without JavaScript, leaving works the same: the confirmation is a plain form.
- Keyboard only: Tab reaches each "Leave this group" link, then on the confirmation both choices in order.
- Phone width: the sentence wraps and the two buttons fill the width.
- A participant in no group sees "You're not in any groups."

## Joining a group by link (`/join/<token>/`, the token from a group in the admin)

- In a private window with the enrolment code on, the link leads to sign up with no "Enrolment code" field. Signing up leads to the consent text; agreeing leads to "Join Example Church, Autumn cohort?" (the group's own names) with the sentence on what its admins see, the same words as on the consent text's group line. "Join" lands on the hub, and the admin's Memberships list now shows the new account in that group.
- In a fresh private window, `/accounts/signup/` opened without a join link still asks for the enrolment code.
- Signed in and consented, the link shows the join page at once; "Not now, go to your pathway" leads to the hub and the Memberships list is unchanged. Opening the link again after joining says "You're already in this group" with "Go to your pathway".
- Signed out with an existing account, following "Sign in" from the sign-up page the link led to and signing in lands on the join page, not the hub.
- A made-up token in the link says "This link no longer works" and to ask whoever sent it for a new one, and names no group or organisation.
- Phone width: the join page's heading, sentence and "Join" button fit without the page scrolling sideways.

## Error pages (with `DJANGO_DEBUG` off, as a deployment runs)

Run with `DJANGO_DEBUG=false DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` before `python manage.py runserver`, after `python manage.py collectstatic --noinput`, since WhiteNoise then serves the styles from `staticfiles/`.

- `/observe/made-up-token/nothing-here/` shows "Page not found" in the site's styles, with the footer's Credits link and a "Go to the homepage" pill that leads there. Neither the address nor "made-up-token" appears anywhere on the page.
- Open a page with a form (sign in), delete the `csrftoken` cookie in the browser's developer tools, then send the form: "This page was out of date", with the same layout.
- At `/admin/`, five wrong passwords for the operator's username bring "Too many failed login attempts. Try again later." under the form, and the right password is then refused too, for five minutes.
- Phone width: each page's heading, sentence and pill fit without the page scrolling sideways.
- The server error and bad request pages are drawn the same way; the tests render them, since neither is easy to cause by hand.

## Your organisations (`/organisations/`, after giving the account a permission in the admin)

- With no permission, the hub's foot shows "Your consent · Your groups" only, and `/organisations/` says the page is for admins and offers the pathway, naming no organisation or group. After adding a permission, "Your organisations" joins the same line, as quiet as the others.
- With `manage` on Example Church: the page has the header, as the hub does, and shows Example Church with each of its groups under it, each with its name, "Cohort" or "Team", its member count ("1 member", "3 members"), and its join link in a read-only field with Copy. A group in another organisation does not appear.
- Copy puts the whole link on the clipboard and reads "Copied"; pasting it in a private window opens the join page for that group. Without JavaScript, there is no Copy button, and the link in the field can be selected and copied by hand.
- The browser's console shows no error on loading the page or pressing Copy.
- With `manage` on the Autumn cohort only: the page shows Example Church with the Autumn cohort alone. With `see_progress` only, the group shows its type and member count but no join link.
- An account that has not consented reaches the page by typing `/organisations/`, and is not sent to the consent text. Opening the hub instead lands on the consent text, whose foot links "Your organisations" for an account holding a permission (and not for one without).
- Phone width: the link field and Copy stay on one line without the page scrolling sideways.
- With `manage` on Example Church: under its groups (or under "No groups yet.") is a "New group" form with a Name field and Type as two radio buttons, Cohort already chosen. Creating "Worship team" as a Team comes back to the page scrolled to the new group, which shows "Team", "0 members" and its own join link; reloading asks nothing about resending a form. Creating with an empty name keeps the browser on the form; with the browser's check bypassed (removing `required` in the inspector), the page comes back with a message on the Name field and nothing created.
- With `manage` on the Autumn cohort only, or `see_progress` on Example Church, there is no "New group" form.
- Keyboard only: Tab reaches Name, the type radios (arrow keys move between Cohort and Team) and "Create group".
- Under each join link is "Replace link", quieter than Copy. It opens a page asking "Replace the join link for Autumn cohort?" (the group's own name), with "Replace link" and "Keep this link" stacked and alike in size. "Keep this link" goes back to the group with the same link; "Replace link" comes back to the group with a different link, the member count unchanged, and reloading asks nothing about resending a form. In a private window the old link says "This link no longer works"; the new one opens the join page.
- With `manage` on the Autumn cohort only, typing the "Replace link" address with another group's number in it is refused.
- Members' progress (after `seed_cohort`, signed in as the admin it prints): the Autumn cohort lists its twelve members by first name, A to Z. Ada, Ben and Cara say "not started"; Femi says "hasn't consented" and nothing else; the rest say "N of M sections · last active" with today's date and no time, the finished ones with N equal to M. No email address, answer, result or letter text appears, and the list sits in a "Members" card under the join link, each name in bold with a line between members and a clear gap before the next group, and reads well at phone width.

## Review fixes (fix-2)

- Five trusted voices' page (fix 4): change a listed person's name, then Tab: "Saved" shows in their row, with no Save button, and the focus stays in the next field. Type a new name in an empty row, then change someone else and Tab: the new row keeps what was typed. "Get link" on a new row opens the link in a dialog with Copy and "Done"; Reissue does too. `jo@` as an email: "Not saved. Check the email address." under that row's fields, the fields not narrowed. "Remove" for someone with a working link asks in a dialog; "Keep Jo" closes it. Without JavaScript: Save shows, and each button reloads the page at that person, the link shown open in the row. Phone width: the dialog fits, nothing scrolls sideways.
- Typing on Five trusted voices' page, with someone listed: change their name and stop typing without leaving the field: "Saved" shows in their row within a second, and reloading keeps it. Type steadily through their email: nothing typed is lost or the cursor moved while saves go. Leave the field: "Saved" again. Type `jo@` and pause: "Not saved. Check the email address." under the fields, gone as you type on. A new row still saves nothing until "Get link".
- Dialogs on Five trusted voices' page: scroll down so the list is part way up the window, then "Get link" on a new row: the link's dialog sits in the middle of the window over a dimmed page, not in the row or a corner; Tab stays inside it, and Esc or "Done" closes it. Reissue, and Remove for someone with a working link, do the same. Phone width: the dialog is centred with a margin each side.
- Ratings (fix 5; Before we begin's ratings as someone new, beside v3's `.rate`): each rating shows ten pale buttons and a muted dash on the right of the prompt. Choosing 6 turns 6 deep green with white text, 1 to 5 pale green, the dash a large 6, and "Saved" follows; reloading keeps it. Keyboard: Tab to a rating, arrow keys move the choice and save, with a ring on the point. Once Before we begin is complete, page 2 shows each rating the same way, nothing clickable or highlighted on hover. Without JavaScript the meter still fills as you choose, and Save keeps it; the number by the prompt shows after the reload. Phone width: all ten buttons fit on one line.
- Observer's landing (fix 7; load the pathway again, open a new link in a private window): the notice ends "This link is yours alone, so you answer only once and can stop the reminders or withdraw. Sam sees your answers among everyone else's, never with your name on them."
- Back from the green wipe (fix 8): on the homepage press "Begin your journey", let the green wipe finish, then Back: the homepage shows, not a green page, and the button works again.
- Hub (fixes 9, 12): the Five trusted voices title reads in light text on the brown card and turns lime when hovered. Section titles ("Before we begin") and side card titles ("Walk with a coach") are in the serif heading face, as v3's hub.
- Wizard page 2 (fix 10; someone new, wide window): the sun photo is the same size and crop as on page 1, and stays in view while the ratings scroll. Phone width: the photo sits above the form as before.
- Ghost buttons (fix 11): "Your pathway" and "Sign out" in the header have a pale fill on the cream, as do "Back" and "Keep Jo"; the homepage's "Begin your journey" ghost in "How it works" and "Ask us about coaching" stay clear on their dark panels.
- Five trusted voices' page (fix 13): "Needed" and "Optional" are small quiet labels, as v3's tags.
- Observer's assessment (fix 14): the relationship drop-down has the same border, corners, padding and font as the page's text inputs, its caret at the right, and the focus ring when focused.

## Review fixes (fix-3, cards outlined again in fix-8)

- Cards outlined: the sort's card on show, fine-tuning's groups of sliders, each section of the results page and each of the comparison's sections ("Biggest Gaps", "Questions to sit with" and each framework's) are on the paper with 12px corners and a thin pale outline, as the onboarding question cards and the account form card have. The sort's card's outline is the same 1px as the others' (fix-9). The bucket buttons, the bucket headings above fine-tuning's groups, the results' standing colours and the comparison's marks and gap badges keep their colours; the gap cards inside "Biggest Gaps" keep their own outline.
- Hub (signed in, framed): the paper side cards (the strengths assessment's and any other's on the right) have the same thin outline; Five trusted voices' dark card has no pale line round it and is the same width as the cards beside it. The section list and "Your next step" are unchanged.
- The sort, framed (a participant's Section 1) and on the cream (an observer's link, in a private window): the card on show stands out from the page, with its outline and soft shadow, before and while it flies to a bucket, and reads as easily as before. Keyboard only: each bucket button, Undo and each fine-tuning slider still shows its ring when focused.
- The coach's view of the results and comparison (the coach's link, once shared): the sections look the same as the participant's, outline included.
- Phone width: on the hub, the sort, fine-tuning, results and the comparison, each card fits with a margin each side, its outline whole, its words clear of its edges, and nothing scrolls sideways.
- Homepage (signed out): the header's "Coaches", the hero's "For coaches" and the footer's "For coaches" each scroll to the coach panel in "How it works"; the pillars read "Coach oversight". No "mentor" shows on the page.

## Hand-check fixes (fix-14; rebuild the frontend first)

- Homepage, "How it works": the selected tab's number is green and its title in light text, as clear as the others' or clearer, never dark on the brown; its bar fills green while the others stay faint. The panel beside it shows that step's words, and the photo changes with each step (step 1 the notebook, step 5 the hills), never the hills throughout. Clicking a tab, the arrows beside the tabs, and waiting each move the step on.
- Keyboard on "How it works": Tab to a tab: a green ring shows round it, inside the tab strip. The left and right arrow keys move to the previous and next step, the ring following the selected tab, and the panel's words change with it. Tab on to the arrow buttons: each shows a green ring.
- At about 375px, "How it works": the heading, the panel's words and its photo all fit inside the brown panel with a margin each side, nothing cut off at the right and nothing scrolling sideways; the tab strip alone scrolls sideways, and the selected tab scrolls into view as the step moves on.
- Homepage, the callings carousel near the foot ("Everyone has a purpose. Do you know yours?"): the photo cards turn round in a loop, Teacher, Electrician, Parent, Church planter, Student and back to Teacher, a card always in view, never the green background alone. Watch it for a full turn (about 35 seconds). The buttons below the cards sit clear of their words; ← and → each turn the ring by one card. Its pause button and what stops it are under fix-17 below. Same at about 375px.
- With reduced motion on (macOS: System Settings, Accessibility, Display, Reduce motion), reload the homepage: the callings show as plain cards, nothing turning and no buttons.
- Before we begin's wizard (someone new), both pages: "Ephesians 2:10" under the verse on the photo is in the verse's own light colour, in the same small capitals as before, and easy to read. Same at about 375px, where the photo sits above the page.

## Review fixes (fix-6)

- Signing in and out leaves no message behind: sign in (by email, and by Google where its pair is set), then "Sign out" in the header, then "Begin your journey" on the homepage. The sign-up page shows the demo notice, if on, and no green box: no "Successfully signed in as …" and no "You have signed out.". "Sign in" from there shows none either. Phone width: the same.
- A message still shows where it belongs: "Forgot your password?" from sign-in, follow the emailed link, set a new password: the page after says "Password successfully changed." in the green box; the sign-in page after it does not.

## Results coloured by standing (fix-16; load the pathway again first)

- The results page, Whatever You Do (a fresh participant whose sort gives a spread, a few cards in "Definitely not me"): on APEST(d) and on PEP, every construct's dot, the short line to the dashed tick and its standing word are one colour, by the word: "Leading" dark green, "Strong" green, "Present" light green, "Less used" orange (Present's light green from fix-17; the words in darker shades, as below). Constructs with the same word match, whatever their order on the card; orange shows beside "Less used" only. An APEST(d) role no longer keeps a colour of its own. "Show item scores" keeps each construct's own colour for its heading.
- PEP all "Present" (as in the screenshot that raised this: every energy level): all six dots are the same light green and all six words the same green, none orange.
- The faithful port's results: the same colours by the same words.
- Section 1: neither pathway shows results there, as before; its "View my results →" opens the results page above.
- The coach's view (a coach's link, once the results are shared): the same colours as the participant's page. The comparison on both is unchanged: "You" green, "Others" blue.
- Phone width: each standing word stays on one line in its dot's colour, and nothing scrolls sideways.

## Hand-check fixes (fix-17; rebuild the frontend first)

- Homepage, the callings carousel, on a wide screen: below the cards, ← then a small round pause button (two bars) then →, evenly spaced and clear of the cards' words. The ring keeps turning while the pointer rests on a card or a button, and after clicking ← or →. Clicking the pause button stops it; the button then shows a play triangle, and clicking it starts the ring again. ← and → still turn it by one card while it is stopped, and it stays stopped.
- At about 375px: the three buttons sit in one centred row below the cards, nothing cut off and nothing scrolling sideways; tapping the pause button stops and starts the ring as above.
- Keyboard only: Tab reaches ←, the pause button and → in that order, each showing a green ring round it, whole, not cut off at the foot. Tabbing in does not stop the ring; Enter or Space on the pause button does, and again starts it. With VoiceOver, the button is read "Pause carousel" while it turns and "Play carousel" while it is stopped.
- With reduced motion on, reload the homepage: plain cards, nothing turning, and no pause button or arrows.
- Results colours, Whatever You Do and the faithful port (a fresh participant whose sort gives a spread, a few cards in "Definitely not me"): on APEST(d) and on PEP, the dots and their lines are Leading dark green, Strong green, Present a lighter green and Less used orange, so only "Less used" is warm. Each standing word is a darker shade of its dot's colour and easy to read on the card; "Present" is a mid green rather than its pale dot's, "Less used" a deep brown-orange. Phone width: the same, nothing scrolling sideways.
- The coach's view (a coach's link, once the results are shared): the same dot and word colours as the participant's page.

## Retaking the assessment, demo only (fix-19; `DJANGO_DEBUG` on or `ANVILLE_DEMO_NOTICE` set)

- A participant with their results in (`seed_tie_break --profile tied-both --answers leader`, pairs answered, is quickest): at the foot of the results page, below "Compare with how others see you →", nothing at first. Tab through the page: the focus never reaches a retake link.
- Hidden until revealed (fix-20): on a Mac, hold Option on its own for about a second; a small grey "Retake the assessment (demo only)" appears there. Let go: it stays, and clicks normally. Reload: hidden again. A brief Option press, Option held with another key, or Option held while clicking shows nothing. On Windows, the same with Alt. Once shown, Tab reaches it.
- On a phone (or a browser's device mode with touch): press and hold the page's title for about a second; the link appears, with no text selected and no menu opened. A short tap, or a hold that turns into a scroll, shows nothing.
- With JavaScript turned off, the link never appears. It is not on the comparison, Section 1, the hub or the coach's view of the results.
- The link opens "Retake the assessment?", in the participant's frame, with "Demo only: …" first, what will be cleared, what stays, "Clear and retake" and "Keep my results". "Keep my results" and "← Back to results" go back to the results with nothing changed.
- With Section 1 marked complete, the page also says "“How you've been designed” will no longer be marked complete …"; with collection frozen (three observers answered, compared), that the people invited can send again; with the results shown to the coach, that the coach will no longer see them. Each line shows only when it applies.
- "Clear and retake" opens the Strengths assessment's sort with no cards placed. On the hub, the Strengths assessment and Section 1 are no longer "Complete"; Section 1's card shows "Open Strengths Assessment →" again, and the gifts summary written there is still there. "View my results" from a bookmark leads back to the sort. The invitations page still lists everyone, with their answers counted, and the coach page still has the coach.
- Sorting again leads to the results (or the pairs) as a first sort does; pressing "Compare with how others see you →" with three answers in asks "Before you look" again.
- With `DJANGO_DEBUG` off and no demo notice: no link on the results page, and typing `/results/strengths-sort/retake/` shows the not-found page.
- Phone width: the link and the page's buttons fit, nothing scrolls sideways.
- Demo profiles (fix-21, fix-25): "Retake the assessment?" also has "A demo profile places the cards for you, … Choose where the sort starts and how you will answer the pairs." and two drop-downs. "Starting profile" has "Sort the cards myself" first, then `seed_tie_break`'s five profiles by their summaries ("Tied on APEST(d) only: …", "Tied on PEP only: …", "Tied on both frameworks, not flat: …", "One role just Leading, …", "Flat on both frameworks: …"). With "Sort the cards myself", "How to answer the pairs" is greyed out and "Clear and retake" does exactly as above.
- With JavaScript on, choose each profile in turn: "How to answer the pairs" offers "Choose the leader each time: …", "Choose the one behind each time: …", "One answer each way: …" and "Skip every pair." for the four tied ones, and the two "… separated, …; … skipped." lines only for "Tied on both frameworks, …"; the rest are greyed out and cannot be chosen. For "Flat on both frameworks: …" only "No pairs" can be chosen, and it is chosen for you. Choosing a profile that greys out the answer chosen moves it to the first one left.
- With JavaScript off, every answer can be chosen: "Tied on APEST(d) only: …" with "APEST(d) separated, …" and "Clear and retake" shows only "separate-apest-skip-pep fits only tied-both." and clears nothing; "Flat on both frameworks: …" with any answer but "No pairs" is refused the same way, saying it takes no answers, and a tied profile with "No pairs" says it needs a way of answering them.
- Choose "Tied on both frameworks, not flat: …" with "Choose the leader each time: …" and press "Clear and retake" (fix-23): the address ends `?profile=tied-both&answers=leader`; the Strengths assessment's sort opens on "All 36 sorted!", the ✅, each bucket's count, "Continue to fine-tuning →" and "↩ Undo last"; the progress bar is at the sort's end. The sort has the page's usual width, nothing beside it (fix-24). Below it, under a thin line, one small grey line, "Demo profile", closed; opening it shows, in the same small grey text: "Demo only: …", the profile's summary followed by the answers' ("Tied on both frameworks, not flat: … Choose the leader each time: …"), "Every card is placed and every slider set for this profile. …", "If you change a card or a slider, …", "Answer the 4 pairs, in order:" with each answer in the pair screen's words, "The results should then show:" with each framework's two leaders and its tie-break note, and "No generalist box." The lines match `seed_tie_break --profile tied-both --answers leader`'s; each pair's answer chooses the role or energy that was ahead. Load it again with "Skip every pair.": every answer is now a skip, and the results show "Skipped" on both. On the hub nothing has changed yet: the assessment is not in until sent.
- "Continue to fine-tuning →": every bucket's sliders sit at different values, not all at the bucket's middle. "Demo profile" stays below the sliders and the "See my results →" button. "See my results →" opens the pair marked "1 of 4", at its usual width, with "Demo profile" closed below "1 of 4"; opened, it has the same lines (no "Every card is placed …" lines). Answering as listed, it is below each pair, closed again, and the results are as it promised.
- "↩ Undo last" on "All 36 sorted!" brings back one card to sort; placing it in the same bucket keeps its slider's value, in another starts it at that bucket's middle. Changed or not, the sort sends and is scored as any other.
- Choose "Flat on both frameworks: …" with "No pairs" (the address ends `?profile=flat`): "Demo profile", opened, says "No pairs: the results show straight away." and the generalist's box, and sending the sort opens the results with that box. Try "Tied on APEST(d) only: …" and "Tied on PEP only: …" with "Choose the one behind each time: …" and "One answer each way: …", and "Tied on both frameworks, …" with each "… separated, …; … skipped." line, the same way: the results are as the guide promised each time.
- Before any sort, a new participant on the Strengths assessment's sort page: nothing below the sort at first; hold Option (Alt), or press and hold the title on a phone, and a small grey "Load a demo profile (demo only)" appears below it. It opens "Load a demo profile?", with "← Back to the sort", "Demo only: …", the two drop-downs, "Starting profile" without "Sort the cards myself" and its first profile chosen (no "will be cleared" lines), "Load this profile" and "Sort the cards myself". "Sort the cards myself" goes back to the untouched sort; "Load this profile" opens the sort on "All 36 sorted!" with "Demo profile" below it, as above (the hidden link, revealed, comes after it). Reloading that page starts from the profile again; the sort page's own address, without `?profile=…`, starts from a full deck, and so does `?profile=tied-both&answers=nonsense`.
- On the faithful port (load `pathways/whatever-you-do-faithful-port.json`): the sort page has no "Load a demo profile" link, and "Retake the assessment?" has no drop-downs or demo-profile line; `/results/strengths-sort/retake/` before any sort says "No demo profile fits this pathway." with only "Sort the cards myself".
- With `DJANGO_DEBUG` off and no demo notice: the sort page has no hidden link, and `/sections/strengths/?profile=tied-both&answers=leader` shows the sort from a full deck, with no "Demo profile".
- Phone width (375px): both drop-downs fit the card, each under its label (a long summary may be cut short in one, in full once opened); on the sort and the pairs "Demo profile" is below them, closed, one line; opened, its lists wrap and nothing scrolls sideways. The sort and the pairs fill the width as they do without a profile. Wide (1200px and more) it is below them too, never beside, and the page is no wider than usual.

## Deacon in text, deacon beside its line (fix-27; load both pathways again first)

- Beside the lines, deacon stays in lower case, as the prototype wrote it: the results page's APEST(d) profile, the comparison's rows and a coach's link all read "deacon".
- Wherever text names it, it is "Deacon": the tie-break boxes (`seed_tie_break --profile tied-apest --answers behind` reads "Evangelist now sits on top, in place of Deacon, after your answers to “Which is more true of you?”."), the heading over its item scores under "Show item scores", a largest-gaps card on the comparison that names it ("Deacon (APEST(d))"; `seed_observers`, until deacon is among the largest gaps), and the leaders listed under "The results should then show:", in the "Demo profile" guide and in `seed_tie_break`'s output.
- The faithful port reads the same, beside its lines and in its item scores and largest gaps. A result scored against a pathway version loaded before this change still reads "deacon" everywhere, as before. Same at phone width.
