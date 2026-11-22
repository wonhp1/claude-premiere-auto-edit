# make_test_media.ps1 — 무음 컷·자막 검증용 테스트 영상을 만든다 (Windows: System.Speech TTS + ffmpeg).
# make_test_media.sh(macOS)와 같은 구성을 Windows에서 만든다.
#
# 사용법: powershell -ExecutionPolicy Bypass -File make_test_media.ps1 -Out <출력폴더> [-Samples <샘플영상폴더>] [-Voice <음성 이름>]
# 출력:  speech.wav (48kHz 모노 원본 오디오), layout.json (말·쉼 구간 설계값),
#        test_2997.mp4 (29.97fps), test_23976.mp4 (23.976fps), test_30.mp4 (30fps)
#
# 구성: 말 5덩어리(한국어, 기본 "Microsoft Heami Desktop" 음성) 사이에 2.0/3.0/2.5/2.2초 무음, 3번째 덩어리 안에는 1.0초 짧은 쉼.
#       기본 설정(-30dB, 2.0초)이면 긴 무음 4개만 잘리고 1.0초 쉼은 남아야 한다.
#       Windows TTS는 문장 앞뒤에 약간의 무음을 붙이므로 실제 무음은 설계값보다 조금 길다(layout.json은 파일 경계 기준).
# 주의: 이 파일은 BOM 붙은 UTF-8로 저장해야 Windows PowerShell 5.1이 한글을 깨뜨리지 않는다.
param(
  [Parameter(Mandatory = $true)][string]$Out,
  [string]$Samples = "",
  [string]$Voice = "Microsoft Heami Desktop"
)
$ErrorActionPreference = "Stop"

if (-not $Samples) {
  $root = "C:\Users\Public\Documents\Adobe\Premiere Pro"
  $Samples = Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
    Sort-Object { [version]($_.Name -replace '[^\d.]', '') } -Descending |
    ForEach-Object { Join-Path $_.FullName "Sample Media" } |
    Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $Samples) { throw "Premiere 샘플 미디어 폴더를 찾지 못함. -Samples로 지정하세요." }
}
foreach ($exe in "ffmpeg", "ffprobe") {
  if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { throw "$exe 없음 (winget install Gyan.FFmpeg)" }
}

$parts = Join-Path $Out "parts"
New-Item -ItemType Directory -Force $parts | Out-Null
Add-Type -AssemblyName System.Speech
$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer
$syn.SelectVoice($Voice)

function Spk($text, $name) {
  $tmp = Join-Path $parts "$name.raw.wav"
  $syn.SetOutputToWaveFile($tmp); $syn.Speak($text); $syn.SetOutputToNull()
  ffmpeg -v error -y -i $tmp -ar 48000 -ac 1 -c:a pcm_s16le (Join-Path $parts "$name.wav")
  Remove-Item $tmp
}
function Sil($sec, $name) {
  ffmpeg -v error -y -f lavfi -i "anullsrc=r=48000:cl=mono" -t $sec -c:a pcm_s16le (Join-Path $parts "$name.wav")
}

Spk "안녕하세요. 오늘은 프리미어 자동 편집을 테스트합니다." u1
Spk "무음 구간을 찾아서 자동으로 잘라내는 기능입니다." u2
Spk "말하는 사이에" u3a
Spk "이삼 초 정도 쉬는 구간을 넣었습니다." u3b
Spk "자막은 위스퍼로 받아쓰기한 뒤 타임라인에 올립니다." u4
Spk "테스트가 끝나면 결과를 확인해 주세요." u5
Sil 0.5 lead; Sil 2.0 g1; Sil 3.0 g2; Sil 1.0 g3s; Sil 2.5 g3; Sil 2.2 g4; Sil 0.6 tail
$syn.Dispose()

$order = "lead u1 g1 u2 g2 u3a g3s u3b g3 u4 g4 u5 tail".Split(" ")
$t = 0.0; $rows = @(); $list = @()
foreach ($n in $order) {
  $d = [double](ffprobe -v error -show_entries format=duration -of csv=p=0 (Join-Path $parts "$n.wav"))
  $rows += [ordered]@{ part = $n; start = [math]::Round($t, 4); end = [math]::Round($t + $d, 4) }
  $t += $d; $list += "file '$n.wav'"
}
$utf8 = New-Object System.Text.UTF8Encoding $false
[IO.File]::WriteAllText((Join-Path $Out "layout.json"), ([ordered]@{ total = [math]::Round($t, 4); parts = $rows } | ConvertTo-Json -Depth 4), $utf8)
[IO.File]::WriteAllLines((Join-Path $parts "list.txt"), $list, $utf8)
ffmpeg -v error -y -f concat -safe 0 -i (Join-Path $parts "list.txt") -c:a pcm_s16le (Join-Path $Out "speech.wav")
$dur = ffprobe -v error -show_entries format=duration -of csv=p=0 (Join-Path $Out "speech.wav")

# 샘플 영상 2개를 이어 붙여 음성 길이만큼 자른다(샘플 클립 자체 오디오는 무음이라 버린다).
foreach ($spec in @(@("30000/1001", "2997"), @("24000/1001", "23976"), @("30", "30"))) {
  $r = $spec[0]; $tag = $spec[1]
  $fc = "[0:v]scale=1920:1080,setsar=1,fps=$r[a];[1:v]scale=1920:1080,setsar=1,fps=$r[b];[a][b]concat=n=2:v=1:a=0[v]"
  ffmpeg -v error -y -i (Join-Path $Samples "Sample Media Clip 1.mp4") -i (Join-Path $Samples "Sample Media Clip 10.mp4") -i (Join-Path $Out "speech.wav") `
    -filter_complex $fc -map "[v]" -map 2:a -t $dur -r $r -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p `
    -c:a aac -b:a 192k -ar 48000 -ac 2 (Join-Path $Out "test_$tag.mp4")
}
Remove-Item -Recurse -Force $parts
Get-ChildItem $Out | Select-Object Name, Length
