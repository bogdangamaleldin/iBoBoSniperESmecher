"""Transcribe every work/<clip>.16k.wav as the ingest produces them -> work/<clip>.words.json (+ .txt).
Polls until all clips in manifest.json are done. small.en, word timestamps, VAD off (keep timing honest)."""
import json, os, time, glob, wave
import numpy as np
from faster_whisper import WhisperModel
os.chdir(os.path.dirname(os.path.abspath(__file__)))
names = sorted(k.rsplit('.', 1)[0] for k in json.load(open('manifest.json'))['files'] if k.upper().endswith('.MOV'))
m = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
while True:
    todo = [n for n in names if not os.path.exists(f'work/{n}.words.json')]
    if not todo: break
    ready = [n for n in todo if os.path.exists(f'proxy/{n}.mp4') and os.path.exists(f'work/{n}.16k.wav')]
    if not ready: time.sleep(30); continue
    n = ready[0]
    w = wave.open(f'work/{n}.16k.wav')
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    segs, info = m.transcribe(audio, word_timestamps=True, condition_on_previous_text=False)
    words, lines = [], []
    for s in segs:
        words += [[round(w.start, 2), round(w.end, 2), w.word.strip()] for w in s.words]
        lines.append(f'[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}')
    json.dump({'duration': info.duration, 'words': words}, open(f'work/{n}.words.json', 'w'))
    open(f'work/{n}.txt', 'w').write('\n'.join(lines) + '\n')
    print(f'{n} {info.duration:.0f}s {len(words)} words', flush=True)
print('TRANSCRIBE_DONE')
