# Claude × Premiere Pro 자동 편집 툴킷

Claude(Claude Code/Desktop)가 `premiere-pro` MCP로 **Adobe Premiere Pro를 직접 조작**해서
영상의 **무음 구간 자동 컷편집**과 **자막 자동 생성**을 수행합니다. 편집이 실제 프리미어 타임라인에 반영됩니다.

이 레포 하나에 **① 연결 셋업**과 **② 편집 스킬**이 모두 들어 있습니다. 아래 순서대로 설치하세요.

---

## 설치 순서 (2단계)

### 1단계 — `mcp-setup/` : 클로드 ↔ 프리미어 연결 (필수 토대)

먼저 이걸 해야 프리미어가 클로드 명령에 응답합니다. Premiere 2025/2026의 CEP 12 `evalScript` 버그를
고치는 패치가 핵심입니다.

```bash
npm install -g premiere-pro-mcp
premiere-pro-mcp --install-cep
bash mcp-setup/install.sh        # CSInterface.js 패치 + 설정 등록 (macOS)
```

→ 자세한 내용·Windows 안내: [`mcp-setup/README.md`](mcp-setup/README.md)

> ⚠️ 이 단계 없이는 **아무것도 안 됩니다** (모든 명령이 undefined/타임아웃).

### 2단계 — `skill/` : 편집 자동화 스킬

자기 OS 폴더를 Claude 스킬 폴더에 복사합니다.

```bash
# macOS (검증됨)
cp -R skill/mac "$HOME/.claude/skills/premiere-auto-edit"

# Windows (미검증 — 설계본)
# %USERPROFILE%\.claude\skills\premiere-auto-edit\ 에 skill\windows\ 내용 복사
```

→ 자세한 내용: [`skill/README.md`](skill/README.md)

그다음 Claude에게 **"이 영상 무음 -30dB로 잘라줘"**, **"자막 달아줘"** 라고 하면 스킬이 자동 발동합니다.

---

## 구성

```
.
├─ mcp-setup/     ① 연결 + CSInterface.js 패치 (install.sh, 진단 패널, 문제해결)
└─ skill/         ② 편집 스킬
   ├─ mac/        ✅ 검증됨 (bash + ExtendScript, Premiere 2025/2026)
   └─ windows/    ⚠️ 미검증 (Python + ExtendScript, 크로스플랫폼 설계)
```

## 동작 원리

```
ffmpeg/Whisper = 귀(무음·음성 인식)  →  Claude = 두뇌+손(판단·명령)  →  Premiere = 작업대
```

Claude는 영상을 직접 듣지 못하므로, ffmpeg(무음 타임스탬프)·Whisper(받아쓰기)로 정보를 뽑은 뒤
`execute_extendscript`로 프리미어를 직접 편집합니다.

## 핵심 기술 메모

- **MCP 기본 편집 도구는 2026에서 버그**(성공 보고만, 미실행) → 모든 편집은 `execute_extendscript` 직접 호출.
- **프레임 정확 컷**(비표준 fps): `setPlayerPosition(frameTicks)` → `CTI.timecode` → `razor(tc)`, ripple는 `qeItem.remove(true,true)`.
- **오디오 export**: `exportAsMediaDirect(out, WAV_Mono_16bit_16kHz.epr, 0)` — 현재 타임라인 그대로(사람이 다듬어도 정확).
- **자막 한계**: 캡션 트랙은 스크립트로 못 올림(2026 API 미노출) → SRT import 후 타임라인 드래그 1회 수동.

## 의존성

- 공통: Node.js(MCP), `premiere-pro-mcp`
- macOS: `brew install ffmpeg whisper-cpp` (+ ggml large-v3 모델)
- Windows: `pip install faster-whisper imageio-ffmpeg` (Python3, 모델 자동 다운로드)

## 라이선스

MIT
