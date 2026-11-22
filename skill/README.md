# premiere-auto-edit — Claude로 Premiere Pro 무음 컷 + 자막 자동화 (스킬)

Claude(Claude Code/Desktop)가 `premiere-pro` MCP로 **Adobe Premiere Pro를 직접 조작**해서:

- 🔇 영상의 **무음 구간 자동 컷편집** (dB·최소 길이 지정 가능, 프레임 단위로 정확)
- 💬 **자막 자동 생성** (시퀀스 오디오 → Whisper 단어 타임스탬프 → 쉼 기반 1줄 SRT → 자막 트랙)

을 수행하는 Claude **스킬**입니다. 편집이 실제 프리미어 타임라인에 반영됩니다.

## 두 가지 버전

| 폴더 | 대상 | 상태 | 구현 |
|---|---|---|---|
| [`mac/`](mac/) | macOS | ✅ **검증됨** (Premiere Pro 2027 27.0.0, premiere-pro-mcp 1.31.0) | bash·Python + MCP 기본 도구 |
| [`windows/`](windows/) | Windows | ✅ **검증됨** (Windows 11, Premiere Pro 2027 27.0.0 한국어 UI, premiere-pro-mcp 1.31.0) | Python + MCP 기본 도구 |

검증 기록: [`../tests/README.md`](../tests/README.md)

## 원본 추적

- 원본 MCP 서버: https://github.com/leancoderkavy/premiere-pro-mcp
- 각 폴더의 `upstream.json`에 검증한 버전(1.31.0)과 이 스킬이 쓰는 도구(`requiredTools`)를 적어 두었습니다.
- 스킬은 시작할 때 `premiere-mcp-setup/scripts/check-upstream.mjs --baseline <스킬>/upstream.json`으로 원본의 최신 버전과 CHANGELOG를 확인하고, 도구·권한이 바뀌었으면 원본을 따릅니다.

## 설치

1. 먼저 레포 최상위의 [`premiere-mcp-setup/`](../premiere-mcp-setup/) 스킬로 MCP를 설치·연결합니다.
2. 자기 OS 폴더를 Claude 스킬 폴더에 복사합니다.
   - macOS: `~/.claude/skills/premiere-auto-edit/`
   - Windows: `%USERPROFILE%\.claude\skills\premiere-auto-edit\`

```bash
# 예 (macOS, 레포 최상위에서)
cp -R skill/mac "$HOME/.claude/skills/premiere-auto-edit"
```

```powershell
# 예 (Windows PowerShell, 레포 최상위에서)
Copy-Item -Recurse skill\windows "$env:USERPROFILE\.claude\skills\premiere-auto-edit"
```

그다음 Claude에게 "이 영상 무음 -30dB로 잘라줘" / "자막 달아줘"라고 하면 스킬이 발동합니다.

## 의존성 (Python 3 필요)

- 컷: `ffmpeg` (macOS `brew install ffmpeg` / Windows `winget install Gyan.FFmpeg` 또는 `pip install imageio-ffmpeg`)
- 자막: `pip install faster-whisper "av<16"` (Windows: `python -m pip install faster-whisper "av<16" imageio-ffmpeg`)
  - faster-whisper 1.2.1은 PyAV 16 이상에서 실패해서 `av<16`을 같이 설치합니다.
  - 모델은 처음 쓸 때 내려받습니다(small 약 0.5GB, medium 약 1.5GB, large-v3 약 3GB). Mac CPU는 medium을 권합니다.
  - Windows판 `transcribe_words.py`는 CUDA로 받아쓰다 실패하면(CUDA 런타임 없는 NVIDIA PC 등) CPU로 자동 전환합니다.

## 동작 원리

```
ffmpeg/Whisper = 귀(무음·음성 인식)   →   Claude = 두뇌(판단)   →   premiere-pro MCP 도구 = 손   →   Premiere = 작업대
```

| 단계 | 로컬 스크립트 | MCP 도구 |
|---|---|---|
| 연결 확인 | — | `verify_premiere_connection`, `get_project_info`, `get_active_sequence` |
| 무음 감지 | `detect_silence.sh` / `detect_silence.py` (ffmpeg) | (`detect_silence`로 원본 경로 확인) |
| 컷 계획 | `plan_cut_ranges.py` (프레임 경계, 50개 묶음) | — |
| 컷 | — | `ripple_remove_timeline_ranges` (dry run → 적용). 대체: `razor_all_tracks` + `ripple_delete` |
| 오디오 export | — | `export_sequence` (`WAV_Mono_16bit_16kHz.epr`) |
| 받아쓰기·분할 | `transcribe_words.py`, `segment_subtitles.py` | — |
| 자막 트랙 | — | `import_media` + `create_caption_track` |

`execute_extendscript`는 쓰지 않습니다. 1.31.0에서 이 도구는 unsafe-script 권한이 있어야 등록되고, 이 스킬은 그 권한을 켜지 않습니다. 예전 ExtendScript 코드는 [`../legacy/extendscript-assets/`](../legacy/extendscript-assets/)에 기록으로만 남겨 두었습니다.

## 라이선스

MIT
