# Hook -> board reel #1: what the user approved and changed

Final posted version: user's own export (4K60, 34.73s), built on our v5 (35.0s).
Pipeline + edit list: `pipeline/hook-to-board-01/`.

## Approved (keep as the default for this format)
- Face sections: full screen, static ~1.33x crop of the 4K phone original. NO zoom/push-in. Captions only, no other graphics.
- iPhone footage is HLG / Dolby Vision HDR: always tone-map to SDR (zscale + hable, contrast 1.06, sat 1.08). Without it the image looks washed-out white.
- Board sections: two rounded cards on #08090A (the user's board-only format):
  webcam card x68 y189 945x727 r45, caption centered between, board card x30 y1020 1020x621 r36, 1px #1F2125 border.
  Webcam: static crop, no motion, no graphics. Board: static (no Ken Burns), decision pills + CTA button allowed.
- Zoomed-out board shots: fit all board content in the card, pad with the board colour (#E5F7FC).
- Captions: groups of 1-3 words, whole group pops in (100ms blur+scale) and holds until the next group (no gaps).
  Geist SemiBold white; key words Instrument Serif Italic (blue #3D8BFF, money green #3FCF8E), lifted -0.05em to sit level.
  Lowercase, real words corrected ("miro boards" plural as spoken).
- Audio: laptop mic (screen recording) wherever it exists; phone mic only where the laptop wasn't recording,
  with LIGHT cleanup (heavy afftdn sounds bad). Per-line level to -18 LUFS, final loudnorm -14 LUFS.
- Pacing: cut pauses > 0.18s, tight line joins, 1.08x speed. Drop false starts (re-transcribe suspicious stretched words).
- Export: 2160x3840, 60fps.

## User added by hand in CapCut (do this automatically next time)
- **Transitions:** CapCut "glare" effect at every face <-> board switch, ~0.3s centred on the cut
  (warm golden/white flare blowing out the frame + rainbow prism fringe). Hard cuts everywhere else.
- **Transition SFX:** `brand/sfx/camera-shutter.mp3`, SECOND HALF ONLY (second click: start at 0.66s of the file),
  placed on each face <-> board transition.
- **Riser at the start:** `brand/sfx/riser.mp3` under the hook.
- **Song:** a music bed under the whole reel (chosen per reel; not in the Drive export, so likely added at posting).
- **Zoom keyframes (face shots only, ease-out, centred on the face).** Measured against our v5:
  | t (user cut) | line | zoom |
  |---|---|---|
  | 0.0 -> 0.2s | "ai can build your miro boards" | punch-in 1.00 -> 1.10, hold |
  | 2.4 -> 4.1s | "that's exactly why it won't book you a call" | 1.10 -> 1.05, then slow ease-out to 1.00 |
  | 4.3 -> 4.6s | "the board is 10% of it" | punch-in 1.00 -> 1.05 on the number |
  | 5.6 -> 5.9s | "the other 90%..." | punch-in 1.05 -> 1.10, hold to the transition |
  | 8.5 -> 33s | board section | none |
  | 33.0 -> 33.1s | close, "you still have to decide" | snap 1.00 -> 1.06, hold to end |
  Rule of thumb: punches of +5% on emphasis words/numbers, 0.2-0.3s ease-out, levels 1.00/1.05/1.10,
  one zoom-out after the opening beat. Never a slow continuous push-in (rejected).
- Slightly tighter (~0.1s each) in two places: around the first transition and mid board section.

## SFX library (`brand/sfx/`)
| file | length | loudness | use |
|---|---|---|---|
| camera-shutter.mp3 | 1.23s | -17 LUFS | transitions (2nd click only, from 0.66s) |
| riser.mp3 | 5.33s | -32 LUFS | under the hook / build into the first cut |
| camera-switch.wav | 0.79s | -25 LUFS | available (alt. transition) |
| pop.mp3 | 0.97s | -20 LUFS | available (pills / CTA pop-ins) |
| pencil-lines.mp3 | 2.14s | -46 LUFS | available (board drawing / highlighting) |

## Rejected along the way
- Graphics on the face shots (big numbers, titles, stat cards). Cool/blue-white flash. Zoom-ins anywhere.
- Full-bleed split with no card margins (v2-v3) - user prefers the rounded-card board format.

## Reel 02 (four gaps) - what changed
- User: rendered zoom-ins/outs "aren't really clean" -> removed; he adds zooms, riser and sound in CapCut.
  Default for future exports: no zoom keys, no riser. Keep the glare + shutter transitions ("i like the transitions").
- No script outline sent: structured like reel 01 and the user approved the structure as is.
- Phone wasn't centred and the user moved between takes: per-take `face_x` re-centring (face_x.py) worked.
- Screen recorder skipped 3.2s between the hook and the board section -> hook audio was misaligned in the
  first preview; caught by the render-transcript QA. sync.py now prints a jump map.
- CTA keyword spoken mid-phrase ("comment board down below") -> CTA button 'comment "board"', kept on screen
  until the end of the board section (`to_line`), not just its line.
- Both reels "got cut out too fast" at the end: the last word was trimmed ~0.06s after speech.
  Kit default now keeps 0.9s of footage after the last word (`cut.end_hold`) + 0.35s audio fade-out.
- Reel 02: "close to twelve thousand" was cut after "twelve" on a `hard_out` line - the ASR put the next word
  ("and") 0.35s too early. For every hard_out, check the loudness envelope for where the last word really
  ends (look for the dip before the next word) instead of trusting ASR word starts; `_` in the caption
  markup absorbs the mistimed ASR token.
- Reel 03 notes: face captions overlapped the laptop -> `captions.face_top` 960. Last syllables clipped on
  non-hard lines ("ques(tions)", "31(k)") -> lines now auto-extend to the real end of speech. Cut a redundant
  set-up line. CTA board must FREEZE on the last board frame, not replay (`screen_freeze: "prev"`).
- Reel 03: per-take re-centring made the frame jump at every hook cut -> one fixed framing per reel;
  don't cut short (<0.4s) pauses on face shots.
- Reel 04: the last face caption leaked into the board section (held until the board's first word).
  Captions now end exactly on every face<->board cut (overlay.html). Reels 02/03 exports had this too.
