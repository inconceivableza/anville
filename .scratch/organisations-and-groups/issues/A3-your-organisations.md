# A3: Your organisations

**What to build:** An organisation or group admin follows "Your organisations" from the foot of their hub and sees the organisations and groups they have rights over, each group with its type, member count and a join link they can copy.

**Blocked by:** A2 (Joining by link)

**Status:** ready-for-agent

**Spec:** Pages; Models; User Stories › Organisation admin; User Stories › Group admin

- [ ] The hub shows "Your organisations" only to an account holding a permission; an account without one is refused the page
- [ ] An organisation admin sees every group in the organisation, each with its type, member count and join link; a group admin sees only their group
- [ ] The join link can be copied with one click, without eval in htmx (ADR 0006)
- [ ] The page needs sign-in but not consent, so an admin who has not started the pathway can use it
