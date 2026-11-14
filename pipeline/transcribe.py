import sys,json,wave,numpy as np
from faster_whisper import WhisperModel
src,out=sys.argv[1],sys.argv[2]
w=wave.open(src);a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
m=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4)
segs,_=m.transcribe(a,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
res=[]
for s in segs:
    res.append({'start':s.start,'end':s.end,'text':s.text.strip(),'words':[[round(x.start,2),round(x.end,2),x.word.strip()] for x in s.words]})
    print(f'[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}',flush=True)
json.dump(res,open(out,'w'),indent=0)
