"""Compare the user's posted version of a reel with our export: what did they change by hand in CapCut?

usage: compare_posted.py <reel_dir> [posted.mp4] [ours.mp4]
  defaults: <reel_dir>/posted/posted.mp4 vs <reel_dir>/out/*_4k60.mp4
prints
  - timing: length difference and where the posted version is ahead/behind (trims)
  - zoom timeline: scale of the posted frame vs ours (feature matching), compressed into keyframes
  - audio: loudness, music bed level (in our quiet gaps), extra sound events (riser / SFX) with times
"""
import glob, json, re, subprocess, sys
import numpy as np
import cv2

D = sys.argv[1]
P = sys.argv[2] if len(sys.argv) > 2 else f'{D}/posted/posted.mp4'
O = sys.argv[3] if len(sys.argv) > 3 else sorted(glob.glob(f'{D}/out/*_4k60.mp4'))[-1]
SR, FPS, W, H = 16000, 10, 270, 480


def audio(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def frames(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vf', f'fps={FPS},scale={W}:{H},format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W)


def db(x, hop=SR // 20):
    x = x[:len(x) // hop * hop]
    return 20 * np.log10(np.sqrt((x.reshape(-1, hop) ** 2).mean(1)) + 1e-9)


def lufs(p):
    e = subprocess.run(['ffmpeg', '-i', p, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])


print(f'posted: {P}\nours:   {O}')
ap, ao = audio(P), audio(O)
print(f'length: posted {len(ap) / SR:.2f}s vs ours {len(ao) / SR:.2f}s ({(len(ap) - len(ao)) / SR:+.2f}s)')
print(f'loudness: posted {lufs(P):.1f} LUFS vs ours {lufs(O):.1f} LUFS')

# --- timing map: local offset (posted_t = ours_t + off) along our timeline, from voice envelopes
eo, ep = db(ao), db(ap)                                # 20 frames/s
offs = []
for st in range(0, len(eo) - 40, 20):
    a = eo[st:st + 40]
    if a.max() < -35:
        continue
    best = None
    for d in range(-30, 31):
        b = ep[st + d:st + d + 40] if st + d >= 0 else None
        if b is None or len(b) < 40:
            continue
        c = np.corrcoef(a, b)[0, 1]
        if best is None or c > best[0]:
            best = (c, d)
    if best and best[0] > 0.6:
        offs.append((st / 20, best[1] / 20))
print('timing (posted - ours):', ' '.join(f'{t:.0f}s:{o:+.2f}' for t, o in offs[::2]))


def off_at(t):
    if not offs:
        return 0.0
    return min(offs, key=lambda x: abs(x[0] - t))[1]


# --- zoom timeline
fo, fp = frames(O), frames(P)
orb = cv2.ORB_create(900)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
zoom = []
for i in range(0, len(fo), 2):                         # every 0.2s of our timeline
    t = i / FPS
    j = int(round((t + off_at(t)) * FPS))
    s = np.nan
    if 0 <= j < len(fp):
        ko, do_ = orb.detectAndCompute(fo[i], None)
        kp, dp = orb.detectAndCompute(fp[j], None)
        if do_ is not None and dp is not None and len(ko) > 20 and len(kp) > 20:
            m = bf.match(do_, dp)
            if len(m) > 15:
                A, inl = cv2.estimateAffinePartial2D(np.float32([ko[x.queryIdx].pt for x in m]),
                                                     np.float32([kp[x.trainIdx].pt for x in m]), ransacReprojThreshold=2)
                if A is not None and inl.sum() > 12:
                    s = float(np.hypot(A[0, 0], A[1, 0]))
    zoom.append((t, s))
keys, last = [], None
for t, s in zoom:
    if np.isnan(s):
        continue
    if last is None or abs(s - last) > 0.015:
        keys.append((t, s)); last = s
print('zoom keys (our time -> posted scale):', ' '.join(f'{t:.1f}s:{s:.2f}' for t, s in keys))

# --- audio: music bed + extra sound events
d_o, d_p = db(ao), db(ap)
gaps = [k for k in range(len(d_o)) if d_o[k] < -50]
bed = []
for k in gaps:
    kk = k + int(round(off_at(k / 20) * 20))
    if 0 <= kk < len(d_p):
        bed.append(d_p[kk])
if bed:
    print(f'music bed in our silent gaps: median {np.median(bed):.1f} dBFS (ours there: {np.median([d_o[k] for k in gaps]):.1f})')
ev = []
for k in range(len(d_o)):
    kk = k + int(round(off_at(k / 20) * 20))
    if 0 <= kk < len(d_p) and d_p[kk] - d_o[k] > 10 and d_p[kk] > -30:
        ev.append(k / 20)
groups = []
for t in ev:
    if groups and t - groups[-1][1] < 0.3:
        groups[-1][1] = t
    else:
        groups.append([t, t])
print('extra loud sound events (our time):', ' '.join(f'{a:.1f}-{b:.1f}s' for a, b in groups) or 'none')
try:
    edl = json.load(open(f'{D}/work/edl.json'))
    sp = json.load(open(f'{D}/reel.json')).get('speed', 1.0)
    print('our transitions at:', ' '.join(f'{t / sp:.2f}s' for t in edl['transitions']))
except Exception:
    pass
