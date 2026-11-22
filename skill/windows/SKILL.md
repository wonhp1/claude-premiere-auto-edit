---
name: premiere-auto-edit-win
description: >-
  (Windows판, 미검증) Adobe Premiere Pro를 premiere-pro MCP(원본 leancoderkavy/premiere-pro-mcp)의 기본 도구로 조작해
  영상의 무음 구간을 자동 컷편집하고 자막을 단다. 사용자가 "프리미어 무음 잘라줘", "무음 구간 컷편집", "조용한 부분 제거",
  "-30dB 이하 잘라줘", "자막 만들어줘", "받아쓰기", "silence cut", "subtitle" 같은 말을 하거나 프리미어 타임라인의
  무음·여백을 줄이고 싶어 할 때 사용한다. Windows 환경(Python+pip, %APPDATA% 경로)에 맞춰져 있다. 컷은
  ripple_remove_timeline_ranges(dry run 후 적용), 오디오는 export_sequence, 자막은 create_caption_track을 쓴다.
  execute_extendscript와 unsafe-script 권한은 쓰지 않는다. 시작할 때 원본 레포의 최신 버전과 바뀐 도구를 먼저 확인한다.
  모든 산출물은 세션 프로젝트 폴더의 premiere-auto-edit\ 하위에 둔다.
---

# Premiere 무음 컷 + 자막 (Windows판)

> ⚠️ **Windows에서 검증하지 않았다.** macOS(Premiere Pro 2027, premiere-pro-mcp 1.31.0)에서 검증한 `skill/mac`과 같은 MCP 도구·순서를 쓰도록 맞춘 설계본이다. 셸 스크립트 대신 Python을 쓰고, 경로만 Windows에 맞췄다. 막히면 `references/setup-and-troubleshooting-windows.md`를 본다.

## 원본과 검증 버전

- 원본 MCP 서버: https://github.com/leancoderkavy/premiere-pro-mcp (npm `premiere-pro-mcp`)
- 기준 버전과 필수 도구: 이 폴더의 `upstream.json` (macOS 검증 기준 1.31.0, Windows 실측 없음)
- 도구 이름·인자·권한이 이 문서와 다르면 **원본을 따른다.**

## 작업 폴더

모든 산출물은 **세션 프로젝트 폴더** 아래 `premiere-auto-edit\`에 둔다. 이하 `<WORK>`. 경로는 영문으로 둔다(사용자 이름이 한글이면 `%TEMP%` 대신 `C:\premiere-work` 같은 폴더를 쓴다).
Python 스크립트엔 `--workdir <WORK>`, MCP 도구의 경로 인자엔 `C:/.../premiere-auto-edit/...`처럼 슬래시 경로를 넣는다.

## 사전 조건

- premiere-pro MCP 연결: 이 레포의 `premiere-mcp-setup/` 스킬(Windows 메모는 `premiere-mcp-setup/references/windows.md`)
- `pip install faster-whisper "av<16" imageio-ffmpeg` (Python 3 필요)
  - faster-whisper 1.2.1은 PyAV 16 이상에서 `metadata_errors` TypeError로 실패한다(macOS 실측). 그래서 `av<16`을 같이 설치한다.
  - 모델은 처음 쓸 때 내려받는다(small 약 0.5GB, medium 약 1.5GB, large-v3 약 3GB). 1GB가 넘으면 먼저 사용자에게 묻는다.
- ffmpeg: PATH의 ffmpeg 또는 `imageio-ffmpeg`. MCP `detect_silence` 도구는 PATH의 ffmpeg가 있어야 한다(`winget install Gyan.FFmpeg`).
- 한국어 UI에서 실패하는 모션·불투명도·볼륨 단축 도구는 이 스킬에서 쓰지 않는다.

## 0) 원본 최신 상태 확인 (매번 먼저)

```powershell
node "$env:USERPROFILE\.claude\skills\premiere-mcp-setup\scripts\check-upstream.mjs" --baseline "<이 스킬 폴더>\upstream.json"
```

- 새 버전이 있으면 출력된 CHANGELOG 중 `requiredTools`의 도구가 나온 줄을 읽고, 바뀐 도구는 `get_capabilities`(tool_query)로 지금 스키마를 확인해 따른다. 권한이 바뀌어 숨겨진 도구는 사용자에게 알린다. unsafe-script를 대신 켜지 않는다.
- 레포 이름 변경·보관·deprecated 경고가 나오면 진행하기 전에 사용자에게 묻는다.

## 무음 컷

1. **연결과 대상 확인**
   - `verify_premiere_connection` → `overall: ready`
   - `get_project_info` → `path`를 이후 모든 호출의 `expected_project_path`로 그대로 쓴다.
   - `get_active_sequence` → V1 클립의 `name`·`start`·`inPoint`·`end`, `syncCheck.frameTicks`, 시퀀스 `end`, `transitionCount`
   - `detect_silence`(`project_item_id`: V1 클립 이름) → 결과 `mediaPath`가 원본 경로
2. **파라미터**: dB(기본 -30), 최소 길이(기본 2.0초). 사용자가 안 정했으면 제안하고 확인받는다.
3. **무음 감지** — `python scripts/detect_silence.py "<영상경로>" --noise -30 --min-sec 2.0 --workdir "<WORK>"` → `<WORK>\cuts.json` + 요약. 무음이 많으면 요약을 먼저 보여 주고 확인받는다.
4. **타임라인 구간으로 변환** — `python scripts/plan_cut_ranges.py "<WORK>\cuts.json" --frame-ticks <frameTicks> --clip-start <start> --clip-in <inPoint> --clip-end <end> > "<WORK>\cut_plan.json"`
5. **컷** — `chunks`를 배열 순서대로(뒤쪽 묶음부터) 처리한다. 묶음마다:
   - `ripple_remove_timeline_ranges`(`ranges`, `scope: "sync_locked"`, `range_content: "delete"`, `dry_run: true`) → `adjustments`·`clipsRemoved`·`totalRemovedSeconds` 확인
   - 같은 인자 + `dry_run: false` + `confirmation_token` + `idempotency_key`로 적용
   - 거부되면(트랜지션, 잠긴 트랙, 400개 넘는 이동) 사용자에게 알린다. 도구가 없거나 계속 거부되면 대체 경로: `razor_times`마다 `razor_all_tracks` → `get_active_sequence`로 조각 확인 → 지울 조각을 뒤에서부터 `ripple_delete`
6. **확인** — `get_active_sequence`로 V1·A1 클립 수(컷 수+1)와 시퀀스 `end`(컷 전 길이 − `removed_seconds`, 1프레임 이내)를 본다. 결과를 보고하고 저장(`save_project`)은 사용자에게 묻는다.

## 자막

S1. **오디오만 export** — `export_sequence`
  - `output_path`: `C:/.../premiere-auto-edit/cut_audio.wav`
  - `preset_path`: `C:/Program Files/Adobe/Adobe Premiere Pro <버전>/Settings/EncoderPresets/WAV_Mono_16bit_16kHz.epr` (설치 위치를 먼저 확인한다. 없으면 `get_encoder_presets`의 WAV 프리셋)
  - `audio_check: "expect_signal"`, 다시 뽑을 때는 `overwrite: true`
S2. **받아쓰기** — `python scripts/transcribe_words.py "<WORK>/cut_audio.wav" --lang ko --workdir "<WORK>"` → `<WORK>\words.json`. GPU(CUDA)가 있으면 large-v3도 빠르다.
S3. **쉼 기반 1줄 분할** — `python scripts/segment_subtitles.py --workdir "<WORK>" --soft 16 --gap 0.4` → `<WORK>\cut_audio.srt`. 조절: `--gap 0.6`(덜 분리) / `--soft 14`(짧게).
S4. **자막 트랙** — `import_media`로 SRT를 가져와 `nodeId`를 얻고, `create_caption_track`(`action: "import"`, `item_id`, `caption_format: "subtitle"`, `start_seconds: 0`).
  - 결과는 보통 `committed_unverified`다(CEP에 자막 읽기 API가 없음). 실패가 아니다.
  - 화면으로 확인한다. 타임라인 위쪽 `C1 Subtitle` 트랙과 프로그램 모니터의 자막 글자를 스크린샷이나 사용자 확인으로 본다.
  - 다시 실행하면 트랙이 하나 더 생기고, CEP로는 지울 수 없다.

## 막혔을 때

- 타임아웃: `get_bridge_telemetry` → 대화상자면 사용자에게 처리를 부탁한다.
- `HOST_RECOVERY_REQUIRED`: `inspect_operation_recovery` → 실제 상태 재조회 → `acknowledge_operation_recovery`.
- 자세한 내용: `references/setup-and-troubleshooting-windows.md`

## 하지 않을 일

- `execute_extendscript`를 쓰거나 unsafe-script 권한을 켜지 않는다. 예전 ExtendScript는 `legacy/`에 기록으로만 남겼다.
- 옛 CSInterface.js 패치(`legacy/mcp-setup-1.1.1`)를 설치하지 않는다. 최신 커넥터를 망가뜨린다.
- 다른 프로젝트를 건드리지 않는다. 모든 호출에 `expected_project_path` 가드를 넣는다.
