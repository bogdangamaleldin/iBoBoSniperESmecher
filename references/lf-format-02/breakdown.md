# LF clip format 02: "letterbox" (reference: SnapReels download, 720x1280, 42.8s)

The long-form video cut up and placed into 9:16 AS IS, with a title on top.
| element | 1080x1920 position | style |
|---|---|---|
| background | full | black |
| video | full width 1080x608, vertically centred (y 656-1264) | untouched 16:9 frame (webcam bubble, graphics, B-roll all stay) |
| title | 2 centred lines just above the video (~y 510-640) | white bold sans ~48px, soft dark glow; the clip's promise ("$1,6M/mo story / sequences for trading course sellers") |
| captions | small, white, low inside the video | part of THEIR source video |
| end card | last ~2s | YouTube channel card + "full video on YouTube" (red) |
Kit: `"layout": "wide"` lines, `R.title` (persistent, plain text), captions in the black band under the video.

Notes:
- The whole 16:9 frame is visible in this format: pick windows without on-screen UI you don't want
  (e.g. LF #1's mid-video CTA banner "...your business, not just explained" near 10:00), or paint it out.
- No hook panel: the title IS the hook. CTA button sits under the captions (captions.cta_top ~1420).
