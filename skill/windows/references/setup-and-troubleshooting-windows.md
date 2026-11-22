# Windows 설정과 문제 해결

> ⚠️ **미검증**: 이 Windows 버전은 macOS 검증본(premiere-pro-mcp 1.31.0, Premiere Pro 2027)과 같은 MCP 도구를 쓰도록 맞춘 설계본이다. 실제 Windows에서는 아직 확인하지 않았다. 동작 보고·수정 환영.

## 의존성 (pip 중심)

Windows에는 brew가 없으므로 Python + pip로 통일한다. 전제는 Python 3(python.org 또는 `winget install Python.Python.3`).

```powershell
pip install faster-whisper "av<16" imageio-ffmpeg
```

- `faster-whisper`: 받아쓰기. 모델은 첫 실행 때 `%USERPROFILE%\.cache\huggingface`에 내려받는다.
- `av<16`: faster-whisper 1.2.1이 PyAV 16 이상에서 `metadata_errors` TypeError로 실패한다(macOS 실측).
- `imageio-ffmpeg`: `detect_silence.py`용 ffmpeg. MCP `detect_silence` 도구는 PATH의 ffmpeg가 필요하므로 `winget install Gyan.FFmpeg`도 권한다.
- GPU(CUDA)가 있으면 faster-whisper가 자동으로 쓰고, 없으면 CPU(int8).

## premiere-pro MCP 연결

설치·등록·연결 확인은 이 레포의 `premiere-mcp-setup/` 스킬을 따른다. Windows 메모는 `premiere-mcp-setup/references/windows.md`에 있다.

- `npm install -g premiere-pro-mcp` → `premiere-pro-mcp --install-cep`
- 커넥터: `%APPDATA%\Adobe\CEP\extensions\MCPBridgeCEP`
- npm 전역 명령이 `.cmd`라서 Claude Code에는 node 경로와 `dist\index.js` 경로로 등록한다.
- **옛 CSInterface.js 패치·manifest 수정은 하지 않는다.** npm 1.1.1 전용이었고(`legacy/mcp-setup-1.1.1`), 1.31.0에서는 최신 커넥터를 옛 파일로 덮어써 망가뜨린다.

## 경로(workdir)

- 산출물(`cuts.json`, `cut_plan.json`, `cut_audio.wav`, `words.json`, `cut_audio.srt`)은 세션 프로젝트 폴더 아래 `premiere-auto-edit\`에 둔다.
- MCP 도구에 넘기는 경로는 슬래시(`C:/Users/me/proj/premiere-auto-edit/cut_audio.wav`)로 쓴다.
- 사용자 이름에 한글이 있으면 `%USERPROFILE%`·`%TEMP%`에도 한글이 들어간다. 작업 폴더와 프로젝트는 영문 경로에 둔다.
- `expected_project_path`에는 `get_project_info`가 돌려준 `path`를 그대로 넣는다.

## 오디오 프리셋

- Premiere 설치본: `C:\Program Files\Adobe\Adobe Premiere Pro <버전>\Settings\EncoderPresets\WAV_Mono_16bit_16kHz.epr` (macOS에서는 같은 이름의 파일이 설치본 안에 있었다. Windows 위치는 확인 필요)
- `get_encoder_presets`는 Media Encoder 폴더만 훑는다. 16kHz 프리셋이 목록에 없어도 위 파일 경로를 직접 넘길 수 있다.

## 증상별

| 증상 | 해결 |
|---|---|
| `verify_premiere_connection`이 커넥터 응답 없음 | Premiere 실행·대화상자 확인, `get_bridge_telemetry`. 가드를 넣을 때만 그렇다면 경로 문자열 불일치 |
| 도구가 30초 타임아웃 | 대화상자가 막음. 사용자에게 처리 부탁 → `get_last_operations` 확인 후 재시도 |
| `HOST_RECOVERY_REQUIRED` | `inspect_operation_recovery` → 상태 재조회 → `acknowledge_operation_recovery` |
| 컷 도구 거부 | 트랜지션, 잠긴 트랙, sync lock, 400개 넘는 이동(`allow_large_ripple`) |
| 자막 도구가 `committed_unverified` | 정상(CEP에 자막 읽기 API 없음). 화면으로 확인 |
| `python`/`pip` 없음 | python.org 또는 winget으로 Python 설치 |
| faster-whisper 설치 실패 | Visual C++ 재배포 패키지가 필요할 수 있다 / `pip install --upgrade pip` 후 재시도 |
