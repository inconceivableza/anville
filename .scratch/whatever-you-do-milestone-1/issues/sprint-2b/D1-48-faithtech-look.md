# 48: FaithTech look and final tweaks

**What to build:** The whole app takes the look of the content owner's final hackathon prototype: cream panels on deep brown, one green accent, pill buttons, Switzer for text and Newsreader for headings. The look is changed once, in the shared styles, so every page moves together; the layouts of particular pages are the tickets after this one.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

**Sprint:** 2b (12–16 Oct)

**Spec:** Operating and demonstrating; Delivery and hosting; Legalities are parked, not forgotten

- [ ] Colours, type, buttons, panels and the header follow the prototype, each defined once and used by every page
- [ ] Both fonts are served from the deployment's own files: no page requests anything from Google or any other outside host
- [ ] The construct colours on results and the comparison are unchanged
- [ ] Body text and buttons meet WCAG AA contrast, at desktop and phone width
- [ ] Nothing but the look changes: the journey tests pass untouched

**Context**

- Prototype reference: `Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3-nc-copy-copy.zip` (`index.html`), the canonical look. v1 and v2 are superseded. It has three screens only: the homepage, the wizard and the hub
- The `hackathon-ui` branch is a reference for flow only. Nothing is merged or copied from it
- The prototype loads Newsreader from Google Fonts, which sends every visitor's address to Google; check both fonts' licences allow serving them ourselves
