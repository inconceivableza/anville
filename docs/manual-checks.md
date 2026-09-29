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

## Sign up

- "I am 18 or over" sits beside its checkbox, as "Remember me" does on sign in.
- Submitting with it unticked: the browser stops the form and points at the box. Without JavaScript the same happens, since the check is the browser's own `required`.
- Keyboard only: Tab reaches the box and Space ticks it.

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
- Saving shows "Sam is your coach" with their email, "Choose someone else" and "Remove", without reloading the page. A reload, or coming back through the hub, shows the same.
- Before a coach is kept, the page's way on beneath the checklist is a secondary "I'll sort this later →", so it never reads as a second "Continue →" under the checklist's own. Saving turns it into the primary "Continue →" without a reload, with no jump; "Remove" turns it back. Pressing "I'll sort this later →" with details typed but not saved leaves no coach.
- "Choose someone else" starts the checklist again; a reload before saving anyone new still shows the coach saved before. "Remove" goes back to the intro, and a reload shows the intro.
- Without JavaScript: saving and "Remove" come back to the coach page at the checklist; a refused save comes back as the whole coach page with its reason.
- Screen reader: the refusal is announced; a refused field is announced as invalid when Tab reaches it.
- Phone width: the details and buttons fill the card's width.

## The gate and "Mark complete"

- The button fills the width of the page, in every section. Onboarding's reads "Continue →"; every other section's reads "Mark complete".
- Completing onboarding opens Section 1, not the hub. Completing the last open section returns to the hub.

- Every requirement is listed below the button, a met one ticked (✓) and quieter, an unmet one with a dot. As you type, an item changes between the two in place: scrolled to the very bottom of the page, nothing moves.
- Screen reader: a met item is read as "Done: …", and the tick and dot are not read.
- A refused completion ("This section was not marked complete…") also shows below the button.

## Pages within a section (onboarding)

- Onboarding plays as three pages in Whatever You Do (the reason and the five ratings; "Walking with a coach"; "Who knows you best?") and two in the faithful port (no coach page). Each page is headed by the section's title, with no page count.
- Every page but the last ends in a full-width "Continue →", disabled until that page's own requirements are met, which are listed beneath it as the gate's are. The coach page lists none, and its way on is never disabled: a secondary "I'll sort this later →" until a coach is kept, then "Continue →". The last page ends in onboarding's own "Continue →", which completes it.
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

- PEP bars that tie share a colour.
