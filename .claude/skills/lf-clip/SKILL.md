---
name: lf-clip
description: Cut a short Instagram clip out of one of the user's long-form (LF) YouTube videos - board card on top + webcam card below (or the "letterbox" format: untouched 16:9 frame with a title), hook overlay, captions, riser + L.E.S. song. Use when the user sends an "LF #N CLIP (x of 7)" brief with CUT / HOOK OVERLAY / FRAME / CTA / CAPTION / CLIP RULES.
---

# LF clip SOP (from LF #1 clips 1-3)

Toolkit: `reel-kit/` (see its README, section "Long-form clips"). One clip = one dir `lf/<NN-name>/` with `reel.json`.

## 1. Source window
- LF source lives in `lf/01-miro-board-11885/raw/source.bin` (LF #1; Drive link in its reel.json).
- Stream-copy the brief's window with ~5s margin: `ffmpeg -ss <start-5> -i source.bin -t <len+10> -map 0:v:0 -map 0:a:0 -c copy raw/clip.mov`.
- Copy a previous clip's reel.json (card format: `lf/03-clip3-result-led`, letterbox: `lf/02b-clip2-letterbox`), clear `lines`, run `make.sh <dir> prep`.

## 2. Make it SHORT (the user's standing rule)
The brief's CUT is the outer window, not the edit. Target **~20-25s final** (speed 1.12):
- Keep: the claim, the one-line method, at most 1-2 concrete examples, the payoff line. End where the brief says.
- Drop: restatements ("so it's tied to the 100k a month" after the example already said it), "not necessarily X... it's a very
  specific Y... you should always break..." loops, filler "right?" tags in the middle (keep a final "right?" if the brief ends on it).
- Never cut so a sentence starts mid-thought; a line may start on "so" / "what".
- Audible swear words in examples: cut the whole example (clip 3: the "F*CK IT Leaking..." title).

## 3. Cut points (where every past complaint came from)
- All lines `hard_out: true`. Place `in`/`out` in loudness dips (20ms RMS envelope of `work/face_16k.wav`), never at ASR word times:
  the end of a word often runs 50-150ms past the ASR end, and the next word's onset sneaks in otherwise.
- After the render, transcribe EACH segment of `work/base_preview.mov` on its own with **medium.en** (0.5s silence pad):
  the last word must be complete and nothing may follow it ("video" + start of next word, "time", "creator", "twelve thousand").
- A word that ASR "hears" but the envelope says isn't there (clip 2 "today" = "to...") is a false start: end before it, consume
  the ASR token with `_` in the caption.
- `build_edl` hard_out WARNINGs are expected after you checked the dip by hand.

## 4. Frame
- Card format: `board_card` top, `cam_card` bottom third, captions between (`captions.board_top`), hook panel over the board.
  `screen_fit [x,w]` = the board content only; `screen_canvas.mask` paints out the webcam bubble AND Miro UI ("You are
  presenting" pill, top-right toolbar).
- Board still panning/zooming in early lines: `"screen_freeze": <screen time>` holds a clean frame of the finished board while
  the webcam card stays live and lip-synced.
- Letterbox: see `references/lf-format-02`; the brief's hook becomes the persistent `title`.

## 5. Clip rules (LF #1, all 7 clips)
Never show the original board, its title or thumbnail; never $57,386. Skip 15:11-16:04 (names a client and his numbers).
Audio "12k" -> on-screen "$11,885". Never name or show the $11,885 client. Captions lowercase, no em dashes, real numbers only.
Check a contact sheet of the window before cutting.

## 6. Audio / finish
Riser at the very start (`sfx.riser {}`), `transition: null`, song `brand/music/les-instrumental-slowed.mp3` at -2 dB.
CTA "comment “board”" for the last 2s when the brief asks; the user dropped it on the clip 2 letterbox export.

## 7. Deliver
Preview 1080p -> user notes -> fix -> `final` (2160x3840 @60) -> SendUserFile. Commit + push reel.json each round.
