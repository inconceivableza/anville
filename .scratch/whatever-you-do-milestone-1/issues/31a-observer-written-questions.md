# 31a: The observer's written questions

**What to build:** After the thank-you for their observer assessment, the observer is offered a second part: the six written questions from the content owner's qualitative-strengths prototype, in observer wording. They may leave any question blank, and send the written part once.

**Blocked by:** 15b (The observer's relationship and withdrawal)

**See also:** `Prototypes for reference/qualitative-strengths-prototype.html`, the authority for this part: its observer questions (`O_QS`) and its "Notes for implementation", which give the reasoning for the six.

**Status:** ready-for-agent

**Sprint:** 2 (ends 8 Oct, for the 9 Oct tech showcase)

**Spec:** Observers (ADR 0005); Open content and product items; Legalities are parked, not forgotten; Testing Decisions

- [ ] The written part is offered after the thank-you as an addition ("there's a second part, if you have a little longer"); the observer assessment already counts without it (ADR 0008)
- [ ] The six questions (most energised, three best qualities, one skill to grow or add, one area of character, biggest change in recent years, work they struggle with) are authored content in observer wording, three best qualities as three single-word inputs; observer copy never says the participant "won't know who wrote this"
- [ ] Any question may be left blank, and a partly answered set is still sent; it is sent once, then locked, and never shown back through any link
- [ ] Until the written part is sent, following the claimed link leads back to it rather than only the thank-you and withdrawal (changing 15b's view after sending)
- [ ] Both pathway documents' observer privacy notices say what the participant will see of the written answers: shown without names, shuffled per question, once at least three observers have sent the written part (ADR 0008). They no longer say "{name} never sees your written answers"

**Carried from 15a**

- Sending the observer assessment creates the observer's one observer response, bound to their claimed secret and unique to it (ADR 0009). The written part is stored in that same response, never a second one

**Carried from 31**

- Nothing an observer types is saved before they send it (spec, Open content and product items, "Observer autosave")
- The prototype's "Send me a link for later" becomes the observer's own claimed link, valid for its lifetime; no reminder is sent while there is no email
