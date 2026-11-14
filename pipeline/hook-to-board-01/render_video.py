"""Render the base video (no captions/graphics): face segments full-frame, board segments split-screen.

Board layout (1080x1920), measured from the user's board-only reel:
  webcam card  x68  y189  945x727  r45
  board card   x30  y1020 1020x621 r36
"""
import json, subprocess, os
from PIL import Image, ImageDraw

W, H = 1080, 1920
BG = (8, 9, 10)
CAM = (68, 189, 945, 727, 45)
BOARD = (30, 1020, 1020, 621, 36)
MIRO_CROP = (1522, 927, 519, 278)        # w h x y on the 2560x1440 screen recording
MIRO_CROP_OVERVIEW_X = 442               # line 4 (both columns)
ME_CAM_CROP = (1080, 831, 0, 420)        # from the 1080x1920 phone proxy

edl = json.load(open('edl.json'))
os.makedirs('seg', exist_ok=True)


def make_mask():
    s = 2  # supersample for smooth corners
    im = Image.new('RGBA', (W * s, H * s), BG + (255,))
    d = ImageDraw.Draw(im)
    # faint 44px grid at the top, fading downward (brand page grid)
    for y in range(0, 700, 44):
        for x in range(0, W, 44):
            pass
    grid = Image.new('RGBA', (W * s, H * s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 44):
        for y in range(0, 900):
            a = int(8 * max(0, 1 - y / 900))
            if a:
                gd.point((x * s, y * s), fill=(255, 255, 255, a))
    for y in range(0, 900, 44):
        a = int(8 * max(0, 1 - y / 900))
        gd.line([(0, y * s), (W * s, y * s)], fill=(255, 255, 255, a), width=1)
    im = Image.alpha_composite(im, grid)
    d = ImageDraw.Draw(im)
    for x, y, w, h, r in (CAM, BOARD):
        box = [x * s, y * s, (x + w) * s, (y + h) * s]
        # border (1px @1080 ~ 2px supersampled)
        d.rounded_rectangle([box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2], r * s + 2, fill=(31, 33, 37, 255))
        d.rounded_rectangle(box, r * s, fill=(0, 0, 0, 0))
    im = im.resize((W, H), Image.LANCZOS)
    im.save('board_mask.png')


make_mask()

ENC = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', '30',
       '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2']

files = []
for i, s in enumerate(edl['segments']):
    out = f'seg/{i:02d}.mp4'
    dur = s['out'] - s['in']
    afade = f"afade=t=in:d=0.012,afade=t=out:st={dur - 0.015:.3f}:d=0.015"
    if s['layout'] == 'face':
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', 'me_proxy.mp4',
               '-vf', 'fps=30,setsar=1', '-af', afade, *ENC, out]
    else:
        cw, ch, cx, cy = MIRO_CROP
        if s['line'] == 4:
            cx = MIRO_CROP_OVERVIEW_X
        mw, mh, mx, my = ME_CAM_CROP
        fc = (f"color=c=0x08090A:s={W}x{H}:r=30:d={dur:.3f}[bg];"
              f"[0:v]fps=30,crop={mw}:{mh}:{mx}:{my},scale={CAM[2]}:{CAM[3]}[cam];"
              f"[1:v]fps=30,crop={cw}:{ch}:{cx}:{cy},scale={BOARD[2]}:{BOARD[3]}:flags=lanczos[brd];"
              f"[bg][cam]overlay={CAM[0]}:{CAM[1]}[a];[a][brd]overlay={BOARD[0]}:{BOARD[1]}[b];"
              f"[b][2:v]overlay=0:0,setsar=1[v];[0:a]{afade}[au]")
        cmd = ['ffmpeg', '-v', 'error', '-y',
               '-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', 'me_proxy.mp4',
               '-ss', f"{s['miro_in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/miro.mp4',
               '-i', 'board_mask.png',
               '-filter_complex', fc, '-map', '[v]', '-map', '[au]', '-t', f'{dur:.3f}', *ENC, out]
    subprocess.run(cmd, check=True)
    files.append(out)
    print('ok', out, s['layout'], f'{dur:.2f}s', flush=True)

with open('seg/list.txt', 'w') as f:
    for p in files:
        f.write(f"file '{os.path.basename(p)}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'seg/list.txt', '-c', 'copy', 'base.mp4'], check=True)
print('base.mp4 done')
