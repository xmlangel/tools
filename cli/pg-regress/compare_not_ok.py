#!/usr/bin/env python3
import argparse
import difflib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom


NOT_OK_RE = re.compile(r"^\s*not ok\s+\d+\s+-\s+(\S+)")


def clean_xml_string(s: str | None) -> str:
    if s is None:
        return ""
    illegal_chars_re = re.compile(u"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
    return illegal_chars_re.sub("", s)


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    """Resolve a path relative to a base directory.

    Args:
        base_dir (Path): Base directory for relative paths.
        value (str | None): Path value to resolve.

    Returns:
        Path | None: Resolved path or None if value is None.
    """
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path


def find_not_ok_tests(regression_path: Path) -> list[str]:
    tests: list[str] = []
    for line in regression_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = NOT_OK_RE.match(line)
        if m:
            tests.append(m.group(1))
    return tests


def resolve_expected(test: str, expected_dir: Path, ora_expected_dir: Path | None, mode: str) -> Path:
    if mode == "ags":
        if ora_expected_dir:
            ora_path = ora_expected_dir / f"{test}.out"
            if ora_path.exists():
                return ora_path
            ora_alt = ora_expected_dir / f"expected_{test}.out"
            if ora_alt.exists():
                return ora_alt
        return (ora_expected_dir or expected_dir) / f"{test}.out"
    return expected_dir / f"{test}.out"


def unified_diff(expected_path: Path, actual_path: Path, context: int) -> str:
    exp_text = expected_path.read_text(encoding="utf-8", errors="replace").splitlines()
    act_text = actual_path.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = difflib.unified_diff(
        exp_text,
        act_text,
        fromfile=str(expected_path),
        tofile=str(actual_path),
        n=context,
    )
    return "\n".join(diff)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"(failed to read: {path})"


def write_junit(
    output_path: Path,
    results: list[dict],
) -> None:
    testsuites = ET.Element("testsuites")
    testsuite = ET.SubElement(
        testsuites,
        "testsuite",
        {
            "name": "compare_not_ok",
            "tests": str(len(results)),
            "failures": str(sum(1 for r in results if r["status"] != "ok")),
            "errors": "0",
            "skipped": "0",
        },
    )

    for r in results:
        tc = ET.SubElement(testsuite, "testcase", name=r["test"])
        if r["status"] != "ok":
            fail = ET.SubElement(tc, "failure", {"message": "Test failed", "type": "Failure"})
            fail.text = clean_xml_string(r.get("message", r["status"]))
        if "expected_text" in r:
            exp_elem = ET.SubElement(tc, "expected")
            exp_elem.text = clean_xml_string(r.get("expected_text", ""))
        if "actual_text" in r:
            act_elem = ET.SubElement(tc, "actual")
            act_elem.text = clean_xml_string(r.get("actual_text", ""))
        sysout = ET.SubElement(tc, "system-out")
        sysout.text = clean_xml_string(r.get("output", ""))

    xml_str = ET.tostring(testsuites, encoding="utf-8")
    try:
        pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    except Exception:
        pretty = xml_str.decode("utf-8")
    output_path.write_text(pretty, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare expected vs actual outputs for NOT OK tests in regression.out",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory for regression/expected/results/sql paths",
    )
    parser.add_argument("--regression", default="regression.out", help="Path to regression.out")
    parser.add_argument("--expected-dir", default="expected", help="Base expected output dir")
    parser.add_argument("--ora-expected-dir", default="ora_expected/expected", help="Oracle expected dir")
    parser.add_argument("--results-dir", default="results", help="Actual results dir")
    parser.add_argument("--tests", nargs="*", help="Optional list of tests to compare")
    parser.add_argument("-U", "--context", type=int, default=3, help="Unified diff context lines")
    parser.add_argument(
        "--mode",
        choices=["pg", "ags"],
        default="ags",
        help="expected dir selection: pg=expected, ags=ora_expected/expected",
    )
    parser.add_argument(
        "--junit-output",
        default=None,
        help="Write JUnit XML to this path (e.g., junit.xml)",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    regression_path = resolve_path(base_dir, args.regression)
    if not regression_path.exists():
        print(f"regression.out not found: {regression_path}", file=sys.stderr)
        return 2

    tests = args.tests or find_not_ok_tests(regression_path)
    if not tests:
        print("No NOT OK tests found.")
        return 0

    expected_dir = resolve_path(base_dir, args.expected_dir)
    ora_expected_dir = resolve_path(base_dir, args.ora_expected_dir)
    results_dir = resolve_path(base_dir, args.results_dir)

    junit_results: list[dict] = []

    for test in tests:
        sql_path = base_dir / "sql" / f"{test}.sql"
        expected_path = resolve_expected(test, expected_dir, ora_expected_dir, args.mode)
        actual_path = results_dir / f"{test}.out"

        output_lines = [
            f"step: {sql_path}",
            f"expected: {expected_path}",
            f"actual: {actual_path}",
        ]

        if not expected_path.exists():
            msg = f"missing expected: {expected_path}"
            print(msg, file=sys.stderr)
            junit_results.append(
                {
                    "test": test,
                    "status": "missing_expected",
                    "message": msg,
                    "output": "\n".join(output_lines),
                    "expected_text": "",
                    "actual_text": read_text_safe(actual_path) if actual_path.exists() else "",
                }
            )
            continue
        if not actual_path.exists():
            msg = f"missing actual: {actual_path}"
            print(msg, file=sys.stderr)
            junit_results.append(
                {
                    "test": test,
                    "status": "missing_actual",
                    "message": msg,
                    "output": "\n".join(output_lines),
                    "expected_text": read_text_safe(expected_path),
                    "actual_text": "",
                }
            )
            continue

        diff = unified_diff(expected_path, actual_path, args.context)
        if diff:
            output_lines.append(diff)
            status = "diff"
            message = "diff found"
        else:
            output_lines.append("no diff")
            status = "ok"
            message = ""

        junit_results.append(
            {
                "test": test,
                "status": status,
                "message": message,
                "output": "\n".join(output_lines),
                "expected_text": read_text_safe(expected_path),
                "actual_text": read_text_safe(actual_path),
            }
        )

        print(f"== {test} ==")
        for line in output_lines:
            print(line)
        print()

    if args.junit_output:
        write_junit(Path(args.junit_output), junit_results)
        print(f"junit written: {args.junit_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
