# 77: Google sign-up: Google's own address, the account chooser, and a refusal that says what to do

**What to build:** A Google sign-up makes an account only at the address Google gave. "Continue with Google" always lets the person choose which Google account to use (Google's account chooser, its `select_account` prompt). An address that already has a password account is refused, and the refusal sends the person to sign in with their password, since nothing in the app connects a Google account to an existing one.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 3b (coherence fixes, from 23 Oct)

**Spec:** Participants, access and consent (ADR 0004)

- [x] The Google sign-up form shows the address Google gave, and it cannot be changed there
- [x] A sign-up sent with any other address is refused on the server and makes no account, so the refusal of an address that already has a password account cannot be stepped round, no two accounts share an address, and every username is its email
- [x] "Continue with Google", on sign-up and on sign-in, always opens Google's account chooser, even when the browser is already signed in to a Google account
- [x] The refusal reads "There's already an account with this email address, made with a password. Sign in with your email and password instead.", links to sign in and to "Forgot your password?", and says nothing about connecting a Google account
- [ ] Where Google sign-in is offered, sign-up and sign-in show "Continue with Google" first, above the email-and-password form, with "or" between them

**Context**

- Found on the coherence walk (54): choosing the first Google account and typing a second address made an account whose username was the second address and whose email was the first, beside the password account at the first
- Whether to offer connecting a Google account to an existing account is a separate call, still open
