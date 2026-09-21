---
status: accepted
---

# The pathway document configures named behaviours; it is data, not a language

Recaps, scoring and gates all need logic that depends on a participant's answers. The pathway document does not express that logic: it selects a behaviour by name (a recap view, a scoring method, a gate clause) and supplies its parameters, and the behaviour itself is implemented in code. Authors combine and configure behaviours; new behaviours ship as code.

> ✨ Drafted with AI assistance; the decision was reviewed and agreed by the team.

## Considered options

**An expression or formula language inside the document.** The prior plans allowed a small allowlist of numeric operators for scoring and declarative conditions for routing. Rejected, because:

- Every operator is a surface to validate, sandbox and keep safe when a document arrives from an import or a preview. An evaluator that grows becomes a remote-code-execution path.
- The authors are expected to be non-technical. A studio can only generate forms for parameters whose shape is fixed, and an open expression cannot be given a form.
- Two of the three uses (recap views, gate clauses) are already small and enumerable in the prototype, so a language buys generality nobody has asked for.

## Consequences

- A gate is a list of clauses drawn from a fixed set (a count, a distinct count, a minimum text length, "every item has a chapter"), each with its own authored message.
- A named scoring method is part of the measurement, so once any response has been scored with it, its behaviour is frozen. A change in behaviour needs a new method name, never an edit, or historical results silently stop being comparable.
- The document's JSON Schema must be stable before studio forms are built, since the forms are generated from it.
- Adding a behaviour is a code release. That is the price of keeping the document safe to import, and it is accepted.
