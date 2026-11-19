#!/usr/bin/env bash
# Stream each Drive video (no local copy of the 4K original): 720p proxy + 16k mono wav + metadata.
cd "$(dirname "$0")"; mkdir -p proxy work
python3 -c "import json;[print(k,v) for k,v in json.load(open('manifest.json'))['files'].items() if k.upper().endswith('.MOV')]" |
while read name id; do
  b=${name%.*}; [ -s proxy/$b.mp4 ] && continue
  U="https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t"
  P=(-http_proxy "$HTTPS_PROXY" -ca_file /root/.ccr/ca-bundle.crt -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 30)
  ffprobe -v error "${P[@]}" -show_format -show_streams -of json "$U" > work/$b.probe.json
  ffmpeg -v error -y "${P[@]}" -i "$U" -map 0:v:0 -map 0:a:0 \
    -vf "scale='if(gt(iw,ih),1280,-2)':'if(gt(iw,ih),-2,1280)',fps=30,format=yuv420p" -c:v libx264 -preset veryfast -crf 30 \
    -c:a aac -b:a 96k proxy/$b.tmp.mp4 && mv proxy/$b.tmp.mp4 proxy/$b.mp4 &&
  ffmpeg -v error -y -i proxy/$b.mp4 -vn -ac 1 -ar 16000 work/$b.16k.wav && echo "done $b $(date +%T)"
done
echo ALL_DONE
