"""reel.json + speech islands -> edl.json (segments, captions, zoom keyframes, pills, cta, transitions).

usage: build_edl.py <reel_dir>
reads  <reel_dir>/reel.json, <reel_dir>/work/face_islands.json, <reel_dir>/work/face_16k.wav
writes <reel_dir>/work/edl.json   (times are on the edit timeline BEFORE the final speed-up)

Caption markup (per line, see README):
  '|' group break          *word* accent key (serif italic blue)     **word** money key (green)
  key phrases may span words: *5 minutes.*
  'have~them.'  one spoken word shown as two (ASR heard one token)
  'gonna+'      this caption token consumes TWO ASR tokens
"""
import json, sys, wave, os
import numpy as np

D = sys.argv[1]
R = json.load(open(f'{D}/reel.json'))
W = f'{D}/work'
islands = json.load(open(f'{W}/face_islands.json'))
allwords = [wd for isl in islands for wd in isl['words']]

w = wave.open(f'{W}/face_16k.wav')
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
RMS = 20 * np.log10(np.sqrt((A[:len(A) // 320 * 320].reshape(-1, 320) ** 2).mean(1)) + 1e-9)  # 20ms
THR = float(min(max(np.percentile(RMS, 10) + 20, -48), -35))   # ~20 dB over room tone (tuned on reel 01)

CUT = R.get('cut', {})
MAX_GAP = CUT.get('max_pause', 0.18)       # pauses longer than this inside a line get cut ...
KEEP_GAP = CUT.get('keep_pause', 0.06)     # ... down to this
PAD_IN, PAD_OUT = CUT.get('pad_in', 0.03), CUT.get('pad_out', 0.06)
END_HOLD = CUT.get('end_hold', 0.9)        # keep this much footage after the LAST word (ending felt cut off)
OFFSET_SPEC = R.get('screen_offset')       # face_time = screen_time + offset (None: no screen recording)
# a number, or [[face_time_from, offset], ...] when the screen recorder skipped (sync.py prints the map)
OFFSETS = (None if OFFSET_SPEC is None else
           [[0.0, float(OFFSET_SPEC)]] if isinstance(OFFSET_SPEC, (int, float)) else sorted(OFFSET_SPEC))


def offset_at(t):
    if OFFSETS is None:
        return None
    o = OFFSETS[0][1]
    for t0, v in OFFSETS:
        if t >= t0:
            o = v
    return o


OFFSET = OFFSETS[0][1] if OFFSETS else None


def speech_bounds(a, b):
    i0, i1 = int(a * 50), int(b * 50)
    v = np.where(RMS[i0:i1] > THR)[0]
    if not len(v):
        raise SystemExit(f'no speech between {a} and {b}')
    return (i0 + v[0]) / 50, (i0 + v[-1] + 1) / 50


def split_pauses(a, b):
    i0, i1 = int(a * 50), int(b * 50)
    voiced = RMS[i0:i1] > THR
    out, start, j, n = [], a, 0, len(voiced)
    while j < n:
        if not voiced[j]:
            k = j
            while k < n and not voiced[k]:
                k += 1
            gs, ge = a + j / 50, a + k / 50
            if 0 < j and k < n and ge - gs > MAX_GAP:
                out.append([start, gs + KEEP_GAP / 2]); start = ge - KEEP_GAP / 2
            j = k
        else:
            j += 1
    out.append([start, b])
    return [[round(x, 3), round(y, 3)] for x, y in out if y - x > 0.04]


def norm_tokens(words):
    out = []
    for s, e, t in words:
        if out and (t == '%' or t.startswith(',')):     # "10" "%"  /  "$12" ",000"
            out[-1][1] = e; out[-1][2] += t; continue
        out.append([s, e, t])
    return out


def clean(t):
    return t.lower().strip('*.,!?:;"“”').replace('~', ' ')


segments, captions, zooms, transitions = [], [], [], []
line_t, line_end, T, prev_layout = {}, {}, 0.0, None
for li, L in enumerate(R['lines']):
    layout = L['layout']
    a, b = L['in'], L['out']
    hard = L.get('hard_out', False)
    a, b0 = speech_bounds(a, b)
    a = a - PAD_IN
    b = b if hard else b0 + PAD_OUT
    if li == len(R['lines']) - 1 and not hard:     # let the last word land: hold on the speaker
        later = [isl['s'] for isl in islands if isl['s'] > b0 + 0.1]
        b = min(b0 + END_HOLD, (later[0] - 0.25) if later else 1e9)
    subs = split_pauses(a, b)
    wl = norm_tokens([wd for wd in allwords if wd[0] < b - 0.05 and wd[1] > a + 0.05])
    groups = [g.strip().split() for g in L['caption'].split('|')]
    need = sum(2 if t.rstrip('*').endswith('+') else 1 for g in groups for t in g)
    if need != len(wl):
        raise SystemExit(f"line {li} ({L['caption']!r}): caption needs {need} ASR tokens, found {len(wl)}:\n"
                         f"{[x[2] for x in wl]}\n-> fix the caption markup (~ / +) or the line's in/out")

    def map_t(t, T0=T, subs=subs):
        acc = T0
        for x, y in subs:
            if t < x:
                return acc
            if t <= y:
                return acc + (t - x)
            acc += y - x
        return acc

    if prev_layout is not None and prev_layout != layout:
        transitions.append(round(T, 3))
    line_t[li] = round(T, 3)
    k, in_key, words_here = 0, None, []
    for gi, g in enumerate(groups):
        for tok in g:
            t = round(map_t(max(wl[k][0], a)), 3)
            two = tok.rstrip('*').endswith('+')
            # '~' splits one ASR token into several shown words; each word carries its own * markers
            for sub in tok.replace('+', '').split('~'):
                if sub.startswith('**'):
                    in_key = 'money'
                elif sub.startswith('*'):
                    in_key = 'accent'
                key = in_key
                if sub.endswith('*'):
                    in_key = None
                text = sub.strip('*')
                captions.append({'t': t, 'text': text, 'key': key, 'group': f'{li}-{gi}', 'layout': layout})
                words_here.append((clean(text), t))
            k += 2 if two else 1

    # zoom keyframes (face layout only): {"at": "start" | "<word>" | "+0.4", "to": 1.05, "dur": 0.25}
    if layout == 'face':
        if prev_layout != 'face':
            zooms.append({'t': round(T, 3), 'to': L.get('zoom_base', 1.0), 'dur': 0})
        for z in L.get('zoom', []):
            at = z.get('at', 'start')
            if at == 'start':
                tz = T
            elif isinstance(at, str) and at.startswith('+'):
                tz = T + float(at[1:])
            else:
                hit = [t for w_, t in words_here if w_ == clean(at)]
                if not hit:
                    raise SystemExit(f'line {li}: zoom word {at!r} not in caption')
                tz = hit[0]
            zooms.append({'t': round(tz + z.get('offset', 0), 3), 'to': z['to'], 'dur': z.get('dur', 0.25)})

    for x, y in subs:
        seg = {'layout': layout, 'in': x, 'out': y, 'line': li, 't0': round(T, 3)}
        if 'face_x' in L:                              # face centre (source px) for this take: re-centres the crops
            seg['face_x'] = L['face_x']
        off = offset_at(x)
        on_screen_rec = off is not None and (x - off) > 0.3 and (y - off) < R.get('screen_duration', 1e9)
        audio = R.get('audio', 'auto')
        seg['audio'] = 'screen' if (audio == 'screen' or (audio == 'auto' and on_screen_rec)) else 'face'
        if off is not None:
            seg['audio_in'] = round(x - off, 3)
        if layout == 'board':
            if 'screen_in' in L:                       # board footage from elsewhere (e.g. screen showed another app)
                seg['screen_in'] = round(L['screen_in'] + (x - subs[0][0]), 3)
            else:
                seg['screen_in'] = round(x - off, 3)
            if 'screen_fit' in L:
                seg['screen_fit'] = L['screen_fit']
        segments.append(seg)
        T += y - x
    line_end[li] = round(T, 3)
    captions[-1]['line_end'] = round(T, 3)
    prev_layout = layout

n = len(R['lines'])


def lt(i):
    return line_t[i] if i < n else round(T, 3)


def word_t(line, word):
    for c in captions:
        if int(c['group'].split('-')[0]) == line and clean(c['text']) == clean(word):
            return c['t']
    return line_t[line]


pills = [{'n': i + 1, 'text': p['text'], 't0': lt(p['from_line']), 't1': lt(p['to_line'])}
         for i, p in enumerate(R.get('pills', []))]
cta = None
if R.get('cta'):
    c = R['cta']
    cta = {'text': c['text'], 't0': word_t(c['line'], c['word']) if c.get('word') else lt(c['line']),
           't1': lt(c['to_line']) if 'to_line' in c else line_end[c['line']]}

edl = {'duration': round(T, 3), 'segments': segments, 'captions': captions, 'zooms': zooms,
       'transitions': transitions, 'pills': pills, 'cta': cta, 'line_t': line_t}
json.dump(edl, open(f'{W}/edl.json', 'w'), indent=1)
print(f'edit: {T:.2f}s before speed-up ({T / R.get("speed", 1.0):.2f}s final), {len(segments)} segments, '
      f'{len(transitions)} transitions, {len(zooms)} zoom keys, speech threshold {THR:.0f} dB')
for s in segments:
    print(f"{s['t0']:6.2f} L{s['line']:<2} {s['layout']:5s} {s['audio']:6s} face {s['in']:.2f}-{s['out']:.2f}"
          + (f"  screen {s['screen_in']:.2f}" if 'screen_in' in s else ''))
