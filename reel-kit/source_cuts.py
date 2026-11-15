"""Find hard cuts that already exist inside a source video (e.g. an edited long-form video with jump cuts).
Segments that start/end a fraction of a second away from such a cut would show a sliver of the other shot
("random frame"), so render_video.py snaps the VIDEO to the cut (audio unchanged) - see 'snap' below.

usage: source_cuts.py <video> <crop w:h:x:y> <out.json>     (crop = a region that changes at cuts, e.g. the webcam)
"""
import json, subprocess, sys
import numpy as np

v, crop, out = sys.argv[1], sys.argv[2], sys.argv[3]
fps = 60
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', v, '-vf', f'fps={fps},crop={crop},scale=96:54,format=gray',
                      '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(np.int16)
d = np.abs(np.diff(f, axis=0)).mean((1, 2))
base = np.median(d)
cuts = [round((i + 1) / fps, 3) for i in np.where(d > max(15, base * 4))[0]]
json.dump(cuts, open(out, 'w'))
print(f'{len(cuts)} source cuts (median frame diff {base:.1f}):', ' '.join(f'{c:.2f}' for c in cuts))
