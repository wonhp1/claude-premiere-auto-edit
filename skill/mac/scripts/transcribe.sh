#!/usr/bin/env bash
#
# transcribe.sh — whisper.cpp 로 오디오를 받아쓰기해 SRT 자막을 만든다.
#
# 사용법:
#   bash transcribe.sh [wav=/tmp/cut_audio.wav] [lang=ko] [model_path]
#
# 출력:
#   <wav과 같은 이름>.srt   (예: /tmp/cut_audio.srt)
#
# 필요:
#   - whisper-cli (brew install whisper-cpp)
#   - ggml large-v3 모델 (.bin) — 자동 탐색, 없으면 경로를 3번째 인자로 지정
#
set -euo pipefail

WAV_IN="${1:-/tmp/cut_audio.wav}"
LANG="${2:-ko}"
MODEL="${3:-}"

[ -f "$WAV_IN" ] || { echo "오디오 없음: $WAV_IN" >&2; exit 1; }

BIN="$(command -v whisper-cli || true)"
[ -n "$BIN" ] || { echo "whisper-cli 없음 → brew install whisper-cpp" >&2; exit 1; }

# 모델 자동 탐색 (whisper.cpp ggml 포맷)
if [ -z "$MODEL" ]; then
  for m in \
    "$HOME/.cache/hyperframes/whisper/models/ggml-large-v3.bin" \
    "$HOME/.cache/whisper.cpp/ggml-large-v3.bin" \
    "/opt/homebrew/share/whisper-cpp/ggml-large-v3.bin" ; do
    [ -f "$m" ] && MODEL="$m" && break
  done
  # 광범위 탐색(최후)
  [ -z "$MODEL" ] && MODEL="$(find "$HOME" -name 'ggml-large-v3.bin' 2>/dev/null | head -1)"
fi
[ -n "$MODEL" ] || { echo "ggml large-v3 모델을 못 찾음. 3번째 인자로 .bin 경로를 주세요." >&2; exit 1; }

# whisper.cpp 는 16kHz 모노 WAV 만 받는다 → 안전하게 변환
WAV16="/tmp/_whisper_in_16k.wav"
ffmpeg -nostats -hide_banner -y -i "$WAV_IN" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV16" >/dev/null 2>&1

OUT="${WAV_IN%.*}"   # 확장자 제거 → whisper 가 .srt 붙임
"$BIN" -m "$MODEL" -f "$WAV16" -l "$LANG" -osrt -of "$OUT"

echo "SRT 생성: ${OUT}.srt"
