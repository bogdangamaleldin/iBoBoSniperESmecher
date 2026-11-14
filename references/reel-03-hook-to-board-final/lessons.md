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

## User added by hand (do this automatically next time)
- Transition at every face <-> board switch: warm light-leak flash, ~0.3s centered on the cut.
  Golden/white flare blowing out the frame + rainbow prism fringe on the incoming shot. Hard cuts everywhere else.
- Slightly tighter (~0.1-0.2s) around the transitions.

## Rejected along the way
- Graphics on the face shots (big numbers, titles, stat cards). Cool/blue-white flash. Zoom-ins anywhere.
- Full-bleed split with no card margins (v2-v3) - user prefers the rounded-card board format.
