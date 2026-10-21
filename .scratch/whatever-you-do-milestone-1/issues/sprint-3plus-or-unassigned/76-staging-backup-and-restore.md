# 76: Staging backup and restore

**What to build:** What ticket 26 left undone on `whatever-you-do-staging`: its nightly dump reaching the Storage Box under a sub-account of its own, a restore tried once from it, and the runbook finished with both and with the corrections the stand-up found. The operator does each step on the host and in the consoles; the repository changes only if the backup job or the documents need it.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

**Sprint:** 3 or later

**Spec:** Delivery and hosting

- [ ] The environment's Storage Box sub-account exists, sees only this environment's directory, and accepts a key made for the backup alone; the environment's backup secrets name it
- [ ] The nightly backup reaches the Storage Box: the job's log shows the dump sent, and the dump is listed there. The "Connection closed" the job ends with is explained or fixed
- [ ] A dump is restored once into a scratch namespace on the staging host, as the deploy README's "Rehearse a restore" says, and an account from it is found with its answers; the scratch namespace and the dump are then removed
- [ ] The staging runbook records the backup set-up and the restore as done, with the commands used and anything that differed
- [ ] The deploy documents say what the stand-up found: the organisation must allow public packages before the package can be made public, and the deploy workflow needs the `ACME_EMAIL` variable

**Carried from 26**

- [ ] The admin's list of users holds no real address beyond the testers' own, and the operator's account has none: parked on 26 until the operator's password is to hand
- The runbook's backup section ends "Above not working yet": the sub-account, its password, the new public key on the sub-account and the private key in the GitHub Environment were still to do
