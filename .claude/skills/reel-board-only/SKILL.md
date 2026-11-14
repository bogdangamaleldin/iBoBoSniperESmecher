---
name: reel-board-only
description: Edit a ContentInfra Labs "board only" Instagram reel - the whole reel is the split layout (webcam card on top, Miro board card below, captions between), no full-screen hook or close. Use when the user sends a Miro screen recording plus webcam/phone footage (or a screen recording that already contains the webcam) and asks for a board / Miro-board reel without a talking-head intro.
---

# Board-only reel

Same toolkit, rules and QA as `reel-hook-to-board` - read that skill and `reel-kit/README.md` first.
Layout reference: `references/reel-02/breakdown.md` (the user's own board-only reel).
Captions: `reel-captions` skill.

## Differences from hook-to-board
- Every line in `reel.json` has `"layout": "board"`. There are no layout switches, so no glare
  transitions and no shutter SFX (finish.py only adds them at face<->board switches).
- Riser: still under the opening line unless the user says otherwise (`"sfx": {"riser": null}` to drop it).
- No zoom keyframes anywhere (board and webcam stay static).
- Webcam source:
  - separate phone/camera file -> `"cam": {"source": "face", "crop": [...]}`, run `prep` for the sync offset;
  - webcam already inside the screen recording (e.g. a Loom/OBS bubble) -> `"cam": {"source": "screen",
    "crop": [...]}` on the screen recording, `sources.face` = the screen recording too, `screen_offset: 0`.
- Audio: the laptop mic is the default (`"audio": "auto"` picks the screen recording when it covers the line).
- The hook is the first board line: give it the strongest key word, and a pill/CTA only if the script has one.

## Workflow
Same 11 steps as reel-hook-to-board (prep -> takes -> board stills -> reel.json -> edl -> preview -> QA ->
iterate -> final -> deliver -> compare with the posted version and update lessons).
