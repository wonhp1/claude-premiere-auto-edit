#!/usr/bin/env bash
# make_test_media.sh — 무음 컷·자막 검증용 테스트 영상을 만든다 (macOS: say + ffmpeg).
#
# 사용법: bash make_test_media.sh <출력폴더> [샘플영상폴더]
# 출력:  speech.wav (48kHz 모노 원본 오디오), layout.json (말·쉼 구간 설계값),
#        test_2997.mp4 (29.97fps), test_23976.mp4 (23.976fps), test_30.mp4 (30fps)
#
# 구성: 말 5덩어리(한국어, Yuna 음성) 사이에 2.0/3.0/2.5/2.2초 무음, 3번째 덩어리 안에는 1.0초 짧은 쉼.
#       기본 설정(-30dB, 2.0초)이면 긴 무음 4개만 잘리고 1.0초 쉼은 남아야 한다.
set -euo pipefail
OUT="${1:?출력 폴더}"
SAMPLES="${2:-/Users/Shared/Adobe/Premiere Pro/27.0/Sample Media}"
VOICE="${VOICE:-Yuna}"
mkdir -p "$OUT/parts"
cd "$OUT/parts"

sil() { ffmpeg -v error -y -f lavfi -i "anullsrc=r=48000:cl=mono" -t "$1" -c:a pcm_s16le "$2"; }
spk() { say -v "$VOICE" -o "$2.aiff" "$1" && ffmpeg -v error -y -i "$2.aiff" -ar 48000 -ac 1 -c:a pcm_s16le "$2"; rm -f "$2.aiff"; }

spk "안녕하세요. 오늘은 프리미어 자동 편집을 테스트합니다." u1.wav
spk "무음 구간을 찾아서 자동으로 잘라내는 기능입니다." u2.wav
spk "말하는 사이에" u3a.wav
spk "이삼 초 정도 쉬는 구간을 넣었습니다." u3b.wav
spk "자막은 위스퍼로 받아쓰기한 뒤 타임라인에 올립니다." u4.wav
spk "테스트가 끝나면 결과를 확인해 주세요." u5.wav
sil 0.5 lead.wav; sil 2.0 g1.wav; sil 3.0 g2.wav; sil 1.0 g3s.wav; sil 2.5 g3.wav; sil 2.2 g4.wav; sil 0.6 tail.wav

ORDER="lead u1 g1 u2 g2 u3a g3s u3b g3 u4 g4 u5 tail"
: > list.txt
python3 - "$ORDER" > ../layout.json <<'PY'
import sys, subprocess, json
t = 0.0; rows = []
for name in sys.argv[1].split():
    d = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",name+".wav"]).decode())
    rows.append({"part": name, "start": round(t, 4), "end": round(t + d, 4)})
    t += d
    open("list.txt","a").write(f"file '{name}.wav'\n")
print(json.dumps({"total": round(t, 4), "parts": rows}, ensure_ascii=False, indent=1))
PY
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c:a pcm_s16le ../speech.wav
cd "$OUT"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 speech.wav)

# 샘플 영상 2개를 이어 붙여 음성 길이만큼 자른다(샘플 클립 자체 오디오는 무음이라 버린다).
for spec in "30000/1001:2997" "24000/1001:23976" "30:30"; do
  R="${spec%%:*}"; TAG="${spec##*:}"
  ffmpeg -v error -y \
    -i "$SAMPLES/Sample Media Clip 1.mp4" -i "$SAMPLES/Sample Media Clip 10.mp4" -i speech.wav \
    -filter_complex "[0:v]scale=1920:1080,setsar=1,fps=$R[a];[1:v]scale=1920:1080,setsar=1,fps=$R[b];[a][b]concat=n=2:v=1:a=0[v]" \
    -map "[v]" -map 2:a -t "$DUR" -r "$R" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -ar 48000 -ac 2 "test_${TAG}.mp4"
done
rm -rf parts
ls -la "$OUT"
