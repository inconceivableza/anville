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
- "I agree" and "I do not agree" are stacked with a gap between them and look like equal choices: neither is hidden, greyed out or smaller.
- "I do not agree" says nothing will be stored, and "Read the text again" goes back to the page.
- Without JavaScript, both buttons work: the page is a plain form.
- Keyboard only: Tab reaches both buttons in order, and Enter presses the focused one.
- Phone width: the text wraps and the buttons fill the width.
- "Your consent" sits quietly at the foot of the hub, including on the empty "Nothing to begin yet" hub.
- Once agreed, "Go to your pathway" and "Withdraw my consent" look alike in size, stacked as the first two buttons were.
- With a section open in one tab, withdraw in another, then type in the first tab: the page goes to the consent page rather than showing "Saved" or an error.

## Autosaved answers (long text, 1–10 scale)

- Typing or choosing shows "Saved"; changing the answer again clears it; a slow save shows "Saving…".
- With the server stopped, a save says "Not saved. Check your connection, then try again."
- A refused answer shows its reason where "Saved" would be.
- Near the 20,000-character limit, the text box says how many characters are left.
- Without JavaScript, a Save button appears and saves the answer. With JavaScript it is hidden.
- Screen reader: "Saved" and a refusal are announced.
- Ghost text (Section 1's reflection, the letter): it shows in grey in the empty box, is readable against the background, and disappears as you type. A screen reader names the box by its prompt, not by the ghost text.

## Fixed ratings (after completing onboarding, or Section 5)

- The chosen point keeps its colour; the other points don't react to hover, and nothing looks clickable.
- "Fixed when you completed this section." shows under each fixed rating, and there is no Save button, with or without JavaScript.
- Keyboard only: Tab moves past the fixed ratings rather than into them.
- Screen reader: a fixed rating is read as its prompt with the chosen point, and announced as unavailable (dimmed).
- A page left open from before completing, in another tab: choosing a new point says "Not saved. This answer was fixed when you completed this section."

## A link to another section (Section 1's Strengths assessment card)

- The card reads as a way somewhere else: the Strengths assessment's title, the text, the "Open Strengths Assessment →" button, then its status chip on a line of its own, coloured as on the hub.
- Before the sort is in, nothing follows the card: no reflection and no "Mark complete". After the sort, coming back to Section 1 shows the reflection.
- Keyboard only: Tab reaches the button, its focus is visible, and Enter opens the Strengths assessment.
- Screen reader: the button is read as "Open Strengths Assessment →", and the status is read after it.
- Phone width: the card's text and button wrap, and the chip doesn't stretch.

## The sort

- The cards come in a different order on each visit. The counter reads "1/36" and counts up.
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
- A 0% bar: the prototype gave every PEP bar at least 4% width so a zero still showed a stub. Check with real sorts whether it is missed (ticket 07).
