"""Composite base video + caption layer, speed-up, voice loudness, SFX + optional song -> final mp4.

usage: finish.py <reel_dir> [preview|final] [out.mp4]
SFX (reel.json "sfx", defaults below; files in brand/sfx/):
  riser       under the hook, starting at 0s
  transition  camera-shutter SECOND click only (file from 0.66s) on every face<->board switch
song (reel.json "song": {"file": "...", "start": 0, "gain_db": -20}) is ducked under the voice.
"""
import json, os, subprocess, sys

D = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else 'preview'
R = json.load(open(f'{D}/reel.json'))
WK = f'{D}/work'
KIT = os.path.dirname(os.path.abspath(__file__))
SFXDIR = os.path.join(KIT, '..', 'brand', 'sfx')
edl = json.load(open(f'{WK}/edl.json'))
b = json.load(open(f'{WK}/base_{MODE}.json'))
FPS, SP = b['fps'], R.get('speed', 1.0)
name = R.get('name', os.path.basename(os.path.abspath(D)))
OUT = sys.argv[3] if len(sys.argv) > 3 else f"{D}/out/{name}_{'preview' if MODE == 'preview' else '4k60'}.mp4"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
dur_out = edl['duration'] / SP

sfx = {'riser': {'file': 'riser.mp3', 'at': 0.0, 'gain_db': 4},
       'transition': {'file': 'camera-shutter.mp3', 'trim_start': 0.66, 'hit': 0.03, 'gain_db': -2}}
for k, v in (R.get('sfx') or {}).items():
    if v is None:
        sfx.pop(k, None)
    else:
        sfx[k] = {**sfx.get(k, {}), **v}

inputs = ['-i', f'{WK}/base_{MODE}.mov', '-framerate', str(FPS), '-i', f'{WK}/ovl_{MODE}/%05d.png']
fc = [f"[0:v][1:v]overlay=format=auto:eof_action=pass,setpts=PTS/{SP},fps={FPS},format=yuv420p[v]",
      f"[0:a]atempo={SP},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[voice]"]
mix = ['[voice]']
idx = 2
song = R.get('song')
if song:
    fc[-1] = fc[-1].replace('[voice]', '[voice0]') + ';[voice0]asplit=2[voice][key]'
if 'riser' in sfx:
    r = sfx['riser']
    inputs += ['-i', os.path.join(SFXDIR, r['file'])]
    ms = int(r.get('at', 0) * 1000)
    fc.append(f"[{idx}:a]aresample=48000,volume={r['gain_db']}dB,adelay={ms}|{ms}[riser]")
    mix.append('[riser]'); idx += 1
trans = [t / SP for t in edl.get('transitions', [])]
if 'transition' in sfx and trans:
    tr = sfx['transition']
    inputs += ['-i', os.path.join(SFXDIR, tr['file'])]
    fc.append(f"[{idx}:a]aresample=48000,atrim=start={tr.get('trim_start', 0)},asetpts=PTS-STARTPTS,"
              f"volume={tr['gain_db']}dB,asplit={len(trans)}" + ''.join(f'[tr{i}]' for i in range(len(trans))))
    for i, t in enumerate(trans):
        ms = max(0, int((t - tr.get('hit', 0)) * 1000))
        fc.append(f"[tr{i}]adelay={ms}|{ms}[trd{i}]"); mix.append(f'[trd{i}]')
    idx += 1
if song:
    inputs += ['-stream_loop', '-1', '-ss', str(song.get('start', 0)), '-i', f"{D}/{song['file']}"]
    fc.append(f"[{idx}:a]aresample=48000,atrim=0:{dur_out:.3f},volume={song.get('gain_db', -20)}dB,"
              f"afade=t=in:d=0.3,afade=t=out:st={dur_out - 0.8:.3f}:d=0.8[song0];"
              f"[song0][key]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=350[song]")
    mix.append('[song]'); idx += 1
fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.94[a]")

enc = (['-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-profile:v', 'high', '-level', '5.2']
       if MODE == 'final' else ['-c:v', 'libx264', '-preset', 'fast', '-crf', '19'])
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '[a]',
                *enc, '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', f'{dur_out:.3f}',
                '-movflags', '+faststart', OUT], check=True)
print(f'{OUT}  ({dur_out:.2f}s)')
