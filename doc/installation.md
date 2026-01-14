# 설치 가이드

이 문서는 YouTube STT & Translation Tools 프로젝트의 설치 방법을 설명합니다.

## 📋 사전 요구사항

### 웹 애플리케이션 (Docker)

- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **운영체제**: macOS, Linux, Windows (WSL2 권장)

### CLI 도구 (Standalone)

- **Python**: 3.8 이상
- **FFmpeg**: 오디오 처리를 위해 필요
- **운영체제**: macOS, Linux, Windows

## 🐳 웹 애플리케이션 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd tools
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env
```

`.env` 파일 예시:

```env
# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=youtube_stt

# MinIO (Object Storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET_NAME=uploads

# Backend
SECRET_KEY=your_secret_key_here
OPENWEBUI_BASE_URL=http://your-openwebui-instance:3000
```

### 3. Docker Compose 실행

```bash
# 전체 스택 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

### 4. 서비스 확인

설치가 완료되면 다음 서비스에 접근할 수 있습니다:

- **Frontend (React)**: http://localhost:5173
- **Backend (FastAPI)**: http://localhost:8000
- **Backend API 문서**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5436
- **MinIO Console**: http://localhost:9003 (User/Pass: `minioadmin`)

### 5. 초기 데이터베이스 설정

컨테이너 실행 후 자동으로 데이터베이스가 초기화됩니다. 수동 마이그레이션이 필요한 경우:

```bash
# Backend 컨테이너에 접속
docker-compose exec backend bash

# 마이그레이션 실행 (필요시)
# python -m alembic upgrade head
```

## 🐍 CLI 도구 설치

### 1. Python 가상 환경 생성 (권장)

```bash
# 가상 환경 생성
python -m venv tools_venv

# 가상 환경 활성화
# macOS/Linux:
source tools_venv/bin/activate
# Windows:
tools_venv\Scripts\activate
```

### 2. FFmpeg 설치

#### macOS (Homebrew)

```bash
brew install ffmpeg
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows (Chocolatey)

```bash
choco install ffmpeg
```

또는 [FFmpeg 공식 웹사이트](https://ffmpeg.org/download.html)에서 다운로드

### 3. Python 의존성 설치

```bash
# 루트 디렉토리의 requirements.txt 설치
pip install -r requirements.txt
```

주요 의존성:
- `yt-dlp`: YouTube 다운로더
- `openai-whisper`: 음성-텍스트 변환
- `youtube-transcript-api`: YouTube 자막 API
- `requests`: HTTP 클라이언트

### 4. 설치 확인

```bash
# YouTube STT 도구 테스트
python youtube_stt.py --help

# 자막 다운로더 테스트
python youtube_subtitle_downloader.py --help

# 번역 도구 테스트
python translate_release_notes.py --help
```

## 🔧 추가 설정

### OpenWebUI 연동 (릴리스 노트 번역용)

릴리스 노트 번역 기능을 사용하려면 OpenWebUI 인스턴스가 필요합니다:

1. `.env` 파일에 OpenWebUI URL 설정:
   ```env
   OPENWEBUI_BASE_URL=http://your-openwebui-instance:3000
   ```

2. 또는 환경 변수로 설정:
   ```bash
   export OPENWEBUI_BASE_URL=http://your-openwebui-instance:3000
   ```

### Whisper 모델 다운로드

최초 실행 시 Whisper 모델이 자동으로 다운로드됩니다. 수동으로 다운로드하려면:

```python
import whisper
whisper.load_model("base")  # tiny, base, small, medium, large 중 선택
```

## 🐛 설치 문제 해결

### Docker 관련 문제

**포트 충돌**
```bash
# 사용 중인 포트 확인
lsof -i :5173
lsof -i :8000
lsof -i :5436

# docker-compose.yml에서 포트 변경
```

**권한 문제 (Linux)**
```bash
# Docker를 sudo 없이 실행하도록 설정
sudo usermod -aG docker $USER
newgrp docker
```

### Python 관련 문제

**FFmpeg 찾을 수 없음**
```bash
# FFmpeg 설치 확인
ffmpeg -version

# PATH 환경 변수에 FFmpeg 추가 필요
```

**Whisper 설치 실패**
```bash
# Rust 컴파일러가 필요할 수 있음
# macOS:
brew install rust
# Linux:
sudo apt install rustc
# Windows:
# https://rustup.rs/ 에서 설치
```

## 📝 다음 단계

설치가 완료되면 다음 문서를 참조하세요:

- [웹 애플리케이션 사용법](./web-application.md)
- [CLI 도구 사용법](./cli-tools.md)
- [기능 설명](./features.md)
