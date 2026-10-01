---
status: accepted
---

# htmx runs with eval disabled

htmx can run JavaScript written inside `hx-*` attributes: `hx-on` handlers, event filters such as `hx-trigger="click[ctrlKey]"`, and `js:` values in `hx-vals` and `hx-vars`. It does so through `eval` and `Function`, behind `htmx.config.allowEval`, which defaults to on. We turn it off. Anville holds reflective free text that may be special category data, so even if an injection ever slipped past output escaping, an injected `hx-*` attribute must not be able to run code.

> ✨ Drafted with AI assistance.

## Considered options

**Keep htmx's default, with eval on.** Rejected. Escaping on render is the first defence, but it is only as strong as the weakest template, and eval turns any lapse into running script rather than stray markup. What eval buys is convenience in templates, and the spec already puts interaction-heavy behaviour in Vite modules rather than inline template code.

## Consequences

- `hx-on:*` handlers, `[…]` trigger filters and `js:` values do nothing. htmx raises `htmx:evalDisallowedError` instead. Behaviour that needs JavaScript belongs in a Vite module.
- The Vite build keeps warning about direct `eval`, because the code is still in the bundle; the setting only stops it running. The warning is expected.
- A Content Security Policy without `'unsafe-eval'` becomes possible later.
- Turning eval back on is a one-line change, which is exactly why it is recorded here. Reopen this decision only for a need a Vite module cannot meet, and agree it as a team rather than flipping the setting to make an attribute work.
