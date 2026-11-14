---
name: reel-hook-to-board
description: Edit a ContentInfra Labs "hook to board" Instagram reel - full-screen talking-head hook, then a split board section (webcam card on top, Miro board card below, captions between), then a full-screen close. Use when the user sends phone footage + a Miro screen recording (usually as Google Drive links) with a script outline marking FACE / SCREEN lines, or asks for a "hook to board" / "hook -> board" reel. Produces a 1080p preview for review, then a 4K60 export.
---

# Hook -> board reel

Toolkit: `reel-kit/` (read `reel-kit/README.md` for the reel.json format). Brand: `brand/design-language.md`.
Captions follow the `reel-captions` skill. Reference edit: `reels/01-hook-to-board-ai-miro/reel.json`
and what the user approved/changed: `references/reel-03-hook-to-board-final/lessons.md` - read it first.

## Inputs to collect
- Phone footage (the whole talking-head recording, retakes included) and the Miro screen recording.
  Usually Google Drive links (attachments cap at 30MB). Download (hosts are allowed in the
  "iBoBoSniperESmecher" cloud environment):
  `curl -sSL -o raw/face.mov "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`
- The script outline: which lines are FACE and which are SCREEN, plus on-screen text ideas. Timings in it are rough.

## Workflow
1. `mkdir -p reels/<NN-name>/raw`, download, `ffprobe` both files (expect iPhone 4K60 HLG + 1440p screen rec).
2. Write a minimal `reel.json` (sources) and run `reel-kit/make.sh reels/<NN-name> prep`.
   It prints every speech island (each take separately) and the screen sync OFFSET -> put it in `screen_offset`.
   The laptop mic hears the same voice; if sync windows disagree by > 0.05s, look for a silent/bad window.
3. Pick takes per script line: by default the LAST complete clean take. Watch for:
   - false starts inside an island ("the first... the first decision"): re-window that region with
     `transcribe.py` on a short clip, start the line at the clean attempt;
   - ASR words stretched > 1s hide a pause, a flub or a whole collapsed retake;
   - a take that runs straight into the next attempt -> `hard_out: true`.
4. Board footage per SCREEN line: grab stills of the screen recording at `face_time - offset`
   (`ffmpeg -ss T -i raw/screen.mp4 -frames:v 1 ...`) and look at them. If the screen shows another app
   (e.g. the script editor while the CTA was recorded), set `screen_in` to a time where the board is visible.
   Zoomed-out board -> `screen_fit` so the whole board fits the card. Measure `screen_canvas` (rows/cols of
   the Miro canvas, no browser bar/dock/toolbar) once per recording.
5. Framing: `face_crop` ~1.33x punch-in centred on the face (the raw phone framing reads "too wide");
   `cam.crop` 945:727 on the face source for the webcam card.
6. Captions per line (see reel-captions), pills for numbered points, `cta` on the CTA word.
7. Zoom keyframes on FACE lines only, the way the user does it in CapCut:
   ease-out punch-ins of +5% on emphasis words/numbers (levels 1.00 / 1.05 / 1.10, `dur` 0.2-0.3),
   first line punches in at `start`, one zoom-out after the opening beat, close snaps in on its key phrase.
   Never a slow continuous push-in. No zoom/motion on the board section (webcam static, board static).
8. `make.sh ... edl` -> check the printed cut, then `make.sh ... preview`. Review the QA output:
   transcript of the render vs script (every word, no doubled starts, plural/singular as spoken),
   loudness -14, 0 black webcam frames, and LOOK at `work/check_sheet.jpg`. Send the preview with SendUserFile.
9. Iterate on the user's notes (edit reel.json, re-run preview). When approved: `make.sh ... final` (4K60).
10. Deliver: SendUserFile (Drive uploads from here cap at 10MB, so Drive won't take the 4K file).
    Commit `reels/<NN-name>/reel.json` (footage/renders are git-ignored) and push.
11. Ask for the posted version afterwards; compare with ours (frames, audio, zoom via
    feature matching) and add what they changed by hand to the lessons file.

## Defaults the user approved (don't regress)
- Face: captions only on full-screen shots, no other graphics. No black margins on face shots.
- Board: two rounded cards on #08090A; webcam card has no graphics; pills + CTA on the board card only.
- Colour: always tone-map the iPhone HDR (automatic in render_video.py) - otherwise "way too white".
- Audio: laptop mic wherever it exists; phone mic only for lines recorded before the screen recording started.
- Pacing: pauses > 0.18s cut, 1.08x speed, tight line joins.
- Transitions: warm glare + camera-shutter second click at face<->board switches only; riser under the hook.
- Song: user picks it; add via reel.json `song` if they send the file, otherwise they add it at posting.
