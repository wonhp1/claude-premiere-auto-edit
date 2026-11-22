# Windows에서 설치·연결할 때

이 문서는 macOS 실측 결과와 premiere-pro-mcp README를 바탕으로 썼다. Windows에서는 아직 검증하지 않았다. 경로와 명령은 실제 환경에서 확인하면서 쓰고, 다르면 사용자에게 알린다.

## 준비물

- **Node.js 20.19 이상**: 없으면 `winget install OpenJS.NodeJS.LTS`로 설치한다.
- **ffmpeg·ffprobe**: `trim_clip`, `slip_edit`, `detect_silence`에 필요하다. 없으면 `winget install Gyan.FFmpeg`로 설치한다.
- 설치한 뒤에는 PATH가 반영되도록 새 셸에서 확인한다.

## 설치

```
npm install -g premiere-pro-mcp
premiere-pro-mcp --install-cep
premiere-pro-mcp --diagnose-cep
premiere-pro-mcp --doctor
```

- 커넥터는 `%APPDATA%\Adobe\CEP\extensions\MCPBridgeCEP`에 설치된다.
- PlayerDebugMode는 `HKCU\Software\Adobe\CSXS.<n>`에 `REG_SZ` 값 `1`로 저장된다. 확인: `reg query HKCU\Software\Adobe\CSXS.12 /v PlayerDebugMode`(Premiere가 쓰는 CSXS 번호로)

## Claude Code 등록

npm 전역 명령은 `premiere-pro-mcp.cmd`라서, stdio 서버로 직접 띄우면 실패할 수 있다. 그래서 node와 서버 파일 경로로 등록한다.

1. `premiere-pro-mcp --print-client-config claude`로 `command`(node.exe 경로)와 `args`(`...\premiere-pro-mcp\dist\index.js`)를 확인한다.
2. Premiere 작업 폴더에서 다음을 실행한다.
   `claude mcp add --scope local premiere-pro -- "<node.exe 경로>" "<index.js 경로>"`
3. `claude mcp get premiere-pro`가 Connected인지 확인한다.

`scripts/mcp-call.mjs`는 `npm root -g`로 index.js를 찾아 지금 실행 중인 node로 띄우므로 Windows에서도 같은 방식으로 동작한다.

## 경로 주의

- 사용자 이름에 한글이 있으면 `%USERPROFILE%`과 `%TEMP%`에도 한글이 들어간다.
- 작업 폴더는 `C:\premiere-mcp-test`처럼 영문 경로에 둔다.
- 브리지 임시 폴더(기본 `%TEMP%\premiere-mcp-bridge`)에 비ASCII 문자가 있으면, 영문 경로를 `PREMIERE_TEMP_DIR`로 정한다. 이 값은 MCP 서버 설정과 CEP 패널 설정에 똑같이 넣어야 한다.
- Windows는 macOS와 달리 자모 분리형 저장 문제가 덜할 수 있지만, ExtendScript의 코드 페이지 문제가 생길 수 있으니 영문 경로를 기본으로 한다.

## Premiere 조작 (computer use)

- **설치본 위치**: `C:\Program Files\Adobe\Adobe Premiere Pro 20xx\`
- **종료**: Windows에는 macOS식 앱 메뉴가 없다. `File › Exit`(한국어 UI: `파일 › 종료`)를 쓴다. 종료 전에 사용자 허락을 받는다.
- **패널 메뉴**: macOS와 같다. `Window › Extensions › MCP for Adobe Premiere Pro`이고, 프로젝트가 열려 있어야 나타난다.
- **샘플 미디어**: `C:\Users\Public\Documents\Adobe\Premiere Pro\<버전>\Sample Media` 근처에서 찾는다. 없으면 디스크를 검색한다.
- **CSXS 로그**: `%TEMP%` 아래 `CEP12-PPRO.log` 등을 찾아본다.
