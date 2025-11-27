# YouTube 자막 다운로더

YouTube 비디오의 자막을 텍스트 파일로 다운로드하는 Python 프로그램입니다.

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

또는 직접 설치:
```bash
pip install youtube-transcript-api
```

## 사용 방법

### 기본 사용법
```bash
python youtube_subtitle_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 옵션

- `-o` 또는 `--output`: 출력 파일 경로 지정
- `-l` 또는 `--language`: 자막 언어 코드 지정 (기본값: `ko`)

### 예시

1. **기본 사용 (한국어 자막)**
```bash
python youtube_subtitle_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

2. **출력 파일명 지정**
```bash
python youtube_subtitle_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "my_subtitle.txt"
```

3. **영어 자막 다운로드**
```bash
python youtube_subtitle_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -l en
```

4. **짧은 URL 형식**
```bash
python youtube_subtitle_downloader.py "https://youtu.be/dQw4w9WgXcQ"
```

## 지원하는 URL 형식

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `VIDEO_ID` (비디오 ID만)

## 주요 언어 코드

- `ko` - 한국어
- `en` - 영어
- `ja` - 일본어
- `zh` - 중국어
- `es` - 스페인어
- `fr` - 프랑스어
- `de` - 독일어

## 기능

- ✅ YouTube URL에서 자동으로 비디오 ID 추출
- ✅ 지정한 언어의 자막 다운로드
- ✅ 자막이 없을 경우 자동 생성 자막 사용
- ✅ 여러 URL 형식 지원
- ✅ UTF-8 인코딩으로 텍스트 파일 저장

## 주의사항

- 자막이 없는 비디오는 다운로드할 수 없습니다.
- 일부 비디오는 자막이 비활성화되어 있을 수 있습니다.
- 네트워크 연결이 필요합니다.

---

# (옵션) 자막이 없는 경우: AI 음성 인식 사용

영상에 자막이 아예 없는 경우, **AI가 영상을 듣고 받아쓰기(STT)**를 하도록 할 수 있습니다.

## 추가 설치 필요

이 기능은 `ffmpeg`가 설치되어 있어야 합니다. (Mac의 경우 `brew install ffmpeg`)

## 사용 방법

```bash
python youtube_stt.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 옵션

- `-m` 또는 `--model`: AI 모델 크기 선택 (`tiny`, `base`, `small`, `medium`, `large`)
  - `base`: 빠르고 적당한 정확도 (기본값)
  - `medium` / `large`: 느리지만 높은 정확도
- `-o` 또는 `--output`: 출력 파일 경로 지정 (미지정시 자동 생성)
- `--keep-audio`: 다운로드한 mp3 파일을 지우지 않고 유지

### 파일명 자동 생성 규칙

프로그램은 YouTube 영상 제목을 기반으로 자동으로 파일명을 생성합니다:

- **MP3 파일**: `{영상제목}_mp3.mp3`
- **STT 결과 파일**: `{영상제목}_stt.txt`

예시:
- 영상 제목: "Python Tutorial for Beginners"
- MP3 파일: `Python_Tutorial_for_Beginners_mp3.mp3`
- STT 파일: `Python_Tutorial_for_Beginners_stt.txt`

### 기존 파일 재사용

동일한 영상의 MP3 파일이 이미 존재하는 경우:
- 자동으로 기존 파일을 재사용하여 다운로드 건너뛰기
- 바로 음성 인식(STT) 단계로 진행
- 시간과 네트워크 대역폭 절약

### 예시

**기본 사용 (대화형 모드)**
```bash
python youtube_stt.py
```

**정확도 높여서 변환하기 (시간 더 걸림)**
```bash
python youtube_stt.py "URL" -m medium
```

**오디오 파일 유지하기**
```bash
python youtube_stt.py "URL" --keep-audio
```

**출력 파일명 직접 지정**
```bash
python youtube_stt.py "URL" -o "my_transcript.txt"
```

## 주요 기능

- ✅ YouTube 영상 제목을 기반으로 자동 파일명 생성
- ✅ 기존 MP3 파일 자동 감지 및 재사용
- ✅ 5단계 AI 모델 선택 (tiny, base, small, medium, large)
- ✅ 대화형 모드 지원 (인자 없이 실행)
- ✅ 오디오 파일 유지/삭제 옵션
- ✅ 다국어 음성 인식 지원
- ✅ UTF-8 인코딩으로 텍스트 파일 저장

## 작동 흐름

1. **영상 정보 확인**: YouTube 영상 제목 추출
2. **파일 존재 확인**:
   - 기존 MP3 파일이 있으면 → 바로 3단계로 진행
   - 없으면 → 오디오 다운로드
3. **AI 음성 인식**: Whisper AI로 음성을 텍스트로 변환
4. **결과 저장**: 텍스트 파일로 저장
5. **정리**: --keep-audio 옵션에 따라 MP3 파일 유지/삭제

