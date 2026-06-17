# 자막(캡션) 삽입 — 검증된 방법과 한계

## 전체 흐름 (대부분 스크립트로 자동화됨)

1. **오디오 export** — `assets/export_sequence_audio.jsx` (execute_extendscript). 현재 시퀀스를 16kHz 모노 WAV로. ✅ 스크립트
2. **받아쓰기 → SRT** — `scripts/transcribe.sh` (whisper.cpp large-v3). SRT 타임스탬프는 시퀀스(0 기준)와 일치. ✅ 스크립트
3. **SRT를 프로젝트로 import** — ExtendScript로 자동. ✅ 스크립트
   ```javascript
   app.project.importFiles(
     ["/tmp/cut_audio.srt"],
     true,
     app.project.rootItem,
     false,
   );
   // → 프로젝트 패널에 "cut_audio.srt" 캡션 아이템 생성 (type 1, 미디어경로가 .srt)
   ```
4. **타임라인에 얹기** — ⚠️ **스크립트 불가(현재)**. 아래 참고.

## ⚠️ 한계: 캡션 트랙은 스크립트로 못 올린다 (Premiere 2025/2026)

검증 결과, 이 버전들은 캡션 트랙 API를 스크립트에 노출하지 않는다:

- DOM `Sequence` 에 caption 관련 메서드/속성 없음 (`seqCaptionProps` 비어 있음).
- QE `getActiveSequence()` 에도 caption 메서드 없음, `numCaptionTracks` undefined.
- 비디오 트랙에 `overwriteClip(captionItem, 0)` 하면 `ok` 는 뜨지만 실제로 안 올라감(clips 그대로 0).
- (조사: 커뮤니티에서도 `captionTrack.getItems is not a function` 등 보고)

## 폴백 (확실히 동작): 사용자 1동작

SRT 는 이미 프로젝트에 import 돼 있으므로, 사용자가:

- 프로젝트 패널의 `cut_audio.srt` 를 **타임라인으로 드래그**, 또는
- 메뉴 **File → Import** 로 `/tmp/cut_audio.srt` 를 가져온 뒤 타임라인에 올림.

→ 캡션 트랙이 생기고 자막이 뜬다. 시간축이 이미 맞으므로 정렬 정확. 편집 가능한 정식 캡션.

스킬 사용 시: 3번까지 자동 실행한 뒤, 사용자에게 "프로젝트 패널의 cut_audio.srt 를 타임라인에 드래그하세요" 라고 안내한다. SRT 경로(`/tmp/cut_audio.srt`)도 함께 알려준다.

## 대안 (선택, 더 복잡)

- **텍스트 그래픽(MOGRT/타이틀)을 자막마다 생성**: `add_text_overlay` 는 2026 버그. 직접 ExtendScript 로
  Essential Graphics 텍스트를 만드는 건 가능하나 복잡하고, 편집 가능한 "캡션"이 아니라 그래픽이 된다.
  대량 자막엔 비권장.
- **번인(하드섭)**: ffmpeg 로 SRT 를 영상에 태워버리기. 프리미어 밖에서 처리. 편집 불가.

→ 대부분의 경우 **SRT import + 드래그** 가 가장 깔끔하다. 향후 Premiere 가 캡션 스크립팅을 노출하면
4번도 자동화로 승격한다.
