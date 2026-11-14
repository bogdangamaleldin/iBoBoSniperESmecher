"""Find the time offset between the face (phone) recording and the screen recording from their audio
(the laptop mic hears the same voice), and detect JUMPS (screen recorder paused / dropped time).

usage: sync.py <face_media> <screen_media>
prints an offset map along the screen recording and a ready-to-paste "screen_offset":
  a single number if constant, else [[face_time_from, offset], ...]   (face_time = screen_time + offset)
"""
import sys, subprocess
import numpy as np

SR = 16000


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def env(x, h=160):                     # 10ms envelope
    x = x[:len(x) // h * h]
    return np.abs(x).reshape(-1, h).mean(1)


face, scr = load(sys.argv[1]), load(sys.argv[2])
EF, ES = env(face), env(scr)
EFc = EF - EF.mean()
dur = len(scr) / SR
WIN = 6
pts = []
for st in np.arange(2, dur - WIN, 3.0):
    e = ES[int(st * 100):int((st + WIN) * 100)]
    if e.mean() < 2e-3:
        continue                                              # silence: no information
    ec = e - e.mean()
    c = np.correlate(EFc, ec, 'valid') / (np.linalg.norm(ec) * np.sqrt(np.convolve(EFc ** 2, np.ones(len(ec)), 'valid')) + 1e-9)
    k = int(np.argmax(c))
    if c[k] < 0.6:
        continue
    pts.append((st, k / 100 - st, c[k]))
    print(f'screen {st:6.1f}s  offset {k / 100 - st:7.2f}  corr {c[k]:.2f}', flush=True)

# group into constant stretches
groups = []
for st, off, c in pts:
    if groups and abs(off - groups[-1][1][-1]) < 0.05:
        groups[-1][1].append(off); groups[-1][2] = st
    else:
        groups.append([st, [off], st])
groups = [g for g in groups if len(g[1]) >= 2]
if len(groups) == 1:
    print(f'OFFSET {np.median(groups[0][1]):.3f}   (constant)')
else:
    m = [[float(round(g[0] + np.median(g[1]), 2)) if i else 0.0, round(float(np.median(g[1])), 3)] for i, g in enumerate(groups)]
    print('JUMPS in the screen recording (recorder paused/dropped time). Use:')
    print(f'"screen_offset": {m}')
