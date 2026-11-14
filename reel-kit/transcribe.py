"""Word-timed transcription with faster-whisper.

usage:
  transcribe.py <media> <out.json>             full pass: [{start,end,text,words:[[s,e,w],...]}]
  transcribe.py <media> <out.json> --islands   split speech into islands (by loudness) and transcribe
                                               each one on its own: [{s,e,words:[[s,e,w],...]}]
--islands is what you want for raw footage with retakes: whisper merges repeated takes
in a full pass, but each island transcribed alone keeps every take separate.
Optional: --from <sec> ignore audio before this time (camera set-up).
"""
import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel

SR = 16000


def load_audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def rms_db(a, hop=SR // 20):
    a = a[:len(a) // hop * hop]
    return 20 * np.log10(np.sqrt((a.reshape(-1, hop) ** 2).mean(1)) + 1e-9)


def speech_islands(a, t_from=0.0):
    r = rms_db(a)                       # 50ms frames
    floor = np.percentile(r, 10)
    thr = min(max(floor + 20, -48), -35)
    sp = r > thr
    isl, s = [], None
    for i, v in enumerate(sp):
        t = i / 20
        if v and s is None:
            s = t
        if not v and s is not None:
            isl.append([s, t]); s = None
    if s is not None:
        isl.append([s, len(sp) / 20])
    merged = []
    for x in isl:
        if merged and x[0] - merged[-1][1] < 0.6:
            merged[-1][1] = x[1]
        else:
            merged.append(x)
    return [x for x in merged if x[1] - x[0] > 0.3 and x[0] >= t_from], thr


def main():
    media, out = sys.argv[1], sys.argv[2]
    islands = '--islands' in sys.argv
    t_from = float(sys.argv[sys.argv.index('--from') + 1]) if '--from' in sys.argv else 0.0
    a = load_audio(media)
    model = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
    res = []
    if islands:
        isl, thr = speech_islands(a, t_from)
        print(f'{len(isl)} speech islands (threshold {thr:.0f} dB)', flush=True)
        for s, e in isl:
            s0, e0 = max(0, s - 0.3), e + 0.3
            segs, _ = model.transcribe(a[int(s0 * SR):int(e0 * SR)], word_timestamps=True,
                                       condition_on_previous_text=False)
            words = [[round(s0 + w.start, 2), round(s0 + w.end, 2), w.word.strip()] for g in segs for w in g.words]
            res.append({'s': round(s, 2), 'e': round(e, 2), 'words': words})
            print(f'{s:7.2f}-{e:7.2f} | ' + ' '.join(w[2] for w in words), flush=True)
    else:
        segs, _ = model.transcribe(a[int(t_from * SR):], word_timestamps=True, condition_on_previous_text=False)
        for g in segs:
            res.append({'start': round(t_from + g.start, 2), 'end': round(t_from + g.end, 2), 'text': g.text.strip(),
                        'words': [[round(t_from + w.start, 2), round(t_from + w.end, 2), w.word.strip()] for w in g.words]})
            print(f'[{t_from + g.start:6.2f}-{t_from + g.end:6.2f}] {g.text.strip()}', flush=True)
    json.dump(res, open(out, 'w'))


if __name__ == '__main__':
    main()
