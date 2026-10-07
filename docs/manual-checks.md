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

## The homepage (`/`, signed out and signed in)

- Side by side with the prototype's homepage (`Prototypes for reference/original-prototype.html`) and its newer "How it works" (`how-it-works-homepagesection.html`), the words match. The only differences: "anonymously" is gone from step 1, the Churches, Writing, Newsletter, Team, Go further, Donate and Contact sections are gone, and so are the footer's Privacy Policy and Terms links.
- The forest video plays muted and loops, with no sound and no controls. With the video blocked (DevTools, Network, right-click `hero.mp4`, "Block request URL", then reload), the still frame shows in its place.
- Reduced motion, and without JavaScript: the still frame shows from the start and the forest never moves, not even for a moment.
- In "How it works", steps 2–4 have greyed mockups, each labelled "In the workbook"; their words and times are as easy to read as step 1's.
- The round menu button stays visible over the video and over the white and pale sections below it. It opens a panel listing About, How it works and Impact only, and each link scrolls to its section and closes the panel.
- Without JavaScript, the menu still opens and its links still scroll.
- Keyboard only: Tab reaches the menu button first, Enter opens it, and the focus ring shows on it and on each link.
- DevTools, Network, reload: every request goes to this site (no Google Fonts, nothing else).
- On a wide screen, About's text is centred in a narrower column than How it works' steps, and Impact is centred beneath them.
- Phone width: the headline fits without sideways scrolling, step 4's four-column roadmap is still legible, the Begin buttons are easy to tap, each step's mockup sits above its words, and the impact figures stay beside their text.
- Signed out, both "Begin →" buttons open sign-up; signed in, both open the hub. Signing in, and agreeing to consent, both land on the hub, not the homepage.

## Sign up

- "I am 18 or over" sits beside its checkbox, as "Remember me" does on sign in.
- Submitting with it unticked: the browser stops the form and points at the box. Without JavaScript the same happens, since the check is the browser's own `required`.
- Keyboard only: Tab reaches the box and Space ticks it.
- "First name" comes first, with "e.g. Ed" as its placeholder, and the browser offers nothing saved for it.
- With `ANVILLE_ENROLMENT_REQUIRED=false` there is no enrolment code field; with it left out, the field sits after the email.

## Consent

- After signing up, and at a first sign-in, the consent page comes before the hub.
- Agreeing as a new participant opens onboarding, with the reason drop-down first, not the hub. "Back to the hub" still reaches the hub.
- "I agree" and "I do not agree" are stacked with a gap between them and look like equal choices: neither is hidden, greyed out or smaller.
- "I do not agree" says nothing will be stored, and "Read the text again" goes back to the page.
- Without JavaScript, both buttons work: the page is a plain form.
- Keyboard only: Tab reaches both buttons in order, and Enter presses the focused one.
- Phone width: the text wraps and the buttons fill the width.
- "Your consent" sits quietly at the foot of the hub, including on the empty "Nothing to begin yet" hub.
- Once agreed, "Go to your pathway" and "Withdraw my consent" look alike in size, stacked as the first two buttons were.
- With a section open in one tab, withdraw in another, then type in the first tab: the page goes to the consent page rather than showing "Saved" or an error.

## Autosaved answers (long text, 1–10 scale, single select)

- Typing or choosing shows "Saved"; changing the answer again clears it; a slow save shows "Saving…".
- With the server stopped, a save says "Not saved. Check your connection, then try again."
- A refused answer shows its reason where "Saved" would be.
- Near the 20,000-character limit, the text box says how many characters are left.
- Without JavaScript, a Save button appears and saves the answer. With JavaScript it is hidden.
- Screen reader: "Saved" and a refusal are announced.
- Ghost text (Section 1's reflection, the letter): it shows in grey in the empty box, is readable against the background, and disappears as you type. A screen reader names the box by its prompt, not by the ghost text.
- The reason in onboarding: it looks like the prototype's account-screen drop-down (a small dark caret at the right, not the browser's arrow), and is amber while "Select..." is showing, turning white once a reason is chosen, with or without JavaScript. The drop-down shows "Select..." until a reason is chosen, and choosing one shows "Saved" with no button press. Going back to "Select..." shows "Saved", turns the drop-down amber again, and unticks "Choose what's bringing you to the course" beneath the button; a reload still shows "Select...". Keyboard only: Tab reaches it, and the arrow keys change it (each change saves). It fills the card's width at phone width.

## The contact list (onboarding's "Who knows you best?")

- It sits on onboarding's last page, reached by "Continue →" from the baseline ratings' page (and, in Whatever You Do, the coach page): a numbered row per person, "First name" narrower than "Email address", two rows in Whatever You Do (five in the faithful port), with "+ Add another person" full width beneath.
- Typing a name and email and leaving the field shows "Saved"; a reload shows them again. Moving from a new row's name to its email shows "Not saved. Add both a name and an email address in row N." until the email is typed and left, then "Saved".
- A bad address (`jo`, `jo@`, `jo@example`) shows "Not saved. Check the email address in row N.", and that email box turns red. The next save that goes through clears the red. A half-filled row marks its empty field the same way.
- "+ Add another person" adds an empty numbered row without reloading, and the cursor goes into its name. At 50 rows it is disabled.
- Emptying every row and leaving the field shows "Saved"; a reload shows empty rows, and onboarding's "Add at least 2 people…" is ticked again.
- With one person added, "Add at least 2 people…" is unticked beneath "Continue →"; with two it is ticked, as it is with none.
- Without JavaScript: the Save button saves the list; "+ Add another person" saves it and comes back with one more row, at the list. A bad address is not stopped by the browser; the save comes back with the server's "Not saved. Check the email address in row N." on a plain page (as any refused save does without JavaScript).
- Screen reader: after a refusal, the marked field is announced as invalid when Tab reaches it.
- Keyboard only: Tab goes name, email, name, email down the rows, then to "+ Add another person"; Enter in a field saves.
- Screen reader: each field is read as "Person 1, first name" and so on; the row numbers themselves are not read. A new row is numbered on.
- Phone width: each row's name and email stack beneath its number, full width.

## The coach's details (Whatever You Do's coach page)

- Going ahead (all Yes, or "I'm still confident — ask Sam"): beneath the gold box come "Their name" (already holding the first name typed on the intro), "Their email", the tick "I've spoken to this person and they're happy to receive a link from me about coaching me through this course.", a full-width "Save Sam as your coach", then "Choose someone else". The two boxes look like the intro's name box; the tick sits beside its words, not above them.
- Saving with the box unticked says "Tick the box to confirm you've spoken to them." beneath the tick, with the name and email kept as typed; a bad address (`sam`, `sam@`, `sam@example`) says "Check their email address." and the email box turns red. Nothing is saved either way.
- Saving shows "You've chosen Sam" with their email, "Choose someone else" and "Remove", without reloading the page. A reload, or coming back through the hub, shows the same.
- Before a coach is kept, the page's way on beneath the checklist is a secondary "I'll sort this later →", so it never reads as a second "Continue →" under the checklist's own. Saving turns it into the primary "Continue with Sam →" without a reload, with no jump; "Remove" turns it back. Pressing "I'll sort this later →" with details typed but not saved leaves no coach.
- "Choose someone else" starts the checklist again, with "Sam stays your coach until you save someone else." and "Keep Sam" beneath its "Continue →"; the page's way on still reads "Continue with Sam →", so no two buttons say the same thing. Enter in the name box goes on to the questions, not "Keep Sam". "Keep Sam" goes back to "You've chosen Sam" (or "Sam is your coach" once they have accepted). A reload before saving anyone new still shows the coach saved before. "Remove" goes back to the intro, and a reload shows the intro.
- Without JavaScript: saving and "Remove" come back to the coach page at the checklist; a refused save comes back as the whole coach page with its reason.
- Screen reader: the refusal is announced; a refused field is announced as invalid when Tab reaches it.
- Phone width: the details and buttons fill the card's width.

## The coach's link (ticket 13c)

- "You've chosen Sam" says the next step is to ask them properly, with "Get a link for Sam". Pressing it shows the link once beneath, with "Copy", "Waiting for Sam to answer. The link works until …", "Reissue link" and "Revoke link", without reloading the page; the link box has focus. "Copy" says "Copied". A reload shows no link, only the status.
- Enter in the link box does nothing: the link stays the same and still works (with and without JavaScript).
- Without JavaScript: "Get a link for Sam", "Reissue link" and "Revoke link" each come back to the coach page at the checklist, the link shown once after issuing.
- In a private window, the link shows "participant has asked you to be their coach" (the participant's display name), the two authored paragraphs, "What you'd be agreeing to" and the six promises, each with its note in smaller type and a box to its left; the box or its words tick it. The line on what is kept sits above "Accept →" and "I can't commit to all of this".
- "Accept →" with a box unticked says "Tick all six to accept…" with the boxes as they were. All six ticked: "Thank you — participant will be told" and the authored line; a reload shows the same, never the boxes again.
- "I can't commit to all of this" (any boxes ticked): "That's a good answer" and the two authored paragraphs.
- Back on the coach page after an accept: "Sam is your coach" in the gold card, with "Sam has accepted." After a decline, the card turns amber: "Sam isn't able to be your coach", choosing someone else or carrying on without a coach, "Choose someone else" as the primary button, and the page's way on reads "Continue without a coach →". Neither says which boxes were ticked.
- Saving another coach, or "Remove", then opening Sam's old link: "This link does not work". So too a revoked link, and Sam's link at `/observe/…` in place of `/coaching/…`.
- Keyboard only: Tab reaches each box, then Accept, then decline; Space ticks a box.
- Phone width: the promises wrap beside their boxes; the buttons fill the card's width.

## The coach sees the results and comparison (ticket 27)

- After accepting, the coach's link shows "What happens next" in a pale box within the gold card, "Sam finishes the strengths assessment and sends it to you. You'll get the results, and how others rate the same strengths. They'll appear on this page, so keep the link." It promises no guide or email.
- On the comparison, with Sam chosen but not yet accepted: "Once Sam accepts being your coach…" with "Your coach page →", in a card at the top, just under "How others experience you", and no box. Once Sam has accepted, in that card at the top: "Give my coach access to my results and this comparison", unticked, and beneath it, lined up under the label's words, "Sam will see your results and the comparison below, which may update if more people answer.", the same however many have answered; no Save button. The tick looks like the coach details' "I've spoken to this person…" tick: same size, normal weight, a gap between box and words, the box level with the first line. Opening the comparison by its typed address, without pressing "Compare with how others see you →" first, shows no box and no empty panel. After Sam declines, the comparison says nothing of Sam. Once Sam's accepted link expires (in the Django shell, set that `Invitation`'s `expires_at` to the past), the comparison says the link has expired, and the hub no longer offers to let them see the results.
- Ticking saves at once: "Saved" at the card's foot, as autosaved answers show it, and the line becomes "Sam can see your results and the comparison below, which may update if more people answer. Untick to stop sharing." without a reload. Unticking saves at once too and turns the line back. With the network off (devtools, Offline), ticking says "Not saved. Check your connection, then try again." Without JavaScript, a "Save" button shows and does the same, coming back to the box. In a private window Sam's link now shows, below the gold card and in place of "What happens next", "participant's results", a line saying the participant is happy for them to see this, the results as the participant sees them (item scores included), then "How others experience participant" and the comparison, whose own sentences say "participant" where the participant's say "you", and whose single-person icon VoiceOver reads as "participant: Leading" where the participant hears "You: Leading" (the pathway's authored headings, gaps and questions still say "you"). Below the minimum: "Not enough answers yet" with the count, and no "Invite people who know you →".
- The coach's page has no form, button or link that changes anything of the participant's.
- Unticking and saving, then reloading Sam's link: "What happens next" again, and no results.
- The hub, beneath "Invite others to assess you →": before a coach is chosen, a white "🧭 Your Coach · Add →" card, "You haven't added a coach yet…", that leads to the coach page at the checklist and turns green-edged on hover and keyboard focus. Once Sam is chosen, a link to the same place instead, saying where things stand: "You've chosen Sam: send Sam a link →", "Waiting for Sam to answer →", "Sam is your coach →" or "Sam isn't able to be your coach →", with "Sam can see your results and comparison." beneath while that stands. The faithful port's hub shows neither.
- Phone width: the shared results and comparison on Sam's link fit as on the participant's own pages.
- As an observer, in a private window: the privacy notice says the participant may also show what they see to a trusted third party (load the pathway again first).

## The gate and "Mark complete"

- The button fills the width of the page, in every section. Onboarding's reads "Continue →"; every other section's reads "Mark complete".
- Completing onboarding opens Section 1, not the hub. Completing the last open section returns to the hub.

- Every requirement is listed below the button, a met one ticked (✓) and quieter, an unmet one with a dot. As you type, an item changes between the two in place: scrolled to the very bottom of the page, nothing moves.
- Screen reader: a met item is read as "Done: …", and the tick and dot are not read.
- A refused completion ("This section was not marked complete…") also shows below the button.

## Pages within a section (onboarding)

- Onboarding plays as three pages in Whatever You Do (the reason and the five ratings; "Walking with a coach"; "Who knows you best?") and two in the faithful port (no coach page). Each page is headed by the section's title, with no page count.
- Every page but the last ends in a full-width "Continue →", disabled until that page's own requirements are met, which are listed beneath it as the gate's are. The coach page lists none, and its way on is never disabled: a secondary "I'll sort this later →" until a coach is kept, then "Continue with Sam →". The last page ends in onboarding's own "Continue →", which completes it.
- "Continue →" goes to the next page, at its top. Pressing it on a page with a requirement unmet (re-enable the button in DevTools) comes back with "This page is not finished yet." beneath it.
- "← Back", a secondary button not the page's full width, sits beneath the way on and its checklist, not beside the button, so "Continue →" is in the same place on every page. It is on every page but the first and goes to the page before, with its answers as left. The first page has none.
- Going back and clearing the reason, then going forward again: the last page's checklist also lists "Choose what's bringing you to the course…" unticked, and completing is refused with it.
- Typing `/sections/onboarding/pages/3/` before reaching it lands on the page reached. The hub's "Carry on" and onboarding's entry lead to the page reached, not the first.
- Refreshing any page keeps you on it. (A refused "Continue →" is the exception, as a refused completion is: the browser offers to send the form again.)
- Without JavaScript: "Continue →" and "← Back" both work, and the coach checklist's buttons come back to the coach page, not the first.
- Keyboard only: after the page's fields, Tab reaches "Continue →", then "← Back".
- Screen reader: each page's heading is read on arrival; "← Back" is read as a link.
- Phone width: "Continue →" fills the width, and "← Back" sits on its own line beneath the checklist.

## Fixed ratings (after completing onboarding, or Section 5)

- The chosen point keeps its colour; the other points don't react to hover, and nothing looks clickable.
- "Fixed when you completed this section." shows under each fixed rating, and there is no Save button, with or without JavaScript.
- Keyboard only: Tab moves past the fixed ratings rather than into them.
- Screen reader: a fixed rating is read as its prompt with the chosen point, and announced as unavailable (dimmed).
- A page left open from before completing, in another tab: choosing a new point says "Not saved. This answer was fixed when you completed this section."

## Time estimates (the hub, each section, Section 5's two activities)

- On the hub, each entry's estimate is quieter than its title: at the right-hand end of the title's line on a wide screen, lined up down the page, and on a line of its own under the title at phone width. A locked entry's note sits beneath.
- Once something in a section is answered (the sort submitted, one onboarding rating), its estimate has gone from its hub entry and its page.
- Section 5's "This part: ? min" above its two activities stays after answering.
- On a section page the estimate sits under the heading as "Whole section: …"; in Section 5, "This part: ? min" also sits above the letter's task and above the closing ratings' introduction, and reads as belonging to what follows it. The two labels at the top of Section 5 read as different things.
- Phone width: a long title wraps, and its estimate stays on the line beneath it.

## A link to another section (Section 1's Strengths assessment card)

- The card reads as a way somewhere else: the Strengths assessment's title, the text, the "Open Strengths Assessment →" button, then its status chip on a line of its own, coloured as on the hub.
- Before the sort is in, nothing follows the card: no reflection and no "Mark complete". After the sort, coming back to Section 1 shows the reflection.
- Keyboard only: Tab reaches the button, its focus is visible, and Enter opens the Strengths assessment.
- Screen reader: Tab to the button. It is a link styled as a button, since it goes to another page, so VoiceOver reads "Open Strengths Assessment, right arrow, link" and tells you how to follow it. Control-Option-Right arrow then reads the status.
- Phone width: the card's text and button wrap, and the status chip stays a small pill the width of its words rather than stretching across the card.

## The Workbook (after Section 1, with the coach's and two observers' links issued)

- The hub lists onboarding, Section 1, the Strengths assessment, the Workbook and Section 5, and nothing of Sections 2–4.
- Section 1's checklist ticks "Choose a coach and send them their link" and "Send at least 2 people their links" as each link is issued, after a reload.
- "Download the workbook (PDF)" opens the PDF in the browser's own viewer, not a blank page or a download of an HTML error, and saving it from there keeps the name `whatever-you-do-workbook.pdf`. The page's last paragraph says the workbook is a draft.
- Keyboard only: Tab reaches the button and Enter opens the PDF; Tab then reaches "I've finished the workbook".
- Phone width: the button wraps rather than running off the screen, and the PDF opens in the phone's viewer.

## Scripture and the credits page (Section 1's reading, the homepage, `/credits/`)

- Section 1's passages show their references with no "(ESV)"; the homepage footer reads "Colossians 3:23 (NIV)".
- "Credits" sits at the foot of every page, the homepage's among its footer links, and leads to the credits page, signed in or not. It shows the ESV notice beginning "Unless otherwise indicated", then the NIV notice "marked NIV", each under its translation's name and word for word, with "®", "©" and "&" intact.
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
- PEP dots that tie share a colour.
- Phone width: each row's line still spans the width, the standing stays on one line beside the name, and no dot is cut off at either end.
- A screen reader reads each construct's name, persona and standing, and passes over the drawing.

## The comparison (the results page's "Compare with how others see you →")

- Seed with `python manage.py seed_observers` and sign in as the participant it prints, with the banner saying the comparison is illustrative. Each construct is laid out as variant F (`prototype/result-bars`, `?variant=F`) did: the name on the left in a narrow column, any persona ("The Philosopher") on its own line beneath it and never wrapping, the line in the middle with a dashed tick at an even share, a green dot for you and a blue dot for the others, the stretch between them shaded grey, and on the right "You: Leading" in green, "Others: Strong" in blue, then in small grey "Others place this higher", "Others place this lower" or "Much the same". No agreement words until the spread is ticked (below). Over and above F, a green single-person icon sits just above your dot and a blue group icon just below the others', each centred on its dot, so where the dots overlap (a construct reading "Much the same") both icons still show in full. Only green and blue, in both frameworks. No "You / Others (average)" legend, and no percent anywhere on the page. The tick lines up down a framework's rows.
- With one or two observers (`seed_observers --observers 2`): "Not enough answers yet", "2 of 3 have answered so far", no percent anywhere and no banner. "Invite people who know you →" leads to the invitations page.
- "← Back to results" returns to the results page.
- Section 1, with the sort in and the reflection written, before any visit: the checklist lists "View the 'Compare with how others see you' results to continue." unticked, between the assessment and the reflections, and "Mark complete" stays disabled. Find the way there from Section 1 alone (the Strengths card, then its results link, then "Compare with how others see you →"). With no observers, that page is "Not enough answers yet"; back in Section 1 the item is ticked and the section completes.
- "Compare with how others see you →" is now a button in a form: it looks and sits as it did, works without JavaScript and by keyboard, and VoiceOver reads it as a button. Opening the comparison by typing its address shows it but leaves Section 1's item unticked.
- Phone width (under 600px): each construct stacks, the name, then the line full width with neither icon cut off at either end, then the words, then (while ticked) the agreement; the page never scrolls sideways.
- VoiceOver reads each construct as its name, then "You: Leading", "Others: Strong" and the "Others place this…" words, and skips the drawing. It reads the spread's tick as a checkbox, ticked or not.
- Below both frameworks, "🔍 Biggest Gaps" lists five cards, largest first, each naming its framework. A gap of five or more has a green "Others rate higher (+n)" or red "You rate higher (+n)" badge and its matching description; a smaller one reads "A modest gap…", and a gap of nothing has no badge. The badge's points are the only number on the page, until the content owner decides whether they stay (ticket 38).
- "💬 Questions to sit with" follows with four gold-edged prompts, and its introduction says "coach".
- Phone width: a gap card's badge wraps under the construct's name instead of running off the card.
- At the foot of each profile card, under a thin rule, one tick, "Show how the 3 responses were spread", unticked, the same size and green tick as "Give my coach access…". Ticking it (mouse, or Tab then Space), with JavaScript on or off, does it for every construct in that card at once, the other card unchanged: each construct's blue dot, group icon and grey gap give way to a small blue dot per person, your dot and icon staying, and "Strong agreement", "Some variation" or "Divided views" appears in the observers' blue under that construct's line, centred where the group icon stood a moment before (set against the nearer side instead when the icon was near either end, never cut off), the same size at any window width. People at the same place as each other, or as you, never cover one another: the later ones drop into a lane just below the line, and however many share a place, the lanes squeeze closer together to stay inside the drawing, never over the agreement words or the next construct. Ticking and unticking move nothing: the card stays the same height and the tick stays where it is, as the room for the agreement line is kept while it is hidden. Unticking puts everything back. Ticking saves nothing: a reload shows it unticked. VoiceOver, while it is ticked, also reads "Each person's place, lowest first:" and their standings under each construct, which never show on screen. With two observers there is no comparison at all.

## Inviting observers (the hub's "Invite others to assess you →")

- Issuing a link shows it under that person's name, in a read-only field with Copy. Copy puts the whole link on the clipboard and reads "Copied"; pasting it in a private window opens "You've been invited".
- Without JavaScript, there is no Copy button, and the link in the field can be selected and copied by hand.
- With enough people listed that the page scrolls: with JavaScript, issuing, reissuing or revoking a lower person's link changes only their row, and the page does not move; the new link is focused. Without JavaScript, the page comes back opened at that person, not at the top.
- Reloading the page after issuing no longer shows the link (only its hash is kept), asks nothing about resending a form, and issues nothing new (the link from before still opens "You've been invited"), and the person shows "Link works until …" with "Reissue link" and "Revoke link".
- Going Back in the browser after issuing does not bring the link back from the cache.
- Phone width: the link field and Copy stay on one line without the page scrolling sideways.
- The contact list under "Add or change people": adding someone and pressing "Save list" comes back to the page, scrolled to the list rather than the top, with them listed above, ready to issue a link. A refused save (an email like `priya@`) comes back at the list too, as typed, with the field marked and why beside "Save list". With JavaScript, "+ Add another person" adds a row in place; without it, it saves and comes back with one more row.
- Autosave keeps people's links: in onboarding, add Jo and Priya in new rows without reloading (each field autosaves), issue Jo's link on the invitations page in another tab, then back in onboarding (still not reloaded) change Jo's email. Jo's link still opens "You've been invited".
- The observer's landing (a link opened in a private window): the notice's paragraphs, then "I'm answering for …" naming the participant, with nothing asked before it. Pressing it shows "Bookmark this link, it's yours" with Copy, as on the invitations page; reloading, or Back then Forward, does not bring the link back.
- After starting, the link as sent says "This link has already been used", in that window and in another; the bookmarked link, and `/observe/` in the same window, still reach "Answering for …". In a different browser, the bookmarked link reaches it too, but `/observe/` there says "This link does not work" (only starting sets the cookie). Reissuing from the invitations page stops them all.
- Signed in as the participant in the same browser, opening and starting their own link changes nothing on their hub or sections.

## The observer's assessment (after starting from a link, in a private window)

- The sort widget runs as the participant's does, about them: "Sort …'s strengths", "Choose the bucket that fits … best", buckets "Definitely not …" and "Not really …", the four reworded items ("outlast them", "different from theirs", "matters to them", "they could explain it"), "How strong is each one in …?", sliders from "Not …" to "Real strength", and "Send my assessment →", in the observer's own voice. Nothing speaks as the participant: no "Not me", "outlast you" or "your strengths".
- Sending shows "Thank you" in place of the widget, without a reload, and nothing of the assessment sent. Reloading, the bookmarked link, and `/observe/` all show the thanks, never the widget.
- From the bookmarked link in a different browser (no cookie), the assessment can be sent too, and the page it lands on is that link's.
- With the widget open in two tabs, sending from the second says "Your assessment has already been sent." beneath its button, not a connection error.
- The participant's own sort widget still reads in the first person, with "See my results →".
