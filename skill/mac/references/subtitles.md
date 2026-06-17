# 자막(캡션) 삽입 — 전 과정 자동화

## 전체 흐름 (전부 스크립트)

1. **오디오 export** — `assets/export_sequence_audio.jsx` (execute_extendscript). 현재 시퀀스를 16kHz 모노 WAV로. ✅
2. **받아쓰기 → SRT** — `scripts/transcribe.sh` (whisper.cpp large-v3). SRT 타임스탬프는 시퀀스(0 기준)와 일치. ✅
3. **자막 타임라인에 올리기** — `assets/add_subtitles.jsx` (execute_extendscript). SRT import + 캡션 트랙 생성. ✅

→ **수동 드래그 단계 없음.** 3번까지 자동으로 끝난다.

## 핵심: createCaptionTrack (직접 호출)

```javascript
var seq = app.project.activeSequence;
app.project.importFiles(
  ["/tmp/cut_audio.srt"],
  true,
  app.project.rootItem,
  false,
);
// 프로젝트에서 cut_audio.srt projectItem 찾은 뒤:
seq.createCaptionTrack(cap, 0, Sequence.CAPTION_FORMAT_SUBTITLE); // → true
```

- **주의(과거의 함정):** `for (var k in seq)` 로는 `createCaptionTrack`이 **안 보인다**(ExtendScript가
  네이티브 메서드를 열거 안 함). 그래서 "캡션 API 없음"으로 오판하기 쉽다. 실제로는 존재하니 **직접 호출**하면 된다.
- **포맷 상수**: `CAPTION_FORMAT_SUBTITLE`=0(크리에이터 자막, 권장), `_608`=1, `_708`=2(방송용 CC),
  `_TELETEXT`=3, `_OPEN_EBU`=65539, `_OP42`=131075, `_OP47`=196611.
- **startTime** 인자는 초(0). 반환값 `true`면 성공.

## 폴백 (혹시 createCaptionTrack 실패 시)

구버전/예외로 실패하면, SRT는 이미 프로젝트에 import 돼 있으니 사용자가 프로젝트 패널의 `cut_audio.srt`를
타임라인에 드래그(또는 File→Import)하면 된다. 하지만 2025/2026에서는 `createCaptionTrack`이 정상 동작하므로
보통 필요 없다.

## 대안 (선택)

- **번인(하드섭)**: ffmpeg로 SRT를 영상에 태우기 — 프리미어 밖, 편집 불가. 특수 상황에만.
- **텍스트 그래픽 개별 생성**: `add_text_overlay`(MCP)는 2026 버그. 편집 가능한 "캡션"이 아니라 그래픽이 됨. 비권장.
