"""Render the base video for the hook->board reel (v2).

Face layout : full screen, cropped in ~1.33x from the 4K phone original (closer framing);
              smooth continuous push-in across the hook lines; close is static.
Board layout (full-bleed, no black margins):
              webcam  y0-860    1080x860  static crop from the 4K original (no motion)
              caption band y860-970  #08090A
              board   y970-1920 1080x950  Miro canvas crop with a slow push-in per line
Audio       : laptop mic (screen recording) wherever it exists, phone mic (denoised) for the hook;
              every line levelled to -18 LUFS before the final loudness pass.
"""
import json, subprocess, os, re

W, H = 1080, 1920
CAM_H, BAND_H = 860, 110
BOARD = (30, CAM_H + 115, 1020, 621, 36)  # rounded board card: x y w h radius (v1 look)
FACE_CROP = (1620, 2880, 280, 650)        # on the 2160x3840 phone original
CAM_CROP = (1700, 1354, 240, 1058)        # webcam card crop on the phone original
MIRO_Y, MIRO_H = 278, 927                 # Miro canvas rows in the 2560x1440 screen recording
MIRO_W = round(MIRO_H * BOARD[2] / BOARD[3])  # crop width matching the board card aspect
MIRO_OVERVIEW = {4: (440, 1520), 10: (800, 1140)}   # zoomed-out lines: (x, width) that fits all content
MIRO_BG = 'E5F7FC'                        # Miro board background colour (sampled)
MIRO_CENTER_DEFAULT = 1280
TARGET_LUFS = -18.0
# iPhone records HLG/Dolby Vision HDR: tone-map to SDR or it looks washed-out white
TONEMAP = ('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
           'zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'
           'eq=contrast=1.06:saturation=1.08')

from PIL import Image, ImageDraw


def make_card_mask():
    k = 3
    bx, by, bw, bh, r = BOARD
    im = Image.new('RGBA', (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([(bx - 4) * k, (by - 4) * k, (bx + bw + 4) * k, (by + bh + 4) * k], fill=(8, 9, 10, 255))
    d.rounded_rectangle([(bx - 1) * k, (by - 1) * k, (bx + bw + 1) * k, (by + bh + 1) * k], (r + 1) * k, fill=(31, 33, 37, 255))
    d.rounded_rectangle([bx * k, by * k, (bx + bw) * k, (by + bh) * k], r * k, fill=(0, 0, 0, 0))
    im.resize((W, H), Image.LANCZOS).save('card_mask.png')


make_card_mask()
edl = json.load(open('edl.json'))
segs = edl['segments']
os.makedirs('seg', exist_ok=True)
line_dur = {}
for s in segs:
    line_dur[s['line']] = line_dur.get(s['line'], 0) + s['out'] - s['in']
line_t0 = {}
for s in segs:
    line_t0.setdefault(s['line'], s['t0'])


def loudness(src, start, dur):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', src, '-vn',
                        '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])


# per-line gain (measured over the whole line in its audio source)
gain = {}
for li in sorted(line_dur):
    s0 = next(s for s in segs if s['line'] == li)
    s1 = [s for s in segs if s['line'] == li][-1]
    if s0['audio'] == 'laptop':
        L = loudness('raw/miro.mp4', s0['audio_in'], s1['out'] - s0['in'])
    else:
        L = loudness('me_proxy.mp4', s0['in'], s1['out'] - s0['in'])
    gain[li] = TARGET_LUFS - L
    print(f'line {li}: {s0["audio"]} {L:.1f} LUFS -> gain {gain[li]:+.1f} dB')

ENC = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '30',
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
    fw, fh, fx, fy = FACE_CROP
    if s['layout'] == 'face':
        vf = (f"[0:v]fps=30,crop={fw}:{fh}:{fx}:{fy},{TONEMAP},"
              f"scale={W}:{H}:flags=lanczos,setsar=1[v]")
        inputs = v_in + a_in
        fc = vf + f";[1:a]{a_chain}[au]"
    else:
        cw, ch, cx, cy = CAM_CROP
        bx, by, bw, bh, _ = BOARD
        if s['line'] in MIRO_OVERVIEW:   # zoomed-out board: fit all content, pad with the board colour
            ox, ow = MIRO_OVERVIEW[s['line']]
            board_src = (f"crop={ow}:{MIRO_H}:{ox}:{MIRO_Y},"
                         f"scale={bw}:{bh}:force_original_aspect_ratio=decrease:flags=lanczos,"
                         f"crop='min(iw,{bw})':'min(ih,{bh})',"
                         f"pad={bw}:{bh}:(ow-iw)/2:(oh-ih)/2:color=0x{MIRO_BG}")
        else:
            mx = MIRO_CENTER_DEFAULT - MIRO_W // 2
            board_src = f"crop={MIRO_W}:{MIRO_H}:{mx}:{MIRO_Y},scale={bw}:{bh}:flags=lanczos"
        fc = (f"color=c=0x08090A:s={W}x{H}:r=30:d={dur:.3f}[bg];"
              f"[0:v]fps=30,crop={cw}:{ch}:{cx}:{cy},{TONEMAP},scale={W}:{CAM_H}:flags=lanczos[cam];"
              f"[1:v]fps=30,{board_src}[brd];"
              f"[bg][cam]overlay=0:0[a];[a][brd]overlay={bx}:{by}[b];[b][3:v]overlay=0:0,setsar=1[v];"
              f"[2:a]{a_chain}[au]")
        inputs = v_in + ['-ss', f"{s['miro_in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/miro.mp4'] + a_in + ['-i', 'card_mask.png']
    cmd = ['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', fc,
           '-map', '[v]', '-map', '[au]', '-t', f'{dur:.3f}', *ENC, out]
    subprocess.run(cmd, check=True)
    files.append(out)
    print('ok', out, s['layout'], s['audio'], f'{dur:.2f}s', flush=True)

with open('seg/list.txt', 'w') as f:
    for p in files:
        f.write(f"file '{os.path.basename(p)}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'seg/list.txt', '-c', 'copy', 'base.mov'], check=True)
print('base.mov done')
