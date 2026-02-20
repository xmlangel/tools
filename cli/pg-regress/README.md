# pg-regress 도구

이 디렉터리의 최신 PostgreSQL 회귀 테스트 산출물(`regression.out`, `regression.diffs`, `results/`,
`expected/`, `ora_expected/expected/`, `sql/`)을 기준으로 동작합니다.  
현재 pg_regress 결과를 비교/검증하고, JUnit XML 등 보고서를 생성하는 목적입니다.

## 스크립트

### `jira_regress_update.py`
pg_regress 실패(`not ok`)에 대한 Jira 이슈를 업데이트/생성합니다.

하는 일:
- `regression.out`에서 실패 테스트(`not ok`)를 찾습니다.
- `regression.diffs`에서 해당 테스트의 diff 블록을 추출합니다.
- 실패 테스트별 첨부 파일(`expected`, `result`, `sql`, 필요 시 diff/description)을 준비합니다.
- `../jira_api/jira_cli.py`로 Jira 이슈를 업데이트/생성합니다.

주요 동작:
- 처리 이력은 `.jira_regress_state.json`에 기록합니다.
- 대화형(이슈 키 입력) 또는 비대화형으로 동작합니다.
- 전체 실패 항목을 자동 생성하는 모드를 지원합니다.

실행 예시:

```bash
# 현재 디렉터리 산출물을 사용 (regression.out, regression.diffs, results/, sql/ 등)
pwd

# 대화형 모드 (이슈 키를 순차 입력)
python jira_regress_update.py

# 다음 실패 항목을 특정 Jira 이슈 키로 업데이트
python jira_regress_update.py PG-1024

# 첨부 파일만 준비 (Jira 업데이트 없음)
python jira_regress_update.py --prepare-only

# 모든 실패 항목 자동 생성/업데이트
python jira_regress_update.py --auto-create \
  --project-key PG \
  --issue-type Bug \
  --summary-format "pg_regress failure: {test}" \
  --epic-summary "PG 회귀 테스트 실패 모음"
```

옵션:
- `issue_key`: 다음 실패 항목에 사용할 Jira 이슈 키(선택 positional).
- `--test`: 특정 테스트만 업데이트/준비 (예: `packages`).
- `--interactive`: 실패 항목별 이슈 키를 대화형으로 입력.
- `--description-attach`: 설명을 본문 대신 파일로 첨부.
- `--dry-run`: Jira 실행 없이 명령만 출력.
- `--prepare-only`: 첨부 파일만 준비.
- `--auto-create`: 실패 항목 자동 생성.
- `--project-key`: Jira 프로젝트 키 (`--auto-create` 필수).
- `--issue-type`: Jira 이슈 타입 (`--auto-create` 필수).
- `--summary-format`: 요약 포맷, `{test}` 포함 필수 (`--auto-create` 필수).
- `--duplicate-handling`: 이미 매핑된 실패 항목 처리 방식 `update` 또는 `duplicate`.
- `--epic-summary`: 자동 생성 Epic 요약 (`--auto-create`에서 `--epic-key` 없으면 필수).
- `--epic-issue-type`: Epic 이슈 타입 (기본: `Epic`).
- `--epic-key`: 기존 Epic 키 사용.

### `compare_not_ok.py`
`regression.out`의 `not ok` 테스트에 대해 expected vs actual을 비교합니다.

하는 일:
- `regression.out`에서 실패 테스트를 추출합니다.
- `expected`(또는 `ags` 모드 시 `ora_expected/expected`)와 `results`를 비교합니다.
- 실패 항목별 unified diff를 출력합니다.
- 필요 시 JUnit XML 리포트를 생성합니다.

실행 예시:

```bash
# 현재 산출물을 사용해 비교 (기본: ags -> ora_expected/expected)
python compare_not_ok.py --regression regression.out --results-dir results

# 모든 NOT OK 테스트 비교 (기본: ags)
python compare_not_ok.py

# 특정 테스트만 비교
python compare_not_ok.py --tests test1 test2

# pg expected 디렉터리 사용
python compare_not_ok.py --mode pg

# JUnit XML 출력
python compare_not_ok.py --junit-output junit.xml
```

옵션:
- `--regression`: `regression.out` 경로.
- `--expected-dir`: expected 디렉터리 (기본: `expected`).
- `--ora-expected-dir`: Oracle expected 디렉터리 (기본: `ora_expected/expected`).
- `--results-dir`: 결과 디렉터리 (기본: `results`).
- `--tests`: 비교 대상 테스트 목록.
- `-U`, `--context`: diff 컨텍스트 라인 수 (기본: `3`).
- `--mode`: `pg` 또는 `ags` (기본: `ags`).
- `--junit-output`: JUnit XML 출력 경로.

### `convert_to_junit.py`
pg_regress 결과를 JUnit XML로 변환합니다.

하는 일:
- `regression.out`에서 테스트 결과/시간을 파싱합니다.
- `regression.diffs`에서 실패 diff를 읽습니다.
- expected/actual 및 단계별 diff를 JUnit XML에 포함합니다.
- `pg_test_result_make_check_YYYYMMDD_HHMMSS.xml` 형태로 출력합니다.

실행 예시:

```bash
# 현재 결과를 변환하여 타임스탬프 포함 JUnit 파일 생성
python convert_to_junit.py regression.out regression.diffs

# pg expected 디렉터리 사용
python convert_to_junit.py regression.out regression.diffs --mode pg
```

옵션:
- `regression_out`: `regression.out` 경로(필수 positional).
- `regression_diffs`: `regression.diffs` 경로(선택 positional, 기본: `regression.diffs`).
- `--mode`: `pg`는 `expected/`, `ags`는 `ora_expected/` 사용 (기본: `ags`).

## 참고

- 본 스크립트들은 **현재** pg_regress 실행 결과물을 기준으로 동작합니다.
- `compare_not_ok.py`, `convert_to_junit.py`는 최신 pg 테스트 결과 검증/리포팅 용도입니다.
- Jira 업데이트는 `../jira_api/jira_cli.py`가 준비되어 있어야 합니다.
