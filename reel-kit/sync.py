"""Find the time offset between the face (phone) recording and the screen recording
from their audio (the laptop mic hears the same voice).

usage: sync.py <face_media> <screen_media>
prints: face_time = screen_time + OFFSET   (checked on several windows; they must agree)
"""
import sys, subprocess
import numpy as np

SR = 16000


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def env(x, h=16):
    x = x[:len(x) // h * h]
    return np.abs(x).reshape(-1, h).mean(1)


face, scr = load(sys.argv[1]), load(sys.argv[2])
E = env(face)
E = E - E.mean()
dur = len(scr) / SR
offs = []
for start in np.linspace(5, max(6, dur - 25), 4):
    a = scr[int(start * SR):int((start + 20) * SR)]
    if np.sqrt((a ** 2).mean()) < 1e-3:
        continue                               # silent window, skip
    e = env(a); e = e - e.mean()
    c = np.correlate(E, e, 'valid')
    k = int(np.argmax(c))
    off = k * 16 / SR - start
    s0 = int((start + off) * SR); r = 800
    cc = [np.dot(face[s0 + d:s0 + d + len(a)], a) for d in range(-r, r) if 0 <= s0 + d and s0 + d + len(a) <= len(face)]
    off += (int(np.argmax(cc)) - r) / SR
    offs.append(round(off, 3))
    print(f'window @{start:6.1f}s of screen rec -> offset {off:.3f}s', flush=True)
print(f'OFFSET {np.median(offs):.3f}  (spread {max(offs) - min(offs):.3f}s; > 0.05s means drift or a bad window)')
