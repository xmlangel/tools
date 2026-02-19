# CLI Tools Collection

이 디렉토리는 YouTube 미디어 처리, Jira 연동, 회귀 테스트 결과 변환 등을 위한 Python CLI 도구 모음입니다.

## 🛠️ 도구 목록 (Tools List)

### 1. YouTube Tools

#### `youtube_sst.py`
**YouTube AI 음성 인식 자막 생성기 (STT)**
YouTube 영상의 음성을 다운로드하여 OpenAI Whisper AI를 통해 텍스트로 변환합니다.

- **기능**:
  - YouTube 영상에서 오디오 추출
  - Whisper 모델(tiny, base, small, medium, large)을 이용한 STT 변환
  - 대화형 모드 지원
- **사용법**:
  ```bash
  # 기본 사용 (대화형)
  python youtube_sst.py

  # 인자 사용
  python youtube_sst.py "https://youtu.be/..." --model medium --output result.txt
  ```

#### `youtube_subtitle_downloader.py`
**YouTube 자막 다운로더**
YouTube에 존재하는 자막(수동 또는 자동 생성)을 다운로드하여 텍스트 파일로 저장합니다.

- **기능**:
  - 비디오 ID 자동 추출
  - 특정 언어(기본: 한국어 `ko`) 자막 다운로드
  - 자동 생성 자막 지원
- **사용법**:
  ```bash
  python youtube_subtitle_downloader.py "https://youtu.be/..." -l en
  ```

### 2. Testing & CI Utilities

#### `convert_to_junit.py`
**PostgreSQL Regression 결과 변환기**
PostgreSQL 회귀 테스트 결과(`regression.out`, `regression.diffs`)를 CI/CD 파이프라인에서 사용할 수 있는 **JUnit XML** 포맷으로 변환합니다.

- **기능**:
  - 테스트 성공/실패 여부 파싱
  - 실패한 테스트의 상세 Diff 내용을 XML에 포함
  - 실패 단계(Step)별 Expected/Actual 분리 표시
- **사용법**:
  ```bash
  python convert_to_junit.py regression.out regression.diffs
  ```

#### `pg-regress/` 디렉토리
PostgreSQL 회귀 테스트 심화 분석 도구 모음입니다.
- **`compare_not_ok.py`**: 실패한 테스트의 상세 비교 및 분석
- **`jira_regress_update.py`**: 테스트 실패 건을 Jira 이슈로 자동 등록/업데이트
- 자세한 내용은 `pg-regress/README.md`를 참고하세요.

### 3. Jira & Confluence Integration

#### `jira_api/` 디렉토리
Atlassian Jira 및 Confluence 자동화 도구입니다.
- **`jira_cli.py`**: Jira 이슈 생성, 수정, 첨부파일 관리
- **`create_page.py`**: Confluence 페이지 자동 생성
- 자세한 내용은 `jira_api/README.md`를 참고하세요.

### 4. 기타
- **`translate_release_notes.py`**: 릴리스 노트 번역 도구 (현재 코드 확인 필요 - `youtube_subtitle_downloader.py`와 동일한 내용으로 보임)

## 📦 설치 및 의존성 (Installation)

이 도구들을 사용하기 위해서는 Python 3.8+ 환경이 필요합니다.

주요 의존성 패키지 설치:
```bash
pip install yt-dlp openai-whisper youtube-transcript-api
```

`jira_api` 및 `pg-regress` 관련 도구는 해당 디렉토리 내의 `requirements.txt` 또는 `README.md`를 확인하여 추가 의존성을 설치해야 할 수 있습니다.

## 🚀 시작하기

1. 저장소를 클론합니다.
2. 필요한 Python 패키지를 설치합니다.
3. 각 도구의 도움말(`-h` 또는 `--help`)을 확인하여 사용법을 익힙니다.
   ```bash
   python youtube_sst.py -h
   ```
