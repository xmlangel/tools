# CLI 도구 사용법

이 문서는 독립 실행형 명령줄 도구의 사용 방법을 설명합니다.

## 📋 목차

- [youtube_stt.py - YouTube STT 도구](#youtube_sttpy---youtube-stt-도구)
- [youtube_subtitle_downloader.py - 자막 다운로더](#youtube_subtitle_downloaderpy---자막-다운로더)
- [translate_release_notes.py - 릴리스 노트 번역](#translate_release_notespy---릴리스-노트-번역)

---

## youtube_stt.py - YouTube STT 도구

YouTube 동영상의 음성을 텍스트로 변환하는 CLI 도구입니다.

### 기본 사용법

```bash
python youtube_stt.py <VIDEO_URL> [OPTIONS]
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--model` | Whisper 모델 (tiny/base/small/medium/large) | `base` |
| `--language` | 음성 언어 코드 (en, ko, ja 등) | 자동 감지 |
| `--output-format` | 출력 형식 (txt/srt/vtt/json) | `txt` |
| `--output`, `-o` | 출력 파일 경로 | 자동 생성 |
| `--device` | 사용할 디바이스 (cpu/cuda) | `cpu` |
| `--verbose`, `-v` | 상세 로그 출력 | `False` |

### 사용 예제

#### 1. 기본 사용 (base 모델, 자동 언어 감지)

```bash
python youtube_stt.py "https://youtu.be/dQw4w9WgXcQ"
```

출력:
```
Downloading video...
Extracting audio...
Transcribing with Whisper (base model)...
Detected language: English
[00:00.000] Never gonna give you up
[00:03.500] Never gonna let you down
...
Saved to: dQw4w9WgXcQ_transcript.txt
```

#### 2. 한국어 동영상, medium 모델 사용

```bash
python youtube_stt.py "https://youtu.be/VIDEO_ID" \
  --model medium \
  --language ko
```

#### 3. SRT 자막 파일로 저장

```bash
python youtube_stt.py "https://youtu.be/VIDEO_ID" \
  --output-format srt \
  --output subtitles.srt
```

#### 4. GPU 가속 사용 (CUDA 사용 가능 시)

```bash
python youtube_stt.py "https://youtu.be/VIDEO_ID" \
  --model large \
  --device cuda \
  --verbose
```

#### 5. JSON 형식으로 타임스탬프 포함

```bash
python youtube_stt.py "https://youtu.be/VIDEO_ID" \
  --output-format json \
  --output transcript.json
```

### 출력 형식 예제

#### TXT 형식
```
[00:00.000 --> 00:03.500] Never gonna give you up
[00:03.500 --> 00:06.800] Never gonna let you down
[00:06.800 --> 00:10.200] Never gonna run around and desert you
```

#### SRT 형식
```
1
00:00:00,000 --> 00:00:03,500
Never gonna give you up

2
00:00:03,500 --> 00:00:06,800
Never gonna let you down

3
00:00:06,800 --> 00:00:10,200
Never gonna run around and desert you
```

#### VTT 형식
```
WEBVTT

00:00.000 --> 00:03.500
Never gonna give you up

00:03.500 --> 00:06.800
Never gonna let you down

00:06.800 --> 00:10.200
Never gonna run around and desert you
```

#### JSON 형식
```json
{
  "text": "Never gonna give you up Never gonna let you down...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "Never gonna give you up"
    },
    {
      "id": 1,
      "start": 3.5,
      "end": 6.8,
      "text": "Never gonna let you down"
    }
  ],
  "language": "en"
}
```

### 처리 시간 가이드

| 모델 | 10분 영상 처리 시간 (CPU) | 10분 영상 처리 시간 (GPU) |
|------|---------------------------|---------------------------|
| tiny | ~5분 | ~1분 |
| base | ~10분 | ~2분 |
| small | ~20분 | ~5분 |
| medium | ~40분 | ~10분 |
| large | ~80분 | ~20분 |

### 지원 언어

Whisper는 100개 이상의 언어를 지원합니다. 주요 언어 코드:

- `en` - English
- `ko` - 한국어
- `ja` - 日本語
- `zh` - 中文
- `es` - Español
- `fr` - Français
- `de` - Deutsch
- `ru` - Русский

전체 언어 목록은 [Whisper GitHub](https://github.com/openai/whisper#available-models-and-languages)을 참조하세요.

---

## youtube_subtitle_downloader.py - 자막 다운로더

YouTube에서 기존 자막을 다운로드하는 CLI 도구입니다.

### 기본 사용법

```bash
python youtube_subtitle_downloader.py <VIDEO_URL> [OPTIONS]
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-l`, `--language` | 자막 언어 코드 | `ko` |
| `-o`, `--output` | 출력 파일 경로 | 자동 생성 |
| `--list-languages` | 사용 가능한 언어 목록 표시 | - |
| `--format` | 출력 형식 (srt/vtt/json) | `srt` |
| `--auto` | 자동 생성 자막 포함 | `True` |

### 사용 예제

#### 1. 사용 가능한 자막 언어 확인

```bash
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" --list-languages
```

출력:
```
Available subtitles for video "VIDEO_ID":
- ko (Korean) [auto-generated]
- en (English)
- ja (Japanese) [auto-generated]
```

#### 2. 한국어 자막 다운로드

```bash
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" -l ko
```

#### 3. 영어 자막을 특정 파일로 저장

```bash
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" \
  -l en \
  -o english_subtitles.srt
```

#### 4. VTT 형식으로 다운로드

```bash
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" \
  -l ko \
  --format vtt
```

#### 5. 수동 자막만 다운로드 (자동 생성 제외)

```bash
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" \
  -l en \
  --no-auto
```

### 자막 유형

YouTube는 두 가지 유형의 자막을 제공합니다:

1. **수동 자막**: 동영상 제작자가 직접 작성
   - 정확도: 높음
   - 타이밍: 정확
   - 가용성: 제한적

2. **자동 생성 자막**: YouTube의 STT 기술로 생성
   - 정확도: 보통~높음
   - 타이밍: 대체로 정확
   - 가용성: 대부분의 동영상

### 오류 처리

```bash
# 자막이 없는 경우
$ python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" -l ko
Error: No Korean subtitles available for this video.
Available languages: en, ja

# 잘못된 URL
$ python youtube_subtitle_downloader.py "invalid-url"
Error: Invalid YouTube URL
```

---

## translate_release_notes.py - 릴리스 노트 번역

Markdown 형식의 릴리스 노트를 LLM을 이용해 번역하는 CLI 도구입니다.

### 기본 사용법

```bash
python translate_release_notes.py <INPUT_FILE> [OPTIONS]
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o`, `--output` | 출력 파일 경로 | `{input}_translated.md` |
| `--model` | 사용할 LLM 모델 | OpenWebUI 기본값 |
| `--source-lang` | 원본 언어 | 자동 감지 |
| `--target-lang` | 대상 언어 | `ko` |
| `--base-url` | OpenWebUI 기본 URL | 환경 변수 참조 |

### 환경 변수 설정

```bash
# OpenWebUI 엔드포인트 설정
export OPENWEBUI_BASE_URL=http://localhost:3000

# 또는 .env 파일에 추가
echo "OPENWEBUI_BASE_URL=http://localhost:3000" >> .env
```

### 사용 예제

#### 1. 기본 사용 (영어 → 한국어)

```bash
python translate_release_notes.py RELEASE_NOTES.md
```

출력:
```
Reading RELEASE_NOTES.md...
Connecting to OpenWebUI...
Translating...
Progress: [████████████████████] 100%
Saved to: RELEASE_NOTES_translated.md
```

#### 2. 출력 파일 지정

```bash
python translate_release_notes.py RELEASE_NOTES.md -o RELEASE_NOTES_KO.md
```

#### 3. 특정 LLM 모델 사용

```bash
python translate_release_notes.py RELEASE_NOTES.md --model gpt-4
```

#### 4. 다른 언어로 번역 (한국어 → 일본어)

```bash
python translate_release_notes.py RELEASE_NOTES_KO.md \
  --source-lang ko \
  --target-lang ja
```

#### 5. 사용자 정의 OpenWebUI 인스턴스

```bash
python translate_release_notes.py RELEASE_NOTES.md \
  --base-url http://custom-openwebui:3000
```

### 입력 파일 예제

```markdown
# Release Notes v2.0.0

## New Features

- Added user authentication
- Implemented file upload functionality
- Enhanced UI/UX

## Bug Fixes

- Fixed memory leak in audio processing
- Resolved timezone display issues

## Breaking Changes

- Updated API endpoints (see migration guide)
```

### 출력 파일 예제

```markdown
# 릴리스 노트 v2.0.0

## 새로운 기능

- 사용자 인증 추가
- 파일 업로드 기능 구현
- UI/UX 개선

## 버그 수정

- 오디오 처리 메모리 누수 수정
- 시간대 표시 문제 해결

## 주요 변경 사항

- API 엔드포인트 업데이트 (마이그레이션 가이드 참조)
```

### Markdown 요소 처리

번역 도구는 다음 Markdown 요소를 올바르게 처리합니다:

- ✅ **헤더**: `# Header` → `# 헤더`
- ✅ **리스트**: `- Item` → `- 항목`
- ✅ **코드 블록**: 원문 유지
- ✅ **인라인 코드**: 원문 유지
- ✅ **링크**: URL 및 참조 유지
- ✅ **볼드/이탤릭**: 서식 유지
- ✅ **테이블**: 구조 및 정렬 유지

### 번역 품질 최적화 팁

1. **코드 블록 사용**: 번역하지 않을 내용은 코드 블록으로 감싸기
   \```
   DO_NOT_TRANSLATE_THIS
   \```

2. **기술 용어**: 자주 사용하는 용어는 용어집 파일 사용 (계획 중)

3. **검토**: LLM 번역이므로 항상 결과 검토 필요

4. **배치 처리**: 여러 파일 번역 시 스크립트 작성
   ```bash
   for file in *.md; do
     python translate_release_notes.py "$file" -o "translated_$file"
   done
   ```

### 문제 해결

```bash
# OpenWebUI 연결 실패
$ python translate_release_notes.py RELEASE_NOTES.md
Error: Cannot connect to OpenWebUI at http://localhost:3000
Solution: Check OPENWEBUI_BASE_URL and ensure OpenWebUI is running

# 파일 읽기 오류
$ python translate_release_notes.py nonexistent.md
Error: File not found: nonexistent.md
Solution: Check file path and permissions

# 모델 오류
$ python translate_release_notes.py RELEASE_NOTES.md --model invalid-model
Error: Model 'invalid-model' not found
Solution: List available models in OpenWebUI and use valid model name
```

---

## 🔧 고급 사용법

### 배치 처리

여러 동영상을 한 번에 처리:

```bash
#!/bin/bash
# batch_stt.sh

VIDEOS=(
  "https://youtu.be/VIDEO_ID_1"
  "https://youtu.be/VIDEO_ID_2"
  "https://youtu.be/VIDEO_ID_3"
)

for video in "${VIDEOS[@]}"; do
  echo "Processing: $video"
  python youtube_stt.py "$video" --model base
done
```

### 파이프라인 구성

STT → 번역 파이프라인:

```bash
# 1. YouTube 동영상 → 영어 텍스트
python youtube_stt.py "https://youtu.be/VIDEO_ID" \
  --language en \
  --output temp_transcript.txt

# 2. 영어 텍스트 → 한국어 번역
python translate_release_notes.py temp_transcript.txt \
  --source-lang en \
  --target-lang ko \
  -o final_transcript_ko.txt

# 3. 임시 파일 삭제
rm temp_transcript.txt
```

### 스케줄링

cron을 이용한 자동 실행 (Linux/macOS):

```bash
# crontab 편집
crontab -e

# 매일 새벽 2시에 특정 채널의 최신 동영상 STT
0 2 * * * /path/to/script/auto_stt_latest_video.sh
```

---

## 📚 관련 문서

- [설치 가이드](./installation.md)
- [기능 설명](./features.md)
- [웹 애플리케이션 사용법](./web-application.md)
- [트러블슈팅](./troubleshooting.md)
