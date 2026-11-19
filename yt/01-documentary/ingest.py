"""Stream each Drive video (no local copy of the 4K original) -> proxy/<clip>.mp4 (720p30) + work/<clip>.16k.wav.
Retries with backoff and checks the proxy is as long as the original (a dropped connection truncates silently)."""
import json, os, subprocess, time
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('proxy', exist_ok=True); os.makedirs('work', exist_ok=True)
P = ['-http_proxy', os.environ['HTTPS_PROXY'], '-ca_file', '/root/.ccr/ca-bundle.crt',
     '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_on_network_error', '1', '-reconnect_delay_max', '30']
files = {k: v for k, v in json.load(open('manifest.json'))['files'].items() if k.upper().endswith('.MOV')}
dur = lambda f: float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                                     capture_output=True, text=True).stdout or 0)
failed = []
for name, fid in sorted(files.items()):
    b = name.rsplit('.', 1)[0]
    if os.path.exists(f'proxy/{b}.mp4'):
        continue
    url = f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t'
    for attempt in range(5):
        pr = subprocess.run(['ffprobe', '-v', 'error', *P, '-show_format', '-show_streams', '-of', 'json', url],
                            capture_output=True, text=True, stdin=subprocess.DEVNULL)
        try:
            src = float(json.loads(pr.stdout)['format']['duration'])
        except Exception:
            print(f'{b}: probe failed (try {attempt + 1}): {pr.stderr.strip()[-200:]}', flush=True); time.sleep(30 * (attempt + 1)); continue
        open(f'work/{b}.probe.json', 'w').write(pr.stdout)
        tmp = f'proxy/{b}.tmp.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', *P, '-i', url, '-map', '0:v:0', '-map', '0:a:0',
                        '-vf', "scale='if(gt(iw,ih),1280,-2)':'if(gt(iw,ih),-2,1280)',fps=30,format=yuv420p",
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-c:a', 'aac', '-b:a', '96k', tmp],
                       stdin=subprocess.DEVNULL)
        got = dur(tmp) if os.path.exists(tmp) else 0
        if abs(got - src) < 1.0:
            os.replace(tmp, f'proxy/{b}.mp4')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', f'proxy/{b}.mp4', '-vn', '-ac', '1', '-ar', '16000',
                            f'work/{b}.16k.wav'], check=True)
            print(f'done {b} {src:.0f}s {time.strftime("%H:%M:%S")}', flush=True); break
        print(f'{b}: proxy {got:.1f}s of {src:.1f}s (try {attempt + 1}), retrying', flush=True)
        time.sleep(30 * (attempt + 1))
    else:
        failed.append(b)
print('ALL_DONE', 'failed:', failed)
