# YouTube STT & Translation Tools 문서

이 프로젝트는 YouTube 동영상의 음성을 텍스트로 변환(STT)하고 번역하는 기능을 제공하는 포괄적인 도구 모음입니다.

## 📚 문서 목차

- [설치 가이드](./installation.md) - 프로젝트 설치 및 초기 설정
- [웹 애플리케이션](./web-application.md) - Docker 기반 풀스택 웹 애플리케이션 사용법
- [CLI 도구](./cli-tools.md) - 독립 실행형 명령줄 도구 사용법
- [기능 설명](./features.md) - 각 기능에 대한 상세 설명
- [개발 가이드](./development.md) - 개발 환경 설정 및 컨벤션
- [API 문서](./api.md) - Backend API 엔드포인트 및 사용법
- [트러블슈팅](./troubleshooting.md) - 자주 발생하는 문제 및 해결 방법

## 🚀 빠른 시작

### 웹 애플리케이션 (추천)

```bash
# Docker Compose로 전체 스택 실행
docker-compose up --build
```

웹 인터페이스: http://localhost:5173

### CLI 도구

```bash
# 의존성 설치
pip install -r requirements.txt

# YouTube 동영상 STT
python youtube_stt.py "https://youtu.be/..." --model base
```

## 💡 주요 기능

- **YouTube 음성-텍스트 변환 (STT)**: OpenAI Whisper 모델을 이용한 고품질 음성 인식
- **자막 다운로드**: YouTube 자막 다운로드 기능
- **릴리스 노트 번역**: LLM을 활용한 Markdown 문서 번역
- **웹 인터페이스**: React 기반의 사용자 친화적인 UI
- **작업 큐 관리**: 비동기 작업 처리 및 모니터링
- **파일 업로드**: m4a 등 오디오 파일 직접 업로드 및 처리

## 📖 상세 문서

각 기능에 대한 자세한 내용은 위의 문서 링크를 참조하세요.
