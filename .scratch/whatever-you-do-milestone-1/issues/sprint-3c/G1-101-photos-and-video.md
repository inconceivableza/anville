# 101: Photos and the new video

**What to build:** The homepage plays the video the content owner chose, the churches section can take a new photo, and the wizard's pages and the hub's side cards carry photos, as the content owner asked. Each is credited.

**Blocked by:** 92 (The wizard's first page), C2; 95 (The hub's cards and next steps), D3; 99 (The homepage's lower half and footer), F2

**Status:** resolved

**Sprint:** 3c (ends Fri 30 Oct)

**Spec:** Sprint 3c: the content owner's feedback; Engine: sections, tracks, gates, progress

- [x] The homepage's hero plays the new video, with a poster from it shown until it plays and in its place where video does not play
- [x] "For churches" shows the new photo if one has been put in place; otherwise the photo it has now
- [x] Each wizard page shows a different photo and fills the screen with no strip below it, and each hub side card has a photo behind it, following the hackathon prototype where it chose one; their text stays readable on them
- [x] The credits page lists the video and each new photo as a courtesy
- [x] The same with JavaScript off and at phone width

**Context**

- The video and its poster are in place beside today's hero video (26 Oct), at 720p. Its credit: "Video by Marian Croitoru from Pexels", linking to https://www.pexels.com/video/healthy-light-landscape-nature-4524595/
- The developer puts the churches photo in place if one is picked by Wed 28 Oct
- The churches photo is in place (27 Oct): `frontend/img/churches.jpg`, 1920 × 1280, from https://unsplash.com/photos/woman-reading-book-dGxOgeXAXm8. Its credit: "Photograph of a church gathering with Bibles open, by Sincerely Media on Unsplash."
- Last but one in the cut order: if time runs short, the video and churches photo go before the wizard and side-card photos (spec)
