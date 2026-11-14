import wave,json,numpy as np
from faster_whisper import WhisperModel
w=wave.open('me_audio.wav');a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
sr=16000;h=sr//20
r=20*np.log10(np.sqrt((a[:len(a)//h*h].reshape(-1,h)**2).mean(1))+1e-9)
sp=r>-45
# islands: merge gaps < 0.6s, drop < 0.3s
isl=[];s=None
for i,v in enumerate(sp):
  t=i/20
  if v and s is None: s=t
  if not v and s is not None:
    isl.append([s,t]);s=None
m=[]
for x in isl:
  if m and x[0]-m[-1][1]<0.6: m[-1][1]=x[1]
  else: m.append(x)
m=[x for x in m if x[1]-x[0]>0.3 and x[0]>88]
model=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4)
out=[]
for s,e in m:
  s0,e0=max(0,s-0.3),e+0.3
  seg,_=model.transcribe(a[int(s0*sr):int(e0*sr)],word_timestamps=True,condition_on_previous_text=False)
  words=[[round(s0+x.start,2),round(s0+x.end,2),x.word.strip()] for g in seg for x in g.words]
  out.append({'s':round(s,2),'e':round(e,2),'words':words})
  print(f'{s:7.2f}-{e:7.2f} | '+' '.join(x[2] for x in words),flush=True)
json.dump(out,open('islands.json','w'))
