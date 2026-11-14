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
BOARD_Y, BOARD_H = CAM_H + BAND_H, H - CAM_H - BAND_H        # 970, 950
FACE_CROP = (1620, 2880, 280, 650)        # on the 2160x3840 phone original
CAM_CROP = (1700, 1354, 240, 1058)        # webcam card crop on the phone original
MIRO_Y, MIRO_H = 278, 927                 # Miro canvas rows in the 2560x1440 screen recording
MIRO_W = round(MIRO_H * W / BOARD_H)      # crop width matching the board card aspect
MIRO_OVERVIEW = {4: (440, 1520), 10: (800, 1140)}   # zoomed-out lines: (x, width) that fits all content
MIRO_BG = 'E5F7FC'                        # Miro board background colour (sampled)
MIRO_CENTER_DEFAULT = 1280
HOOK_ZOOM = 0.10                          # +10% push-in over the whole hook
BOARD_ZOOM = 0.06                         # +6% push-in per board line
TARGET_LUFS = -18.0

edl = json.load(open('edl.json'))
segs = edl['segments']
os.makedirs('seg', exist_ok=True)
hook_end = max(s['t0'] + s['out'] - s['in'] for s in segs if s['layout'] == 'face' and s['line'] < 4)
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
        a_chain = f"highpass=f=80,afftdn=nr=12:nf=-45,volume={gain[s['line']]:.2f}dB,{fade}"
    v_in = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/me.mp4']
    fw, fh, fx, fy = FACE_CROP
    if s['layout'] == 'face':
        if s['line'] < 4:   # hook: continuous push-in across all hook cuts
            z = f"(1+{HOOK_ZOOM}*({s['t0']:.3f}+t)/{hook_end:.3f})"
        else:               # close: barely-moving hold
            z = f"(1+0.02*({s['t0'] - line_t0[s['line']]:.3f}+t)/{line_dur[s['line']]:.3f})"
        vf = (f"[0:v]fps=30,crop={fw}:{fh}:{fx}:{fy},"
              f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame:flags=bicubic,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.35,setsar=1[v]")
        inputs = v_in + a_in
        fc = vf + f";[1:a]{a_chain}[au]"
    else:
        cw, ch, cx, cy = CAM_CROP
        z = f"(1+{BOARD_ZOOM}*({s['t0'] - line_t0[s['line']]:.3f}+t)/{line_dur[s['line']]:.3f})"
        if s['line'] in MIRO_OVERVIEW:   # zoomed-out board: fit full width, pad with the board colour
            ox, ow = MIRO_OVERVIEW[s['line']]
            board_src = (f"crop={ow}:{MIRO_H}:{ox}:{MIRO_Y},scale={W}:-2:flags=lanczos,"
                         f"pad={W}:{BOARD_H}:0:(oh-ih)/2:color=0x{MIRO_BG},")
        else:
            mx = MIRO_CENTER_DEFAULT - MIRO_W // 2
            board_src = f"crop={MIRO_W}:{MIRO_H}:{mx}:{MIRO_Y},"
        fc = (f"color=c=0x08090A:s={W}x{H}:r=30:d={dur:.3f}[bg];"
              f"[0:v]fps=30,crop={cw}:{ch}:{cx}:{cy},scale={W}:{CAM_H}:flags=lanczos[cam];"
              f"[1:v]fps=30,{board_src}"
              f"scale=w='trunc({W}*{z}/2)*2':h='trunc({BOARD_H}*{z}/2)*2':eval=frame:flags=lanczos,"
              f"crop={W}:{BOARD_H}:(iw-{W})/2:(ih-{BOARD_H})/2[brd];"
              f"[bg][cam]overlay=0:0[a];[a][brd]overlay=0:{BOARD_Y},setsar=1[v];"
              f"[2:a]{a_chain}[au]")
        inputs = v_in + ['-ss', f"{s['miro_in']:.3f}", '-t', f'{dur:.3f}', '-i', 'raw/miro.mp4'] + a_in
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
