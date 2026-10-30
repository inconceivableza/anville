# Coding standards

> ✨ Drafted with AI assistance.

Read during review, not implementation. Each rule is a judgement call; anything a test or tool already enforces (colours as `:root` variables, no inline styles, document validity) is left to it. Apply every rule below to the diff, and cite the rule by its heading.

## Where the rules live

- **Tests:** the spec's *Testing Decisions* (`.scratch/<feature>/spec.md`): two seams, tests assert behaviour rather than wording or layout, engine-wide behaviour is tested once, and each ticket keeps to its agreed list.
- **Decisions:** `docs/adr/`. A change that contradicts an ADR needs a new ADR, not a quiet exception; ADR 0003 (the pathway document is data, not a language) binds every schema change.
- **Names:** `CONTEXT.md` is the glossary. Code, copy and tests use its terms; a new domain term is flagged for `/domain-modeling`.
- **Tickets and specs:** `docs/agents/issue-tracker.md` (ticket shape, resolving, no ✨ in `.scratch` files).
- **Provenance:** ✨ on AI-produced comments and docs; one note at the top of a mostly-AI document.

## Locality

- A block type's rules live in its entry in `engine/document/blocks.py`, or in a function beside it that the view calls. A view that decides how a block's content is shown has split the block type in two.
- A rule the JSON Schema cannot express goes in `engine/document/lint.py`, with each problem at its document path and one message per kind of problem.
- Anything sitewide (a footer link, a notice) goes in all three layouts: `engine/templates/engine/base.html`, the homepage's own `body` in `home.html`, and the account pages' `access/templates/allauth/layouts/base.html`.

## Faithful text

- Text quoted from a third party (a publisher's notice, scripture) is word for word, its own spelling and symbols kept. A cut is marked with "…", or by a partial-verse reference ("7a"); anything of ours added to it, such as "Unless otherwise indicated", is named in the README or spec.
- Authored copy says only what is true of the app today. Copy about observers or the people a participant invites never promises anonymity: the app shows answers without names, which is not the same thing (ADR 0008).
- Text in a shared include (a template several pages draw in, such as the consent text) is true on every page that includes it. Words that point at their surroundings ("this page", "above", "below") are checked against each page.

## Refusals

- A refused press is answered where it was pressed: with JavaScript the refusal appears beside the button without the page reloading or moving, and a reload without JavaScript opens at the refusal, not the top. One refusal says what is missing once, not again in a general line beneath it.

## Idiom

- Match the surrounding file: its comment density, ✨ docstrings, and British English in prose and comments.
- Views are named by bare nouns, as in `home`, `hub`, `comparison`; a suffix only avoids a Python builtin (`credits_page`).
- A docstring or comment states only what the code does. A claim about other files ("every page", "both documents") is checked against them.
