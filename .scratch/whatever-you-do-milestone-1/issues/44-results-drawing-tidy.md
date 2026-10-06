# 44: Results drawing tidy

**What to build:** Nothing a participant sees changes. The results page's and the comparison's drawings take their geometry from one place, and the comparison builds on what the results page gives it rather than editing it.

**Blocked by:** 38 (Results and comparison in words)

**Status:** needs-triage

**Sprint:** 3 or later

**Spec:** The instrument and scoring

- [ ] The drawings' sizes and positions (the line's height, the view boxes, the dot sizes, the gap's shading, the arrow past the end) are each written once, not repeated between the engine and the templates
- [ ] The comparison reads the results page's places and standings for the participant without removing or renaming them
- [ ] Each construct's place on the line, and whether it is past the end, is worked out once
- [ ] The tests pass unchanged

**Carried from 38**

- Raised by ticket 38's second review and left, as tidying with no change in behaviour, until after the 9 Oct demo
