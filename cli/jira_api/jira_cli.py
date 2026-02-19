"""
Jira 이슈 생성/수정/첨부 통합 스크립트

Usage:
    python jira_cli.py create PROJECT_KEY ISSUE_TYPE SUMMARY [--description "..."] [--assignee "..."] [--labels "a,b"] [--priority "..."] [--components "a,b"] [--comment "..."] [--attachment /path/to/file] [--epic KEY]
    python jira_cli.py update ISSUE_KEY [--description "..."] [--summary "..."] [--assignee "..."] [--labels "a,b"] [--priority "..."] [--components "a,b"] [--comment "..."] [--attachment /path/to/file] [--epic KEY]
    python jira_cli.py get ISSUE_KEY [--expand "changelog,renderedFields"] [--epic]
    python jira_cli.py types [--project PROJECT_KEY]

Environment Variables:
    ATLASSIAN_URL: Atlassian 인스턴스 URL
    ATLASSIAN_USERNAME: 사용자 이름 (이메일)
    ATLASSIAN_API_TOKEN: API 토큰
"""

import os
import sys
import json
import logging
import argparse
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Sequence

from dotenv import load_dotenv
from atlassian import Jira


# ============================================================
# 설정
# ============================================================

@dataclass(frozen=True)
class Config:
    """Jira 연결 설정"""
    url: str
    username: str
    api_token: str
    is_cloud: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """환경 변수에서 설정을 로드합니다."""
        load_dotenv()

        required_vars = {
            "ATLASSIAN_URL": os.getenv("ATLASSIAN_URL"),
            "ATLASSIAN_USERNAME": os.getenv("ATLASSIAN_USERNAME"),
            "ATLASSIAN_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
        }

        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ConfigurationError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            )

        return cls(
            url=required_vars["ATLASSIAN_URL"],
            username=required_vars["ATLASSIAN_USERNAME"],
            api_token=required_vars["ATLASSIAN_API_TOKEN"],
        )


# ============================================================
# 예외 클래스
# ============================================================

class JiraIssueError(Exception):
    """Jira 이슈 관련 기본 예외"""
    pass


class ConfigurationError(JiraIssueError):
    """설정 오류"""
    pass


class IssueUpdateError(JiraIssueError):
    """이슈 수정 오류"""
    pass


class IssueCreationError(JiraIssueError):
    """이슈 생성 오류"""
    pass


class IssueDeletionError(JiraIssueError):
    """이슈 삭제 오류"""
    pass


class IssueFetchError(JiraIssueError):
    """이슈 조회 오류"""
    pass


class AttachmentUploadError(JiraIssueError):
    """첨부파일 업로드 오류"""
    pass


# ============================================================
# 로깅 설정
# ============================================================

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """로깅을 설정하고 로거를 반환합니다.

    Args:
        level (int): 로깅 레벨.

    Returns:
        logging.Logger: 설정된 로거.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================
# Jira 클라이언트
# ============================================================

def create_jira_client(config: Config) -> Jira:
    """Jira 클라이언트를 생성합니다.

    Args:
        config (Config): Jira 연결 설정.

    Returns:
        Jira: Jira 클라이언트 인스턴스.

    Raises:
        ConfigurationError: 초기화 실패 시.
    """
    try:
        client = Jira(
            url=config.url,
            username=config.username,
            password=config.api_token,
            cloud=config.is_cloud,
        )
        logger.info("Jira 연결 성공: %s", config.url)
        return client
    except Exception as e:
        raise ConfigurationError(f"Jira 클라이언트 초기화 실패: {e}") from e


# ============================================================
# 유틸리티
# ============================================================

def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    """쉼표 구분 문자열을 리스트로 변환합니다.

    Args:
        value (Optional[str]): 쉼표 구분 문자열.

    Returns:
        Optional[List[str]]: 리스트 또는 None.
    """
    if value is None:
        return None
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def _parse_assignee(value: Optional[str]) -> Optional[Dict[str, str]]:
    """담당자 입력을 Jira API 형식으로 변환합니다.

    Args:
        value (Optional[str]): accountId 또는 name: 접두어 문자열.

    Returns:
        Optional[Dict[str, str]]: Jira assignee 필드 형식 또는 None.
    """
    if value is None:
        return None
    # Cloud는 accountId를 기본으로, Server/Data Center는 name: 접두어를 허용
    if value.startswith("name:"):
        return {"name": value[len("name:"):].strip()}
    if value.startswith("accountId:"):
        return {"accountId": value[len("accountId:"):].strip()}
    return {"accountId": value.strip()}


def _expand_attachments(values: Optional[List[str]]) -> List[str]:
    """첨부파일 인수를 펼쳐 단일 리스트로 변환합니다.

    Args:
        values (Optional[List[str]]): --attachment 인수 리스트.

    Returns:
        List[str]: 정규화된 첨부파일 경로 리스트.
    """
    if not values:
        return []
    expanded: List[str] = []
    for value in values:
        if not value:
            continue
        # "--attachment a,b --attachment c" 형태를 모두 지원
        parts = [item.strip() for item in value.split(",")]
        expanded.extend([item for item in parts if item])
    return expanded


def _normalize_field_name(name: str) -> str:
    """필드 이름을 비교 가능한 형태로 정규화합니다.

    Args:
        name (str): 원본 필드 이름.

    Returns:
        str: 정규화된 필드 이름.
    """
    return name.strip().lower()


def resolve_field_id(
    jira: Jira,
    field_names: Sequence[str],
) -> Optional[str]:
    """필드 이름 목록으로 Jira 필드 ID를 조회합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        field_names (Sequence[str]): 후보 필드 이름 목록.

    Returns:
        Optional[str]: 찾은 필드 ID 또는 None.

    Raises:
        IssueFetchError: 필드 메타데이터 조회 실패 시.
    """
    try:
        all_fields = jira.get_all_fields()
    except Exception as e:
        raise IssueFetchError(f"필드 메타데이터 조회 실패: {e}") from e

    if not isinstance(all_fields, list):
        raise IssueFetchError("필드 메타데이터 응답이 비정상입니다.")

    normalized_targets = {_normalize_field_name(name) for name in field_names}
    for field in all_fields:
        if not isinstance(field, dict):
            continue
        field_name = field.get("name")
        field_id = field.get("id")
        if not field_name or not field_id:
            continue
        if _normalize_field_name(field_name) in normalized_targets:
            return str(field_id)
    return None


def build_epic_summary(
    jira: Jira,
    issue_data: Dict[str, Any],
) -> Dict[str, Any]:
    """이슈의 에픽 관련 필드 정보를 요약합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_data (Dict[str, Any]): Jira 이슈 데이터.

    Returns:
        Dict[str, Any]: 에픽 필드 요약 정보.

    Raises:
        IssueFetchError: 필드 메타데이터 조회 실패 시.
    """
    epic_link_field_id = resolve_field_id(jira, ["Epic Link", "에픽 링크"])
    epic_name_field_id = resolve_field_id(jira, ["Epic Name", "에픽 이름"])

    fields = issue_data.get("fields", {})
    issue_type = None
    if isinstance(fields, dict):
        issue_type = (fields.get("issuetype") or {}).get("name")

    epic_link_value = None
    epic_name_value = None
    parent_issue = None
    if isinstance(fields, dict):
        parent_issue = fields.get("parent")
        if epic_link_field_id:
            epic_link_value = fields.get(epic_link_field_id)
        if epic_name_field_id:
            epic_name_value = fields.get(epic_name_field_id)

    if epic_link_value is None and isinstance(parent_issue, dict):
        parent_fields = parent_issue.get("fields") or {}
        parent_type = (parent_fields.get("issuetype") or {}).get("name")
        if parent_type in {"Epic", "에픽"}:
            epic_link_value = parent_issue.get("key")
            if epic_name_value is None:
                epic_name_value = parent_fields.get("summary")

    if epic_name_value is None and issue_type in {"Epic", "에픽"}:
        if isinstance(fields, dict):
            epic_name_value = fields.get("summary")

    return {
        "issue_key": issue_data.get("key"),
        "issue_type": issue_type,
        "epic_key": issue_data.get("key") if issue_type in {"Epic", "에픽"} else None,
        "epic_link_field_id": epic_link_field_id,
        "epic_link": epic_link_value,
        "epic_name_field_id": epic_name_field_id,
        "epic_name": epic_name_value,
    }


def resolve_epic_link_target(jira: Jira) -> tuple[Optional[str], str]:
    """에픽 링크 필드/parent 중 어떤 필드를 사용할지 결정합니다.

    Args:
        jira (Jira): Jira 클라이언트.

    Returns:
        tuple[Optional[str], str]: (에픽 링크 필드 ID 또는 None, 사용 필드명).

    Raises:
        IssueFetchError: 필드 메타데이터 조회 실패 시.
    """
    epic_link_field_id = resolve_field_id(jira, ["Epic Link", "에픽 링크"])
    if epic_link_field_id:
        return epic_link_field_id, "epic_link"
    return None, "parent"


def resolve_epic_key(
    epic_link: Optional[str],
    epic: Optional[str],
    error_cls: type,
) -> Optional[str]:
    """에픽 키 입력을 단일 값으로 정규화합니다.

    Args:
        epic_link (Optional[str]): --epic-link 입력 값.
        epic (Optional[str]): --epic 입력 값.
        error_cls (type): 충돌 시 던질 예외 클래스.

    Returns:
        Optional[str]: 에픽 키.

    Raises:
        error_cls: 두 옵션이 서로 다른 값으로 동시에 지정된 경우.
    """
    if epic_link and epic and epic_link != epic:
        raise error_cls("--epic-link와 --epic을 동시에 지정할 수 없습니다.")
    return epic_link or epic


def get_issue_types(
    jira: Jira,
    project_key: Optional[str],
) -> List[Dict[str, Any]]:
    """이슈 타입 목록을 조회합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        project_key (Optional[str]): 프로젝트 키(없으면 전체 타입 조회).

    Returns:
        List[Dict[str, Any]]: 이슈 타입 목록.

    Raises:
        IssueFetchError: 이슈 타입 조회 실패 시.
    """
    try:
        if not project_key:
            issue_types = jira.get_issue_types()
            if not isinstance(issue_types, list):
                raise IssueFetchError("이슈 타입 응답이 비정상입니다.")
            return issue_types

        results: List[Dict[str, Any]] = []
        start_at = 0
        max_results = 50

        while True:
            response = jira.issue_createmeta_issuetypes(
                project=project_key,
                start=start_at,
                limit=max_results,
            )
            if not isinstance(response, dict):
                raise IssueFetchError("프로젝트 이슈 타입 응답이 비정상입니다.")

            values = response.get("values", [])
            if isinstance(values, list):
                results.extend(values)

            is_last = response.get("isLast")
            total = response.get("total")

            if is_last is True:
                break

            if total is not None and isinstance(total, int):
                if start_at + max_results >= total:
                    break

            if not values:
                break

            start_at += max_results

        return results
    except Exception as e:
        raise IssueFetchError(f"이슈 타입 조회 실패: {e}") from e


def upload_attachment(
    jira: Jira,
    issue_key: str,
    attachment_path: str,
) -> str:
    """이슈에 첨부파일을 업로드합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        attachment_path (str): 첨부파일 경로.

    Returns:
        str: 업로드된 파일명.

    Raises:
        AttachmentUploadError: 파일 없음/업로드 실패 시.
    """
    if not os.path.exists(attachment_path):
        raise AttachmentUploadError(f"첨부파일을 찾을 수 없습니다: {attachment_path}")

    try:
        response = jira.add_attachment(issue_key, attachment_path)
        if isinstance(response, dict):
            return response.get("filename", os.path.basename(attachment_path))
        return os.path.basename(attachment_path)
    except Exception as e:
        raise AttachmentUploadError(f"첨부파일 업로드 실패: {e}") from e


def add_issue_comment(
    jira: Jira,
    issue_key: str,
    comment: str,
    error_cls: type,
) -> None:
    """이슈에 코멘트를 추가합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        comment (str): 코멘트 본문.
        error_cls (type): 예외 래핑 클래스.

    Raises:
        error_cls: 코멘트 추가 실패 시.
    """
    try:
        jira.add_comment(issue_key, comment)
    except Exception as e:
        raise error_cls(f"이슈 코멘트 추가 실패: {e}") from e


# ============================================================
# 이슈 수정 로직
# ============================================================

@dataclass
class IssueUpdateResult:
    """이슈 수정 결과"""
    issue_key: str
    updated_fields: List[str]
    attachments: List[str]
    attachment_failures: List[str]


def update_issue_fields(
    jira: Jira,
    issue_key: str,
    fields: Dict[str, Any],
) -> None:
    """이슈 필드를 업데이트합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        fields (Dict[str, Any]): 업데이트할 필드 딕셔너리.

    Raises:
        IssueUpdateError: 업데이트 실패 시.
    """
    if not fields:
        # 변경점이 없으면 API 호출을 생략
        return
    try:
        jira.issue_update(issue_key, fields=fields)
    except Exception as e:
        raise IssueUpdateError(f"이슈 필드 업데이트 실패: {e}") from e


def update_issue(
    jira: Jira,
    issue_key: str,
    description: Optional[str],
    summary: Optional[str],
    assignee: Optional[str],
    labels: Optional[str],
    priority: Optional[str],
    components: Optional[str],
    comment: Optional[str],
    attachment_paths: Optional[List[str]],
    epic_link: Optional[str],
    epic_name: Optional[str],
) -> IssueUpdateResult:
    """이슈의 설명/코멘트/첨부파일을 처리합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        description (Optional[str]): 새 설명.
        summary (Optional[str]): 새 요약.
        assignee (Optional[str]): 담당자.
        labels (Optional[str]): 라벨 CSV.
        priority (Optional[str]): 우선순위 이름.
        components (Optional[str]): 컴포넌트 CSV.
        comment (Optional[str]): 코멘트.
        attachment_paths (Optional[List[str]]): 첨부파일 경로 리스트.
        epic_link (Optional[str]): 에픽 키(필드 없으면 parent로 연결).
        epic_name (Optional[str]): 에픽 이름(필드 없으면 summary로 반영).

    Returns:
        IssueUpdateResult: 업데이트 결과.

    Raises:
        IssueUpdateError: 업데이트 실패/수정 내용 없음.
    """
    updated_fields: List[str] = []
    attachments: List[str] = []
    attachment_failures: List[str] = []

    fields: Dict[str, Any] = {}

    if description is not None:
        fields["description"] = description
        updated_fields.append("description")

    if summary is not None:
        fields["summary"] = summary
        updated_fields.append("summary")

    assignee_value = _parse_assignee(assignee)
    if assignee_value is not None:
        fields["assignee"] = assignee_value
        updated_fields.append("assignee")

    label_items = _split_csv(labels)
    if label_items is not None:
        fields["labels"] = label_items
        updated_fields.append("labels")

    if priority is not None:
        fields["priority"] = {"name": priority}
        updated_fields.append("priority")

    component_items = _split_csv(components)
    if component_items is not None:
        fields["components"] = [{"name": name} for name in component_items]
        updated_fields.append("components")

    if epic_link is not None:
        epic_link_field_id, target_name = resolve_epic_link_target(jira)
        if epic_link_field_id:
            fields[epic_link_field_id] = epic_link
        else:
            fields["parent"] = {"key": epic_link}
        updated_fields.append(target_name)

    if epic_name is not None:
        epic_name_field_id = resolve_field_id(jira, ["Epic Name", "에픽 이름"])
        if epic_name_field_id:
            fields[epic_name_field_id] = epic_name
            updated_fields.append("epic_name")
        elif summary is None:
            fields["summary"] = epic_name
            updated_fields.append("summary")

    update_issue_fields(jira, issue_key, fields)

    if comment is not None:
        add_issue_comment(jira, issue_key, comment, IssueUpdateError)
        updated_fields.append("comment")

    attachment_list = _expand_attachments(attachment_paths)
    for attachment_path in attachment_list:
        try:
            filename = upload_attachment(jira, issue_key, attachment_path)
            attachments.append(filename)
        except AttachmentUploadError as e:
            attachment_failures.append(f"{attachment_path} -> {e}")

    if not updated_fields and not attachments and not attachment_failures:
        raise IssueUpdateError("수정할 내용이 없습니다. 옵션을 하나 이상 지정하세요.")

    return IssueUpdateResult(
        issue_key=issue_key,
        updated_fields=updated_fields,
        attachments=attachments,
        attachment_failures=attachment_failures,
    )


# ============================================================
# 이슈 생성 로직
# ============================================================

@dataclass
class IssueCreationResult:
    """이슈 생성 결과"""
    issue_key: str
    issue_id: str
    updated_fields: List[str]
    attachments: List[str]
    attachment_failures: List[str]


@dataclass
class IssueDeletionResult:
    """이슈 삭제 결과"""
    issue_key: str
    delete_subtasks: bool


@dataclass
class IssueFetchResult:
    """이슈 조회 결과"""
    issue_key: str
    issue_data: Dict[str, Any]


def create_issue(
    jira: Jira,
    project_key: str,
    issue_type: str,
    summary: str,
    description: Optional[str],
    assignee: Optional[str],
    labels: Optional[str],
    priority: Optional[str],
    components: Optional[str],
    epic_link: Optional[str],
    epic_name: Optional[str],
) -> Dict[str, Any]:
    """이슈를 생성하고 응답을 반환합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        project_key (str): 프로젝트 키.
        issue_type (str): 이슈 타입.
        summary (str): 요약.
        description (Optional[str]): 설명.
        assignee (Optional[str]): 담당자.
        labels (Optional[str]): 라벨 CSV.
        priority (Optional[str]): 우선순위 이름.
        components (Optional[str]): 컴포넌트 CSV.
        epic_link (Optional[str]): 에픽 키(필드 없으면 parent로 연결).
        epic_name (Optional[str]): 에픽 이름(필드 없으면 summary로 반영).

    Returns:
        Dict[str, Any]: Jira 생성 응답.

    Raises:
        IssueCreationError: 생성 실패 시.
    """
    fields: Dict[str, Any] = {
        "project": {"key": project_key},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }

    if description is not None:
        fields["description"] = description

    assignee_value = _parse_assignee(assignee)
    if assignee_value is not None:
        fields["assignee"] = assignee_value

    label_items = _split_csv(labels)
    if label_items is not None:
        fields["labels"] = label_items

    if priority is not None:
        fields["priority"] = {"name": priority}

    component_items = _split_csv(components)
    if component_items is not None:
        fields["components"] = [{"name": name} for name in component_items]

    if epic_link is not None:
        epic_link_field_id, _ = resolve_epic_link_target(jira)
        if epic_link_field_id:
            fields[epic_link_field_id] = epic_link
        else:
            fields["parent"] = {"key": epic_link}

    if epic_name is not None:
        epic_name_field_id = resolve_field_id(jira, ["Epic Name", "에픽 이름"])
        if epic_name_field_id:
            fields[epic_name_field_id] = epic_name
        elif issue_type in {"Epic", "에픽"}:
            fields["summary"] = epic_name

    try:
        response = jira.issue_create(fields)
        if not isinstance(response, dict):
            raise IssueCreationError("이슈 생성 응답 형식이 올바르지 않습니다.")
        return response
    except Exception as e:
        raise IssueCreationError(f"이슈 생성 실패: {e}") from e


def create_issue_with_extras(
    jira: Jira,
    project_key: str,
    issue_type: str,
    summary: str,
    description: Optional[str],
    assignee: Optional[str],
    labels: Optional[str],
    priority: Optional[str],
    components: Optional[str],
    comment: Optional[str],
    attachment_paths: Optional[List[str]],
    epic_link: Optional[str],
    epic_name: Optional[str],
) -> IssueCreationResult:
    """이슈 생성 후 코멘트/첨부파일을 처리합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        project_key (str): 프로젝트 키.
        issue_type (str): 이슈 타입.
        summary (str): 요약.
        description (Optional[str]): 설명.
        assignee (Optional[str]): 담당자.
        labels (Optional[str]): 라벨 CSV.
        priority (Optional[str]): 우선순위 이름.
        components (Optional[str]): 컴포넌트 CSV.
        comment (Optional[str]): 코멘트.
        attachment_paths (Optional[List[str]]): 첨부파일 경로 리스트.
        epic_link (Optional[str]): 에픽 키(필드 없으면 parent로 연결).
        epic_name (Optional[str]): 에픽 이름(필드 없으면 summary로 반영).

    Returns:
        IssueCreationResult: 생성 결과.

    Raises:
        IssueCreationError: 생성 실패/응답 이상.
    """
    updated_fields: List[str] = ["summary", "issuetype", "project"]

    if description is not None:
        updated_fields.append("description")
    if assignee is not None:
        updated_fields.append("assignee")
    if labels is not None:
        updated_fields.append("labels")
    if priority is not None:
        updated_fields.append("priority")
    if components is not None:
        updated_fields.append("components")
    if epic_link is not None:
        _, target_name = resolve_epic_link_target(jira)
        updated_fields.append(target_name)
    if epic_name is not None:
        updated_fields.append("epic_name")

    response = create_issue(
        jira=jira,
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description=description,
        assignee=assignee,
        labels=labels,
        priority=priority,
        components=components,
        epic_link=epic_link,
        epic_name=epic_name,
    )

    issue_key = response.get("key")
    issue_id = response.get("id")
    if not issue_key or not issue_id:
        raise IssueCreationError("이슈 생성 결과에서 key/id를 찾을 수 없습니다.")

    if comment is not None:
        add_issue_comment(jira, issue_key, comment, IssueCreationError)
        updated_fields.append("comment")

    attachments: List[str] = []
    attachment_failures: List[str] = []
    attachment_list = _expand_attachments(attachment_paths)
    for attachment_path in attachment_list:
        try:
            filename = upload_attachment(jira, issue_key, attachment_path)
            attachments.append(filename)
        except AttachmentUploadError as e:
            attachment_failures.append(f"{attachment_path} -> {e}")

    return IssueCreationResult(
        issue_key=issue_key,
        issue_id=issue_id,
        updated_fields=updated_fields,
        attachments=attachments,
        attachment_failures=attachment_failures,
    )


# ============================================================
# 이슈 삭제 로직
# ============================================================

def delete_issue(
    jira: Jira,
    issue_key: str,
    delete_subtasks: bool,
) -> IssueDeletionResult:
    """이슈를 삭제합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        delete_subtasks (bool): 서브태스크 삭제 여부.

    Returns:
        IssueDeletionResult: 삭제 결과.

    Raises:
        IssueDeletionError: 삭제 실패 시.
    """
    try:
        # atlassian-python-api의 delete_issue 사용
        jira.delete_issue(issue_key, delete_subtasks=delete_subtasks)
    except Exception as e:
        raise IssueDeletionError(f"이슈 삭제 실패: {e}") from e

    return IssueDeletionResult(
        issue_key=issue_key,
        delete_subtasks=delete_subtasks,
    )


# ============================================================
# 이슈 조회 로직
# ============================================================

def get_issue(
    jira: Jira,
    issue_key: str,
    expand: Optional[str],
) -> IssueFetchResult:
    """이슈 정보를 조회합니다.

    Args:
        jira (Jira): Jira 클라이언트.
        issue_key (str): 이슈 키.
        expand (Optional[str]): 확장 옵션 (예: changelog,renderedFields).

    Returns:
        IssueFetchResult: 조회 결과.

    Raises:
        IssueFetchError: 조회 실패 또는 응답 형식 이상 시.
    """
    try:
        issue_data = jira.issue(issue_key, fields="*all", expand=expand)
    except Exception as e:
        raise IssueFetchError(f"이슈 조회 실패: {e}") from e

    if not isinstance(issue_data, dict):
        raise IssueFetchError("이슈 조회 응답이 비정상입니다.")

    return IssueFetchResult(
        issue_key=issue_key,
        issue_data=issue_data,
    )


# ============================================================
# CLI 인터페이스
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    """명령줄 인수 파서를 구성합니다.

    Returns:
        argparse.ArgumentParser: 파서.
    """
    parser = argparse.ArgumentParser(description="Jira 이슈 생성/수정 통합")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="이슈 생성")
    create_parser.add_argument("project_key", help="Jira 프로젝트 키 (예: PROJ)")
    create_parser.add_argument("issue_type", help="이슈 타입 (예: Task, Bug)")
    create_parser.add_argument("summary", help="이슈 요약")
    create_parser.add_argument("--description", help="이슈 설명")
    create_parser.add_argument(
        "--assignee",
        help="담당자(accountId 또는 name:사용자명). 기본은 accountId",
    )
    create_parser.add_argument("--labels", help="라벨 목록(쉼표로 구분)")
    create_parser.add_argument("--priority", help="우선순위 이름(예: Highest, High)")
    create_parser.add_argument("--components", help="컴포넌트 목록(쉼표로 구분)")
    create_parser.add_argument("--comment", help="이슈에 추가할 코멘트")
    create_parser.add_argument(
        "--attachment",
        action="append",
        help="첨부파일 경로 (여러 개는 --attachment 반복 또는 쉼표로 구분)",
    )
    create_parser.add_argument("--epic-link", help="에픽 링크 대상 이슈 키(회사 관리)")
    create_parser.add_argument("--epic", help="에픽 키(회사/팀 관리 공통)")
    create_parser.add_argument("--epic-name", help="에픽 이름(필드 없으면 summary로 반영)")

    update_parser = subparsers.add_parser("update", help="이슈 수정/첨부")
    update_parser.add_argument("issue_key", help="Jira 이슈 키 (예: PROJ-123)")
    update_parser.add_argument("--description", help="이슈 설명으로 설정할 내용")
    update_parser.add_argument("--summary", help="이슈 요약(summary)")
    update_parser.add_argument(
        "--assignee",
        help="담당자(accountId 또는 name:사용자명). 기본은 accountId",
    )
    update_parser.add_argument("--labels", help="라벨 목록(쉼표로 구분)")
    update_parser.add_argument("--priority", help="우선순위 이름(예: Highest, High)")
    update_parser.add_argument("--components", help="컴포넌트 목록(쉼표로 구분)")
    update_parser.add_argument("--comment", help="이슈에 추가할 코멘트")
    update_parser.add_argument(
        "--attachment",
        action="append",
        help="첨부파일 경로 (여러 개는 --attachment 반복 또는 쉼표로 구분)",
    )
    update_parser.add_argument("--epic-link", help="에픽 링크 대상 이슈 키(회사 관리)")
    update_parser.add_argument("--epic", help="에픽 키(회사/팀 관리 공통)")
    update_parser.add_argument("--epic-name", help="에픽 이름(필드 없으면 summary로 반영)")

    delete_parser = subparsers.add_parser("delete", help="이슈 삭제")
    delete_parser.add_argument("issue_key", help="Jira 이슈 키 (예: PROJ-123)")
    delete_parser.add_argument(
        "--keep-subtasks",
        action="store_true",
        help="서브태스크를 삭제하지 않음 (기본은 서브태스크 포함 삭제)",
    )
    delete_parser.add_argument(
        "--confirm",
        action="store_true",
        help="삭제 확인 플래그 (필수)",
    )
    delete_parser.add_argument(
        "--force",
        action="store_true",
        help="삭제 강제 플래그 (확인 없이 진행)",
    )

    get_parser = subparsers.add_parser("get", help="이슈 조회")
    get_parser.add_argument("issue_key", help="Jira 이슈 키 (예: PROJ-123)")
    get_parser.add_argument(
        "--expand",
        help="확장 옵션 (예: changelog,renderedFields)",
    )
    get_parser.add_argument(
        "--epic",
        action="store_true",
        help="에픽 필드만 요약 출력",
    )

    types_parser = subparsers.add_parser("types", help="이슈 타입 목록 조회")
    types_parser.add_argument(
        "--project",
        help="프로젝트 키로 필터링 (예: PROJ)",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """메인 진입점.

    Args:
        argv (Optional[Sequence[str]]): 인자 리스트 (None이면 sys.argv 사용).

    Returns:
        int: 종료 코드.
    """
    try:
        parser = build_parser()
        args = parser.parse_args(argv)

        config = Config.from_env()
        jira = create_jira_client(config)

        if args.command == "create":
            logger.info("이슈 생성 중... (Project: %s, Type: %s)", args.project_key, args.issue_type)

            epic_key = resolve_epic_key(args.epic_link, args.epic, IssueCreationError)
            result = create_issue_with_extras(
                jira=jira,
                project_key=args.project_key,
                issue_type=args.issue_type,
                summary=args.summary,
                description=args.description,
                assignee=args.assignee,
                labels=args.labels,
                priority=args.priority,
                components=args.components,
                comment=args.comment,
                attachment_paths=args.attachment,
                epic_link=epic_key,
                epic_name=args.epic_name,
            )

            logger.info("-" * 50)
            logger.info("✅ 이슈 생성 성공!")
            logger.info("Issue: %s", result.issue_key)
            logger.info("Issue ID: %s", result.issue_id)
            if result.updated_fields:
                logger.info("Fields: %s", ", ".join(result.updated_fields))
            if result.attachments:
                logger.info("Attachments: %s", ", ".join(result.attachments))
            if result.attachment_failures:
                logger.error("Attachment failures:")
                for failure in result.attachment_failures:
                    logger.error("- %s", failure)
            logger.info("-" * 50)

            return 1 if result.attachment_failures else 0

        if args.command == "update":
            logger.info("이슈 업데이트 중... (Key: %s)", args.issue_key)

            epic_key = resolve_epic_key(args.epic_link, args.epic, IssueUpdateError)
            result = update_issue(
                jira=jira,
                issue_key=args.issue_key,
                description=args.description,
                summary=args.summary,
                assignee=args.assignee,
                labels=args.labels,
                priority=args.priority,
                components=args.components,
                comment=args.comment,
                attachment_paths=args.attachment,
                epic_link=epic_key,
                epic_name=args.epic_name,
            )

            logger.info("-" * 50)
            logger.info("✅ 이슈 업데이트 성공!")
            logger.info("Issue: %s", result.issue_key)
            if result.updated_fields:
                logger.info("Updated fields: %s", ", ".join(result.updated_fields))
            if result.attachments:
                logger.info("Attachments: %s", ", ".join(result.attachments))
            if result.attachment_failures:
                logger.error("Attachment failures:")
                for failure in result.attachment_failures:
                    logger.error("- %s", failure)
            logger.info("-" * 50)

            return 1 if result.attachment_failures else 0

        if args.command == "delete":
            logger.info("이슈 삭제 중... (Key: %s)", args.issue_key)

            # 실수 방지: 명시적 확인이 없으면 삭제 금지
            if not (args.confirm or args.force):
                raise IssueDeletionError("삭제하려면 --confirm 또는 --force를 지정해야 합니다.")

            result = delete_issue(
                jira=jira,
                issue_key=args.issue_key,
                delete_subtasks=not args.keep_subtasks,
            )

            logger.info("-" * 50)
            logger.info("✅ 이슈 삭제 성공!")
            logger.info("Issue: %s", result.issue_key)
            logger.info("Delete subtasks: %s", "yes" if result.delete_subtasks else "no")
            logger.info("-" * 50)

            return 0

        if args.command == "get":
            logger.info("이슈 조회 중... (Key: %s)", args.issue_key)

            result = get_issue(
                jira=jira,
                issue_key=args.issue_key,
                expand=args.expand,
            )

            logger.info("-" * 50)
            logger.info("✅ 이슈 조회 성공!")
            logger.info("Issue: %s", result.issue_key)
            logger.info("-" * 50)
            if args.epic:
                epic_summary = build_epic_summary(jira, result.issue_data)
                print(json.dumps(epic_summary, ensure_ascii=False, indent=2))
                return 0

            print(json.dumps(result.issue_data, ensure_ascii=False, indent=2))

            return 0

        if args.command == "types":
            logger.info("이슈 타입 조회 중... (Project: %s)", args.project or "ALL")

            issue_types = get_issue_types(jira, args.project)

            logger.info("-" * 50)
            logger.info("✅ 이슈 타입 조회 성공!")
            logger.info("Count: %s", len(issue_types))
            logger.info("-" * 50)
            print(json.dumps(issue_types, ensure_ascii=False, indent=2))

            return 0

        raise JiraIssueError("지원하지 않는 명령입니다.")

    except ConfigurationError as e:
        logger.error("설정 오류: %s", e)
        return 1

    except (IssueUpdateError, IssueCreationError, IssueDeletionError, IssueFetchError, AttachmentUploadError) as e:
        logger.error("❌ %s", e)
        return 1

    except Exception as e:
        logger.exception("예상치 못한 오류 발생: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
