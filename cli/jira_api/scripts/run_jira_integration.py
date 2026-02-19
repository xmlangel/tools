"""
실서버 Jira 통합 테스트 스크립트

- COIN 프로젝트에 테스트 이슈를 생성하고
- 간단한 업데이트 후
- 삭제합니다.

주의: 실제 Jira에 이슈가 생성/삭제됩니다.

필요 환경 변수:
    ATLASSIAN_URL
    ATLASSIAN_USERNAME
    ATLASSIAN_API_TOKEN

실행 예시:
    python scripts/run_jira_integration.py
    python scripts/run_jira_integration.py --project COIN
    python scripts/run_jira_integration.py --issue-type Task --keep-subtasks
    python scripts/run_jira_integration.py --force
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from jira_cli import (
    Config,
    create_jira_client,
    create_issue_with_extras,
    update_issue,
    delete_issue,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jira 통합 테스트 (생성/수정/삭제)")
    parser.add_argument("--project", default="COIN", help="프로젝트 키 (기본 COIN)")
    parser.add_argument("--issue-type", default="Task", help="이슈 타입 (기본 Task)")
    parser.add_argument("--keep-subtasks", action="store_true", help="서브태스크 삭제하지 않음")
    parser.add_argument(
        "--force",
        action="store_true",
        help="삭제 강제 플래그 (확인 없이 진행)",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if not args.force:
        print("실서버에서 이슈를 생성/수정/삭제합니다. 진행하려면 --force를 지정하세요.")
        return 1

    config = Config.from_env()
    jira = create_jira_client(config)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    summary = f"[INTEGRATION TEST] {args.project} {timestamp}"
    description = "자동 통합 테스트로 생성된 이슈입니다. 완료 후 삭제됩니다."

    tmp_path = Path("/tmp") / f"jira_test_{timestamp}.txt"
    tmp_path.write_text("integration test attachment")

    created = create_issue_with_extras(
        jira=jira,
        project_key=args.project,
        issue_type=args.issue_type,
        summary=summary,
        description=description,
        assignee=None,
        labels="integration,test",
        priority=None,
        components=None,
        comment="통합 테스트 코멘트",
        attachment_paths=[str(tmp_path)],
    )

    update_issue(
        jira=jira,
        issue_key=created.issue_key,
        description=description + " (업데이트됨)",
        summary=summary + " (updated)",
        assignee=None,
        labels="integration,test",
        priority=None,
        components=None,
        comment="통합 테스트 업데이트 코멘트",
        attachment_paths=None,
    )

    delete_issue(
        jira=jira,
        issue_key=created.issue_key,
        delete_subtasks=not args.keep_subtasks,
    )

    print(f"완료: {created.issue_key} 생성/수정/삭제")
    return 0


if __name__ == "__main__":
    sys.exit(main())
