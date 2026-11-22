# Claude × Premiere Pro 자동 편집 툴킷

Claude(Claude Code/Desktop)가 `premiere-pro` MCP로 **Adobe Premiere Pro를 직접 조작**해서
영상의 **무음 구간 자동 컷편집**과 **자막 자동 생성**을 합니다. 편집은 실제 프리미어 타임라인에 반영됩니다.

이 레포에는 **① MCP 설치·연결 스킬**과 **② 편집 스킬**이 함께 들어 있습니다.

## 검증 환경

| 항목 | 값 |
|---|---|
| OS | macOS (Windows는 미검증) |
| Premiere Pro | 2027 (27.0.0, CEP 12), 영어 UI |
| MCP 서버 | [leancoderkavy/premiere-pro-mcp](https://github.com/leancoderkavy/premiere-pro-mcp) 1.31.0 (npm `premiere-pro-mcp`), CEP 브리지 |
| 검증 날짜 | 2026-11-22 |

원본 MCP 서버는 자주 업데이트됩니다. 두 스킬 모두 `upstream.json`에 원본 주소와 검증 버전을 적어 두었고, 시작할 때 원본의 최신 버전과 변경 기록을 확인한 뒤 바뀐 점이 있으면 원본을 따릅니다.

## 설치 순서

### 1단계 — `premiere-mcp-setup/`: MCP 설치와 Premiere 연결

스킬 폴더에 복사한 뒤 Claude에게 "프리미어 MCP 설치해줘"라고 하면 됩니다. 원본 최신 버전 확인 → 점검 → 설치 → Claude Code 등록 → (computer use로) Premiere 패널 열기 → 연결 확인(`verify_premiere_connection` = `overall: ready`)까지 진행합니다.

```bash
cp -R premiere-mcp-setup "$HOME/.claude/skills/premiere-mcp-setup"
```

직접 하려면 원본 README의 순서를 따릅니다.

```bash
npm install -g premiere-pro-mcp
premiere-pro-mcp --install-cep
claude mcp add --scope local premiere-pro -- "$(command -v premiere-pro-mcp)"
```

설치 후 Premiere를 다시 켜고 프로젝트를 열면 연결됩니다(커넥터가 백그라운드로 자동 실행). 자세한 내용: [`premiere-mcp-setup/SKILL.md`](premiere-mcp-setup/SKILL.md)

> ⚠️ 예전 `mcp-setup/`(CSInterface.js 패치)은 **npm 1.1.1 전용**이라 [`legacy/mcp-setup-1.1.1/`](legacy/mcp-setup-1.1.1/)로 옮겼습니다. 1.31.0 이상에서 쓰면 최신 커넥터를 옛 파일로 덮어써 망가뜨립니다. 쓰지 마세요.

### 2단계 — `skill/`: 편집 자동화 스킬

```bash
# macOS (검증됨)
cp -R skill/mac "$HOME/.claude/skills/premiere-auto-edit"

# Windows (미검증) — %USERPROFILE%\.claude\skills\premiere-auto-edit\ 에 skill\windows\ 내용 복사
```

의존성: `ffmpeg`, Python 3, `pip install faster-whisper "av<16"`

그다음 Claude에게 **"이 영상 무음 -30dB로 잘라줘"**, **"자막 달아줘"**라고 하면 스킬이 발동합니다. 자세한 내용: [`skill/README.md`](skill/README.md)

## 주의: 한국어 UI와 한글 경로

- **한글 경로는 피하세요.** macOS는 한글 파일 이름을 자모 분리형(NFD)으로 저장하고, 입력한 경로는 완성형(NFC)입니다. 그래서 MCP의 프로젝트 가드(`expected_project_path`)가 같은 프로젝트를 다른 프로젝트로 보고 거부합니다. 작업 폴더와 프로젝트 파일 이름을 영문으로 두면 해결됩니다.
- **한국어 UI에서는 MCP 도구 28개가 실패합니다.** 도구가 'Opacity', 'Volume', 'Lumetri Color' 같은 영어 이름으로 속성을 찾기 때문입니다(모션·불투명도·볼륨 단축 도구, `color_correct`, `add_caption_graphics` 등). 이 레포의 편집 스킬은 그 도구들을 쓰지 않으므로 한국어 UI에서도 동작합니다. 다른 작업까지 하려면 영어 UI를 권합니다. UI 언어 바꾸는 법: [`premiere-mcp-setup/references/known-issues.md`](premiere-mcp-setup/references/known-issues.md)

## 테스트 결과 요약

### premiere-pro-mcp 1.31.0 전체 도구 (453개)

| UI | 성공 | 부분 | 실패 | 건너뜀 |
|---|---:|---:|---:|---:|
| 한국어 | 362 | 30 | 43 | 18 |
| 영어 | 390 | 26 | 19 | 18 |

- 453개 = 등록 451 + unsafe-script 권한이 있어야 등록되는 2개(`execute_extendscript` 등)
- 건너뜀: After Effects 필요, UXP 필요, 외부 업로드, CC Libraries, unsafe-script
- 언어와 상관없이 남은 실패: 설계상 미지원 10개, Premiere 2027 API 문제 7개 등. 목록은 [`premiere-mcp-setup/references/known-issues.md`](premiere-mcp-setup/references/known-issues.md)

### 이 레포 편집 스킬 (실제 영상)

테스트 영상(30.4초, 긴 무음 4개 + 남겨야 할 1초 쉼)으로 검증했습니다. 상세: [`tests/README.md`](tests/README.md)

| 항목 | 결과 |
|---|---|
| 무음 컷 (29.97·23.976fps, `ripple_remove_timeline_ranges`) | 감지 4 / 잘림 4, 30.4초 → 20.3초, 모든 컷 경계가 기대값과 0프레임 차이 |
| 무음 컷 (30fps, `razor_all_tracks` + `ripple_delete`) | 감지 4 / 잘림 4, 0프레임 차이 |
| 오디오 export (`export_sequence`) | 16kHz 모노 WAV(오디오만), 길이 일치 |
| 자막 (`create_caption_track`) | 자막 트랙 생성, 큐 8개를 화면에서 확인 (도구 자체는 확인 API가 없어 `committed_unverified`) |

## 구성

```
.
├─ premiere-mcp-setup/   ① MCP 설치·연결 스킬 (원본 추적 check-upstream.mjs, Premiere 켜기 ensure-premiere.mjs, 점검·호출 스크립트, 알려진 문제)
├─ skill/                ② 편집 스킬
│  ├─ mac/               ✅ 검증됨
│  └─ windows/           ⚠️ 미검증
├─ tests/                실제 영상 검증 스크립트와 결과
└─ legacy/               npm 1.1.1 시절 파일 (쓰지 말 것)
```

## 예전 버전과 달라진 점

- 예전 스킬은 Premiere 2026에서 MCP 기본 도구(`razor_all_tracks`, `ripple_delete` 등)가 "성공만 보고하고 실제로는 동작하지 않아" 모든 편집을 `execute_extendscript`로 직접 처리했습니다.
- premiere-pro-mcp 1.31.0에서는 이 도구들이 실제로 동작하고 결과를 다시 읽어 확인하며, 실측에서 프레임 단위로 정확했습니다. 반대로 `execute_extendscript`는 unsafe-script 권한이 있어야 등록되도록 바뀌었습니다.
- 그래서 편집 스킬을 기본 도구(`ripple_remove_timeline_ranges`, `export_sequence`, `create_caption_track`)로 바꿨습니다. 무음 감지(ffmpeg), faster-whisper 단어 타임스탬프, 쉼 기반 자막 분할은 그대로입니다.

## 라이선스

MIT
