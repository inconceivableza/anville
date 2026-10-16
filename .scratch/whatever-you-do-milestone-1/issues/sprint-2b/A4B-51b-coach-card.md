# 51b: Coach card

**What to build:** The Walk with a coach card says where things stand, and leads through the coach checklist to the coach's name and then their link, in one act, so nobody misses the step of making the link. The trusted voices card is 51a.

**Blocked by:** A3-50 (Before we begin as a wizard)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Implementation Decisions › Coach; Feedback from others

- [ ] The card's tag comes from its section's status and then the coach's answer: waiting, accepted or declined
- [ ] The card's sentence is authored in the pathway document, and says only what is true
- [ ] Inviting leads through the checklist to the coach's name, and then their link, shown to copy, in one act. The coach's email is optional
- [ ] The coach can still be invited, and their link reissued, once Before we begin is complete

**Context**

- The system sends the coach nothing, so the sentence leaves out the prototype's "We'll send them a short briefing pack"
- Answer collection freezing (B2B-55) leaves the coach untouched
- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the hub's coach card. Its name box on the card itself is not kept: the link is made at the end of the checklist
- As merged from the `hackathon-ui` branch in A0-48, the card says "Invite a mentor"; the glossary says coach
- Split from ticket 51 on 15 Oct

**Carried from 50**

- Walk with a coach is now the side card section `walk-with-a-coach`, holding the coach checklist on its one page. Its side-card sentence is authored already, without the briefing pack: "When you're ready, ask someone to walk this with you."
- The hub's own "Walk with a mentor" card in the template still shows beside the side card, as 49a noted. With the coach on a page of its own, nothing in *Whatever You Do* now uses the way-on wording "I'll sort this later →" or "Continue with Sam →"
