# 릴리즈 노트 한글 번역기

Git 로그로부터 생성된 릴리즈 노트를 LLM을 사용하여 자연스러운 한글로 번역하는 도구입니다.

## 특징

- ✨ **섹션 단위 번역**: 날짜별/타입별 섹션을 유지하며 문맥을 고려한 번역
- 📝 **마크다운 형식 보존**: 마크다운 구조와 형식을 그대로 유지
- 🔧 **기술 용어 정확성**: 소프트웨어 개발 용어를 정확하게 번역
- 💾 **식별자 보존**: 커밋 해시, 코드, 파일명 등을 변경하지 않음
- 🌐 **OpenWebUI 연동**: 다양한 LLM 모델 사용 가능

## 요구사항

- Python 3.6 이상
- `requests` 라이브러리
- `python-dotenv` 라이브러리
- OpenWebUI 또는 호환 API 서버

## 설치

### 1. 의존성 설치

```bash
pip install requests python-dotenv
```

또는 requirements.txt 사용:

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 편집:

```env
OPENWEBUI_URL=http://localhost:3000
OPENWEBUI_API_KEY=sk-your-api-key-here
OPENWEBUI_MODEL=llama3
```

## 사용 방법

### 기본 사용법

환경변수가 설정되어 있는 경우:

```bash
python translate_release_notes.py RELEASE_NOTES.md
```

결과: `RELEASE_NOTES_ko.md` 파일 생성

### 옵션 지정

```bash
python translate_release_notes.py RELEASE_NOTES.md \
  --url http://localhost:3000 \
  --key sk-xxx \
  --model llama3 \
  --output RELEASE_NOTES_한글.md
```

### 전체 워크플로우 (릴리즈 노트 생성 + 번역)

```bash
# 1. 릴리즈 노트 생성 (영문)
cd /path/to/your/project
python /path/to/generate_release_notes.py \
  --repo . \
  -v 1.0.0 \
  -o RELEASE_NOTES.md

# 2. 한글로 번역
python /path/to/tools/translate_release_notes.py \
  RELEASE_NOTES.md \
  -o RELEASE_NOTES_ko.md
```

## 옵션 상세

### 필수 인자

| 인자 | 설명 |
|------|------|
| `input_file` | 번역할 릴리즈 노트 파일 (Markdown) |

### 선택 옵션

| 옵션 | 환경변수 | 설명 | 예시 |
|------|----------|------|------|
| `--url` | `OPENWEBUI_URL` | OpenWebUI API 주소 | `http://localhost:3000` |
| `--key` | `OPENWEBUI_API_KEY` | API 인증 키 | `sk-xxx` |
| `--model` | `OPENWEBUI_MODEL` | 사용할 LLM 모델 | `llama3`, `qwen2.5`, `gpt-4` |
| `-o, --output` | - | 출력 파일 경로 | `RELEASE_ko.md` |

## 번역 규칙

번역 시 다음 규칙이 적용됩니다:

### 유지되는 요소

- ✅ 마크다운 구조 (`##`, `###`, `-`, `*`, etc.)
- ✅ 커밋 해시 (`` [`abc123`] ``)
- ✅ 날짜 형식 (`YYYY-MM-DD`)
- ✅ 이모지
- ✅ 코드, 파일명, 함수명
- ✅ URL 링크

### 번역되는 용어

| 영문 | 한글 |
|------|------|
| Features | 새로운 기능 |
| Bug Fixes | 버그 수정 |
| Performance | 성능 개선 |
| Refactoring | 리팩토링 |
| Documentation | 문서 |
| Tests | 테스트 |
| Chores | 기타 작업 |
| Build System | 빌드 시스템 |
| CI/CD | CI/CD |
| Styles | 스타일 |
| Reverts | 되돌리기 |

## 예시

### 입력 (RELEASE_NOTES.md)

```markdown
# Release Notes - MyProject v1.0.0

Generated on: 2024-12-12 10:30:00

## 📅 2024-12-12

### ✨ Features

- **auth**: Add JWT-based authentication ([`abc123`])
- **dashboard**: Implement real-time data updates ([`def456`])

### 🐛 Bug Fixes

- **payment**: Prevent duplicate requests on payment failure ([`ghi789`])
```

### 출력 (RELEASE_NOTES_ko.md)

```markdown
# 릴리즈 노트 - MyProject v1.0.0

생성일: 2024-12-12 10:30:00

## 📅 2024-12-12

### ✨ 새로운 기능

- **auth**: JWT 기반 인증 추가 ([`abc123`])
- **dashboard**: 실시간 데이터 업데이트 구현 ([`def456`])

### 🐛 버그 수정

- **payment**: 결제 실패 시 중복 요청 방지 ([`ghi789`])
```

## 지원 LLM 모델

OpenWebUI를 통해 다음 모델들을 사용할 수 있습니다:

### 오픈소스 모델
- **Llama 3** / **Llama 3.1**: 범용 성능
- **Qwen 2.5**: 다국어 번역에 강함
- **Mistral**: 빠른 처리 속도
- **Gemma**: Google의 경량 모델

### 상용 모델 (API 연동 시)
- **GPT-4**: 최고 품질의 번역
- **Claude**: 자연스러운 문맥 이해
- **Gemini Pro**: Google의 고급 모델

### 권장 모델

| 사용 사례 | 권장 모델 | 이유 |
|-----------|-----------|------|
| 일반적인 번역 | `qwen2.5:14b` | 한국어 번역 품질 우수 |
| 빠른 처리 | `llama3:8b` | 처리 속도 빠름 |
| 최고 품질 | `gpt-4` | 가장 정확한 번역 |
| 로컬 환경 | `qwen2.5:7b` | 적당한 성능과 속도 |

## 문제 해결

### API 연결 오류

**증상**: `❌ 모든 API 경로 시도 실패`

**해결**:
1. OpenWebUI 서버가 실행 중인지 확인
```bash
curl http://localhost:3000/health
```

2. API Key가 올바른지 확인
3. 방화벽 설정 확인

### 번역 품질이 낮을 때

**해결**:
1. 더 큰 모델 사용 (예: `qwen2.5:14b` → `qwen2.5:32b`)
2. 기술 문서 번역에 특화된 모델 선택
3. Temperature 값 조정 (기본값: 0.3)

### 느린 번역 속도

**해결**:
1. 더 작은 모델 사용 (예: `qwen2.5:14b` → `qwen2.5:7b`)
2. GPU 가속 활성화 (CUDA, Metal)
3. 섹션 단위로 나눠서 처리 (이미 구현됨)

### 메모리 부족

**해결**:
1. 더 작은 모델 사용
2. `max_tokens` 값 조정 (스크립트 내부)
3. 시스템 메모리 확인 및 정리

## 고급 사용법

### 1. 다른 언어로 번역

스크립트 내부의 프롬프트를 수정하여 다른 언어로 번역 가능:

```python
# translate_release_notes.py 내부
prompt = f"""
Translate the following release notes to Japanese...
日本語に翻訳してください...
"""
```

### 2. 커스텀 용어집 적용

특정 용어를 원하는 방식으로 번역하려면 프롬프트에 용어집 추가:

```python
prompt = f"""
용어 번역 규칙:
- Authentication → 인증
- Authorization → 권한 부여
- Cache → 캐시
...
"""
```

### 3. Python 스크립트에서 사용

```python
from translate_release_notes import ReleaseNotesTranslator

# 번역기 초기화
translator = ReleaseNotesTranslator(
    api_url="http://localhost:3000",
    api_key="sk-xxx",
    model="qwen2.5:14b"
)

# 번역 실행
translator.translate_release_notes(
    input_file="RELEASE_NOTES.md",
    output_file="RELEASE_NOTES_ko.md"
)
```

## 자동화

### Bash 스크립트로 통합

`generate_and_translate.sh`:

```bash
#!/bin/bash

REPO_PATH=$1
VERSION=$2

# 릴리즈 노트 생성
python generate_release_notes.py \
  --repo "$REPO_PATH" \
  -v "$VERSION" \
  -o "RELEASE_v${VERSION}.md"

# 한글 번역
python tools/translate_release_notes.py \
  "RELEASE_v${VERSION}.md" \
  -o "RELEASE_v${VERSION}_ko.md"

echo "✅ 완료!"
echo "   영문: RELEASE_v${VERSION}.md"
echo "   한글: RELEASE_v${VERSION}_ko.md"
```

사용:
```bash
chmod +x generate_and_translate.sh
./generate_and_translate.sh /path/to/repo 1.0.0
```

### GitHub Actions

`.github/workflows/release-notes.yml`:

```yaml
name: Generate Release Notes

on:
  release:
    types: [created]

jobs:
  generate-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install requests python-dotenv

      - name: Generate Release Notes (English)
        run: |
          python generate_release_notes.py \
            -v ${{ github.event.release.tag_name }} \
            -o RELEASE_NOTES.md

      - name: Translate to Korean
        env:
          OPENWEBUI_URL: ${{ secrets.OPENWEBUI_URL }}
          OPENWEBUI_API_KEY: ${{ secrets.OPENWEBUI_API_KEY }}
          OPENWEBUI_MODEL: qwen2.5:14b
        run: |
          python tools/translate_release_notes.py \
            RELEASE_NOTES.md \
            -o RELEASE_NOTES_ko.md

      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: release-notes
          path: |
            RELEASE_NOTES.md
            RELEASE_NOTES_ko.md
```

## 비용 및 성능

### 로컬 모델 (무료)

| 모델 | 처리 속도 | 메모리 사용 | 번역 품질 |
|------|-----------|-------------|-----------|
| qwen2.5:7b | 빠름 | ~8GB | 좋음 |
| qwen2.5:14b | 보통 | ~16GB | 매우 좋음 |
| llama3:8b | 빠름 | ~8GB | 좋음 |

### 상용 API (유료)

| 모델 | 비용 (1K tokens) | 번역 품질 |
|------|------------------|-----------|
| GPT-4 | ~$0.03 | 최고 |
| GPT-3.5 | ~$0.002 | 좋음 |
| Claude 3 | ~$0.025 | 매우 좋음 |

**예상 비용**: 1000줄 릴리즈 노트 번역 시 약 $0.10 ~ $0.50

## 참고 자료

- [OpenWebUI 공식 문서](https://docs.openwebui.com/)
- [Ollama 모델 목록](https://ollama.ai/library)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [generate_release_notes.py](../generate_release_notes.py) - 릴리즈 노트 생성

## 라이선스

MIT License

---

**Made with ❤️ for better multilingual documentation**
