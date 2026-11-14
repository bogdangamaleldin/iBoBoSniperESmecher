# ContentInfra Labs: design language for reels

Source of truth for every reel edit. Taken from the site's code.

## Fonts (installed files in `brand/fonts/`)

| Use | Font | Settings |
|---|---|---|
| Body, UI, headlines, numbers | **Geist Sans** | Headlines semibold (600), letter-spacing -2% to -3%. Body regular (400). `cv11` + `ss01` on. |
| Big numbers ($31,515, 61K) | **Geist Sans** semibold (600) | Letter-spacing -3.5%, tabular numerals |
| Wordmark and accent words | **Instrument Serif** *italic* | Regular (400), letter-spacing -1% to -2% |
| Code and data (rare) | **Geist Mono** | |
| Small labels ("WHERE YOU ARE NOW") | **Geist Sans** medium (500) or semibold (600) | ALL CAPS, small, +8% to +16% tracking, grey |

Wordmark: *content* (Instrument Serif italic, white) + *infra* (same, grey `#8B9099`), next to the flask logo.

## Colors (dark is primary)

| Role | Hex |
|---|---|
| Background | `#08090A` |
| Card / panel | `#0E0F11` |
| Raised surface | `#141518` |
| Text | `#F3F4F6` |
| Secondary text | `#8B9099` |
| Faint text | `#5D626B` |
| Border | `#1F2125` |
| Strong border | `#2C2F34` |
| **Accent: signal blue** | **`#3D8BFF`** |
| Blue pressed / strong | `#2F76EC` |
| Blue tint | `#3D8BFF` @ 14% |
| Win / money / success | `#3FCF8E` |
| Warning | `#F0A43A` |
| Problem / leak / ✕ | `#F05A5A` |
| Extra chart colors | `#5CC4FF`, `#38BDF8`, `#A78BFA` |

Light (secondary): bg `#FAFAFB`, text `#0C0D10`, blue `#1F6FE5`, green `#13A36A`, red `#D93A3A`, grey `#5D636E`.

## Signature effects
- **Cash gradient** (one hero money number per frame): `#9BE8FA → #5CC4FF → #3D8BFF` at ~100°.
- **Hero card:** bg gradient `#0D1828 → #0A0F18 → #0E0F11` at 160°, 1px border `#1B2A44`, faint 1px blue top highlight.
- **Page grid:** faint square grid every 44px, white ~3%, fading out downward.
- **Panels:** 1px border `#1F2125`, 1px top highlight white 4%, **no drop shadows**.
- **One glow only** per frame: soft blue `#3D8BFF` ~50% around the single most important element.
- **Corners:** cards 16px, large panels ~20px, buttons 10-12px, pills fully rounded.

## Recurring components
- **"Prepared for" pill:** dark rounded pill, pulsing blue dot, blue caps label, thin divider, round photo + name in white semibold.
- **Stat card:** big number in green (wins) or red (leaks), short grey label under.
- **Check bullets:** small blue circle with check + text. Problems use red ✕.
- **Numbered steps:** blue outlined circles joined by a thin vertical line, "WEEK 1" labels in blue caps.
- **Recommended tag:** solid blue pill, white caps.
- **Primary button:** solid `#3D8BFF`, white semibold, 12px corners, soft blue shadow. Secondary: outlined `#2C2F34`.

## Voice and text rules
- Short. No paragraph over 2 lines; bullets are a few words.
- **No em dashes.** Use a colon, full stop or "+".
- Only real numbers, never rounded: "$11,885 | 1 Miro board, 56 calls", "$31,515 | 6 student interviews, 84 calls", "$15K | from 7 stories / 1 sequence".
- **Never name or show the $11,885 client.**
- Personal captions casual lowercase; headlines sentence case.
- Arrows (→) and "+" are fine as connectors.

## Reel defaults
- Canvas 1080x1920, bg `#08090A` with faint grid at top. Keep top and bottom 15% clear (IG UI).
- Captions: Geist Sans semibold white, key word `#3D8BFF` (green `#3FCF8E` for money).
- Max one Instrument Serif italic accent word per frame.
- Cash gradient on the money number, once per reel.
