# 기능 설명

이 문서는 YouTube STT & Translation Tools 프로젝트의 주요 기능을 상세히 설명합니다.

## 📋 목차

- [YouTube 음성-텍스트 변환 (STT)](#youtube-음성-텍스트-변환-stt)
- [YouTube 자막 다운로드](#youtube-자막-다운로드)
- [릴리스 노트 번역](#릴리스-노트-번역)
- [파일 업로드 및 처리](#파일-업로드-및-처리)
- [작업 큐 관리](#작업-큐-관리)
- [사용자 관리](#사용자-관리)

---

## YouTube 음성-텍스트 변환 (STT)

YouTube 동영상의 음성을 텍스트로 변환하는 핵심 기능입니다.

### 주요 특징

- **OpenAI Whisper 모델 사용**: 최첨단 음성 인식 기술
- **다양한 모델 크기 지원**: tiny, base, small, medium, large
- **다국어 지원**: 100개 이상의 언어 자동 감지 및 변환
- **타임스탬프 포함**: 각 문장의 시작/끝 시간 정보
- **고품질 변환**: 자막이 없는 동영상도 처리 가능

### 사용 방법

#### CLI 도구

```bash
# 기본 사용법 (base 모델)
python youtube_stt.py "https://youtu.be/VIDEO_ID"

# 특정 모델 지정
python youtube_stt.py "https://youtu.be/VIDEO_ID" --model medium

# 언어 지정
python youtube_stt.py "https://youtu.be/VIDEO_ID" --language ko

# 출력 형식 지정
python youtube_stt.py "https://youtu.be/VIDEO_ID" --output-format srt
```

#### 웹 인터페이스

1. YouTube URL 입력
2. Whisper 모델 선택 (tiny ~ large)
3. "변환 시작" 버튼 클릭
4. 작업 진행 상황 모니터링
5. 완료 후 결과 다운로드

### 지원하는 출력 형식

- **TXT**: 순수 텍스트
- **VTT**: WebVTT 자막 형식
- **SRT**: SubRip 자막 형식
- **JSON**: 타임스탬프 포함 구조화된 데이터

### 모델 선택 가이드

| 모델 | 크기 | 속도 | 정확도 | 권장 용도 |
|------|------|------|--------|-----------|
| tiny | ~75MB | 매우 빠름 | 낮음 | 빠른 테스트, 실시간 처리 |
| base | ~150MB | 빠름 | 보통 | 일반적인 용도 |
| small | ~500MB | 보통 | 좋음 | 균형잡힌 선택 |
| medium | ~1.5GB | 느림 | 매우 좋음 | 고품질 필요 시 |
| large | ~3GB | 매우 느림 | 최고 | 최고 품질 필요 시 |

---

## YouTube 자막 다운로드

YouTube에서 기존 자막을 다운로드하는 기능입니다.

### 주요 특징

- **자동 생성 자막 지원**: YouTube의 자동 자막 다운로드
- **수동 자막 지원**: 업로더가 제공한 자막
- **다국어 지원**: 사용 가능한 모든 언어의 자막
- **다양한 형식**: SRT, VTT, JSON 등

### 사용 방법

#### CLI 도구

```bash
# 기본 사용법 (한국어 자막)
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" -l ko

# 영어 자막 다운로드
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" -l en

# 사용 가능한 자막 언어 목록 확인
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" --list-languages

# 출력 파일명 지정
python youtube_subtitle_downloader.py "https://youtu.be/VIDEO_ID" -l ko -o output.srt
```

#### 웹 인터페이스

1. YouTube URL 입력
2. 원하는 자막 언어 선택
3. "다운로드" 버튼 클릭
4. 자막 파일 다운로드

### 자막 vs STT 선택 가이드

**자막 다운로드를 선택해야 할 때:**
- YouTube에 정확한 자막이 이미 존재
- 빠른 처리가 필요
- 타임스탬프 정확도가 중요

**STT를 선택해야 할 때:**
- 자막이 없는 동영상
- 자동 생성 자막의 품질이 낮음
- 특정 언어로 번역이 필요

---

## 릴리스 노트 번역

Markdown 형식의 릴리스 노트를 LLM을 이용해 번역하는 기능입니다.

### 주요 특징

- **Markdown 형식 보존**: 원본의 서식 유지
- **LLM 기반 번역**: OpenWebUI 연동
- **컨텍스트 인식**: 기술 용어 및 맥락 이해
- **배치 처리**: 여러 섹션 동시 번역

### 사용 방법

#### CLI 도구

```bash
# 기본 사용법
python translate_release_notes.py RELEASE_NOTES.md

# 출력 파일 지정
python translate_release_notes.py RELEASE_NOTES.md -o RELEASE_NOTES_KO.md

# 특정 LLM 모델 지정
python translate_release_notes.py RELEASE_NOTES.md --model gpt-4
```

#### 환경 변수 설정

```bash
# OpenWebUI 엔드포인트 설정
export OPENWEBUI_BASE_URL=http://your-openwebui-instance:3000
```

### 번역 품질 최적화

- **기술 용어**: 코드 블록과 기술 용어는 원문 유지
- **링크 보존**: URL 및 참조 링크 보존
- **구조 유지**: 헤더, 리스트, 코드 블록 등 Markdown 구조 유지

---

## 파일 업로드 및 처리

오디오 파일을 직접 업로드하여 STT 변환을 수행하는 기능입니다.

### 주요 특징

- **다양한 오디오 형식 지원**: m4a, mp3, wav, flac 등
- **대용량 파일 처리**: 스트리밍 업로드
- **MinIO 기반 스토리지**: 안정적인 파일 관리
- **자동 형식 변환**: FFmpeg를 통한 자동 변환

### 사용 방법

#### 웹 인터페이스

1. "파일 업로드" 탭 선택
2. 오디오 파일 선택 또는 드래그 앤 드롭
3. Whisper 모델 선택
4. "변환 시작" 버튼 클릭
5. 작업 진행 상황 모니터링
6. 완료 후 결과 다운로드

### 지원하는 오디오 형식

- **일반 형식**: mp3, wav, m4a, aac
- **무손실 형식**: flac, alac, wav
- **동영상 형식**: mp4, avi, mkv (오디오 트랙 추출)

### 파일 크기 제한

- **웹 인터페이스**: 최대 500MB
- **API**: 최대 2GB
- **CLI**: 제한 없음 (디스크 공간에 따름)

---

## 작업 큐 관리

비동기 작업을 관리하고 모니터링하는 기능입니다.

### 주요 특징

- **비동기 처리**: 백그라운드에서 작업 실행
- **작업 상태 추적**: 대기, 진행 중, 완료, 실패
- **우선순위 큐**: 작업 우선순위 설정
- **재시도 메커니즘**: 실패한 작업 자동 재시도

### 작업 상태

| 상태 | 설명 | 다음 단계 |
|------|------|-----------|
| PENDING | 대기 중 | 처리 시작 대기 |
| PROCESSING | 진행 중 | 작업 실행 중 |
| COMPLETED | 완료 | 결과 다운로드 가능 |
| FAILED | 실패 | 오류 확인 및 재시도 |
| CANCELED | 취소됨 | - |

### 웹 인터페이스

"작업 목록" 페이지에서:
- 모든 작업 상태 확인
- 진행 중인 작업 모니터링
- 완료된 작업 결과 다운로드
- 실패한 작업 재시도
- 작업 취소 (진행 중인 작업만)

### API 엔드포인트

```http
GET /api/jobs - 모든 작업 조회
GET /api/jobs/{job_id} - 특정 작업 상세 정보
POST /api/jobs - 새 작업 생성
DELETE /api/jobs/{job_id} - 작업 취소
```

---

## 사용자 관리

웹 애플리케이션의 사용자 인증 및 권한 관리 기능입니다.

### 주요 특징

- **JWT 기반 인증**: 안전한 토큰 기반 인증
- **역할 기반 권한**: 관리자, 일반 사용자
- **사용자 프로필**: 개인 설정 및 이력 관리

### 기본 계정

개발 환경에서 사용 가능한 기본 계정:

```
관리자 계정:
- 이메일: admin@example.com
- 비밀번호: admin123

일반 사용자:
- 이메일: user@example.com
- 비밀번호: user123
```

> ⚠️ **주의**: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

### 회원가입

웹 인터페이스에서:
1. "회원가입" 페이지로 이동
2. 이메일, 비밀번호, 이름 입력
3. "가입하기" 버튼 클릭
4. 이메일 인증 (개발 환경에서는 자동)

### 권한 관리

| 역할 | 권한 |
|------|------|
| 관리자 | 모든 기능 접근, 사용자 관리, 시스템 설정 |
| 일반 사용자 | STT, 자막 다운로드, 번역, 파일 업로드 |

---

## 🔜 계획 중인 기능

- **화자 분리**: 여러 화자 구분
- **실시간 STT**: 라이브 스트림 실시간 변환
- **자동 요약**: 변환된 텍스트 자동 요약
- **다국어 번역**: STT 결과 자동 번역
- **API 키 관리**: 외부 서비스 API 키 관리
- **웹훅**: 작업 완료 알림

---

## 📚 관련 문서

- [설치 가이드](./installation.md)
- [웹 애플리케이션 사용법](./web-application.md)
- [CLI 도구 사용법](./cli-tools.md)
- [API 문서](./api.md)
