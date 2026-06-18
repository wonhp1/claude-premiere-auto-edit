#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
segment_subtitles.py — 어절 JSON(words.json)을 읽기 좋은 "1줄 자막" SRT로 분할한다. (크로스플랫폼)

사용법:
  python segment_subtitles.py [--workdir .] [--soft 16]

입력:  <workdir>/words.json   ([{start,end,text}, ...] 어절 + 정확한 시간)
출력:  <workdir>/cut_audio.srt (읽기 좋은 1줄 자막, 정확한 타이밍)

원칙(고정: 1줄 / 적응: 길이는 내용 따라):
  - 화면 넘침 방지용 소프트 상한(--soft, 기본 16자) + 하드 상한(soft+8).
  - 실제 말의 쉼(pause)·연결어미·구두점에서 우선 끊어 자연스럽게.
  - 의존명사("수","것")·"하는" 등 붙어야 할 말 앞에서는 안 끊음(glue).
  - look-ahead로 상한 내 "가장 자연스러운" 지점을 선택. 짧은 고아 줄은 병합.
  - 타이밍은 어절의 실제 시작/끝을 그대로 사용(정확).
"""

import argparse, json, os, sys

NO_START = (
    "수",
    "것",
    "거",
    "게",
    "때",
    "줄",
    "등",
    "들",
    "점",
    "중",
    "후",
    "전",
    "데",
    "만큼",
    "뿐",
    "채",
    "척",
    "분",
    "개",
    "명",
    "번",
    "건",
    "걸",
    "하는",
    "한",
    "할",
    "해서",
    "하고",
    "하던",
    "하지",
    "했",
    "있는",
    "있다",
    "있고",
    "있어",
    "없는",
    "없다",
    "같은",
    "같이",
    "위해",
    "통해",
    "대해",
    "대한",
    "위한",
    "수도",
    "수가",
    "코딩",
)
NO_END = (
    "그",
    "이",
    "저",
    "한",
    "두",
    "세",
    "네",
    "매우",
    "아주",
    "정말",
    "너무",
    "좀",
    "막",
    "딱",
    "그냥",
    "더",
    "덜",
    "꼭",
    "잘",
    "바이브",
)
CONN = (
    "고",
    "며",
    "면",
    "서",
    "데",
    "만",
    "나",
    "까",
    "요",
    "죠",
    "는데",
    "지만",
    "어서",
    "아서",
    "거나",
    "니까",
    "는데요",
)


def conn(w):
    if w and w[-1] in ".?!,":
        return 3
    return 2 if any(w.endswith(c) for c in CONN) else 0


def fmt(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--soft", type=float, default=16)
    a = ap.parse_args()
    SOFT = a.soft
    HARD = SOFT + 8
    PAUSE = 0.45
    src = os.path.join(a.workdir, "words.json")
    if not os.path.isfile(src):
        sys.exit(f"words.json 없음: {src} (먼저 transcribe_words.py 실행)")
    W = json.load(open(src, encoding="utf-8"))
    if not W:
        sys.exit("words.json 비어 있음")

    def gap_after(i):
        return (W[i + 1]["start"] - W[i]["end"]) if i + 1 < len(W) else 99

    def valid(i):
        return (W[i]["text"] not in NO_END) and (
            i + 1 >= len(W) or W[i + 1]["text"] not in NO_START
        )

    lines = []
    i = 0
    while i < len(W):
        j = i
        length = 0
        best = None
        bestsc = -1e9
        while j < len(W):
            length += len(W[j]["text"]) + (1 if j > i else 0)
            if j > i and valid(j) and length <= HARD:
                sc = (
                    gap_after(j) * 6
                    + conn(W[j]["text"]) * 3
                    - max(0, length - SOFT) * 1.5
                )
                if sc > bestsc:
                    bestsc = sc
                    best = j
            if length >= HARD:
                break
            if gap_after(j) >= PAUSE and length >= SOFT * 0.5 and j > i:
                best = best if best is not None else j
                break
            j += 1
        if best is None:
            best = min(j, len(W) - 1)
        s = W[i]["start"]
        e = W[best]["end"]
        ns = W[best + 1]["start"] if best + 1 < len(W) else None
        e = min(ns, e + 0.6) if ns else e + 0.3
        lines.append(
            [
                round(s, 3),
                round(e, 3),
                " ".join(W[k]["text"] for k in range(i, best + 1)),
            ]
        )
        i = best + 1

    # 짧은 고아 줄 병합
    merged = []
    for ln in lines:
        if merged and len(ln[2]) <= 5 and len(merged[-1][2]) + 1 + len(ln[2]) <= HARD:
            merged[-1][1] = ln[1]
            merged[-1][2] += " " + ln[2]
        else:
            merged.append(ln)
    lines = merged

    dst = os.path.join(a.workdir, "cut_audio.srt")
    with open(dst, "w", encoding="utf-8") as f:
        for k, (s, e, t) in enumerate(lines, 1):
            f.write(f"{k}\n{fmt(s)} --> {fmt(e)}\n{t}\n\n")
    L = [len(t) for _, _, t in lines]
    print(f"자막 {len(lines)}개 -> {dst} (글자수 평균 {sum(L)//len(L)}, 최대 {max(L)})")


if __name__ == "__main__":
    main()
