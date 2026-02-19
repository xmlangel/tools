import os
from pathlib import Path

import pytest

import jira_cli
from conftest import record_junit_case


class DummyJira:
    def __init__(self):
        self.created_fields = None
        self.updated_fields = None
        self.comments = []
        self.attachments = []
        self.deleted = []
        self.issues = []

    def issue_create(self, fields):
        self.created_fields = fields
        return {"key": "COIN-1", "id": "10001"}

    def issue_update(self, issue_key, fields):
        self.updated_fields = {"issue_key": issue_key, "fields": fields}

    def add_comment(self, issue_key, comment):
        self.comments.append((issue_key, comment))

    def add_attachment(self, issue_key, attachment_path):
        self.attachments.append((issue_key, attachment_path))
        return {"filename": Path(attachment_path).name}

    def delete_issue(self, issue_key, delete_subtasks=True):
        self.deleted.append((issue_key, delete_subtasks))

    def issue(self, key, fields="*all", expand=None):
        self.issues.append((key, fields, expand))
        return {
            "id": "10001",
            "key": key,
            "fields": {"summary": "요약"},
        }


class DummyJiraBadCreate(DummyJira):
    def issue_create(self, fields):
        return "unexpected"


class DummyJiraBadGet(DummyJira):
    def issue(self, key, fields="*all", expand=None):
        return "unexpected"


class DummyJiraRaises(DummyJira):
    def issue_update(self, issue_key, fields):
        raise RuntimeError("boom")


def test_split_and_assignee_parsing(record_property):
    record_junit_case(
        record_property,
        description="CSV 파싱과 assignee 파싱이 규칙대로 동작한다.",
        step="CSV/assignee 입력을 각각 변환 함수에 전달한다.",
        actual="리스트/assignee 딕셔너리 반환.",
        expected="공백 제거 및 접두어 규칙에 맞는 결과.",
    )
    assert jira_cli._split_csv(None) is None
    assert jira_cli._split_csv("a, b, ,c") == ["a", "b", "c"]

    assert jira_cli._parse_assignee(None) is None
    assert jira_cli._parse_assignee("name:alice") == {"name": "alice"}
    assert jira_cli._parse_assignee("accountId:123") == {"accountId": "123"}
    assert jira_cli._parse_assignee("abcd") == {"accountId": "abcd"}


def test_create_issue_with_extras_and_attachment(tmp_path, record_property):
    record_junit_case(
        record_property,
        description="이슈 생성과 코멘트/첨부파일 처리 흐름을 검증한다.",
        step="더미 Jira로 create_issue_with_extras 호출.",
        actual="이슈 키/ID, 첨부파일 목록 반환.",
        expected="필드 매핑과 첨부 처리 성공.",
    )
    jira = DummyJira()
    attachment = tmp_path / "file.txt"
    attachment.write_text("hello")

    result = jira_cli.create_issue_with_extras(
        jira=jira,
        project_key="COIN",
        issue_type="Task",
        summary="요약",
        description="설명",
        assignee="accountId:123",
        labels="backend,urgent",
        priority="High",
        components="API,Infra",
        comment="초기 코멘트",
        attachment_paths=[str(attachment)],
    )

    assert result.issue_key == "COIN-1"
    assert result.issue_id == "10001"
    assert "comment" in result.updated_fields
    assert result.attachments == ["file.txt"]
    assert result.attachment_failures == []

    assert jira.created_fields["project"] == {"key": "COIN"}
    assert jira.created_fields["issuetype"] == {"name": "Task"}
    assert jira.created_fields["summary"] == "요약"
    assert jira.created_fields["description"] == "설명"
    assert jira.created_fields["assignee"] == {"accountId": "123"}
    assert jira.created_fields["labels"] == ["backend", "urgent"]
    assert jira.created_fields["priority"] == {"name": "High"}
    assert jira.created_fields["components"] == [{"name": "API"}, {"name": "Infra"}]


def test_create_issue_bad_response(record_property):
    record_junit_case(
        record_property,
        description="이슈 생성 응답이 비정상일 때 예외를 던진다.",
        step="issue_create가 비딕셔너리를 반환하도록 설정.",
        actual="IssueCreationError 발생.",
        expected="비정상 응답 형식 검증.",
    )
    jira = DummyJiraBadCreate()
    with pytest.raises(jira_cli.IssueCreationError):
        jira_cli.create_issue(
            jira=jira,
            project_key="COIN",
            issue_type="Task",
            summary="요약",
            description=None,
            assignee=None,
            labels=None,
            priority=None,
            components=None,
        )


def test_update_issue_fields_and_comment(tmp_path, record_property):
    record_junit_case(
        record_property,
        description="이슈 업데이트와 코멘트/첨부 처리 성공을 검증한다.",
        step="update_issue로 다양한 필드와 첨부를 전달.",
        actual="업데이트 결과 및 첨부 목록 반환.",
        expected="모든 필드가 업데이트에 포함됨.",
    )
    jira = DummyJira()
    attachment = tmp_path / "file.txt"
    attachment.write_text("hello")

    result = jira_cli.update_issue(
        jira=jira,
        issue_key="COIN-2",
        description="설명",
        summary="요약",
        assignee="name:alice",
        labels="a,b",
        priority="High",
        components="API",
        comment="코멘트",
        attachment_paths=[str(attachment)],
    )

    assert result.issue_key == "COIN-2"
    assert "description" in result.updated_fields
    assert "summary" in result.updated_fields
    assert "assignee" in result.updated_fields
    assert "labels" in result.updated_fields
    assert "priority" in result.updated_fields
    assert "components" in result.updated_fields
    assert "comment" in result.updated_fields
    assert result.attachments == ["file.txt"]
    assert result.attachment_failures == []

    assert jira.updated_fields["issue_key"] == "COIN-2"
    assert jira.updated_fields["fields"]["assignee"] == {"name": "alice"}


def test_update_issue_no_changes_raises(record_property):
    record_junit_case(
        record_property,
        description="수정 내용이 없으면 예외를 발생시킨다.",
        step="모든 옵션을 None으로 update_issue 호출.",
        actual="IssueUpdateError 발생.",
        expected="수정 내용 없음 처리.",
    )
    jira = DummyJira()
    with pytest.raises(jira_cli.IssueUpdateError):
        jira_cli.update_issue(
            jira=jira,
            issue_key="COIN-3",
            description=None,
            summary=None,
            assignee=None,
            labels=None,
            priority=None,
            components=None,
            comment=None,
            attachment_paths=None,
        )


def test_update_issue_fields_error(record_property):
    record_junit_case(
        record_property,
        description="필드 업데이트 실패 시 예외를 래핑한다.",
        step="issue_update가 예외를 던지는 더미 Jira 사용.",
        actual="IssueUpdateError 발생.",
        expected="원인 예외를 업데이트 오류로 변환.",
    )
    jira = DummyJiraRaises()
    with pytest.raises(jira_cli.IssueUpdateError):
        jira_cli.update_issue_fields(jira, "COIN-4", {"summary": "x"})


def test_upload_attachment_missing_file(record_property):
    record_junit_case(
        record_property,
        description="첨부파일이 없으면 업로드 오류를 반환한다.",
        step="존재하지 않는 파일 경로로 upload_attachment 호출.",
        actual="AttachmentUploadError 발생.",
        expected="파일 없음 검증.",
    )
    jira = DummyJira()
    with pytest.raises(jira_cli.AttachmentUploadError):
        jira_cli.upload_attachment(jira, "COIN-5", "/no/such/file.txt")


def test_main_create_and_update(monkeypatch, tmp_path, record_property):
    record_junit_case(
        record_property,
        description="CLI create/update/delete 흐름이 정상 종료된다.",
        step="main에 create/update/delete 인자를 순차 전달.",
        actual="각 호출의 종료 코드 0.",
        expected="CLI 플로우 정상 동작.",
    )
    jira = DummyJira()
    attachment = tmp_path / "file.txt"
    attachment.write_text("hello")

    monkeypatch.setattr(jira_cli, "create_jira_client", lambda config: jira)
    monkeypatch.setattr(jira_cli.Config, "from_env", classmethod(lambda cls: jira_cli.Config("url", "user", "token")))

    exit_code = jira_cli.main(
        [
            "create",
            "COIN",
            "Task",
            "요약",
            "--comment",
            "코멘트",
            "--attachment",
            str(attachment),
        ]
    )
    assert exit_code == 0

    exit_code = jira_cli.main(
        [
            "delete",
            "COIN-7",
            "--confirm",
        ]
    )
    assert exit_code == 0

    exit_code = jira_cli.main(
        [
            "update",
            "COIN-6",
            "--summary",
            "요약",
            "--comment",
            "코멘트",
        ]
    )
    assert exit_code == 0


def test_delete_issue_calls_api(record_property):
    record_junit_case(
        record_property,
        description="이슈 삭제 API 호출이 수행된다.",
        step="delete_issue 호출 후 더미 상태 확인.",
        actual="delete_issue 호출 내역 기록.",
        expected="issue_key와 delete_subtasks가 기록됨.",
    )
    jira = DummyJira()
    result = jira_cli.delete_issue(jira, "COIN-8", delete_subtasks=False)
    assert result.issue_key == "COIN-8"
    assert result.delete_subtasks is False
    assert jira.deleted == [("COIN-8", False)]


def test_get_issue_success(record_property):
    record_junit_case(
        record_property,
        description="이슈 조회가 정상적으로 수행된다.",
        step="get_issue로 이슈 키를 조회한다.",
        actual="이슈 데이터와 키를 반환한다.",
        expected="요청한 키가 결과에 포함된다.",
    )
    jira = DummyJira()
    result = jira_cli.get_issue(jira, "COIN-10", expand="changelog")
    assert result.issue_key == "COIN-10"
    assert result.issue_data["key"] == "COIN-10"
    assert jira.issues == [("COIN-10", "*all", "changelog")]


def test_get_issue_bad_response(record_property):
    record_junit_case(
        record_property,
        description="이슈 조회 응답이 비정상일 때 예외를 던진다.",
        step="issue가 문자열을 반환하는 더미 Jira 사용.",
        actual="IssueFetchError 발생.",
        expected="응답 형식 검증.",
    )
    jira = DummyJiraBadGet()
    with pytest.raises(jira_cli.IssueFetchError):
        jira_cli.get_issue(jira, "COIN-11", expand=None)


def test_main_delete_requires_confirm(monkeypatch, record_property):
    record_junit_case(
        record_property,
        description="삭제는 confirm/force가 없으면 실패한다.",
        step="delete 명령에 confirm/force 없이 실행.",
        actual="종료 코드 1.",
        expected="안전장치 동작.",
    )
    jira = DummyJira()
    monkeypatch.setattr(jira_cli, "create_jira_client", lambda config: jira)
    monkeypatch.setattr(jira_cli.Config, "from_env", classmethod(lambda cls: jira_cli.Config("url", "user", "token")))

    exit_code = jira_cli.main(
        [
            "delete",
            "COIN-9",
        ]
    )
    assert exit_code == 1


def test_main_get(monkeypatch, capsys, record_property):
    record_junit_case(
        record_property,
        description="CLI get 명령이 정상 종료된다.",
        step="main에 get 인자를 전달한다.",
        actual="종료 코드 0과 JSON 출력.",
        expected="이슈 키가 출력 JSON에 포함된다.",
    )
    jira = DummyJira()
    monkeypatch.setattr(jira_cli, "create_jira_client", lambda config: jira)
    monkeypatch.setattr(jira_cli.Config, "from_env", classmethod(lambda cls: jira_cli.Config("url", "user", "token")))

    exit_code = jira_cli.main(
        [
            "get",
            "COIN-12",
            "--expand",
            "changelog",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "COIN-12" in captured.out
