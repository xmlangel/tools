# Confluence Page Creator

Python을 사용하여 Confluence 페이지를 자동으로 생성하는 스크립트입니다.

## 📋 요구 사항

- Python 3.8+
- Atlassian Cloud Confluence 계정
- API 토큰

## 🚀 설치

```bash
# 가상환경 생성 및 활성화
python -m venv confluence_venv
source confluence_venv/bin/activate  # macOS/Linux
# confluence_venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

## ⚙️ 환경 설정

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
ATLASSIAN_URL=https://your-domain.atlassian.net
ATLASSIAN_USERNAME=your-email@example.com
ATLASSIAN_API_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY
```

> **Note**: API 토큰은 [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)에서 생성할 수 있습니다.
```
# Confluence URL (예: https://your-domain.atlassian.net)
# Atlassian 계정 이메일
# Atlassian API Token
# 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens
# 페이지를 생성할 Space Key
# 개인 스페이스의 경우 보통 '~'로 시작하는 긴 문자열이거나 사용자 이름입니다.
# CONFLUENCE_SPACE_KEY=~557058cb35330950ab4419910c43b2c90f9975
```

## 📖 사용법

```bash
# 기본 실행 (Space 루트에 페이지 생성)
python create_page.py

# 특정 부모 페이지 하위에 생성
python create_page.py <parent_page_id>
```

### Jira 이슈 생성/수정/삭제(통합)

`.env`에 Jira 환경 변수를 추가하세요:

```env
ATLASSIAN_URL=https://your-domain.atlassian.net
ATLASSIAN_USERNAME=your-email@example.com
ATLASSIAN_API_TOKEN=your-api-token
```

사용 예시:

```bash
# 도움말
python jira_cli.py --help

# 이슈 수정 (update)
python jira_cli.py update PROJ-123 --description "새로운 설명 내용" --summary "요약"

# 담당자 설정 (Cloud: accountId, Server: name:사용자명)
python jira_cli.py update PROJ-123 --assignee accountId:5b10a2844c20165700ede21g
python jira_cli.py update PROJ-123 --assignee name:your.username

# 라벨/우선순위/컴포넌트
python jira_cli.py update PROJ-123 --labels "backend,urgent" --priority "High" --components "API,Infra"

# 코멘트 추가
python jira_cli.py update PROJ-123 --comment "작업 완료했습니다."

# 첨부파일 업로드 (여러 개)
python jira_cli.py update PROJ-123 --attachment /path/to/file1.txt --attachment /path/to/file2.txt
python jira_cli.py update PROJ-123 --attachment "/path/to/file1.txt,/path/to/file2.txt"

# 여러 작업을 함께 수행
python jira_cli.py update PROJ-123 --description "설명" --comment "코멘트" --attachment /path/to/file.txt

# 이슈 삭제 (delete)
python jira_cli.py delete PROJ-123 --confirm
python jira_cli.py delete PROJ-123 --force
python jira_cli.py delete PROJ-123 --confirm --keep-subtasks
```

> **Note**: `--assignee`는 기본적으로 Cloud `accountId`를 기대합니다. Server/Data Center는 `name:사용자명` 형식을 사용하세요.

```bash
# 이슈 생성 (create)
python jira_cli.py create PROJ Task "요약"

# 설명/담당자/라벨/우선순위/컴포넌트 포함
python jira_cli.py create PROJ Bug "요약" --description "설명" --assignee accountId:5b10a2844c20165700ede21g \\
  --labels "backend,urgent" --priority "High" --components "API,Infra"

# 코멘트 및 첨부파일
python jira_cli.py create PROJ Task "요약" --comment "초기 코멘트" --attachment /path/to/file1.txt --attachment /path/to/file2.txt
```

> **Note**: `jira_create.py`, `jira_update.py`는 호환을 위해 남겨두었으며 내부적으로 `jira_cli.py`를 호출합니다.
> **Note**: 삭제는 안전을 위해 `--confirm` 또는 `--force`가 필요합니다.

## 🏗️ 코드 구조

```
create_page.py
│
├── 📦 Config (dataclass)
│   └── from_env()              # 환경 변수에서 설정 로드
│
├── ⚠️ 예외 클래스
│   ├── ConfluencePageError     # 기본 예외
│   ├── ConfigurationError      # 설정 오류
│   └── PageCreationError       # 페이지 생성 오류
│
├── 🔧 유틸리티 함수
│   ├── setup_logging()         # 로깅 설정
│   ├── create_confluence_client()  # Confluence 클라이언트 생성
│   ├── generate_page_title()   # 타임스탬프 포함 제목 생성
│   ├── generate_page_body()    # HTML 본문 생성
│   ├── create_page()           # 페이지 생성 (핵심 로직)
│   └── parse_args()            # CLI 인수 파싱
│
├── 📊 PageCreationResult (dataclass)
│   ├── page_id                 # 생성된 페이지 ID
│   ├── page_link               # 페이지 URL
│   └── title                   # 페이지 제목
│
└── 🚀 main()                   # 진입점 (종료 코드 반환)
```

```
jira_cli.py
│
├── 📦 Config (dataclass)
│   └── from_env()              # 환경 변수에서 설정 로드
│
├── ⚠️ 예외 클래스
│   ├── JiraIssueError          # 기본 예외
│   ├── ConfigurationError      # 설정 오류
│   ├── IssueUpdateError        # 이슈 수정 오류
│   ├── IssueCreationError      # 이슈 생성 오류
│   └── AttachmentUploadError   # 첨부파일 업로드 오류
│
├── 🔧 유틸리티 함수
│   ├── create_jira_client()    # Jira 클라이언트 생성
│   ├── update_issue_fields()   # 필드 업데이트
│   ├── add_issue_comment()     # 코멘트 추가
│   ├── upload_attachment()     # 첨부파일 업로드
│   └── build_parser()          # CLI 인수 파싱
│
├── 📊 IssueUpdateResult (dataclass)
│   ├── issue_key               # 이슈 키
│   ├── updated_fields          # 수정된 필드
│   ├── attachments             # 업로드된 첨부파일
│   └── attachment_failures     # 업로드 실패 목록
│
├── 📊 IssueCreationResult (dataclass)
│   ├── issue_key               # 이슈 키
│   ├── issue_id                # 이슈 ID
│   ├── updated_fields          # 설정된 필드
│   ├── attachments             # 업로드된 첨부파일
│   └── attachment_failures     # 업로드 실패 목록
│
└── 🚀 main()                   # 진입점 (종료 코드 반환)
```

### 주요 모듈 설명

| 모듈 | 설명 |
|------|------|
| `Config` | 환경 변수를 관리하는 불변 데이터 클래스 |
| `예외 클래스` | 구체적인 오류 유형별 예외 처리 |
| `create_confluence_client()` | Confluence API 클라이언트 초기화 |
| `create_page()` | 중복 확인 후 페이지 생성 |
| `PageCreationResult` | 생성 결과를 담는 데이터 클래스 |

## 📁 프로젝트 구조

```
confluence/
├── .env                 # 환경 변수 (git 무시)
├── create_page.py       # 메인 스크립트
├── jira_cli.py          # Jira 이슈 생성/수정 통합 스크립트
├── jira_create.py       # (호환) Jira 이슈 생성 스크립트
├── jira_update.py       # (호환) Jira 이슈 수정/첨부 스크립트
├── scripts/run_jira_integration.py  # 실서버 통합 테스트 (생성/수정/삭제)
├── requirements.txt     # Python 의존성
├── confluence_venv/     # 가상환경
└── README.md            # 이 문서
```

## 🔧 확장 방법

## ✅ 단위 테스트

현재 구현된 기능에 대한 유닛 테스트는 `pytest`로 실행합니다.

```bash
# 전체 테스트 실행
pytest

# JUnit XML 리포트 생성
pytest --junitxml=junit.xml
```

### 페이지 콘텐츠 커스터마이징

`generate_page_title()` 및 `generate_page_body()` 함수를 수정하여 원하는 콘텐츠를 생성하세요:

```python
def generate_page_title(prefix: str = "나의 커스텀 제목") -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return f"{prefix} - {timestamp}"

def generate_page_body() -> str:
    return """
    <h2>나의 커스텀 콘텐츠</h2>
    <p>여기에 원하는 HTML을 작성하세요.</p>
    """
```

### 페이지 업데이트 기능 추가

`create_page()` 함수를 수정하여 기존 페이지 업데이트 로직을 추가할 수 있습니다.

## 📝 라이선스

MIT License
