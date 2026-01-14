# 트러블슈팅

이 문서는 자주 발생하는 문제와 해결 방법을 안내합니다.

## 📋 목차

- [설치 관련 문제](#설치-관련-문제)
- [Docker 관련 문제](#docker-관련-문제)
- [YouTube STT 관련 문제](#youtube-stt-관련-문제)
- [파일 업로드 관련 문제](#파일-업로드-관련-문제)
- [성능 문제](#성능-문제)

---

## 설치 관련 문제

### Python 의존성 설치 실패

**증상:** `pip install -r requirements.txt` 실패

**해결방법:**

1. Rust 컴파일러 설치
2. Python 버전 확인 (3.8 이상)
3. 시스템 라이브러리 설치

### FFmpeg 설치 문제

**증상:** FFmpeg를 찾을 수 없음

**해결방법:**

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

---

## Docker 관련 문제

### 컨테이너 시작 실패

**증상:** 포트 이미 사용 중

**해결방법:**

```bash
# 포트 확인
lsof -i :8000

# 기존 컨테이너 정리
docker-compose down
docker-compose up --build
```

---

## YouTube STT 관련 문제

### YouTube 다운로드 실패

**해결방법:**

1. yt-dlp 업데이트: `pip install --upgrade yt-dlp`
2. URL 형식 확인
3. 동영상 접근 권한 확인

### Whisper 메모리 부족

**해결방법:**

1. 작은 모델 사용: `--model base`
2. CPU 모드 사용: `--device cpu`

---

## 파일 업로드 관련 문제

### 파일 크기 제한 초과

**해결방법:**

1. CLI 도구 사용
2. FFmpeg로 파일 압축

---

## 성능 문제

### STT 처리 속도 개선

**해결방법:**

1. GPU 사용 (CUDA)
2. 작은 모델 사용
3. Docker 리소스 증가

---

## 📚 관련 문서

- [설치 가이드](./installation.md)
- [CLI 도구 사용법](./cli-tools.md)
