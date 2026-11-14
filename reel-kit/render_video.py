"""edl.json -> work/base.mov (video layers + levelled voice audio; no captions/graphics).

usage: render_video.py <reel_dir> [preview|final]
  preview: 1080x1920 @30fps (fast, for review)     final: export settings from reel.json (default 2160x3840 @60)

Face layout : full screen, static crop of the phone original + ease-out zoom keyframes (edl.zooms).
Board layout: two rounded cards on #08090A (the user's board format):
              webcam card x68 y189 945x727 r45 | caption band | board card x30 y1020 1020x621 r36
HDR (iPhone HLG / Dolby Vision, or PQ) is detected per source and tone-mapped to SDR (otherwise: washed-out white).
"""
import json, subprocess, os, re, sys, hashlib
from PIL import Image, ImageDraw

D = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else 'preview'
R = json.load(open(f'{D}/reel.json'))
WK = f'{D}/work'
edl = json.load(open(f'{WK}/edl.json'))
EXP = R.get('export', {})
S = 1 if MODE == 'preview' else EXP.get('scale', 2)
FPS = 30 if MODE == 'preview' else EXP.get('fps', 60)
W, H = 1080 * S, 1920 * S
sc = lambda v: int(round(v * S))

LAY = R.get('layout', {})
CAM = tuple(LAY.get('cam_card', (68, 189, 945, 727, 45)))
BOARD = tuple(LAY.get('board_card', (30, 1020, 1020, 621, 36)))
BG = LAY.get('bg', '08090A')
FACE_SRC, SCREEN_SRC = f"{D}/{R['sources']['face']}", (f"{D}/{R['sources']['screen']}" if R['sources'].get('screen') else None)
FACE_CROP = R['face_crop']                     # [w,h,x,y] on the face source (9:16)
FACE_ANCHOR_Y = R.get('face_anchor_y', 0.35)   # where zooms are centred vertically (0=top, 1=bottom)
CAM_SRC = R.get('cam', {}).get('source', 'face')
CAM_CROP = R['cam']['crop']                    # [w,h,x,y] on the cam source, 945:727 aspect
SCR = R.get('screen_canvas', {})               # board area inside the screen recording
SCR_Y, SCR_H = SCR.get('y', 0), SCR.get('h')
SCR_CX = SCR.get('center_x')
SCR_BG = SCR.get('bg', 'E5F7FC')
TARGET_LUFS = -18.0


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,color_transfer', '-of', 'json', path], capture_output=True, text=True).stdout
    return json.loads(out)['streams'][0]


def tonemap_for(path):
    tr = probe(path).get('color_transfer', '')
    if tr not in ('arib-std-b67', 'smpte2084'):
        return 'format=yuv420p'
    return (f'zscale=tin={tr}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,'
            'zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'
            'eq=contrast=1.06:saturation=1.08')


TM_FACE = tonemap_for(FACE_SRC)
FACE_W = int(probe(FACE_SRC)['width'])
TM_CAM = TM_FACE if CAM_SRC == 'face' else tonemap_for(SCREEN_SRC)
if SCREEN_SRC:
    sp = probe(SCREEN_SRC)
    SCR_H = SCR_H or int(sp['height'])
    SCR_CX = SCR_CX or int(sp['width']) // 2
SCR_W = round(SCR_H * BOARD[2] / BOARD[3]) if SCREEN_SRC else 0


def make_mask():
    k = 2
    im = Image.new('RGBA', (W * k, H * k), tuple(int(BG[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    d = ImageDraw.Draw(im)
    for x, y, w, h, r in (CAM, BOARD):
        X, Y, Wd, Ht, Rr = [v * S * k for v in (x, y, w, h, r)]
        b = S * k
        d.rounded_rectangle([X - b, Y - b, X + Wd + b, Y + Ht + b], Rr + b, fill=(31, 33, 37, 255))
        d.rounded_rectangle([X, Y, X + Wd, Y + Ht], Rr, fill=(0, 0, 0, 0))
    im.resize((W, H), Image.LANCZOS).save(f'{WK}/board_mask.png')


def zoom_expr(t0, t1):
    """ffmpeg expression for the zoom factor during [t0,t1] of the edit timeline (variable t = segment-local)."""
    keys = sorted(edl['zooms'], key=lambda z: z['t'])
    z, kf = 1.0, []
    for k in keys:                               # value at each key start = target of the previous key
        if k['t'] <= t0 and k['t'] + max(k['dur'], 1e-3) <= t0:
            z = k['to']; continue
        if k['t'] >= t1:
            break
        kf.append((k['t'], k['to'], max(k['dur'], 1e-3)))
    if not kf:
        return f'{z:.4f}'
    T = f'({t0:.4f}+t)'
    zb, parts = z, []
    for (tk, zk, dk) in kf:
        parts.append((tk, zb, zk, dk)); zb = zk
    expr = f'{zb:.4f}'
    for tk, zfrom, zto, dk in reversed(parts):
        ease = f'{zfrom:.4f}+({zto - zfrom:.4f})*(1-pow(1-({T}-{tk:.4f})/{dk:.4f},3))'
        expr = f'if(lt({T},{tk + dk:.4f}),{ease},{expr})'
        expr = f'if(lt({T},{tk:.4f}),{zfrom:.4f},{expr})'
    return expr


def loudness(src, start, dur):
    r = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', src, '-vn',
                        '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])


make_mask()
segs = edl['segments']
lines = sorted({s['line'] for s in segs})
gain = {}
for li in lines:
    ss = [s for s in segs if s['line'] == li]
    s0 = ss[0]
    src, st = (SCREEN_SRC, s0['audio_in']) if s0['audio'] == 'screen' else (FACE_SRC, s0['in'])
    gain[li] = TARGET_LUFS - loudness(src, st, ss[-1]['out'] - s0['in'])

ENC = ['-c:v', 'libx264', '-preset', 'fast', '-crf', '15' if S > 1 else '17', '-pix_fmt', 'yuv420p', '-r', str(FPS),
       '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2']
os.makedirs(f'{WK}/seg', exist_ok=True)
files = []
for i, s in enumerate(segs):
    dur = s['out'] - s['in']
    fade = f"afade=t=in:d=0.008,afade=t=out:st={max(0, dur - 0.012):.3f}:d=0.012"
    if s['audio'] == 'screen':
        a_in = ['-ss', f"{s['audio_in']:.3f}", '-t', f'{dur:.3f}', '-i', SCREEN_SRC]
        a_chain = f"highpass=f=80,afftdn=nr=8:nf=-50,volume={gain[s['line']]:.2f}dB,{fade}"
    else:   # phone mic: LIGHT cleanup only (heavy denoise sounds watery)
        a_in = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', FACE_SRC]
        a_chain = (f"highpass=f=90,afftdn=nr=4:nf=-55,equalizer=f=280:t=q:w=1.2:g=-3,"
                   f"equalizer=f=3800:t=q:w=1.5:g=2,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120,"
                   f"volume={gain[s['line']]:.2f}dB,{fade}")
    v_in = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.3f}', '-i', FACE_SRC]
    fw, fh, fx, fy = FACE_CROP
    cw, ch, cx, cy = CAM_CROP
    if 'face_x' in s:                              # per-take face tracking (camera not centred / user moved)
        fx = int(min(max(s['face_x'] - fw / 2, 0), FACE_W - fw))
        if CAM_SRC == 'face':
            cx = int(min(max(s['face_x'] - cw / 2, 0), FACE_W - cw))
    if s['layout'] == 'face':
        z = zoom_expr(s['t0'], s['t0'] + dur)
        fc = (f"[0:v]setpts=PTS-STARTPTS,fps={FPS},crop={fw}:{fh}:{fx}:{fy},{TM_FACE},"
              f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame:flags=bicubic,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{FACE_ANCHOR_Y},setsar=1[v];[1:a]{a_chain}[au]")
        inputs = v_in + a_in
    else:
        bx, by, bw, bh, _ = BOARD
        if 'screen_fit' in s:                    # zoomed-out board: fit all content, pad with the board colour
            ox, ow = s['screen_fit']
            board = (f"crop={ow}:{SCR_H}:{ox}:{SCR_Y},"
                     f"scale={sc(bw)}:{sc(bh)}:force_original_aspect_ratio=decrease:flags=lanczos,"
                     f"crop='min(iw,{sc(bw)})':'min(ih,{sc(bh)})',pad={sc(bw)}:{sc(bh)}:(ow-iw)/2:(oh-ih)/2:color=0x{SCR_BG}")
        else:
            board = f"crop={SCR_W}:{SCR_H}:{SCR_CX - SCR_W // 2}:{SCR_Y},scale={sc(bw)}:{sc(bh)}:flags=lanczos"
        cam_in = v_in if CAM_SRC == 'face' else ['-ss', f"{s['screen_in']:.3f}", '-t', f'{dur:.3f}', '-i', SCREEN_SRC]
        fc = (f"color=c=0x{BG}:s={W}x{H}:r={FPS}:d={dur:.3f}[bg];"
              f"[0:v]setpts=PTS-STARTPTS,fps={FPS},crop={cw}:{ch}:{cx}:{cy},{TM_CAM},"
              f"scale={sc(CAM[2])}:{sc(CAM[3])}:flags=lanczos[cam];"
              + (f"[1:v]trim=end_frame=1,setpts=PTS-STARTPTS,{board},"
                 f"tpad=stop_mode=clone:stop_duration={dur + 0.1:.3f},fps={FPS}[brd];"
                 if 'screen_freeze' in s else f"[1:v]setpts=PTS-STARTPTS,fps={FPS},{board}[brd];") +
              f"[bg][cam]overlay={sc(CAM[0])}:{sc(CAM[1])}:eof_action=repeat[a];"
              f"[a][brd]overlay={sc(bx)}:{sc(by)}:eof_action=repeat[b];[b][3:v]overlay=0:0,setsar=1[v];"
              f"[2:a]{a_chain}[au]")
        scr_in = (['-ss', f"{s['screen_freeze']:.3f}", '-i', SCREEN_SRC] if 'screen_freeze' in s
                  else ['-ss', f"{s['screen_in']:.3f}", '-t', f'{dur:.3f}', '-i', SCREEN_SRC])
        inputs = (cam_in + scr_in
                  + a_in + ['-i', f'{WK}/board_mask.png'])
    cmd = [*inputs, '-filter_complex', fc, '-map', '[v]', '-map', '[au]', '-t', f'{dur:.3f}', *ENC]
    key = hashlib.sha1(json.dumps(cmd).encode()).hexdigest()[:10]
    out = f'{WK}/seg/{MODE}_{key}.mov'                  # cache by content: unchanged segments are reused
    if os.path.exists(out):
        print(f'seg {i:02d} {s["layout"]:5s} {dur:5.2f}s cached', flush=True)
    else:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *cmd, out + '.part.mov'], check=True)
        os.replace(out + '.part.mov', out)
        print(f'seg {i:02d} {s["layout"]:5s} {dur:5.2f}s ok', flush=True)
    files.append(out)

with open(f'{WK}/seg/list.txt', 'w') as f:
    f.writelines(f"file '{os.path.basename(p)}'\n" for p in files)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{WK}/seg/list.txt',
                '-c', 'copy', f'{WK}/base_{MODE}.mov'], check=True)
json.dump({'mode': MODE, 'S': S, 'fps': FPS}, open(f'{WK}/base_{MODE}.json', 'w'))
print(f'base_{MODE}.mov done ({W}x{H} @{FPS})')
