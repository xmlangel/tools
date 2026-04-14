---
description: LLM 가이드 문서(CLAUDE.md, GEMINI.md 등)를 프로젝트의 실제 상태와 동기화하는 워크플로우
---

프로젝트의 기술 스택, 파일 구조, 설정값 등이 변경되었을 때 모든 LLM용 가이드 문서를 최신 상태로 유지하기 위한 절차입니다.

## 1. 프로젝트 실제 상태 확인 (Source of Truth)

가장 먼저 다음 파일들을 통해 프로젝트의 실제 상태를 확인합니다.

- **백엔드 버전 및 라이브러리**: `build.gradle` (Spring Boot 버전, Java 버전 확인)
- **런타임 설정**: `src/main/resources/application.yml` (포트, JWT, RAG URL 등)
- **프론트엔드 빌드**: `build.gradle`의 `node` 설정 및 `src/main/frontend/vite.config.js`
- **파일 시스템**: `ls` 명령을 사용하여 실제 존재하는 파일명과 경로(예: i18n 번역 파일, Docker 디렉토리) 확인

## 2. CLAUDE.md (Primary Doc) 업데이트

`CLAUDE.md`는 AI 에이전트의 주된 지침서입니다. 확인된 정보를 바탕으로 다음 섹션들을 업데이트합니다.

1.  **Project Overview**: Spring Boot, Java 버전 등 기술 스택 최신화
2.  **Architecture**: 변경된 모듈 구조나 서비스 흐름 반영
3.  **i18n 가이드**: 실제 파일명과 추가 프로세스 예시 업데이트
4.  **Startup Guide**: Docker 경로(`docker-compose-build`), 포트, 기본 비밀번호 등 최신화

## 3. 타 모델 가이드 파일 동기화

`CLAUDE.md`에 반영된 내용을 동일한 형식으로 다음 파일들에도 전파합니다.

- `AGENTS.MD`
- `GEMINI.md`
- `QWEN.md`

**체크리스트:**
- [ ] Docker 디렉토리 경로 (`docker-compose-build`)
- [ ] Docker compose 파일명 (`docker-compose.yml`)
- [ ] Docker 서비스 목록 (`postgres` 5434 포함 여부)
- [ ] 기본 로그인 비밀번호 (`admin123`)
- [ ] i18n 번역 파일 실제 클래스명

## 4. JIRA 연동 모듈 검증 (선택 사항)

문서 동기화 후 JIRA 연동 기능이 정상인지 확인이 필요한 경우 다음 절차를 수행합니다.

1.  **환경 변수 로드**: `.env` 파일 로드 여부 확인
2.  **API 연결 테스트**: `jira_caller.py`를 이용한 이슈 조회 테스트
3.  **워크플로우 테스트**: `quick_start.py`를 통한 이슈 생성 및 상태 변경 테스트

```bash
# JIRA 연결 확인 예시 (Anaconda 환경 권장)
/opt/anaconda3/bin/python -c "from jira_caller import get_jira_client; print(get_jira_client().issue('ICT-216').key)"
```

## 5. 최종 검증 보고

모든 파일이 성공적으로 동기화되었음을 `walkthrough.md` 또는 `notify_user`를 통해 사용자에게 보고합니다.
