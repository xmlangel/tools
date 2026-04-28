# Google Sheets Translation Tool (OpenWebUI)

이 프로젝트는 Google Sheets의 내용을 OpenWebUI(LLM) API를 사용하여 자동으로 번역하고 시트를 업데이트하는 도구입니다. 영문 텍스트를 읽어와 번역된 한글 텍스트를 원문과 함께 해당 셀에 기록합니다.

## 주요 기능

- **자동 번역**: OpenWebUI(또는 OpenAI 호환 API)를 사용하여 영문을 한글로 번역합니다.
- **다중 열 처리**: 여러 열(예: D, E, F)을 한 번에 지정하여 번역할 수 있습니다.
- **번역 제외 문구**: 특정 문구(예: 'Works fine')가 포함된 셀을 번역에서 제외할 수 있습니다. (정확히 일치할 경우)
- **스타일 지정**: 기술 문서에 적합한 간결한 문체(명사형 종결 어미)로 번역합니다.
- **구조적 설계**: 클래스 기반으로 설계되어 유지보수가 쉽고 확장이 용이합니다.

## 프로젝트 구조

```text
google-sheet/
├── src/                # 핵심 로직 모듈
├── config/             # Google 서비스 계정 키 보관
├── .env                # API 및 시트 설정 파일
├── requirements.txt    # 필요 패키지 목록
└── translator.py       # 실행 엔트리 포인트
```

## 사전 준비 사항

1. **Google 서비스 계정**: 
   - Google Cloud Console에서 서비스 계정을 생성하고 JSON 키 파일을 `config/key.json`으로 저장합니다.
   - 해당 서비스 계정의 이메일 주소를 번역할 구글 시트에 **편집자(Editor)** 권한으로 공유해야 합니다.
2. **OpenWebUI**:
   - OpenWebUI API가 활성화되어 있어야 하며, API Key가 필요합니다.

## 설치 방법

1. 저장소를 클론하거나 다운로드합니다.
2. 가상환경을 생성하고 필요한 패키지를 설치합니다:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 설정 (.env)

`.env` 파일을 열어 본인의 환경에 맞게 수정합니다:

```env
# OpenWebUI 설정
OPENWEBUI_URL=https://your-openwebui-url/api
OPENWEBUI_API_KEY=your-api-key
OPENWEBUI_MODEL=llama3

# 구글 시트 설정
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_FILE=config/key.json
SHEET_NAME=Sheet1
COLUMN=A,B        # 번역할 열 (쉼표로 구분 가능)
START_ROW=1       # 시작 행
END_ROW=100       # 종료 행

# 번역 제외 설정
EXCLUDE_PHRASES=Works fine,Already automated in TAF  # 정확히 일치할 경우 번역 제외
```

## 실행 방법

```bash
python3 translator.py
```

## 라이선스

이 프로젝트는 자유롭게 수정 및 배포가 가능합니다.
