"""
PostgreSQL 회귀 테스트(regression test) 결과에서 실패한 테스트(not ok)를 찾아 
예상 결과(expected)와 실제 결과(results)를 비교하고 diff를 생성하는 스크립트입니다.
필요에 따라 JUnit XML 형식으로 결과를 출력할 수 있습니다.
"""
import argparse
import difflib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom


# regression.out 파일에서 "not ok"로 표시된 테스트 라인을 찾기 위한 정규식
NOT_OK_RE = re.compile(r"^\s*not ok\s+\d+\s+-\s+(\S+)")


def clean_xml_string(s: str | None) -> str:
    """XML 파일에 포함될 수 없는 유효하지 않은 제어 문자들을 제거합니다."""
    if s is None:
        return ""
    illegal_chars_re = re.compile(u"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
    return illegal_chars_re.sub("", s)


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    """기준 디렉토리(base_dir)를 사용하여 상대 경로를 절대 경로로 변환합니다.

    Args:
        base_dir (Path): 상대 경로의 기준이 되는 디렉토리.
        value (str | None): 변환할 경로 문자열.

    Returns:
        Path | None: 변환된 Path 객체 또는 None.
    """
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return base_dir / path


def find_not_ok_tests(regression_path: Path) -> list[str]:
    """regression.out 파일을 읽어 실패(not ok)한 테스트 이름 목록을 반환합니다."""
    tests: list[str] = []
    for line in regression_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = NOT_OK_RE.match(line)
        if m:
            tests.append(m.group(1))
    return tests


def resolve_expected(test: str, expected_dir: Path, ora_expected_dir: Path | None, mode: str) -> Path:
    """테스트 모드(pg/ags)에 따라 적절한 expected(.out) 파일 경로를 결정합니다."""
    if mode == "ags":
        # ags 모드일 경우 Oracle용 expected 디렉토리를 우선 확인합니다.
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
    """두 파일 간의 차이점(Unified Diff)을 생성합니다."""
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
    """파일을 안전하게 읽으며, 실패 시 에러 메시지를 반환합니다."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"(failed to read: {path})"


def write_junit(
    output_path: Path,
    results: list[dict],
) -> None:
    """비교 결과를 JUnit XML 형식으로 파일에 저장합니다."""
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
        # 가독성을 위해 Pretty Print 적용
        pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    except Exception:
        pretty = xml_str.decode("utf-8")
    output_path.write_text(pretty, encoding="utf-8")


def main() -> int:
    """메인 실행 함수: 인자를 파싱하고 실패한 테스트들을 비교합니다."""
    parser = argparse.ArgumentParser(
        description="regression.out 파일에서 NOT OK로 표시된 테스트들의 예상 결과와 실제 결과를 비교합니다.",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="회귀 테스트 관련 파일들이 위치한 기본 디렉토리",
    )
    parser.add_argument("--regression", default="regression.out", help="regression.out 파일 경로")
    parser.add_argument("--expected-dir", default="expected", help="표준 예상 결과 디렉토리")
    parser.add_argument("--ora-expected-dir", default="ora_expected/expected", help="Oracle 호환 예상 결과 디렉토리")
    parser.add_argument("--results-dir", default="results", help="실제 실행 결과 디렉토리")
    parser.add_argument("--tests", nargs="*", help="비교할 특정 테스트 목록 (지정하지 않으면 실패한 모든 테스트 대상)")
    parser.add_argument("-U", "--context", type=int, default=3, help="Diff 생성 시 전후 맥락 라인 수")
    parser.add_argument(
        "--mode",
        choices=["pg", "ags"],
        default="ags",
        help="예상 결과 디렉토리 선택 모드: pg(표준), ags(Oracle 호환 우선)",
    )
    parser.add_argument(
        "--junit-output",
        default=None,
        help="JUnit XML 결과를 저장할 경로 (예: junit.xml)",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    regression_path = resolve_path(base_dir, args.regression)
    if not regression_path.exists():
        print(f"regression.out 파일을 찾을 수 없습니다: {regression_path}", file=sys.stderr)
        return 2

    # 명시적인 테스트 목록이 없으면 regression.out에서 실패한 테스트를 찾음
    tests = args.tests or find_not_ok_tests(regression_path)
    if not tests:
        print("실패(NOT OK)한 테스트가 없습니다.")
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

        # 파일 존재 여부 확인
        if not expected_path.exists():
            msg = f"예상 결과 파일 없음: {expected_path}"
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
            msg = f"실제 결과 파일 없음: {actual_path}"
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

        # Diff 생성 및 상태 결정
        diff = unified_diff(expected_path, actual_path, args.context)
        if diff:
            output_lines.append(diff)
            status = "diff"
            message = "차이점 발견"
        else:
            output_lines.append("차이점 없음")
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

    # JUnit XML 출력
    if args.junit_output:
        write_junit(Path(args.junit_output), junit_results)
        print(f"JUnit XML이 생성되었습니다: {args.junit_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
