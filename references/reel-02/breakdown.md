# Reference reel 02: "board only" format (user's own reel)

Source: `source.mp4` (360x640 download, 30fps, 58.7s). Frames in `frames/`.
Measurements below are scaled to a 1080x1920 canvas (x3).

## Layout (static for the whole reel)
| Element | Box (x, y, w, h) on 1080x1920 | Notes |
|---|---|---|
| Background | full frame | pure black |
| Webcam card | 78, 189, 945, 726 | rounded corners ~45px, face/hands framed, cropped from landscape webcam |
| Caption | centered, baseline ~y 985 (51% down) | sits in the ~105px black gap between the two cards |
| Board card | 30, 1020, 1020, 621 | rounded corners ~36px, Miro screen recording zoomed into the area being discussed, follows the cursor/pan |
| Bottom space | y 1641 to 1920 | empty black (clear of IG caption/UI) |

- Webcam card is slightly narrower than the board card (inset ~48px more per side).
- Board recording is cropped to the canvas area (no browser chrome); it pans/zooms with the talk.

## Captions in this reel
- White, bold geometric sans (looks like SF Pro / Inter Bold), tight tracking, ~48px cap height on 1080 canvas.
- One line, 2 to 5 words, phrase-based.
- **No animation:** hard cut from phrase to phrase.
- No key-word highlight, no color.

## Plan for our version (combine with reel 01)
- Keep this layout exactly (it works and is recognisable).
- Upgrade captions to the reel-01 motion: per-word blur-fade in, group blur-out, key word in
  Instrument Serif Italic blue `#3D8BFF` (green `#3FCF8E` for money). Body words Geist SemiBold white.
- Background: brand near-black `#08090A` (optionally the faint 44px grid at the top) instead of pure black.
- Cards: 1px border `#1F2125` + 1px top highlight (brand panel style), no shadow.
- The "hook to board" format wraps this layout with a full-screen talking-head hook and close,
  which use the reel-01 captions placed low-center on the chest.
