#!/usr/bin/env python3
"""Update Jira issues for pg_regress failures.

This script reads regression.out to find "not ok" test cases, extracts
matching diff blocks from regression.diffs, and attaches renamed expected,
result, and SQL files to a Jira issue via ../jira_api/jira_cli.py.

Each run processes a single test case (the next pending failure). The user
provides the Jira issue key for that test, allowing 1:1 mapping across many
failures.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


DEFAULT_STATE_PATH = ".jira_regress_state.json"
DEFAULT_REGRESSION_OUT = "regression.out"
DEFAULT_REGRESSION_DIFFS = "regression.diffs"
DEFAULT_EXPECTED_DIR = os.path.join("ora_expected", "expected")
DEFAULT_RESULTS_DIR = "results"
DEFAULT_SQL_DIR = "sql"
JIRA_CLI = os.path.join("..", "jira_api", "jira_cli.py")
JIRA_DESCRIPTION_LIMIT = 32767
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"


class JiraRegressError(Exception):
    """Base error for Jira regression updates."""


class MissingFileError(JiraRegressError):
    """Raised when expected input files are missing."""


@dataclass(frozen=True)
class FailureItem:
    """Failure item metadata.

    Args:
        name (str): Test name.
        diff (str): Diff block text.
    """

    name: str
    diff: str


def load_failures(regression_out: str, regression_diffs: str) -> List[FailureItem]:
    """Load failures and their diff blocks.

    Args:
        regression_out (str): Path to regression.out.
        regression_diffs (str): Path to regression.diffs.

    Returns:
        List[FailureItem]: Ordered list of failures.

    Raises:
        MissingFileError: If required input files are missing.
    """
    if not os.path.exists(regression_out):
        raise MissingFileError(f"Missing regression output: {regression_out}")
    if not os.path.exists(regression_diffs):
        raise MissingFileError(f"Missing regression diffs: {regression_diffs}")

    failures = _parse_not_ok(regression_out)
    diff_map = _parse_diffs(regression_diffs)

    items: List[FailureItem] = []
    for name in failures:
        diff_text = diff_map.get(name, "")
        items.append(FailureItem(name=name, diff=diff_text))
    return items


def resolve_path(base_dir: str, value: str) -> str:
    """Resolve a path relative to a base directory.

    Args:
        base_dir (str): Base directory for relative paths.
        value (str): Path value to resolve.

    Returns:
        str: Resolved path.
    """
    if os.path.isabs(value):
        return value
    return os.path.join(base_dir, value)


def _parse_not_ok(regression_out: str) -> List[str]:
    """Parse regression.out to extract test names with 'not ok'.

    Args:
        regression_out (str): Path to regression.out.

    Returns:
        List[str]: Test names in order of appearance.
    """
    pattern = re.compile(r"^not ok\s+\d+\s+[-+]\s+([A-Za-z0-9_]+)\s+")
    names: List[str] = []
    with open(regression_out, "r", encoding="utf-8") as handle:
        for line in handle:
            match = pattern.search(line)
            if match:
                names.append(match.group(1))
    return names


def _parse_diffs(regression_diffs: str) -> Dict[str, str]:
    """Parse regression.diffs into a test->diff mapping.

    Args:
        regression_diffs (str): Path to regression.diffs.

    Returns:
        Dict[str, str]: Mapping from test name to full diff block text.
    """
    diff_header = re.compile(
        r"^diff -U3 .*?/(.+?)\.out .*?/results/\1\.out\s*$"
    )
    diff_map: Dict[str, List[str]] = {}
    current_name: Optional[str] = None

    with open(regression_diffs, "r", encoding="utf-8") as handle:
        for line in handle:
            header = diff_header.match(line)
            if header:
                current_name = header.group(1)
                diff_map[current_name] = [line.rstrip("\n")]
                continue
            if current_name is not None:
                diff_map[current_name].append(line.rstrip("\n"))

    return {name: "\n".join(lines).strip() for name, lines in diff_map.items()}


def load_state(state_path: str) -> Dict[str, str]:
    """Load mapping of processed test names to Jira issue keys.

    Args:
        state_path (str): Path to state JSON.

    Returns:
        Dict[str, str]: Mapping of test name -> issue key.
    """
    if not os.path.exists(state_path):
        return {}
    with open(state_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state_path: str, state: Dict[str, str]) -> None:
    """Persist mapping of processed test names to Jira issue keys.

    Args:
        state_path (str): Path to state JSON.
        state (Dict[str, str]): Mapping of test name -> issue key.
    """
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def next_failure(
    failures: List[FailureItem],
    state: Dict[str, str],
) -> Optional[FailureItem]:
    """Return the next unprocessed failure.

    Args:
        failures (List[FailureItem]): All failures.
        state (Dict[str, str]): Processed mapping.

    Returns:
        Optional[FailureItem]: Next failure or None if done.
    """
    for item in failures:
        if item.name not in state:
            return item
    return None


def build_description(item: FailureItem) -> str:
    """Build Jira description text for a failure.

    Args:
        item (FailureItem): Failure item.

    Returns:
        str: Description text.
    """
    header = f"pg_regress failure: {item.name}"
    if item.diff:
        return f"{header}\n\nregression.diffs block:\n{item.diff}"
    return f"{header}\n\nregression.diffs block not found."


def parse_bool(value: Optional[str]) -> bool:
    """Parse a boolean CLI value.

    Args:
        value (Optional[str]): Raw CLI value.

    Returns:
        bool: Parsed boolean.

    Raises:
        argparse.ArgumentTypeError: If the value cannot be parsed.
    """
    if value is None:
        return True
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(
        "Expected a boolean value (true/false/1/0/yes/no)."
    )


def build_jira_payload(
    item: FailureItem,
    attachments_dir: str,
    expected_dir: str,
    results_dir: str,
    sql_dir: str,
    attach_description: bool,
    include_diff: bool = False,
) -> Tuple[str, List[str]]:
    """Build Jira description and attachments.

    Args:
        item (FailureItem): Failure item.
        attachments_dir (str): Directory for attachments.
        expected_dir (str): Expected output directory.
        results_dir (str): Results output directory.
        sql_dir (str): SQL directory.
        attach_description (bool): Whether to attach description as a file.
        include_diff (bool): Whether to include diff attachment.

    Returns:
        Tuple[str, List[str]]: Description and attachment paths.

    Raises:
        MissingFileError: If required source files are missing.
    """
    full_description = build_description(item)
    attachments = prepare_attachments(
        item.name,
        attachments_dir,
        expected_dir,
        results_dir,
        sql_dir,
    )
    if include_diff:
        attachments.append(write_diff_attachment(item, attachments_dir))

    if not attach_description:
        return full_description, attachments

    description_attachment = os.path.join(
        attachments_dir, f"description_{item.name}.txt"
    )
    with open(description_attachment, "w", encoding="utf-8") as handle:
        handle.write(full_description)

    short_description = (
        f"pg_regress failure: {item.name}\n\n"
        "Description file attached.\n"
        f"name description_{item.name}"
    )
    return short_description, attachments + [description_attachment]


def warn_description_too_long(
    issue_key: Optional[str],
    test_name: str,
    length: int,
) -> None:
    """Warn when Jira description exceeds the limit and will be attached.

    Args:
        issue_key (Optional[str]): Jira issue key if known.
        test_name (str): Test name.
        length (int): Description length.
    """
    key_info = issue_key or "unknown"
    message = (
        f"Description too long ({length} chars) for issue {key_info} "
        f"test '{test_name}'. Attaching description file instead."
    )
    print(f"{ANSI_YELLOW}{message}{ANSI_RESET}")


def prepare_attachments(
    test_name: str,
    workspace_dir: str,
    expected_dir: str,
    results_dir: str,
    sql_dir: str,
) -> List[str]:
    """Create renamed attachments for Jira upload.

    Args:
        test_name (str): Test name.
        workspace_dir (str): Directory to store renamed files.
        expected_dir (str): Expected output directory.
        results_dir (str): Results output directory.
        sql_dir (str): SQL directory.

    Returns:
        List[str]: Attachment file paths.

    Raises:
        MissingFileError: If any required source file is missing.
    """
    expected_src = os.path.join(expected_dir, f"{test_name}.out")
    result_src = os.path.join(results_dir, f"{test_name}.out")
    sql_src = os.path.join(sql_dir, f"{test_name}.sql")

    missing = [path for path in [expected_src, result_src, sql_src] if not os.path.exists(path)]
    if missing:
        raise MissingFileError(f"Missing files for {test_name}: {', '.join(missing)}")

    os.makedirs(workspace_dir, exist_ok=True)

    expected_dst = os.path.join(workspace_dir, f"expected_{test_name}.out")
    result_dst = os.path.join(workspace_dir, f"result_{test_name}.out")
    sql_dst = os.path.join(workspace_dir, f"sql_{test_name}.sql")

    shutil.copyfile(expected_src, expected_dst)
    shutil.copyfile(result_src, result_dst)
    shutil.copyfile(sql_src, sql_dst)

    return [expected_dst, result_dst, sql_dst]


def run_jira_update(
    issue_key: str,
    description: str,
    attachments: List[str],
    dry_run: bool,
    epic_link: Optional[str] = None,
) -> None:
    """Run jira_cli.py update with description and attachments.

    Args:
        issue_key (str): Jira issue key.
        description (str): Description text.
        attachments (List[str]): Attachment paths.
        dry_run (bool): Whether to skip execution.
        epic_link (Optional[str]): Epic link issue key.

    Raises:
        JiraRegressError: If jira_cli.py update fails.
    """
    cmd = [
        "python",
        JIRA_CLI,
        "update",
        issue_key,
        "--description",
        description,
    ]
    if epic_link:
        cmd.extend(["--epic-link", epic_link])
    for attachment in attachments:
        cmd.extend(["--attachment", attachment])

    if dry_run:
        print("DRY RUN:", " ".join(cmd))
        return

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        combined = "\n".join([result.stdout, result.stderr])
        if "Attachment failures" in combined or "첨부파일 업로드 실패" in combined:
            print(
                f"{ANSI_YELLOW}jira_cli.py update had attachment failures "
                f"but issue update succeeded. See logs above.{ANSI_RESET}"
            )
            print(f"{ANSI_YELLOW}{combined.strip()}{ANSI_RESET}")
            return
        raise JiraRegressError(
            f"jira_cli.py update failed (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def fetch_issue_summary(issue_key: str) -> str:
    """Fetch Jira issue summary via jira_cli.py get.

    Args:
        issue_key (str): Jira issue key.

    Returns:
        str: Issue summary.

    Raises:
        JiraRegressError: If jira_cli.py get fails or summary missing.
    """
    cmd = ["python", JIRA_CLI, "get", issue_key]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise JiraRegressError(
            f"jira_cli.py get failed (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    raw = result.stdout.strip()
    if not raw:
        raise JiraRegressError("jira_cli.py get returned empty output.")

    try:
        issue_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JiraRegressError(
            "jira_cli.py get returned non-JSON output."
        ) from exc

    fields = issue_data.get("fields", {})
    summary = fields.get("summary")
    if not summary:
        raise JiraRegressError("Issue summary not found in Jira response.")
    return str(summary)


def issue_summary_matches_test(issue_key: str, test_name: str) -> bool:
    """Check if Jira summary contains the test name.

    Args:
        issue_key (str): Jira issue key.
        test_name (str): Test name.

    Returns:
        bool: True if summary contains test name.

    Raises:
        JiraRegressError: If Jira lookup fails.
    """
    summary = fetch_issue_summary(issue_key)
    return test_name.lower() in summary.lower()


def parse_created_issue_key(raw_output: str) -> str:
    """Parse Jira issue key from jira_cli.py create output.

    Args:
        raw_output (str): Combined stdout/stderr output.

    Returns:
        str: Issue key.

    Raises:
        JiraRegressError: If key cannot be parsed.
    """
    match = re.search(r"Issue:\s+([A-Z][A-Z0-9]+-\d+)", raw_output)
    if not match:
        raise JiraRegressError(
            "Failed to parse created issue key from jira_cli.py output."
        )
    return match.group(1)


def run_jira_create(
    project_key: str,
    issue_type: str,
    summary: str,
    description: Optional[str],
    attachments: List[str],
    dry_run: bool,
    epic_link: Optional[str] = None,
    epic_name: Optional[str] = None,
) -> Optional[str]:
    """Run jira_cli.py create with description and attachments.

    Args:
        project_key (str): Jira project key.
        issue_type (str): Jira issue type.
        summary (str): Issue summary.
        description (Optional[str]): Description text.
        attachments (List[str]): Attachment paths.
        dry_run (bool): Whether to skip execution.
        epic_link (Optional[str]): Epic link issue key.
        epic_name (Optional[str]): Epic name field value.

    Returns:
        Optional[str]: Created issue key if available.

    Raises:
        JiraRegressError: If jira_cli.py create fails.
    """
    cmd = [
        "python",
        JIRA_CLI,
        "create",
        project_key,
        issue_type,
        summary,
    ]
    if description is not None:
        cmd.extend(["--description", description])
    if epic_link:
        cmd.extend(["--epic-link", epic_link])
    if epic_name:
        cmd.extend(["--epic-name", epic_name])
    for attachment in attachments:
        cmd.extend(["--attachment", attachment])

    if dry_run:
        print("DRY RUN:", " ".join(cmd))
        return None

    result = subprocess.run(cmd, capture_output=True, text=True)
    combined = "\n".join([result.stdout, result.stderr])
    if result.returncode != 0:
        if "Attachment failures" in combined or "첨부파일 업로드 실패" in combined:
            print(
                f"{ANSI_YELLOW}jira_cli.py create had attachment failures "
                f"but issue creation succeeded. See logs above.{ANSI_RESET}"
            )
            print(f"{ANSI_YELLOW}{combined.strip()}{ANSI_RESET}")
            return parse_created_issue_key(combined)
        raise JiraRegressError(
            f"jira_cli.py create failed (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return parse_created_issue_key(combined.strip())


def build_summary(summary_format: str, test_name: str) -> str:
    """Build Jira summary from format.

    Args:
        summary_format (str): Summary format containing {test}.
        test_name (str): Test name.

    Returns:
        str: Rendered summary.

    Raises:
        JiraRegressError: If format is invalid or missing {test}.
    """
    if "{test}" not in summary_format:
        raise JiraRegressError(
            "Summary format must include '{test}' placeholder."
        )
    return summary_format.format(test=test_name)


def fetch_epic_metadata(issue_key: str) -> Dict[str, Optional[str]]:
    """Fetch Epic field metadata via jira_cli.py get --epic.

    Args:
        issue_key (str): Jira issue key.

    Returns:
        Dict[str, Optional[str]]: Epic metadata summary.

    Raises:
        JiraRegressError: If jira_cli.py get fails or output is invalid.
    """
    cmd = ["python", JIRA_CLI, "get", issue_key, "--epic"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise JiraRegressError(
            f"jira_cli.py get --epic failed (rc={result.returncode})\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    raw = result.stdout.strip()
    if not raw:
        raise JiraRegressError("jira_cli.py get --epic returned empty output.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JiraRegressError(
            "jira_cli.py get --epic returned non-JSON output."
        ) from exc

    return {
        "epic_link_field_id": data.get("epic_link_field_id"),
        "epic_name_field_id": data.get("epic_name_field_id"),
        "epic_link": data.get("epic_link"),
        "epic_name": data.get("epic_name"),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser.

    Returns:
        argparse.ArgumentParser: Parser.
    """
    parser = argparse.ArgumentParser(
        description="Update Jira issues for pg_regress failures."
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory containing regression/expected/results/sql files.",
    )
    parser.add_argument(
        "issue_key",
        nargs="?",
        help="Jira issue key (e.g., COIN-2) for the next failure.",
    )
    parser.add_argument(
        "--test",
        help="Specific test name to update (e.g., packages).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for issue keys per failure.",
    )
    parser.add_argument(
        "--description-attach",
        "--description_attach",
        nargs="?",
        const=True,
        default=False,
        type=parse_bool,
        help="Attach description as a file instead of inline text.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print jira_cli.py command without executing.",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Only generate attachment files without updating Jira "
        "(always writes description attachments).",
    )
    parser.add_argument(
        "--auto-create",
        action="store_true",
        help="Automatically create or update Jira issues for failures.",
    )
    parser.add_argument(
        "--project-key",
        help="Jira project key for auto-create (e.g., PROJ).",
    )
    parser.add_argument(
        "--issue-type",
        help="Jira issue type for auto-create (e.g., Bug).",
    )
    parser.add_argument(
        "--summary-format",
        help="Summary format for auto-create (must include {test}).",
    )
    parser.add_argument(
        "--duplicate-handling",
        choices=["update", "duplicate"],
        default="update",
        help="If a failure is already mapped, update or create a duplicate.",
    )
    parser.add_argument(
        "--epic-summary",
        help="Summary for auto-created Epic (required with --auto-create).",
    )
    parser.add_argument(
        "--epic-issue-type",
        default="Epic",
        help="Issue type name for auto-created Epic (default: Epic).",
    )
    parser.add_argument(
        "--epic-key",
        help="Use an existing Epic issue key instead of creating one.",
    )
    return parser


def prepare_attachments_only(
    items: List[FailureItem],
    attachments_root: str,
    expected_dir: str,
    results_dir: str,
    sql_dir: str,
    attach_description: bool,
) -> int:
    """Prepare attachment files only.

    Args:
        items (List[FailureItem]): Failure items to prepare.
        attachments_root (str): Root directory for attachments.
        expected_dir (str): Expected output directory.
        results_dir (str): Results output directory.
        sql_dir (str): SQL directory.
        attach_description (bool): Whether to include description files.

    Returns:
        int: Exit code.
    """
    for item in items:
        attachments_dir = os.path.join(attachments_root, item.name)
        if attach_description:
            build_jira_payload(
                item,
                attachments_dir,
                expected_dir,
                results_dir,
                sql_dir,
                attach_description,
            )
        else:
            prepare_attachments(
                item.name,
                attachments_dir,
                expected_dir,
                results_dir,
                sql_dir,
            )
        write_diff_attachment(item, attachments_dir)
        print(f"Prepared attachments for {item.name}.")
    return 0


def write_diff_attachment(item: FailureItem, attachments_dir: str) -> str:
    """Write regression diff block to an attachment file.

    Args:
        item (FailureItem): Failure item.
        attachments_dir (str): Directory to store attachment.

    Returns:
        str: Path to the diff attachment.
    """
    os.makedirs(attachments_dir, exist_ok=True)
    diff_path = os.path.join(attachments_dir, f"diff_{item.name}.diff")
    diff_text = item.diff or "regression.diffs block not found."
    with open(diff_path, "w", encoding="utf-8") as handle:
        handle.write(diff_text)
    return diff_path


def resolve_auto_create_items(
    failures: List[FailureItem],
    test_name: Optional[str],
) -> List[FailureItem]:
    """Resolve failure items for auto-create.

    Args:
        failures (List[FailureItem]): All failures.
        test_name (Optional[str]): Specific test name.

    Returns:
        List[FailureItem]: Selected items.

    Raises:
        JiraRegressError: If test name not found.
    """
    if test_name is None:
        return failures
    name_map = {item.name: item for item in failures}
    item = name_map.get(test_name)
    if item is None:
        raise JiraRegressError(f"Test not found in failures: {test_name}")
    return [item]


def run_auto_create(
    items: List[FailureItem],
    state: Dict[str, str],
    state_path: str,
    attachments_root: str,
    expected_dir: str,
    results_dir: str,
    sql_dir: str,
    project_key: str,
    issue_type: str,
    summary_format: str,
    duplicate_handling: str,
    dry_run: bool,
    epic_summary: str,
    epic_issue_type: str,
    epic_key: Optional[str],
) -> int:
    """Create or update Jira issues for failures.

    Args:
        items (List[FailureItem]): Failure items.
        state (Dict[str, str]): Mapping of test name -> issue key.
        project_key (str): Jira project key.
        issue_type (str): Jira issue type.
        summary_format (str): Summary format.
        duplicate_handling (str): update or duplicate.
        dry_run (bool): Whether to skip execution.
        epic_summary (str): Epic summary.
        epic_issue_type (str): Epic issue type name.
        epic_key (Optional[str]): Existing Epic key, if any.

    Returns:
        int: Exit code.
    """
    epic_issue_key = epic_key
    if not epic_issue_key:
        epic_issue_key = run_jira_create(
            project_key=project_key,
            issue_type=epic_issue_type,
            summary=epic_summary,
            description=None,
            attachments=[],
            dry_run=dry_run,
            epic_name=epic_summary,
        )
        if not epic_issue_key and dry_run:
            epic_issue_key = "DRY-RUN-EPIC"

    if epic_issue_key and not dry_run:
        epic_meta = fetch_epic_metadata(epic_issue_key)
        if not epic_meta.get("epic_link_field_id"):
            print(
                f"{ANSI_YELLOW}Warning: Epic Link field id not found via "
                f"jira_cli.py get --epic. Will rely on Jira defaults."
                f"{ANSI_RESET}"
            )

    for item in items:
        attachments_dir = os.path.join(attachments_root, item.name)
        description, attachments = build_jira_payload(
            item,
            attachments_dir,
            expected_dir,
            results_dir,
            sql_dir,
            True,
            include_diff=True,
        )
        summary = build_summary(summary_format, item.name)

        existing_key = state.get(item.name)
        if existing_key and duplicate_handling == "update":
            run_jira_update(
                existing_key,
                description,
                attachments,
                dry_run,
                epic_link=epic_issue_key,
            )
            print(f"Updated {item.name} -> {existing_key}.")
            continue

        issue_key = run_jira_create(
            project_key,
            issue_type,
            summary,
            description,
            attachments,
            dry_run,
            epic_link=epic_issue_key,
        )
        if issue_key:
            state[item.name] = issue_key
            save_state(state_path, state)
            print(f"Created {item.name} -> {issue_key}.")
        else:
            print(f"DRY RUN: would create issue for {item.name}.")

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point.

    Args:
        argv (Optional[Sequence[str]]): Arguments list.

    Returns:
        int: Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    base_dir = args.base_dir
    regression_out = resolve_path(base_dir, DEFAULT_REGRESSION_OUT)
    regression_diffs = resolve_path(base_dir, DEFAULT_REGRESSION_DIFFS)
    expected_dir = resolve_path(base_dir, DEFAULT_EXPECTED_DIR)
    results_dir = resolve_path(base_dir, DEFAULT_RESULTS_DIR)
    sql_dir = resolve_path(base_dir, DEFAULT_SQL_DIR)
    state_path = resolve_path(base_dir, DEFAULT_STATE_PATH)
    attachments_root = resolve_path(base_dir, ".jira_regress_attachments")

    failures = load_failures(regression_out, regression_diffs)
    if not failures:
        print("No failures found in regression.out.")
        return 0

    state = load_state(state_path)
    if args.auto_create:
        try:
            items = resolve_auto_create_items(failures, args.test)
        except JiraRegressError as exc:
            print(str(exc))
            return 1

        if not args.project_key or not args.issue_type or not args.summary_format:
            print(
                "auto-create requires --project-key, --issue-type, "
                "and --summary-format."
            )
            return 1
        if not args.epic_key and not args.epic_summary:
            print("auto-create requires --epic-summary or --epic-key.")
            return 1

        try:
            return run_auto_create(
                items=items,
                state=state,
                state_path=state_path,
                attachments_root=attachments_root,
                expected_dir=expected_dir,
                results_dir=results_dir,
                sql_dir=sql_dir,
                project_key=args.project_key,
                issue_type=args.issue_type,
                summary_format=args.summary_format,
                duplicate_handling=args.duplicate_handling,
                dry_run=args.dry_run,
                epic_summary=args.epic_summary or "",
                epic_issue_type=args.epic_issue_type,
                epic_key=args.epic_key,
            )
        except JiraRegressError as exc:
            print(f"Auto-create failed: {exc}")
            return 1

    if args.test:
        name_map = {item.name: item for item in failures}
        next_item = name_map.get(args.test)
        if next_item is None:
            print(f"Test not found in failures: {args.test}")
            return 1
        if args.prepare_only:
            return prepare_attachments_only(
                [next_item],
                attachments_root,
                expected_dir,
                results_dir,
                sql_dir,
                True,
            )
    elif args.issue_key and not args.interactive:
        next_item = next_failure(failures, state)
        if next_item is None:
            print("All failures already mapped.")
            return 0
        if args.prepare_only:
            return prepare_attachments_only(
                [next_item],
                attachments_root,
                expected_dir,
                results_dir,
                sql_dir,
                True,
            )
        try:
            if not issue_summary_matches_test(args.issue_key, next_item.name):
                print(
                    f"Issue {args.issue_key} summary does not include "
                    f"test name '{next_item.name}'."
                )
                return 1
        except JiraRegressError as exc:
            print(f"Failed to fetch Jira issue {args.issue_key}: {exc}")
            return 1
    else:
        if args.prepare_only:
            return prepare_attachments_only(
                failures,
                attachments_root,
                expected_dir,
                results_dir,
                sql_dir,
                True,
            )
        return run_interactive(
            failures,
            state,
            attachments_root,
            expected_dir,
            results_dir,
            sql_dir,
            args.dry_run,
            args.description_attach,
        )

    attach_description = args.description_attach
    description_text = build_description(next_item)
    if not attach_description and len(description_text) > JIRA_DESCRIPTION_LIMIT:
        attach_description = True
        warn_description_too_long(
            args.issue_key,
            next_item.name,
            len(description_text),
        )

    attachments_dir = os.path.join(attachments_root, next_item.name)
    description, attachments = build_jira_payload(
        next_item,
        attachments_dir,
        expected_dir,
        results_dir,
        sql_dir,
        attach_description,
    )

    run_jira_update(args.issue_key, description, attachments, args.dry_run)

    state[next_item.name] = args.issue_key
    save_state(state_path, state)

    remaining = len([item for item in failures if item.name not in state])
    print(
        f"Updated {next_item.name} -> {args.issue_key}. "
        f"Remaining failures: {remaining}."
    )
    return 0


def run_interactive(
    failures: List[FailureItem],
    state: Dict[str, str],
    attachments_root: str,
    expected_dir: str,
    results_dir: str,
    sql_dir: str,
    dry_run: bool,
    attach_description: bool,
) -> int:
    """Run interactive prompts for each failure.

    Args:
        failures (List[FailureItem]): All failures.
        state (Dict[str, str]): Processed mapping.
        attachments_root (str): Root directory for attachments.
        expected_dir (str): Expected output directory.
        results_dir (str): Results output directory.
        sql_dir (str): SQL directory.
        dry_run (bool): Whether to skip actual updates.
        attach_description (bool): Whether to attach description as a file.

    Returns:
        int: Exit code.
    """
    remaining = [item for item in failures if item.name not in state]
    if not remaining:
        print("All failures already mapped.")
        return 0

    for item in remaining:
        prompt = (
            f"not ok {item.name} issue key (empty=skip, q=quit): "
        )
        quit_requested = False
        while True:
            issue_key = input(prompt).strip()
            if not issue_key:
                print(f"Skipped {item.name}.")
                issue_key = ""
                break
            if issue_key.lower() in {"q", "quit", "exit"}:
                print("Stopped by user.")
                quit_requested = True
                issue_key = ""
                break
            try:
                if issue_summary_matches_test(issue_key, item.name):
                    break
            except JiraRegressError as exc:
                print(f"Failed to fetch Jira issue {issue_key}: {exc}")
            print(
                f"Issue {issue_key} summary does not include "
                f"test name '{item.name}'. Please re-enter."
            )

        if quit_requested:
            break
        if not issue_key:
            continue

        effective_attach_description = attach_description
        description_text = build_description(item)
        if (
            not effective_attach_description
            and len(description_text) > JIRA_DESCRIPTION_LIMIT
        ):
            effective_attach_description = True
            warn_description_too_long(
                issue_key,
                item.name,
                len(description_text),
            )

        attachments_dir = os.path.join(attachments_root, item.name)
        description, attachments = build_jira_payload(
            item,
            attachments_dir,
            expected_dir,
            results_dir,
            sql_dir,
            effective_attach_description,
        )
        run_jira_update(issue_key, description, attachments, dry_run)

        state[item.name] = issue_key
        save_state(STATE_PATH, state)
        left = len([it for it in failures if it.name not in state])
        print(f"Updated {item.name} -> {issue_key}. Remaining failures: {left}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
