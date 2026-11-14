"""Render the base video for the hook->board reel (v5).

Resolution/fps are parameters: S=1 -> 1080x1920, S=2 -> 2160x3840 (4K). FPS env var (default 60).
Layout geometry is defined on a 1080x1920 grid and multiplied by S.

Face layout : full screen, static ~1.33x crop of the 4K phone original, HLG HDR tone-mapped to SDR.
Board layout (user's board-only format): two rounded cards on #08090A
              webcam card x68 y189 945x727 r45 | caption between | board card x30 y1020 1020x621 r36
Audio       : laptop mic (screen recording) wherever it exists, phone mic (light cleanup) for the hook;
              every line levelled to -18 LUFS before the final loudness pass.
"""
import json, subprocess, os, re
from PIL import Image, ImageDraw

S = int(os.environ.get('S', '2'))
FPS = int(os.environ.get('FPS', '60'))
W, H = 1080 * S, 1920 * S
CAM = (68, 189, 945, 727, 45)
BOARD = (30, 1020, 1020, 621, 36)
FACE_CROP = (1620, 2880, 280, 650)        # on the 2160x3840 phone original
CAM_CROP = (1700, 1308, 240, 1080)        # webcam card crop on the phone original (945:727 aspect)
MIRO_Y, MIRO_H = 278, 927                 # Miro canvas rows in the 2560x1440 screen recording
MIRO_W = round(MIRO_H * BOARD[2] / BOARD[3])
MIRO_OVERVIEW = {4: (440, 1520), 10: (800, 1140)}   # zoomed-out lines: (x, width) that fits all content
MIRO_BG = 'E5F7FC'
MIRO_CENTER_DEFAULT = 1280
TARGET_LUFS = -18.0
TONEMAP = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
           'zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'
           'eq=contrast=1.06:saturation=1.08')
sc = lambda v: int(round(v * S))


def make_mask():
    """Background with two rounded holes (+1px border) laid over the cards."""
    k = 2
    im = Image.new('RGBA', (W * k, H * k), (8, 9, 10, 255))
    d = ImageDraw.Draw(im)
    for x, y, w, h, r in (CAM, BOARD):
        X, Y, Wd, Ht, R = [v * S * k for v in (x, y, w, h, r)]
        b = S * k
        d.rounded_rectangle([X - b, Y - b, X + Wd + b, Y + Ht + b], R + b, fill=(31, 33, 37, 255))
        d.rounded_rectangle([X, Y, X + Wd, Y + Ht], R, fill=(0, 0, 0, 0))
    im.resize((W, H), Image.LANCZOS).save('board_mask.png')


make_mask()
edl = json.load(open('edl.json'))
segs = edl['segments']
os.makedirs('seg', exist_ok=True)
line_dur, line_t0 = {}, {}
for s in segs:
    line_dur[s['line']] = line_dur.get(s['line'], 0) + s['out'] - s['in']
    line_t0.setdefault(s['line'], s['t0'])


def loudness(src, start, dur):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', src, '-vn',
                        '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])


gain = {}
for li in sorted(line_dur):
    s0 = next(s for s in segs if s['line'] == li)
    s1 = [s for s in segs if s['line'] == li][-1]
    L = (loudness('raw/miro.mp4', s0['audio_in'], s1['out'] - s0['in']) if s0['audio'] == 'laptop'
         else loudness('me_proxy.mp4', s0['in'], s1['out'] - s0['in']))
    gain[li] = TARGET_LUFS - L

ENC = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', str(FPS),
       '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2']
files = []
for i, s in enumerate(segs):
    out = f'seg/{i:02d}.mov'
    dur = s['out'] - s['in']
    fade = f"afade=t=in:d=0.008,afade=t=out:st={max(0, dur - 0.012):.3f}:d=0.012"
    if s['audio'] == 'laptop':
        a_in = ['-ss', f"{s['audio_in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/miro.mp4']
        a_chain = f"highpass=f=80,afftdn=nr=8:nf=-50,volume={gain[s['line']]:.2f}dB,{fade}"
    else:
        a_in = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', 'me_proxy.mp4']
        a_chain = (f"highpass=f=90,afftdn=nr=4:nf=-55,equalizer=f=280:t=q:w=1.2:g=-3,"
                   f"equalizer=f=3800:t=q:w=1.5:g=2,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120,"
                   f"volume={gain[s['line']]:.2f}dB,{fade}")
    v_in = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/me.mp4']
    if s['layout'] == 'face':
        fw, fh, fx, fy = FACE_CROP
        fc = (f"[0:v]setpts=PTS-STARTPTS,fps={FPS},crop={fw}:{fh}:{fx}:{fy},{TONEMAP},scale={W}:{H}:flags=lanczos,setsar=1[v];"
              f"[1:a]{a_chain}[au]")
        inputs = v_in + a_in
    else:
        cw, ch, cx, cy = CAM_CROP
        bx, by, bw, bh, _ = BOARD
        if s['line'] in MIRO_OVERVIEW:
            ox, ow = MIRO_OVERVIEW[s['line']]
            board_src = (f"crop={ow}:{MIRO_H}:{ox}:{MIRO_Y},"
                         f"scale={sc(bw)}:{sc(bh)}:force_original_aspect_ratio=decrease:flags=lanczos,"
                         f"crop='min(iw,{sc(bw)})':'min(ih,{sc(bh)})',"
                         f"pad={sc(bw)}:{sc(bh)}:(ow-iw)/2:(oh-ih)/2:color=0x{MIRO_BG}")
        else:
            mx = MIRO_CENTER_DEFAULT - MIRO_W // 2
            board_src = f"crop={MIRO_W}:{MIRO_H}:{mx}:{MIRO_Y},scale={sc(bw)}:{sc(bh)}:flags=lanczos"
        fc = (f"color=c=0x08090A:s={W}x{H}:r={FPS}:d={dur:.3f}[bg];"
              f"[0:v]setpts=PTS-STARTPTS,fps={FPS},crop={cw}:{ch}:{cx}:{cy},{TONEMAP},scale={sc(CAM[2])}:{sc(CAM[3])}:flags=lanczos[cam];"
              f"[1:v]setpts=PTS-STARTPTS,fps={FPS},{board_src}[brd];"
              f"[bg][cam]overlay={sc(CAM[0])}:{sc(CAM[1])}:eof_action=repeat[a];[a][brd]overlay={sc(bx)}:{sc(by)}:eof_action=repeat[b];"
              f"[b][3:v]overlay=0:0,setsar=1[v];[2:a]{a_chain}[au]")
        inputs = (v_in + ['-ss', f"{s['miro_in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/miro.mp4']
                  + a_in + ['-i', 'board_mask.png'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc,
                    '-map', '[v]', '-map', '[au]', '-t', f'{dur:.3f}', *ENC, out], check=True)
    files.append(out)
    print('ok', out, s['layout'], f'{dur:.2f}s', flush=True)

with open('seg/list.txt', 'w') as f:
    for p in files:
        f.write(f"file '{os.path.basename(p)}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'seg/list.txt', '-c', 'copy', 'base.mov'], check=True)
print('base.mov done')
