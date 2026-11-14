"""Build the edit decision list + caption timeline for the hook->board reel (v2).

v2: tighter cuts (pauses > 0.12s cut down to 0.05s, small line pads),
audio source per line (laptop mic wherever the screen recording exists), caption groups of 1-3 words.
Output: edl.json  {duration, segments:[...], captions:[...]}  (times before the final speed-up)
"""
import json, wave
import numpy as np

MIRO_OFFSET = 157.18  # me_time = miro_time + MIRO_OFFSET

w = wave.open('me_audio.wav')
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
RMS = 20 * np.log10(np.sqrt((A[:len(A) // 320 * 320].reshape(-1, 320) ** 2).mean(1)) + 1e-9)  # 20ms frames
islands = json.load(open('islands.json'))
allwords = [wd for isl in islands for wd in isl['words']]
THR = -45


def speech_bounds(a, b):
    i0, i1 = int(a * 50), int(b * 50)
    v = np.where(RMS[i0:i1] > THR)[0]
    return (i0 + v[0]) / 50, (i0 + v[-1] + 1) / 50


def split_pauses(a, b, max_gap=0.18, keep=0.06):
    i0, i1 = int(a * 50), int(b * 50)
    voiced = RMS[i0:i1] > THR
    ranges, start, j, n = [], a, 0, len(voiced)
    while j < n:
        if not voiced[j]:
            k = j
            while k < n and not voiced[k]:
                k += 1
            gs, ge = a + j / 50, a + k / 50
            if 0 < j and k < n and ge - gs > max_gap:
                ranges.append([start, gs + keep / 2])
                start = ge - keep / 2
            j = k
        else:
            j += 1
    ranges.append([start, b])
    return [[round(x, 3), round(y, 3)] for x, y in ranges if y - x > 0.04]


# (layout, me_in, me_out, caption markup, miro override, hard_out)
# '|' = group break, *w* = accent key word, **w** = money key word, '~' joins two shown words on one timing
LINES = [
    ('face', 90.40, 92.80, "ai can build | your miro board | in *5 minutes.*", None, False),
    ('face', 99.60, 101.95, "that's exactly why | it *won't* | book you a call.", None, False),
    ('face', 129.25, 130.90, "the board | is *10%* of it.", None, False),
    ('face', 149.90, 153.50, "the other *90%* | is 4 decisions | which ai cannot | make for you.", None, False),
    ('board', 181.90, 185.75, "the left side | is what | ai gives you, | the right side | is what booked | **56 calls.**", None, False),
    ('board', 226.78, 230.85, "the~first decision | is making | the miro board | around the *topic* | that your buyer | is actually | ready for.", None, False),
    ('board', 238.05, 240.58, "the second decision | is the *result* | you actually | lead with", None, True),
    ('board', 251.95, 255.50, "and the number | you start with | in the first | *30 seconds* | to a minute | of your video", None, False),
    ('board', 271.65, 277.10, "then you should | always use | your terms, | your numbers, | your examples | and your wording, | because ai | *doesn't have~them.*", None, False),
    ('board', 284.80, 288.30, "and then lastly, | a cta | that your backend | can actually | *close.*", None, True),
    ('board', 343.20, 346.40, "comment *ai* | and i'll send you | the full breakdown | of the board | that did it.", 155.0, False),
    ('face', 329.45, 333.30, "ai builds | the boxes. | you still have | to *decide* | what goes | in them.", None, False),
]


def norm_tokens(words):
    out = []
    for s, e, t in words:
        if out and (t == '%' or t.startswith(',')):
            out[-1][1] = e
            continue
        out.append([s, e, t])
    return out


segments, captions = [], []
T = 0.0
for li, (layout, a, b, cap, miro_override, hard) in enumerate(LINES):
    hard_out = b if hard else None
    a, b = speech_bounds(a, b)
    a, b = a - 0.03, (hard_out if hard_out else b + 0.06)
    subs = split_pauses(a, b)
    wl = norm_tokens([wd for wd in allwords if wd[0] < b - 0.05 and wd[1] > a + 0.05])
    groups = [g.strip().split() for g in cap.split('|')]
    toks = [t for g in groups for t in g]
    if len(toks) != len(wl):
        raise SystemExit(f'line {li}: {len(toks)} caption tokens vs {len(wl)} words\n{toks}\n{[x[2] for x in wl]}')

    def map_t(t, T0=T):
        acc = T0
        for x, y in subs:
            if t < x:
                return acc
            if t <= y:
                return acc + (t - x)
            acc += y - x
        return acc

    k = 0
    in_key = None   # key phrases can span several words: *5 minutes.*
    for gi, g in enumerate(groups):
        for tok in g:
            s = max(wl[k][0], a)
            if tok.startswith('**'):
                in_key = 'money'
            elif tok.startswith('*'):
                in_key = 'accent'
            key = in_key
            if tok.endswith('*'):
                in_key = None
            captions.append({'t': round(map_t(s), 3), 'text': tok.strip('*').replace('~', ' '), 'key': key,
                             'group': f'{li}-{gi}', 'layout': layout})
            k += 1
    use_laptop = a - MIRO_OFFSET > 0.5
    for x, y in subs:
        seg = {'layout': layout, 'in': x, 'out': y, 'line': li, 't0': round(T, 3),
               'audio': 'laptop' if use_laptop else 'phone', 'audio_in': round(x - MIRO_OFFSET, 3)}
        if layout == 'board':
            seg['miro_in'] = round((miro_override + (x - subs[0][0])) if miro_override is not None else x - MIRO_OFFSET, 3)
        segments.append(seg)
        T += y - x
    captions[-1]['line_end'] = round(T, 3)

json.dump({'duration': round(T, 3), 'segments': segments, 'captions': captions}, open('edl.json', 'w'), indent=1)
print(f'duration {T:.2f}s, {len(segments)} segments')
for s in segments:
    print(f"{s['t0']:6.2f} L{s['line']:<2} {s['layout']:5s} {s['audio']:6s} me {s['in']:.2f}-{s['out']:.2f} ({s['out']-s['in']:.2f}s)")
