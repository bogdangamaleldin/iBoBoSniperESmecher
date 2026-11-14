"""Measure the face centre (x, source pixels) of the face source at given times (median over a few frames).

usage: face_x.py <reel_dir> t1 t2 ...   prints  t -> face_x (and face size), using OpenCV's frontal-face detector
"""
import json, subprocess, sys
import numpy as np, cv2

D = sys.argv[1]
R = json.load(open(f'{D}/reel.json'))
src = f"{D}/{R['sources']['face']}"
info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                  '-of', 'json', src], capture_output=True, text=True).stdout)['streams'][0]
W, H = info['width'], info['height']
w, h = 540, int(540 * H / W) // 2 * 2
det = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
for t in map(float, sys.argv[2:]):
    xs = []
    for dt in (0, 0.4, 0.8):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t + dt:.2f}', '-i', src, '-frames:v', '1', '-vf', f'scale={w}:{h}',
                              '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
        img = np.frombuffer(raw, np.uint8).reshape(h, w)
        f = det.detectMultiScale(img, 1.1, 5, minSize=(40, 40))
        if len(f):
            x, y, fw, fh = max(f, key=lambda r: r[2] * r[3])
            xs.append(((x + fw / 2) * W / w, fw * W / w, (y + fh / 2) * H / h))
    if xs:
        m = np.median(np.array(xs), 0)
        print(f'{t:7.2f}s  face_x {m[0]:6.0f}  face_y {m[2]:6.0f}  width {m[1]:4.0f}   (frame {W}x{H})')
    else:
        print(f'{t:7.2f}s  no face found')
