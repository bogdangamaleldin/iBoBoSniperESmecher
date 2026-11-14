"""Build the edit decision list + caption timeline for the hook->board reel.

Output: edl.json  {segments:[{layout, in, out, miro_in}], words:[{t, text, key, group}], overlays:[...]}
All output times are in seconds on the final timeline.
"""
import json, wave, re
import numpy as np

MIRO_OFFSET = 157.18  # me_time = miro_time + MIRO_OFFSET

w = wave.open('me_audio.wav')
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
SR = 16000
H = SR // 50  # 20ms
RMS = 20 * np.log10(np.sqrt((A[:len(A) // H * H].reshape(-1, H) ** 2).mean(1)) + 1e-9)
islands = json.load(open('islands.json'))
allwords = [wd for isl in islands for wd in isl['words']]


def speech_bounds(a, b, thr=-45):
    """Trim [a,b] to first/last voiced 20ms frame."""
    i0, i1 = int(a * 50), int(b * 50)
    v = np.where(RMS[i0:i1] > thr)[0]
    return (i0 + v[0]) / 50, (i0 + v[-1] + 1) / 50


def split_pauses(a, b, max_gap=0.22, keep=0.10, thr=-45):
    """Return keep sub-ranges of [a,b] with internal silences > max_gap shortened to `keep`."""
    i0, i1 = int(a * 50), int(b * 50)
    voiced = RMS[i0:i1] > thr
    ranges, start, j = [], a, 0
    n = len(voiced)
    while j < n:
        if not voiced[j]:
            k = j
            while k < n and not voiced[k]:
                k += 1
            gs, ge = a + j / 50, a + k / 50
            if k < n and ge - gs > max_gap:
                ranges.append([start, gs + keep / 2])
                start = ge - keep / 2
            j = k
        else:
            j += 1
    ranges.append([start, b])
    return [[round(x, 3), round(y, 3)] for x, y in ranges]


# (layout, me_in, me_out, caption-with-markup, miro_override_in)
# caption markup: '|' = group break, *word* = key word (accent), **word** = money/win key (green)
LINES = [
    ('face', 90.40, 92.80, "ai can build | your miro board | in *5 minutes.*", None),
    ('face', 99.60, 101.95, "that's exactly why | it *won't* book you | a call.", None),
    ('face', 129.25, 130.90, "the board | is *10%* of it.", None),
    ('face', 149.90, 153.50, "the other *90%* | is 4 decisions | which ai cannot | make for you.", None),
    ('board', 181.90, 185.75, "the left side | is what ai gives you, | the right side is | what booked **56 calls.**", None),
    ('board', 225.55, 230.85, "the first decision | is making the miro board | around the *topic* | that your buyer | is actually ready for.", None),
    ('board', 238.05, 240.58, "the second decision | is the *result* | you actually lead with", None),
    ('board', 251.95, 255.50, "and the number | you start with | in the first *30 seconds* | to a minute of your video", None),
    ('board', 271.65, 277.10, "then you should always use | your terms, | your numbers, | your examples | and your wording, | because ai *doesn't* *have~them.*", None),
    ('board', 284.80, 288.30, "and then lastly, | a cta that your backend | can actually *close.*", None),
    ('board', 343.20, 346.40, "comment *ai* | and i'll send you | the full breakdown | of the board that did it.", 155.0),
    ('face', 329.45, 333.30, "ai builds the boxes. | you still have to *decide* | what goes in them.", None),
]

# Whisper tokens that merge into one caption token (e.g. "10" + "%")
def norm_tokens(words):
    out = []
    for s, e, t in words:
        if out and (t in ('%',) or t.startswith(',')):
            out[-1][1] = e
            continue
        out.append([s, e, t])
    return out


segments, captions = [], []
T = 0.0
for li, (layout, a, b, cap, miro_override) in enumerate(LINES):
    hard_out = b if li in (6, 9) else None
    a, b = speech_bounds(a, b)
    a, b = a - 0.06, (hard_out if hard_out else b + 0.10)
    subs = split_pauses(a, b)
    # whisper words in this line
    wl = norm_tokens([wd for wd in allwords if wd[0] < b - 0.05 and wd[1] > a + 0.05])
    groups = [g.strip().split() for g in cap.split('|')]
    toks = [t for g in groups for t in g]
    # "the number you start with" etc: alignment is positional, counts must match
    if len(toks) != len(wl):
        raise SystemExit(f'line {li}: {len(toks)} caption tokens vs {len(wl)} words\n{toks}\n{[x[2] for x in wl]}')

    def map_t(t):
        """source time -> output time, through the sub-range cuts."""
        acc = T
        for x, y in subs:
            if t < x:
                return acc
            if t <= y:
                return acc + (t - x)
            acc += y - x
        return acc

    k = 0
    for gi, g in enumerate(groups):
        for tok in g:
            s = max(wl[k][0], a)
            key = 'money' if tok.startswith('**') else ('accent' if tok.startswith('*') else None)
            captions.append({'t': round(map_t(s), 3), 'text': tok.strip('*').replace('~', ' '), 'key': key,
                             'group': f'{li}-{gi}', 'layout': layout})
            k += 1
    for x, y in subs:
        seg = {'layout': layout, 'in': x, 'out': y, 'line': li, 't0': round(T, 3)}
        if layout == 'board':
            seg['miro_in'] = round((miro_override + (x - subs[0][0])) if miro_override is not None else x - MIRO_OFFSET, 3)
        segments.append(seg)
        T += y - x
    # line end time for group exits
    captions[-1]['line_end'] = round(T, 3)

json.dump({'duration': round(T, 3), 'segments': segments, 'captions': captions}, open('edl.json', 'w'), indent=1)
print(f'duration {T:.2f}s, {len(segments)} segments')
for s in segments:
    print(f"{s['t0']:6.2f} {s['layout']:5s} me {s['in']:.2f}-{s['out']:.2f} ({s['out']-s['in']:.2f}s)" + (f" miro {s['miro_in']:.2f}" if 'miro_in' in s else ''))
