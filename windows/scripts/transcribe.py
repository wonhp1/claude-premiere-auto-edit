#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe.py — faster-whisper 로 오디오를 받아쓰기해 SRT 자막을 만든다. (크로스플랫폼)

사용법:
  python transcribe.py [audio] [--lang ko] [--model large-v3] [--workdir .]
  (audio 기본값: <workdir>/cut_audio.wav)

출력:
  <workdir>/cut_audio.srt

특징:
  - faster-whisper(pip) 사용 → Windows/Mac 공용, brew·컴파일 불필요.
  - 모델은 라이브러리가 "공용 캐시(HF cache)"에 자동 다운로드/재사용한다(옵션 B, OS별 표준 경로 자동).
  - GPU 있으면 자동 사용, 없으면 CPU(int8)로 폴백.
"""

import argparse, os, sys


def fmt_ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", nargs="?", default=None)
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--workdir", default=".")
    a = ap.parse_args()

    audio = a.audio or os.path.join(a.workdir, "cut_audio.wav")
    if not os.path.isfile(audio):
        sys.exit(f"오디오 없음: {audio} (먼저 시퀀스 오디오를 export 하세요)")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper 미설치 → `pip install faster-whisper`")

    # GPU 시도 → 실패 시 CPU
    model = None
    for dev, ct in [("cuda", "float16"), ("auto", "default"), ("cpu", "int8")]:
        try:
            model = WhisperModel(a.model, device=dev, compute_type=ct)
            break
        except Exception:
            continue
    if model is None:
        sys.exit("WhisperModel 로드 실패. faster-whisper/모델 설치를 확인하세요.")

    segments, info = model.transcribe(audio, language=a.lang, vad_filter=False)

    out = os.path.join(a.workdir, "cut_audio.srt")
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for seg in segments:
            n += 1
            f.write(
                f"{n}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n{seg.text.strip()}\n\n"
            )
    print(f"SRT 생성: {out} (자막 {n}개, 언어={a.lang})")


if __name__ == "__main__":
    main()
