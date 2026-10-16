# 30a: Tie detection and the generalist

**What to build:** From a participant's sort, the engine tells whether a framework's top constructs are too close to call. A participant tied on both frameworks is told on their results that they are a generalist. One tied on exactly one framework is who 30b's pairs are for; nothing is asked of them yet.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Sprint:** 2b (12–16 Oct)

**Spec:** The instrument and scoring; The instrument and results; The pathway document and versions; Open content and product items

- [x] A framework is tied when one or more other constructs are within a threshold of its leader (4 percentage points of the rounded percents by default), and at most the top four enter the tie-break. The threshold and the cluster size are set in the pathway document
- [x] A participant tied on exactly one framework is marked for the tie-break. One tied on both is a generalist, and one tied on neither has nothing to break
- [x] A participant tied on both frameworks sees, on their results, that they are a generalist, in wording authored in the pathway document
- [x] Observers are never marked: the tie detection runs on the participant's own sort alone
- [x] The tie detection is a pure function of a result and the document, with no request or database

**Context**

- Prototype reference: `tiebreaker-prototype-v2.html` in Prototypes for reference, the content owner's prototype and the reference for behaviour. Its handling of two tied frameworks (a shared budget, alternating questions) is not built, since a participant tied on both is told they are a generalist
- The faithful port takes neither the settings nor the wording, since the tie-break is not in the original prototype; the drift test sets them aside
- Reshaped on 15 Oct: the generalist message moved here from 30c, and planning the pairs moved to 30b
