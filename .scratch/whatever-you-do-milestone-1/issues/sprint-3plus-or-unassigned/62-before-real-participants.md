# 62: Before real participants: the minimum for data protection

**What to build:** The least that must be true before any real person's data goes into an instance open to the public: the privacy page names who is responsible and how long data is kept, every company that handles the data is named and bound by an agreement, and nothing participant-facing promises what the app does not do. Until every criterion is met, every instance holds fake data only.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

**Sprint:** before any real participant

**Spec:** Legalities are parked, not forgotten

- [ ] The privacy page's four placeholders are filled and its "Draft wording" box removed: the controller's name, postal address and contact email; the data protection registration number (the ICO fee if the controller is in the UK; under POPIA, the information officer registered with the Information Regulator if the controller is in South Africa); the hosting company, email service, Google sign-in and the mailing tool; and how long each kind of information is kept, in one true sentence (deleting by hand is fine if the page says so)
- [ ] Each company named on the privacy page has a data processing agreement accepted by the controller (usually a click-through in the company's account settings)
- [ ] A one-page data protection impact assessment exists: what is collected, who sees it, what could go wrong, what limits it, treating everything a participant writes as possibly about faith or health
- [ ] The observer's notice loses its "[Draft …]" line, and says only what is true while reminders are switched off ("we may email you a reminder"); the consent page's "what happens to it when consent is withdrawn has not been decided yet" is replaced by the retention answer
- [ ] One ADR records the controller, the retention rule and the processors, and the spec's list of parked legal items is updated to match; the instance's test data is wiped before anyone real signs up

**Context**

- Moved out of ticket 26 on 19 Oct; cut to this minimum on 30 Oct, for a small pilot
- Decisions for the content owner, with the developer; not for an agent to make. The wording criterion can be handed to an agent once the answers are in, and the new wording goes to the content owner
- UK and EU data protection law both apply; South Africa's POPIA too if the controller is there. The spec's other parked legal items (the Article 15(4) policy, a fuller impact assessment if the pilot grows) stay listed there
- Staging is publicly reachable and carries a demo notice; its "Stay in touch" form already stores real email addresses, so the privacy page's placeholders are the most urgent part
