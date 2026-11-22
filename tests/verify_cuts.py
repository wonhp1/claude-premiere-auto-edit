#!/usr/bin/env python3
"""verify_cuts.py — 무음 컷 결과를 프레임 단위로 검증한다.

사용법: python3 verify_cuts.py <cuts.json> <readback.json> <fps_num> <fps_den> [--source-frames N]
  cuts.json     : detect_silence 가 만든 컷 구간 [[s,e],...] (원본 초)
  readback.json : 컷 후 get_active_sequence 결과(data 부분)
기대값: 각 경계를 가장 가까운 프레임으로 반올림하고, 남는 구간을 앞에서부터 빈틈없이 붙인 것.
"""
import json, sys
from fractions import Fraction as F

cuts = json.load(open(sys.argv[1]))
rb = json.load(open(sys.argv[2]))
fps = F(int(sys.argv[3]), int(sys.argv[4]))
src_frames = None
if "--source-frames" in sys.argv:
    src_frames = int(sys.argv[sys.argv.index("--source-frames") + 1])

def fr(t):  # 초 → 프레임(실수), 가장 가까운 정수와의 차이도 함께
    x = F(str(t)) * fps
    return x

def nearest(t):
    return round(F(str(t)) * fps)

if src_frames is None:
    # 원본 길이는 컷 전 클립 길이 — readback 의 마지막 클립 outPoint 로 추정
    outs = [c["outPoint"] for tr in rb["videoTracks"] for c in tr["clips"]]
    src_frames = nearest(max(outs))

# 기대 유지 구간(원본 프레임)
keep, cur = [], 0
for s, e in cuts:
    fs, fe = nearest(s), nearest(e)
    keep.append((cur, fs)); cur = fe
keep.append((cur, src_frames))
keep = [k for k in keep if k[1] > k[0]]
exp, t = [], 0
for a, b in keep:
    exp.append({"src_in": a, "src_out": b, "tl_start": t, "tl_end": t + (b - a)}); t += b - a
exp_total = t

def check(kind, clips):
    rows, worst_frame, worst_off = [], 0, 0.0
    if len(clips) != len(exp):
        print(f"[{kind}] 클립 수 불일치: 실제 {len(clips)} / 기대 {len(exp)}")
    for i, (c, x) in enumerate(zip(sorted(clips, key=lambda c: c["start"]), exp)):
        got = {k: fr(c[v]) for k, v in (("src_in", "inPoint"), ("src_out", "outPoint"), ("tl_start", "start"), ("tl_end", "end"))}
        for k in got:
            d = abs(got[k] - x[k])
            worst_frame = max(worst_frame, float(d))
            worst_off = max(worst_off, float(abs(got[k] - round(got[k]))))  # 프레임 경계에서 벗어난 정도
        rows.append((i, {k: round(float(got[k]), 3) for k in got}, x))
    print(f"[{kind}] 클립 {len(clips)}개, 기대값과 최대 차이 {worst_frame:.4f}프레임, 프레임 경계 이탈 최대 {worst_off:.4f}프레임")
    for i, g, x in rows:
        print(f"  #{i}: 원본 {g['src_in']}–{g['src_out']} (기대 {x['src_in']}–{x['src_out']})  타임라인 {g['tl_start']}–{g['tl_end']} (기대 {x['tl_start']}–{x['tl_end']})")
    return worst_frame

print(f"fps={float(fps):.5f}, 원본 {src_frames}프레임, 컷 {len(cuts)}개 → 유지 구간 {len(exp)}개")
for (s, e) in cuts:
    fs, fe = nearest(s), nearest(e)
    print(f"  컷 요청 {s:.3f}–{e:.3f}초 → 프레임 {fs}–{fe} ({float(fs/fps):.4f}–{float(fe/fps):.4f}초, 반올림 오차 ≤ {max(abs(float(F(str(s))*fps-fs)), abs(float(F(str(e))*fps-fe))):.2f}프레임)")
v = [c for tr in rb["videoTracks"] for c in tr["clips"] if tr["index"] == 0]
a = [c for tr in rb["audioTracks"] for c in tr["clips"] if tr["index"] == 0]
wv = check("V1", v); wa = check("A1", a)
end_frames = fr(rb["end"])
print(f"시퀀스 길이: 실제 {float(rb['end']):.4f}초 ({float(end_frames):.3f}프레임) / 기대 {float(exp_total / fps):.4f}초 ({exp_total}프레임)")
ok = wv < 0.01 and wa < 0.01 and abs(end_frames - exp_total) < F(1, 100) and len(v) == len(a) == len(exp)
print("판정:", "프레임 단위 일치" if ok else "불일치 있음")
sys.exit(0 if ok else 1)
