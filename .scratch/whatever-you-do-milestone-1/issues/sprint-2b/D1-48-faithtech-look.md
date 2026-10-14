# 48: FaithTech look and final tweaks

**What to build:** The `hackathon-ui` branch already carries most of the content owner's final hackathon prototype's look: cream panels on deep brown, one green accent, pill buttons, Switzer for text and Newsreader for headings. This ticket makes the branch sound to build on: up to date with `main`, its tests back on in the build and passing, and its look checked against the prototype. It then merges into `main`, and the rest of chain D is worked on `main`.

**Blocked by:** None (can start immediately)

**Status:** claimed

**Sprint:** 2b (12–16 Oct)

**Spec:** Sprints; Operating and demonstrating; Delivery and hosting; Legalities are parked, not forgotten

- [ ] The branch takes in `main`, and the commit that turned the tests off in the build is reverted, so the build runs them again
- [ ] The tests pass, and the branch merges into `main`. Where the new look changed a page's words or markup on purpose, its test changes with it; no other test changes
- [ ] Colours, type, buttons, panels and the header follow the prototype, each defined once and used by every page. Every page sets text in Switzer and headings in Newsreader, as the prototype does, and no other font is loaded
- [ ] No page requests a font, or anything else, from Google or another outside host
- [ ] The construct colours on results and the comparison are unchanged, and body text and buttons meet WCAG AA contrast at desktop and phone width

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, the canonical look, fonts included. v1 and v2 are superseded. It has three screens only: the homepage, the wizard and the hub. Its images are the branch's `frontend/img`
- The branch was built from `docs/plans/target-design.html`, an earlier copy of v3. Where they differ, v3 wins: the homepage's pillars and tabs, its marquee of callings, and its heading "Everyone has a purpose"
- The branch's commit "Temporarily disable pytest blocking build" says it should not reach `main` until reverted
- The branch serves its fonts from the deployment's own files already: Switzer as woff2 files committed in `frontend/fonts`, and Newsreader through an npm package. But it uses Switzer only on the homepage (`.page:has(.hero)`); every other page has Inter for text, Pinyon Script for script and IBM Plex Mono. The prototype has none of the three: its sans and mono are Switzer, its serif and script Newsreader. Drop their packages
- Switzer's licence (ITF Free Font License, section 02) lets us serve it from our own site, but not make the files available through a repository or public server, and the repository is public. So the files are never committed: the build fetches the three weights it uses from Fontshare's kit, unchanged (no conversion or subsetting, which section 02 also forbids), into an ignored `frontend/fonts/` (developer's call, 15 Oct). The branch's committed copies, which did not match the kit, are removed
- Staging runs the branch until this merge, the onboarding migration included; from the merge on it is deployed from `main`
