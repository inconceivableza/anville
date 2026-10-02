# 18: Calling statement (sentence builder)

**What to build:** Section 3a proper: the sentence builder block, which replaces the plain long-text activity used in the Demo 1 slice. A participant fills named slots in a fixed sentence, sees a live preview, and can seed a free-text statement from it and edit it freely.

**Blocked by:** 04 (Hub, locks, gates and explicit completion)

**Status:** ready-for-agent

**Sprint:** 3 or later; parked while the static workbook stands in for Sections 2–4 (ticket 40)

**Parent:** whatever-you-do-milestone-1 spec (Demo 3, 9 Oct)

- [ ] The sentence builder block has a fixed template with named slots (contribution, who, outcome) with hints, and a live preview: "God seems to have designed me to [contribution] among [who], so that [outcome]."
- [ ] "Use this statement" seeds the free-text override, which the participant can edit freely; a separate glory prompt is captured
- [ ] The block submits one answer with the slots and the final statement, validated by the server
- [ ] The section's gate requires a statement of at least ten characters; the slots and the glory prompt are not required
- [ ] Template, slot labels and hints are authored in the pathway document, not hardcoded
- [ ] The Demo 1 section keeps working, now using this block

**Carried from 09**

- [ ] Section 3's time estimate is "? min" in `pathways/whatever-you-do.json` until the sentence builder is in. Once it is, time the section by hand and give it its figure, agreed with the developer, and ideally the content owner. The faithful port has no estimates, and the drift test sets them aside
- The gate's minimum-length message keeps the prototype's sentence with the figure added, "Write your calling statement (at least 10 characters) to continue.", and a test holds every pathway document but the faithful port to saying how much
