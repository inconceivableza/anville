# 36: Observers' answers can't be re-linked by time

**What to build:** Nothing stored lets anyone, the operator included, match an observer's sent answers to their contact by comparing when a link was claimed with when answers were sent. Today the invitation keeps the claim time beside the contact's name and email, and the answers keep their send time to the second; with a handful of observers who claim and send minutes apart, the two orders line up.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct); before any real participant data

**Spec:** Observers (ADR 0005); Testing Decisions

- [ ] An invitation records whether it has been claimed, never when
- [ ] Sent answers keep at most the day they were sent, and no other time
- [ ] Claiming, sending once, revoking, reissuing and removing a contact behave as before
- [ ] ADR 0009 records that answers carry no time that matches a claim, and what still orders them

**Context**

- What reads the times today: the claim time only as "claimed or not", which the stored secret hash already tells; the send time only as "sent or not" (drafts never count); the answers' creation time nowhere
- Server access logs are ticket 26's: observers' links carry their token or secret in the path and are kept out of the web server's logs
- Sent answers' row ids still give the order they were sent in. With no claim times stored, that order can be compared only with the order links were issued in, which says much less, and only to someone with database access. It is an accepted risk, not a criterion: random ids would not hide it, since PostgreSQL keeps rows roughly in the order they were inserted, and hiding it properly costs more than it protects
