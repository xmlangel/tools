"""
Jira 이슈 내용 수정 및 첨부파일 업로드 스크립트 (통합 CLI 래퍼)

Usage:
    python jira_update.py ISSUE_KEY [--description "..."] [--summary "..."] [--assignee "..."] [--labels "a,b"] [--priority "..."] [--components "a,b"] [--comment "..."] [--attachment /path/to/file] [--attachment /path/to/file2]

Environment Variables:
    ATLASSIAN_URL: Atlassian 인스턴스 URL
    ATLASSIAN_USERNAME: 사용자 이름 (이메일)
    ATLASSIAN_API_TOKEN: API 토큰
"""

import sys

from jira_cli import main as jira_cli_main


def main() -> int:
    """기존 CLI 호환을 위한 래퍼"""
    return jira_cli_main(["update", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
