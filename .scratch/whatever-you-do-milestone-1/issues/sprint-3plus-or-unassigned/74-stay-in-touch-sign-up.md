# 74: "Stay in touch" sign-up on the homepage

**What to build:** A visitor to the homepage can leave their email address to show interest in *Whatever You Do*, as in v3's "Stay in touch", stored in the database with nothing sent yet. Parked by the developer on 20 Oct.

**Blocked by:** None (can start immediately)

**Status:** needs-triage

**Sprint:** 3 or later; parked 20 Oct

**Spec:** Legalities are parked, not forgotten

- [ ] The homepage offers an email box and "Subscribe", with a sentence about registering interest, news possible but not promised, and nothing else done with the address
- [ ] The address, the time and the wording's version are stored; a repeat address gets the same thanks, so nobody learns who has signed up
- [ ] The operator can see and export the list
- [ ] It is shown only once a controller and a contact address for the list are set for the deployment, and the sentence names both
- [ ] The decision is recorded in an ADR

**To settle before this is ready**

- Who the controller and contact are, with the content owner. This needs none of ticket 62's other decisions
- The sentence. The draft from 20 Oct: "Interested in Whatever You Do? Leave your email address and we may write with news. We can't promise we will, and we'll use your address for nothing else. [Controller] keeps it until you ask us to remove it: [contact]."
- How someone is removed before any sending exists (on request to the contact, for now), and double opt-in before the first send

**Context**

- From the developer's hand check, 20 Oct (`.claude/findings.md`). v3's line "Thoughtful writing on vocation, faith and work, delivered occasionally" is not kept
- No tickbox: the form's only purpose is this, so submitting it is the clear act consent needs
- A hidden field to turn away bots
- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, "Stay in touch"
