# 70: More than five trusted voices

**What to build:** The Five trusted voices page makes it plain that more than five people can be added: an authored sentence says so, and an "Add another person" control is always shown below the rows, rather than a sixth row appearing only once all five are filled.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 3a (from 20 Oct)

**Spec:** Blocks

- [ ] The page shows the authored sentence "Five is a good number, but you can add more."
- [ ] "Add another person" below the rows adds one empty row, with or without JavaScript, never losing anything typed in other rows
- [ ] It is not shown once the list holds the most it may, and adding past that is still refused
- [ ] A row added this way needs its "Get link" before anyone is stored, as a new row does now
- [ ] The card's meters keep counting beyond five as they do now
