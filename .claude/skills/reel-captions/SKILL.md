---
name: reel-captions
description: ContentInfra Labs caption style for Instagram reels - Geist SemiBold white captions in 1-3 word groups that pop in on the spoken word, with key words in Instrument Serif Italic (blue, or green for money). Use whenever captions are added to a reel (any format, including plain talking-head), when writing caption markup in a reel.json, or when the user asks for "my caption style".
---

# Reel captions

Implementation: `reel-kit/overlay.html` (rendered by `reel-kit/render_overlay.js`). Brand tokens:
`brand/design-language.md`. Fonts: `brand/fonts/`. Origin of the style: `references/reel-01/breakdown.md`
(the reel the user wanted to copy) adapted to the brand; approved in `references/reel-03-hook-to-board-final/lessons.md`.

## The style
- Font: Geist SemiBold (600), white `#F3F4F6`, letter-spacing -2%, `cv11` + `ss01`. Lowercase, casual.
- Key words: Instrument Serif Italic, 1.3x size, lifted -0.05em so they sit level with Geist.
  Accent `#3D8BFF` (blue); money / wins `#3FCF8E` (green). About one key per 2-3 groups; key phrases may
  span words (`*5 minutes.*`, `*30 seconds*`). Numbers and the payoff word are the usual keys.
- Groups: 1-3 words, split at natural phrase breaks. A group pops in whole on its first spoken word
  (100ms blur 6px -> 0, scale 0.92 -> 1, fade in) and holds until the next group starts: no empty gaps,
  no half-revealed lines.
- Placement: full-screen face shots - on the chest, top 1080px of the 1080x1920 grid, 64px, soft dark shadow.
  Board layout - centred between the webcam card and the board card, top 930px, 54px, no shadow.
- Text: exactly what was said (plural/singular as spoken, e.g. "miro boards"), lowercase, punctuation
  only where it helps. Brand voice rules apply: no em dashes, real numbers only, never name the $11,885 client.

## Writing the markup (reel.json `caption`)
`|` group break, `*...*` accent, `**...**` money, `~` one ASR token shown as two words, `+` one caption token
for two ASR tokens. Start from the ASR words of the chosen take (printed by `make.sh prep` / `edl`),
correct mishearings ("minor boards" -> "miro boards", "laid with" -> "lead with", "warning" -> "wording"),
then group. `build_edl.py` checks the token count against the take and lists the ASR tokens if it's off.

## Don'ts (user rejected these)
- Word-by-word reveal with invisible placeholders (left blank space mid-line).
- Big orange/gold serif captions from the reference reel - colours come from the brand.
- Any other text/graphics on full-screen face shots (titles, big numbers, stat cards).
