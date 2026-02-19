"""
Jira 이슈 생성 스크립트 (jira_cli.py로 통합됨)

Usage:
    python jira_create.py PROJECT_KEY ISSUE_TYPE SUMMARY [옵션...]
"""

import sys

from jira_cli import main as jira_main


if __name__ == "__main__":
    sys.exit(jira_main(["create", *sys.argv[1:]]))
