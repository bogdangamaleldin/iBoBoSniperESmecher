# reel-kit

Config-driven pipeline for ContentInfra Labs reels: talking head (face) and Miro-board (board) layouts,
brand captions, the user's zoom/transition/SFX style, 4K60 export. Used by the skills
`reel-captions`, `reel-hook-to-board` and `reel-board-only`.

```
reels/<NN-name>/
  reel.json          the edit (committed)
  raw/               footage (git-ignored; Drive links live in reel.json "drive")
  work/              transcripts, edl.json, segments, caption frames (git-ignored)
  out/               preview + final mp4 (git-ignored)
```

## Steps

```bash
reel-kit/make.sh reels/<NN-name> prep      # audio, speech-island transcript (prints every take), screen sync offset
reel-kit/make.sh reels/<NN-name> edl       # reel.json -> work/edl.json, prints the cut
reel-kit/make.sh reels/<NN-name> preview   # 1080x1920 @30 + QA  -> send to the user, iterate
reel-kit/make.sh reels/<NN-name> final     # 2160x3840 @60 + QA -> deliver
```

Render times on this machine: preview ~3-5 min, final ~12-20 min (most of it is HDR tone-mapping 4K).
Segments are cached by their exact ffmpeg command, so after a small change only the touched segments re-render.

## reel.json

| key | meaning |
|---|---|
| `format` | `hook-to-board`, `board-only` or `talking-head` (informational; layout comes from each line) |
| `drive` | Drive links of the raw files (download: `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t`) |
| `sources.face` / `sources.screen` | paths relative to the reel dir (phone footage / screen recording) |
| `screen_offset` | `face_time = screen_time + offset`, from `prep` (sync.py). If the screen recorder skipped time, sync.py prints a map `[[face_time_from, offset], ...]` - use that (reel 02 had a 3.2s jump) |
| `screen_duration` | length of the screen recording (lines after it fall back to phone audio) |
| `speed` | final speed-up (user liked 1.08) |
| `export` | `{"scale": 2, "fps": 60}` = 2160x3840 @60 |
| `face_crop` | `[w,h,x,y]` 9:16 crop of the face source (closer framing; ~1.33x punch-in of 4K) |
| `face_anchor_y` | vertical anchor for zooms (0.35 = face) |
| `cam` | `{"source": "face"|"screen", "crop": [w,h,x,y]}` webcam card crop (945:727 aspect) |
| `screen_canvas` | `{"y","h","center_x","bg"}` board area in the screen recording (exclude browser chrome + dock) |
| `cut` | optional `{"max_pause":0.18,"keep_pause":0.06,"pad_in":0.03,"pad_out":0.06,"end_hold":0.3}` (footage kept after the last word; posted reels end ~0.15-0.25s after it) |
| `audio` | `auto` (screen mic wherever it exists, else phone), `face` or `screen` |
| `lines[]` | the script, in output order (below) |
| `pills[]` | `{"text","from_line","to_line"}` numbered pills on the board card (to_line exclusive) |
| `cta` | `{"text","line","word","to_line"?}` CTA button on the board card, appears on that word, stays until `to_line` (default: end of its line) |
| `sfx` | override defaults: `{"riser": {...}|null, "transition": {...}|null}` |
| `song` | `{"file","start","gain_db"}` music bed, ducked under the voice; null = none |
| `captions` | `{"face_top": 960}` caption height on face shots (1080 default; raise it when the laptop sits high in frame) |

### lines[]

```json
{"layout": "face", "in": 90.40, "out": 92.80,
 "caption": "ai can build | your miro boards | in *5 minutes.*",
 "zoom": [{"at": "start", "to": 1.10, "dur": 0.2}]}
{"layout": "board", "in": 181.90, "out": 185.75, "screen_fit": [440, 1520], "caption": "..."}
```

- `in`/`out`: rough source times of the chosen take on the FACE recording; trimmed to speech automatically.
- `hard_out: true`: cut exactly at `out` (use when the next word follows with no pause, e.g. a retake starts).
- `screen_in`: take board footage from this screen-recording time instead (when the screen showed something else).
- `screen_fit: [x, w]`: zoomed-out board, fit `w` px of the canvas starting at `x`, pad with the board colour.
- `screen_freeze: "prev"`: hold the last board frame of the previous board line (user wants this for the CTA
  when the screen showed something else / the board would replay). A number holds that screen-time frame
  instead (board still panning in while the webcam card stays live; LF #1 clip 3).
- Non-hard lines automatically run on past `out` to the real end of speech (up to the next take), so a rough
  `out` no longer clips the last syllable ("ques-tions", "31-k").
- `zoom` (face only): ease-out keyframes. `at` = `start`, `+0.5` (seconds after line start) or a caption word.
  Zoom resets to 1.0 when a face section starts after a board section.

### Caption markup

| markup | meaning |
|---|---|
| `\|` | group break (1-3 words per group) |
| `*word*`, `*two words*` | accent key word(s): Instrument Serif Italic, blue |
| `**56 calls.**` | money/win key word(s): serif italic, green |
| `have~them.`, `*“board”*~down~below.` | ASR heard one token, show several words (each word takes its own `*` markers) |
| `gonna+` | caption token consumes two ASR tokens |
| `_` | consume one ASR token without showing it (ASR timing was wrong, e.g. reel 02 'and' after $12,000) |

Token count must equal the ASR tokens in the take (`10` + `%` and `$12` + `,000` merge automatically);
`build_edl.py` stops with the ASR tokens listed if it doesn't, so fix the markup or the in/out.

## Defaults baked in (from the user's approved reel #1, see references/reel-03-hook-to-board-final/lessons.md)
- HDR (HLG/PQ) sources are tone-mapped to SDR automatically.
- Phone-mic audio gets light cleanup only; screen-recording (laptop) mic is preferred.
- Each line levelled to -18 LUFS, final -14 LUFS, limiter at -0.5 dBFS.
- Warm glare (~0.32s) at every face<->board switch + camera-shutter second click; riser under the hook.
- Caption, pill, CTA styling in `overlay.html` (brand tokens from brand/design-language.md).

### Off-centre footage
Set a reel-level `"face_x": <px>` (median face centre in source pixels from `reel-kit/face_x.py`) to re-centre
the full-screen crop and the webcam card crop. Keep ONE value for the whole reel so the frame doesn't jump
at cuts; a per-line `face_x` overrides it only when the user moved a lot.
Face lines cut pauses longer than `cut.max_pause_face` (0.3s); the user hides those jump cuts with zoom changes in CapCut.

## After posting
`python3 reel-kit/compare_posted.py reels/<NN> [posted.mp4]` measures what the user changed in CapCut
(trims, speed, zoom levels over time, music bed level). Put the posted file in `reels/<NN>/posted/` (git-ignored).

## Long-form clips (one edited source with a webcam bubble)
`cam.source: "screen"`, `sources.face = sources.screen = raw/clip.mov` (stream-copy the window you need out of the
long video first), `screen_offset: 0`, `layout` cards, `screen_canvas.mask` to paint out the bubble,
`cut.threshold` (room tone is louder than phone/laptop recordings), `hook`, `cta.last`.
`prep` runs `source_cuts.py`: the long-form video already has jump cuts, and a segment starting/ending a few
frames before one of them shows a sliver of the other shot ("random frame"). The renderer snaps the video
to those cuts (holds the clean frame) while the audio stays untouched.
Video is cut by coarse seek + exact `trim` (input seeking alone let stray frames through on these files).

## Letterbox format (references/lf-format-02)
Lines with `"layout": "wide"`: the untouched 16:9 frame, full width, centred (`layout.wide_y`, default 656).
`"title": {"text": "line one / *accent* line two"}` sits above the video for the whole clip; captions go in the
black band under the video (`.cap.wide`). No cards, no crop, no masks.
