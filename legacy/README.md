# legacy — 옛 버전 기록 (쓰지 말 것)

이 폴더는 **premiere-pro-mcp 1.1.1 시절**(Premiere Pro 2025/2026)에 쓰던 파일을 기록으로 남긴 것이다.
**1.31.0 이상에서는 쓰지 않는다.** 최신 버전 설치·연결은 레포 최상위의 [`premiere-mcp-setup/`](../premiere-mcp-setup/)을, 자동 편집은 [`skill/`](../skill/)을 쓴다.

| 폴더 | 원래 용도 | 지금 쓰면 안 되는 이유 |
|---|---|---|
| [`mcp-setup-1.1.1/`](mcp-setup-1.1.1/) (예전 `mcp-setup/`) | npm 1.1.1의 CSInterface.js `evalScript` 버그 패치, manifest 수정, Claude Desktop 설정 | 1.31.0은 이미 고쳐져 있다. 패치를 덮어쓰면 최신 커넥터가 옛 파일로 되돌아가 망가진다. `install.sh`는 이제 1.1.1이 아니면 멈춘다 |
| [`extendscript-assets/`](extendscript-assets/) (예전 `skill/*/assets/`) | `execute_extendscript`로 실행하던 컷·오디오 export·자막 ExtendScript | 1.31.0에서 `execute_extendscript`는 unsafe-script 권한이 있어야 등록된다. 같은 일을 기본 도구(`ripple_remove_timeline_ranges`, `export_sequence`, `create_caption_track`)가 한다 |

ExtendScript 쪽 기법(프레임 경계 ticks → `CTI.timecode` → QE `razor`, `createCaptionTrack`)은 참고용으로 남겨 두었다.
