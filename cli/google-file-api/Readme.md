# 프로젝트 개요: Google Drive 및 Jenkins 다운로더

이 프로젝트는 Google Drive의 파일/폴더와 Jenkins 빌드 아티팩트를 다운로드하기 위한 유틸리티 모음입니다. 대화형 터미널 환경뿐만 아니라 `nohup`과 같은 백그라운드 프로세스에서도 원활하게 작동하도록 설계되었습니다.

## 주요 기술
- **Python 3**: Google Drive 연동 및 핵심 로직.
- **Google Drive API v3**: 파일 검색, 목록 조회 및 다운로드.
- **Bash**: Jenkins 연동을 위한 유틸리티 스크립트.
- **tqdm**: 다운로드 진행률 표시.

## 주요 구성 요소

### 1. Google Drive 다운로더 (`google_deive_files_api.py`)
Google Drive 폴더를 재귀적으로 다운로드하는 종합 스크립트입니다.
- **주요 기능**:
    - 폴더 ID 및 URL 지원.
    - 재귀적 다운로드 옵션 (`-r`).
    - 사용자 정의 저장 경로 지정 (`-o`).
    - Google OAuth2 지원 (사용자 계정 및 서비스 계정).
    - **복구 기능**: 특정 파일 다운로드 실패(예: 404 에러) 시 해당 파일을 건너뛰고 전체 작업을 계속 진행합니다.
    - **비대화형 환경 지원**: `nohup` 등 백그라운드 실행 시 사용자 입력을 기다리지 않고 기본값을 자동으로 사용합니다.

### 2. Jenkins 아티팩트 다운로더 (`get_jenkinsfile.sh`)
인증된 `wget`을 사용하여 Jenkins 서버에서 아티팩트를 가져오는 쉘 스크립트입니다.

## 설정 및 설치

### 사전 요구 사항
- Python 3.x
- `pip` 또는 가상 환경 (`venv`)

### 설치 방법
```bash
# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 설정
- **Google Drive**: 사용자 인증을 위한 `client_secrit.json` 또는 서비스 계정용 `service_account.json`이 필요합니다. 인증 토큰은 `token.json`에 저장됩니다.
- **Jenkins**: `get_jenkinsfile.sh` 내의 `JENKINS_USER`와 `JENKINS_TOKEN`을 설정해야 합니다.

## 실행 방법

### Google Drive 다운로드
```bash
# 기본 사용 (대화형)
python google_deive_files_api.py

# 특정 폴더를 재귀적으로 특정 경로에 다운로드
python google_deive_files_api.py -r -f "FOLDER_ID_OR_URL" -o "./my_downloads"

# 백그라운드 실행
nohup python google_deive_files_api.py -r > download.log 2>&1 &
```

### Jenkins 아티팩트 다운로드
```bash
./get_jenkinsfile.sh "http://jenkins-server/job/artifact_url"
```

## 개발 규칙
- **에러 처리**: Drive 스크립트는 파일 단위로 예외 처리를 하여 개별 파일의 오류가 전체 배치 작업에 영향을 주지 않도록 합니다.
- **환경 감지**: `sys.stdin.isatty()` 또는 `EOFError` 처리를 통해 대화형 터미널과 백그라운드 작업을 구분합니다.
- **로그**: 콘솔을 통해 상태(발견된 항목, 경로, 로그인 정보)를 출력하며, 백그라운드 로그는 `nohup.out` 또는 지정된 로그 파일에 기록됩니다.
