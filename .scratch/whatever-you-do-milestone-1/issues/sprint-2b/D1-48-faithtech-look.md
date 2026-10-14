# 48: FaithTech look and final tweaks

**What to build:** The `hackathon-ui` branch already carries most of the content owner's final hackathon prototype's look: cream panels on deep brown, one green accent, pill buttons, Switzer for text and Newsreader for headings. This ticket makes the branch sound to build on: up to date with `main`, its tests back on in the build and passing, and its look checked against the prototype. Chain D is worked on this branch, which merges into `main` at the end of D8-54.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Sprints; Operating and demonstrating; Delivery and hosting; Legalities are parked, not forgotten

- [ ] The branch takes in `main`, and the commit that turned the tests off in the build is reverted, so the build runs them again
- [ ] The tests pass on the branch. Where the new look changed a page's words or markup on purpose, its test changes with it; no other test changes
- [ ] Colours, type, buttons, panels and the header follow the prototype, each defined once and used by every page
- [ ] No page requests a font, or anything else, from Google or another outside host
- [ ] The construct colours on results and the comparison are unchanged, and body text and buttons meet WCAG AA contrast at desktop and phone width

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3-nc-copy-copy.zip` (`index.html`), the canonical look. v1 and v2 are superseded. It has three screens only: the homepage, the wizard and the hub
- The branch's commit "Temporarily disable pytest blocking build" says it should not reach `main` until reverted
- The branch bundles its fonts through npm packages, so they are served from the deployment's own files already; check their licences allow it
