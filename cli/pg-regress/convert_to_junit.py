"""
PostgreSQL 회귀 테스트 결과를 JUnit XML 형식으로 변환하는 리팩토링된 스크립트입니다.
테스트 결과를 상세히 분석하여 SQL 단계별 실행 결과와 diff 요약을 XML에 포함합니다.
"""
import sys
import re
import os
import argparse
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET
from xml.dom import minidom
from datetime import datetime

# --- 데이터 모델 ---

@dataclass
class TestStep:
    """테스트 실행의 개별 단계를 나타내는 데이터 클래스"""
    sql: str
    expected: str = ""
    actual: str = ""
    start_line: int = 0
    end_line: int = 0
    index: int = 0

@dataclass
class TestCaseResult:
    """개별 테스트 케이스의 결과를 나타내는 데이터 클래스"""
    name: str
    classname: str
    time: float
    status: str  # 'ok' or 'not ok'
    steps: List[TestStep] = field(default_factory=list)
    failure_message: str = ""
    diff_content: str = ""
    full_actual: str = ""

# --- 유틸리티 클래스 ---

class XMLUtils:
    """XML 조작 및 문자열 세정을 위한 유틸리티 클래스"""
    ILLEGAL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]')

    @classmethod
    def clean_string(cls, s: Optional[str]) -> str:
        """XML에서 사용할 수 없는 유효하지 않은 문자들을 제거합니다."""
        if s is None:
            return ""
        return cls.ILLEGAL_CHARS_RE.sub('', str(s))

    @staticmethod
    def truncate_text(s: str, limit: int) -> str:
        """텍스트가 너무 길 경우 지정된 길이에서 자르고 생략 표시를 추가합니다."""
        if not s or limit <= 0 or len(s) <= limit:
            return s or ""
        return s[:limit] + f"\n...[truncated {len(s) - limit} chars]..."

    @staticmethod
    def prettify(elem: ET.Element) -> str:
        """ElementTree 요소를 읽기 좋은 XML 문자열로 변환합니다."""
        rough_string = ET.tostring(elem, 'utf-8')
        try:
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception:
            return rough_string.decode('utf-8')

# --- 파서 클래스 ---

class RegressionParser:
    """PostgreSQL 회귀 테스트 결과 파일들을 파싱하는 클래스"""
    
    # 정규표현식 패턴 캐싱
    RE_OUT_LINE = re.compile(r'^(ok|not ok)\s+(\d+)\s+([-+])\s+(\S+)\s+(\d+)\s+ms')
    RE_GROUP = re.compile(r'# (parallel group \(.*?\))')
    RE_DIFF_HEADER = re.compile(r'^diff -U\d+ .*?/(?:expected|ora_expected)/(.+?)\.out .*?/results/\1\.out')
    RE_HUNK_HEADER = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')
    
    SQL_KEYWORDS = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
                    'ALTER', 'CALL', 'DO', '\\', 'BEGIN', 'COMMIT', 'ROLLBACK', '-- ')

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.results_dir = os.path.join(base_dir, "results")

    def parse_regression_out(self, file_path: str) -> List[TestCaseResult]:
        """regression.out 파일을 파싱하여 테스트 케이스 목록을 반환합니다."""
        test_cases = []
        current_group = "Default Group"
        
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            return []

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                # 병렬 그룹 정보 확인
                if line.startswith("# parallel group"):
                    match = self.RE_GROUP.search(line)
                    current_group = match.group(1) if match else line[1:].split(":")[0].strip()
                    continue
                
                # 테스트 결과 라인 확인
                match = self.RE_OUT_LINE.match(line)
                if match:
                    status, _, _, test_name, duration_ms = match.groups()
                    test_cases.append(TestCaseResult(
                        name=test_name,
                        classname=current_group,
                        time=int(duration_ms) / 1000.0,
                        status=status
                    ))
        return test_cases

    def parse_regression_diffs(self, diff_file: str) -> Dict[str, str]:
        """regression.diffs 파일을 파싱하여 테스트명별 diff 내용을 매핑합니다."""
        diffs = {}
        if not os.path.exists(diff_file):
            return diffs
            
        current_test = None
        current_content = []
        
        with open(diff_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                match = self.RE_DIFF_HEADER.match(line)
                if match:
                    if current_test:
                        diffs[current_test] = "".join(current_content)
                    current_test = match.group(1)
                    current_content = [line]
                elif current_test:
                    current_content.append(line)
                    
            if current_test:
                diffs[current_test] = "".join(current_content)
        return diffs

    def get_out_file_steps(self, filepath: str) -> List[TestStep]:
        """PostgreSQL .out 파일을 파싱하여 SQL 단계(step) 목록을 추출합니다."""
        if not os.path.exists(filepath):
            return []
        
        steps = []
        current_sql = []
        start_line = 1
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                # 새로운 SQL 구문 시작인지 판단 (휴리스틱)
                is_new = any(line.startswith(kw) for kw in self.SQL_KEYWORDS) and not line.startswith(' ')
                
                if is_new:
                    if current_sql:
                        steps.append(TestStep(
                            sql="\n".join(current_sql).strip(),
                            start_line=start_line,
                            end_line=i,
                            index=len(steps) + 1
                        ))
                    current_sql = [line.rstrip()]
                    start_line = i + 1
                elif current_sql:
                    current_sql.append(line.rstrip())
            
            if current_sql:
                steps.append(TestStep(
                    sql="\n".join(current_sql).strip(),
                    start_line=start_line,
                    end_line=len(lines),
                    index=len(steps) + 1
                ))
        return steps

    def parse_diff_hunks(self, diff_content: str) -> List[Dict]:
        """diff 내용에서 hunk(변경 블록) 정보를 추출합니다."""
        hunks = []
        if not diff_content:
            return hunks
            
        current_hunk = None
        for line in diff_content.splitlines():
            match = self.RE_HUNK_HEADER.match(line)
            if match:
                if current_hunk: hunks.append(current_hunk)
                current_hunk = {
                    'exp_start': int(match.group(1)),
                    'act_start': int(match.group(3)),
                    'lines': []
                }
            elif current_hunk:
                current_hunk['lines'].append(line)
        if current_hunk: hunks.append(current_hunk)
        return hunks

    def read_file_safe(self, filepath: str) -> str:
        """파일을 안전하게 읽어 문자열로 반환합니다."""
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {filepath}: {str(e)}"

# --- 리포터 클래스 ---

class JUnitXMLGenerator:
    """파싱된 데이터를 기반으로 JUnit XML을 생성하는 클래스"""

    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps

    def generate(self, test_results: List[TestCaseResult], output_path: str):
        """JUnit XML 파일 생성 및 저장"""
        root = ET.Element('testsuites')
        failures_count = len([t for t in test_results if t.status == 'not ok'])
        
        suite = ET.SubElement(root, 'testsuite', {
            'name': 'PostgreSQL Regression Tests',
            'tests': str(len(test_results)),
            'failures': str(failures_count),
            'errors': '0',
            'skipped': '0'
        })
        
        for tr in test_results:
            self._add_test_case(suite, tr)
            
        pretty_xml = XMLUtils.prettify(root)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def _add_test_case(self, suite: ET.Element, tr: TestCaseResult):
        tc_elem = ET.SubElement(suite, 'testcase', {
            'name': tr.name,
            'classname': tr.classname,
            'time': str(tr.time)
        })
        
        # 기본 출력 정보
        sys_out = ET.SubElement(tc_elem, 'system-out')
        sys_out.text = XMLUtils.clean_string(tr.full_actual)
        
        sys_err = ET.SubElement(tc_elem, 'system-err')
        sys_err.text = XMLUtils.clean_string(self._format_steps_for_text(tr.steps))
        
        # 실패 정보 처리
        if tr.status == 'not ok':
            failure = ET.SubElement(tc_elem, 'failure', {
                'message': 'Test failed',
                'type': 'Failure'
            })
            failure.text = XMLUtils.clean_string(tr.failure_message)
            self._add_steps_xml(failure, tr.steps)
            
            # 호환성을 위해 첫 번째 실패 단계를 상위 태그에 추가
            if tr.steps:
                ET.SubElement(failure, 'expected').text = XMLUtils.clean_string(tr.steps[0].expected)
                ET.SubElement(failure, 'actual').text = XMLUtils.clean_string(tr.steps[0].actual)
        else:
            # 성공한 케이스도 단계 정보가 있다면 추가
            if tr.steps:
                self._add_steps_xml(tc_elem, tr.steps)
                ET.SubElement(tc_elem, 'expected').text = XMLUtils.clean_string(tr.steps[0].expected)
                ET.SubElement(tc_elem, 'actual').text = XMLUtils.clean_string(tr.steps[0].actual)

    def _add_steps_xml(self, parent: ET.Element, steps: List[TestStep]):
        steps_elem = ET.SubElement(parent, 'steps')
        for s in steps:
            step_elem = ET.SubElement(steps_elem, 'step', {'index': str(s.index)})
            ET.SubElement(step_elem, 'sql').text = XMLUtils.clean_string(s.sql)
            ET.SubElement(step_elem, 'expected').text = XMLUtils.clean_string(s.expected)
            ET.SubElement(step_elem, 'actual').text = XMLUtils.clean_string(s.actual)

    def _format_steps_for_text(self, steps: List[TestStep]) -> str:
        """system-err 등에 포함할 텍스트 형식의 단계 요약"""
        if not steps: return ""
        
        lines = ["", "[STEPS]"]
        for s in steps[:self.max_steps]:
            lines.append(f"STEP {s.index}:")
            lines.append(s.sql or "(no sql)")
            lines.append("EXPECTED:")
            lines.append(XMLUtils.truncate_text(s.expected, 8000))
            lines.append("ACTUAL:")
            lines.append(XMLUtils.truncate_text(s.actual, 8000))
            lines.append("-" * 40)
            
        if len(steps) > self.max_steps:
            lines.append(f"... and {len(steps) - self.max_steps} more steps (not shown)")
            lines.append("-" * 40)
        return "\n".join(lines)

# --- 메인 변환 클래스 ---

class JUnitConverter:
    """전체 변환 절차를 오케스트레이션하는 클래스"""

    def __init__(self, args):
        self.args = args
        self.base_dir, self.reg_out, self.reg_diffs = self._normalize_paths()
        self.parser = RegressionParser(self.base_dir)
        self.generator = JUnitXMLGenerator()
        
        # 모드에 따른 예상 결과 디렉토리 설정
        self.expected_dir = os.path.join(self.base_dir, "ora_expected" if args.mode == 'ags' else "expected")
        self.fallback_dir = os.path.join(self.base_dir, "expected" if args.mode == 'ags' else "ora_expected")

    def _normalize_paths(self) -> Tuple[str, str, str]:
        """경로 중복 결합 버그를 수정하고 정규화된 경로를 반환합니다."""
        reg_out_arg = self.args.regression_out
        
        # regression_out이 디렉토리인 경우
        if os.path.isdir(reg_out_arg):
            base_dir = reg_out_arg
            reg_out = os.path.join(base_dir, "regression.out")
        else:
            base_dir = self.args.base_dir or os.path.dirname(reg_out_arg) or "."
            reg_out = reg_out_arg
            
        reg_diffs = self.args.regression_diffs
        if not os.path.isabs(reg_diffs) and base_dir != ".":
            # 이미 regression_diffs가 base_dir 경로를 포함하고 있는지 확인
            potential_diffs = os.path.join(base_dir, os.path.basename(reg_diffs))
            if os.path.exists(potential_diffs):
                reg_diffs = potential_diffs
                
        return base_dir, reg_out, reg_diffs

    def convert(self):
        """변환 프로세스 실행"""
        print(f"변환 시작: {self.reg_out}")
        
        test_cases = self.parser.parse_regression_out(self.reg_out)
        diff_map = self.parser.parse_regression_diffs(self.reg_diffs)
        
        for tc in test_cases:
            self._process_test_case(tc, diff_map)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"pg_test_result_make_check_{timestamp}.xml"
        
        self.generator.generate(test_cases, output_file)
        print(f"변환 성공: {output_file} ({len(test_cases)} cases)")

    def _process_test_case(self, tc: TestCaseResult, diff_map: Dict[str, str]):
        """개별 테스트 케이스의 상세 정보(단계, 실패 메시지 등)를 채웁니다."""
        results_dir = self.parser.results_dir
        actual_path = os.path.join(results_dir, f"{tc.name}.out")
        expected_path = self._find_expected_file(tc.name)
        
        tc.full_actual = self.parser.read_file_safe(actual_path)
        
        actual_steps = self.parser.get_out_file_steps(actual_path)
        expected_steps = self.parser.get_out_file_steps(expected_path)
        
        if tc.status == 'not ok':
            tc.diff_content = diff_map.get(tc.name, "")
            self._handle_failure(tc, actual_steps, expected_steps, expected_path, actual_path)
        else:
            self._handle_success(tc, actual_steps, expected_steps, expected_path, actual_path)

    def _find_expected_file(self, test_name: str) -> str:
        """기본 및 대체 디렉토리에서 예상 결과 파일을 찾습니다."""
        path = os.path.join(self.expected_dir, f"{test_name}.out")
        if not os.path.exists(path):
            alt_path = os.path.join(self.fallback_dir, f"{test_name}.out")
            if os.path.exists(alt_path):
                return alt_path
        return path

    def _handle_failure(self, tc: TestCaseResult, actual_steps: List[TestStep], 
                        expected_steps: List[TestStep], exp_path: str, act_path: str):
        """실패한 테스트 케이스의 상세 정보 구성"""
        hunks = self.parser.parse_diff_hunks(tc.diff_content)
        failure_lines = [f"[FAIL] {tc.name}\n"]
        
        if hunks:
            for i, hunk in enumerate(hunks):
                # hunk가 시작되는 실제 결과의 단계를 찾음
                target_step = next((s for s in actual_steps if s.start_line <= hunk['act_start'] <= s.end_line), None)
                
                exp_val = "\n".join(l[1:] for l in hunk['lines'] if l.startswith('-') and not l.startswith('---'))
                act_val = "\n".join(l[1:] for l in hunk['lines'] if l.startswith('+') and not l.startswith('+++'))
                
                sql = target_step.sql if target_step else f"(hunk at line {hunk['act_start']})"
                
                step = TestStep(
                    sql=sql,
                    expected=exp_val.strip() or "(no expected output)",
                    actual=act_val.strip() or "(no actual output)",
                    index=i + 1
                )
                tc.steps.append(step)
                
                if i < 10: # 요약에는 최대 10개만
                    failure_lines.append(f"STEP {step.index}:\n{step.sql}\nEXPECTED:\n{step.expected}\nACTUAL:\n{step.actual}\n" + "-"*40)
            
            if len(hunks) > 10:
                failure_lines.append(f"... and {len(hunks) - 10} more mismatching steps.")
        else:
            # hunk를 찾을 수 없는 경우 (전체 비교)
            tc.steps.append(TestStep(
                sql="(full comparison)",
                expected=self.parser.read_file_safe(exp_path).strip(),
                actual=tc.full_actual.strip(),
                index=1
            ))
            failure_lines.append("[GENERAL FAILURE] Output does not match expected result.")
            
        tc.failure_message = "\n".join(failure_lines)

    def _handle_success(self, tc: TestCaseResult, actual_steps: List[TestStep], 
                        expected_steps: List[TestStep], exp_path: str, act_path: str):
        """성공한 테스트 케이스의 단계 정보(SQL 중심) 구성"""
        if not actual_steps: return
        
        # 파일 내용을 미리 읽어둠
        act_lines = self.parser.read_file_safe(act_path).splitlines()
        exp_lines = self.parser.read_file_safe(exp_path).splitlines()
        
        for act_step in actual_steps:
            # 동일한 SQL을 가진 예상 단계를 찾음 (베스트 에포트)
            exp_step = next((s for s in expected_steps if s.sql == act_step.sql), None)
            
            # 단계별 출력 추출
            exp_range = exp_step if exp_step else act_step
            expected_val = "\n".join(exp_lines[exp_range.start_line-1 : exp_range.end_line]).strip()
            actual_val = "\n".join(act_lines[act_step.start_line-1 : act_step.end_line]).strip()
            
            tc.steps.append(TestStep(
                sql=act_step.sql,
                expected=expected_val,
                actual=actual_val,
                index=act_step.index
            ))

# --- 실행부 ---

def main():
    parser = argparse.ArgumentParser(description='PostgreSQL 회귀 테스트 결과를 JUnit XML 형식으로 변환합니다.')
    parser.add_argument('regression_out', help='regression.out 파일 경로 또는 해당 파일을 포함하는 디렉토리')
    parser.add_argument('regression_diffs', nargs='?', default='regression.diffs', help='regression.diffs 파일 경로')
    parser.add_argument('--base-dir', help='regression/expected/results 경로의 기준 디렉토리')
    parser.add_argument('--mode', choices=['pg', 'ags'], default='ags', help='테스트 모드: pg(expected) 또는 ags(ora_expected)')
    
    args = parser.parse_args()
    
    try:
        converter = JUnitConverter(args)
        converter.convert()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
