# Reference reel 01: breakdown ("5 things I'd do if I lost everything")

Source: `source.mp4` (960x720 4:3, 23.976fps, 33s). Talking head, centered, warm lamp background.
Frames used for this breakdown are in `frames/`.

## What the user likes (keep)
- The font pairing: elegant serif for everything, italic for key words.
- Word-by-word blur-fade appear animation.
- Text placement: captions low-center on the chest, big numbers beside the head.
- Key words that "pop" (italic + accent color + slightly bigger).
- Overall calm, premium, editorial feel.

## What the user does NOT like (change)
- The orange/gold color (`~#E8C27A` gradient). Replace with brand colors.

## Measured elements

### 1. Spoken captions
- Font: high-contrast serif, looks like **Cormorant Garamond** (Medium). Normal words upright white `~#F2F0EC`.
- Size: small. Cap height ~3% of frame height. Not a "big bold CapCut" caption.
- Position: horizontally centered, ~70% down the frame (on the chest, below the chin, above the hands).
- No box, no outline. A very soft dark shadow only.
- Grouping: 1 to 4 words per group, one line. Groups follow phrases, not fixed counts.
- **Appear animation (per word, on the word's spoken onset):** opacity 0 → 1 plus blur ~8px → 0,
  over ~4 frames (~160ms). Words already shown stay; the next word fades in beside them.
  Line is centered on the FULL group, so earlier words don't shift as later ones arrive.
- **Exit:** the whole group blurs + fades out together in ~2 frames (~80ms), then the next group starts.
- **Key word:** italic, accent color, ~10-15% bigger than body words (e.g. *nobody*, *most*, *Volume*, *judged.*, *different.*).
  About one key word every 2 to 3 groups. Punctuation kept on key words at the end of a thought.

### 2. Hook title (0 to 4s)
- Line 1: italic serif in accent color ("*things I'd do*"), larger than captions.
- Line 2 under it: small ALL CAPS, very wide letter-spacing (~+30%), white ("IF I LOST EVERYTHING").
- Line 2 reveals left to right as a soft fade.

### 3. Chapter numbers (list items 1 to 5)
- Huge serif numeral (~35% of frame height) in the accent gradient, to the left OR right of the head
  (alternates side per item so it never covers the face).
- Under it: the number spelled out in small, wide-spaced caps ("ONE", "TWO"), white/grey.
- Appear: rises from a thin horizontal line at its baseline with a blur that sharpens (~0.4s).
- Stays on screen for the whole chapter, swaps when the next chapter starts.
- The intro "5" (the count of the list) uses the same component.

## Brand translation (ContentInfra Labs)
| Reference | Ours |
|---|---|
| Cormorant serif body words | **Geist Sans** Medium/SemiBold, white `#F3F4F6`, tight tracking (-2%) |
| Italic gold key words | **Instrument Serif Italic**, signal blue `#3D8BFF` (money: green `#3FCF8E`) |
| Gold gradient numerals | Instrument Serif numerals in the cash gradient `#9BE8FA → #5CC4FF → #3D8BFF` |
| Spaced caps label | Geist Sans SemiBold caps, +14% tracking, grey `#8B9099` |
| Hook title line 1 | Instrument Serif Italic, white or blue |

Alternative to test: keep a serif for body words too (Instrument Serif Regular, white) to stay closest
to the reference look. Render both, user picks.
