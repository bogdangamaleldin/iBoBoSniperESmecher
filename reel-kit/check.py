"""QA for a rendered reel: specs, loudness, re-transcription, black-card frames, contact sheet.

usage: check.py <reel_dir> <video.mp4>
Writes <reel_dir>/work/check_sheet.jpg. Read the transcript against the script: every word present,
no doubled starts, plural/singular exactly as spoken.
"""
import json, os, re, subprocess, sys

D, V = sys.argv[1], sys.argv[2]
R = json.load(open(f'{D}/reel.json'))
edl = json.load(open(f'{D}/work/edl.json'))
SP = R.get('speed', 1.0)
KIT = os.path.dirname(os.path.abspath(__file__))

info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=width,height,r_frame_rate',
                                  '-of', 'json', V], capture_output=True, text=True).stdout)
st = info['streams'][0]
print(f"video  {st['width']}x{st['height']} @{st['r_frame_rate']}  {float(info['format']['duration']):.2f}s  "
      f"{int(info['format']['size']) / 1e6:.0f}MB")
lu = subprocess.run(['ffmpeg', '-i', V, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('loudness', re.findall(r'I:\s+(-?[\d.]+) LUFS', lu)[-1], 'LUFS (target -14)')

# webcam card must never be black inside board segments (first-frame bug)
w = int(st['width']); s = w / 1080
bad = 0
for seg in edl['segments']:
    if seg['layout'] != 'board':
        continue
    t0, t1 = seg['t0'] / SP, (seg['t0'] + seg['out'] - seg['in']) / SP
    o = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', V, '-vf',
                        f'crop={int(900 * s)}:{int(650 * s)}:{int(90 * s)}:{int(220 * s)},scale=90:65,blackdetect=d=0:pix_th=0.12',
                        '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
    bad += o.count('black_start')
print('black webcam frames in board segments:', bad)

subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', V, '-vf', 'fps=1,scale=216:-1,tile=8x5', '-frames:v', '1',
                f'{D}/work/check_sheet.jpg'], check=True)
print('contact sheet:', f'{D}/work/check_sheet.jpg')
subprocess.run([sys.executable, os.path.join(KIT, 'transcribe.py'), V, f'{D}/work/check_words.json'], check=True)
