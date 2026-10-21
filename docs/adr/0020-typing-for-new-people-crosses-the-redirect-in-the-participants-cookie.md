---
status: accepted
---

# Typing for new people crosses the redirect in the participant's own cookie

Without JavaScript, every press on a contact list sends the whole list: edits to people already listed are saved with it, and the empty rows store nobody until their own "Get link" (ticket 70). Text typed into another row must never be lost (fix-1, the developer's call). After a successful "Get link" the page redirects, so that a reload never adds the person twice, and the redirect carries no form data. What was typed in the other empty rows (names and email addresses of people the participant has not yet added) has to cross it somewhere.

It crosses in the cookie that already carries the observer's link just issued, shown once on the page that follows:

- **What it holds:** the person just added and their link, as before, and the name and email address typed in each other empty row, in order. Nothing for people already listed, whose edits were saved by the press.
- **For how long:** at most 60 seconds, and the list's page deletes it as soon as it reads it.
- **Where it goes:** to the list's own page alone (its path), over HTTPS where the site uses it (`Secure`), out of reach of scripts (`HttpOnly`), and `SameSite=Lax`.
- **Signed, not encrypted:** the server rejects a cookie it did not make or one that is too old, but the contents can be read by whoever holds the browser. That person is the participant who typed them, seconds earlier, on the same device. Someone else able to read that browser's cookies could, in that minute, as easily read the page the text was typed into. So encryption would add a key to manage for little gain; the risk left is that short window on the participant's own device, weighed as acceptable.
- **Nothing on our side:** the server writes the typing into the response and keeps no copy of it. The session holds only which person each recent press added, by identifier, so that a resent press is recognised.

When the typing is too long for a cookie (past `ISSUED_COOKIE_MOST`, leaving room within a browser's 4096 bytes), the list's page is drawn in the response to the press itself, with the link and every row as typed, and never cached. A reload would send that press again. So each drawn list carries a `press` value, a fingerprint of who it lists (it changes as soon as anyone is added), the session records which person each press added, and a press already recorded that names the same person, still on the list, adds nobody: the page comes back with them listed.

> ✨ Drafted with AI assistance.

## Considered options

**Keep the typing in the session.** Rejected: the session lives in the database, so names and email addresses of people who have not been invited, and may never be, would be held on our server, however briefly. The issued link already avoids the session for the same reason.

**Drop the typing on a successful "Get link".** Rejected: the participant would lose text typed in other rows, which is what this decision exists to prevent.

**Draw every "Get link" result directly, without a redirect.** Rejected as the rule: the redirect is what keeps a reload from adding someone twice. Drawing directly is kept for typing too long for a cookie, with the `press` check doing that job instead.

**Encrypt the cookie.** Rejected for now: see "Signed, not encrypted" above.

## Consequences

- For up to a minute, the participant's browser holds names and email addresses of other people that have not been saved, readable by anyone with access to that browser's storage in that time. The page they were typed into already shows them to that same person.
- A reload of a page drawn directly does not show the link again (only its hash is kept); the participant can reissue it from the person's row.
- With JavaScript none of this applies: each row is sent and returned on its own, and the other rows are left as they are.
