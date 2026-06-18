---
name: premiere-auto-edit
description: >-
  Adobe Premiere Pro를 premiere-pro MCP로 직접 조작해 영상의 무음 구간을 자동으로 컷편집한다.
  사용자가 "프리미어 무음 잘라줘", "무음 구간 컷편집", "침묵/조용한 부분 제거", "-30dB 이하 잘라줘",
  "프리미어로 자동 편집", "silence cut", "프리미어 컷편집 자동화", "영상에서 빈 부분 빼줘" 같은 말을
  하거나, 프리미어 타임라인의 무음·여백·쉼을 줄여 영상을 짧게 만들고 싶어 할 때 반드시 사용한다.
  프리미어를 Claude가 직접 제어해 타임라인에서 실시간으로 컷이 적용되는 게 특징이다. dB 임계값과
  최소 무음 길이는 사용자 요청대로 조절한다. 자막 생성도 지원한다("자막 만들어줘", "자막 달아줘",
  "받아쓰기", "subtitle", "캡션") — 시퀀스 오디오 export → faster-whisper 단어 타임스탬프 → 쉼 기반 1줄 분할 →
  createCaptionTrack 으로 타임라인에 자막을 정확한 타이밍으로 자동 생성까지 전부 자동(수동 드래그 불필요). 모든 편집은
  MCP 기본 도구 대신 execute_extendscript 직접 호출로 처리한다(2026에서 기본 도구가 버그라서).
---

# Premiere 무음 자동 컷편집

영상의 조용한(무음) 구간을 ffmpeg로 감지하고, Premiere Pro 타임라인에서 직접 잘라 제거한다.
결과는 실제 Premiere 시퀀스에 실시간으로 반영되므로, 사용자가 타임라인에서 바로 보고 다듬을 수 있다.

## 동작 원리 (역할 분담)

Claude는 영상을 직접 듣지 못하므로 도구로 정보를 뽑아 판단·편집한다:

- **ffmpeg** = 귀 (어디가 조용한지 = 무음 타임스탬프)
- **Claude** = 두뇌+손 (어디를 자를지 결정 → 프리미어에 정확한 컷 명령)
- **Premiere(QE DOM)** = 작업대 (실제로 타임라인이 잘림)

## 사전 조건

- `premiere-pro` MCP가 연결돼 있고, Premiere에 **시퀀스(타임라인)** 가 열려 있어야 한다.
- 처음 쓰는 환경이면 연결/패치가 안 돼 있을 수 있다 → `references/setup-and-troubleshooting.md` 참고.

## 절차

### 0) 연결 확인 (항상 먼저)

`execute_extendscript`로 다음을 실행해 실제 값이 오는지 본다:

```javascript
return __result({
  v: app.version,
  hasSeq: app.project.activeSequence ? true : false,
  media: app.project.activeSequence
    ? app.project.activeSequence.videoTracks[0].clips[0].projectItem.getMediaPath()
    : null,
});
```

- `null`/타임아웃 → 연결 또는 CSInterface.js 패치 문제. `references/setup-and-troubleshooting.md`의 CSInterface.js 절을 따른다.
- `hasSeq:false` → 사용자에게 타임라인에 영상을 올려달라고 요청.
- `media` → 원본 파일 경로. 무음 감지에 이 파일을 쓴다.

### 1) 파라미터 확인

사용자가 dB나 최소 길이를 지정했으면 그대로 쓴다. 안 했으면 기본값을 제안하고 확인받는다:

- **noise dB** (기본 -30): 낮을수록(-40) 보수적=적게 자름, 높을수록(-20) 공격적=많이 자름(조용한 말까지).
- **최소 무음 길이** (기본 2.0초): 길수록 큰 쉼만, 짧을수록 잔 끊김 많음.

무음이 매우 많은 영상(예: 60%+)이면 컷이 수십~수백 개가 될 수 있다. 먼저 2)의 요약을 보여주고
"이대로 진행할까요?" 확인하면 사용자가 놀라지 않는다.

### 2) 무음 감지 → 컷 목록 생성

`scripts/detect_silence.sh`를 실행한다 (스킬 디렉터리 기준 경로 사용):

```bash
bash <skill-dir>/scripts/detect_silence.sh "<영상경로>" <dB> <최소초> [pad]
# 예: bash .../detect_silence.sh "/Users/me/Desktop/clip.mov" -30 2.0
```

→ `/tmp/premiere_cuts.json` 에 컷 구간이 저장되고, 감지 개수·제거 시간·예상 결과 길이가 출력된다.
이 요약을 사용자에게 보여준다.

### 3) 일괄 컷 실행

`assets/cut_silence.jsx` 파일을 읽어 그 내용을 `execute_extendscript`의 `code`로 그대로 실행한다.
오래 걸릴 수 있으니 `timeout_ms`를 넉넉히(예: 240000) 준다.

이 스크립트는 `/tmp/premiere_cuts.json`을 읽어 V1·A1에서 각 구간을 프레임 정확하게 razor +
ripple delete 한다(역순 처리). 결과로 `{done, fail, resultMinutes}` 등을 돌려준다.

### 4) 결과 보고

`done/total`, 결과 길이(분), 실패가 있으면 그 구간을 보고한다. 사용자에게 타임라인을 확인·재생해보라고 안내하고,
원하면 ⌘S 저장 또는 되돌리기(troubleshooting 참고)를 알려준다.

## 중요 — 왜 MCP 기본 도구를 안 쓰는가

Premiere 2026에서 MCP의 `razor_all_tracks` / `ripple_delete` / `add_text_overlay`는 "성공" 응답만 주고
실제로는 동작하지 않는다. 그래서 이 스킬은 `execute_extendscript`로 **QE DOM을 직접** 호출한다.
프레임 정확도(비표준 fps 대응)의 핵심 기법은 `assets/cut_silence.jsx` 주석과
`references/setup-and-troubleshooting.md`에 정리돼 있다. 컷이 "성공인데 안 잘리면" 이 방식인지 먼저 확인한다.

## 자막 생성 (단어 타임스탬프 → 1줄 자막, 완전 자동)

자막은 "지금 타임라인"의 오디오에 맞아야 한다. AI 컷 후 사람이 더 다듬었을 수도 있으므로,
낡은 `cuts.json`이 아니라 **현재 시퀀스를 그대로 export** 해서 그 오디오를 받아쓴다.
산출물(`cut_audio.wav`, `words.json`, `cut_audio.srt`)은 작업 폴더에 둔다(아래 `<WORK>`; Mac은 `/tmp` 기본).

### S1) 현재 시퀀스 오디오만 export

`assets/export_sequence_audio.jsx`를 `execute_extendscript`로 실행 (timeout 예: 180000).
→ `<WORK>/cut_audio.wav` (16kHz 모노). 오디오만이라 빠르고, 현재 타임라인을 정확히 반영.
(MCP export 도구는 2026 불안정 → `exportAsMediaDirect` 직접 호출.)

### S2) 단어별 받아쓰기 → words.json

```bash
python <skill-dir>/scripts/transcribe_words.py <WORK>/cut_audio.wav --lang ko --workdir <WORK>
```

→ faster-whisper(`word_timestamps`)로 **정확한 단어 시간**을 어절 단위 `<WORK>/words.json`로.
GPU 있으면 빠름. **Mac CPU는 large-v3가 느림(~20분)** — 급하면 `--model medium`. (pip install faster-whisper 필요)

### S3) 1줄 자막으로 분할 → SRT

```bash
python <skill-dir>/scripts/segment_subtitles.py --workdir <WORK> --soft 16
```

→ 실제 **쉼(pause)·연결어미** 기준으로 자연스럽게 1줄씩 분할, 정확한 타이밍으로 `<WORK>/cut_audio.srt` 생성.
1줄 고정 + 길이는 내용 따라 적응(soft 상한만 화면 넘침 방지). 사용자가 "더 짧게"면 `--soft` 낮춤.

### S4) 자막을 타임라인에 올리기 (완전 자동)

`assets/add_subtitles.jsx`를 `execute_extendscript`로 실행. SRT를 import 하고
`createCaptionTrack(cap, 0, Sequence.CAPTION_FORMAT_SUBTITLE)`로 **자막 트랙을 자동 생성**한다. 수동 드래그 불필요.

> 참고: `createCaptionTrack`은 `for..in`엔 안 보이는 네이티브 메서드지만 동작한다.
> `CAPTION_FORMAT_SUBTITLE`(0)=크리에이터 자막, `_708`(2)=방송 CC. 자세한 건 `references/subtitles.md`.

### 옵션

- 언어/번역: `transcribe_words.py --lang en` 등.
- 자막 길이: `segment_subtitles.py --soft 14`(짧게) ~ `--soft 18`(여유).
- 속도 우선(Mac): `transcribe_words.py --model medium`.
