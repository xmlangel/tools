import sys
import re
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

def clean_xml_string(s):
    """
    Removes characters that are invalid in XML.
    """
    if s is None:
        return ""
    illegal_chars_re = re.compile(u'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]')
    return illegal_chars_re.sub('', s)

def _truncate_for_text(s, limit):
    if s is None:
        return ""
    if limit is None or limit <= 0:
        return s
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n...[truncated {len(s) - limit} chars]..."

def _format_steps_text(steps, max_steps=10, max_expected_chars=8000, max_actual_chars=8000):
    """
    Returns a human-readable text block:
      STEP N: ...
      EXPECTED: ...
      ACTUAL: ...
    Intended to be appended to <system-out> so most JUnit viewers show it.
    """
    if not steps:
        return ""

    lines = []
    lines.append("")
    lines.append("[STEPS]")
    for idx, st in enumerate(steps[:max_steps]):
        sql = st.get('sql', '')
        exp = _truncate_for_text(st.get('expected', ''), max_expected_chars)
        act = _truncate_for_text(st.get('actual', ''), max_actual_chars)
        # Keep STEP header and SQL block on separate lines.
        # Some viewers collapse whitespace when the SQL is on the same line.
        lines.append(f"STEP {idx+1}:")
        lines.append(sql if sql else "(no sql)")
        lines.append("EXPECTED:")
        lines.append(exp)
        lines.append("ACTUAL:")
        lines.append(act)
        lines.append("-" * 40)

    if len(steps) > max_steps:
        lines.append(f"... and {len(steps) - max_steps} more steps (not shown)")
        lines.append("-" * 40)

    lines.append("")
    return "\n".join(lines)

def resolve_path(base_dir, value):
    """
    Resolves a path relative to a base directory.

    Args:
        base_dir (str): Base directory for relative paths.
        value (str): Path value to resolve.

    Returns:
        str: Resolved path.
    """
    if os.path.isabs(value):
        return value
    return os.path.join(base_dir, value)

def summarize_diff(diff_content):
    """
    Analyzes diff content and creates a human-readable summary.
    Returns (summary_string, list_of_mismatches)
    """
    if not diff_content:
        return "", []
        
    summary = []
    errors = []
    mismatches = []
    
    lines = diff_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # 1. Look for Errors
        if "ERROR:" in line:
            errors.append(line.strip())
            
        # 2. Look for Value Mismatches (Look for consecutive - and + blocks)
        # Standard diff format: '-' or '+' followed by the line content.
        if line.startswith("-") and not line.startswith("---"):
            expected_block = []
            while i < len(lines) and lines[i].startswith("-") and not lines[i].startswith("---"):
                expected_block.append(lines[i][1:])
                i += 1
            
            actual_block = []
            while i < len(lines) and lines[i].startswith("+") and not lines[i].startswith("+++"):
                actual_block.append(lines[i][1:])
                i += 1
            
            if expected_block or actual_block:
                expected = "\n".join(expected_block).strip()
                actual = "\n".join(actual_block).strip()
                # If they are just separators, skip if both are just dashes
                if expected.startswith("--") and actual.startswith("--"):
                    continue
                if expected != actual:
                    mismatches.append((expected, actual))
            continue # Already incremented i
        
        i += 1

    if errors:
        summary.append("[RUNTIME ERRORS]")
        for err in list(dict.fromkeys(errors))[:5]: # Unique, max 5
            summary.append(f"  ! {err}")
        summary.append("")

    if mismatches:
        summary.append("[VALUE MISMATCHES]")
        for exp, act in mismatches[:10]: # Max 10
            summary.append(f"  - EXPECTED: {exp[:200] + '...' if len(exp) > 200 else exp}")
            summary.append(f"  + ACTUAL:   {act[:200] + '...' if len(act) > 200 else act}")
            summary.append("  " + "-"*20)
        
        if len(mismatches) > 10:
            summary.append(f"  ... and {len(mismatches) - 10} more mismatches.")
        summary.append("")
        
    if not summary:
        if "QUERY PLAN" in diff_content:
            summary.append("[PLAN CHANGE] Query execution plan has changed.")
        else:
            summary.append("[GENERAL FAILURE] Output does not match expected result.")
        summary.append("")
            
    return "\n".join(summary), mismatches

def parse_regression_diffs(diff_file):
    """
    Parses regression.diffs and returns a mapping of test name to its diff content.
    """
    diffs = {}
    if not os.path.exists(diff_file):
        return diffs
        
    current_test = None
    current_content = []
    
    # Example header: diff -U3 .../expected/test_name.out .../results/test_name.out
    # Some environments use ora_expected. Accept both so we don't miss diffs.
    pattern = re.compile(r'^diff -U\d+ .*?/(?:expected|ora_expected)/(.+?)\.out .*?/results/\1\.out')
    
    with open(diff_file, 'r', errors='replace') as f:
        for line in f:
            match = pattern.match(line)
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

def get_test_output(test_name, results_dir):
    """
    Reads the actual output file for a test from the results directory.
    """
    log_path = os.path.join(results_dir, f"{test_name}.out")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', errors='replace') as f:
                return f.read()
        except:
            return f"Error reading log file at {log_path}"
    return f"Actual output file not found at {log_path}"

def parse_regression_out(file_path):
    """Parses regression.out and returns a list of test case dictionaries.

    Args:
        file_path (str): Path to regression.out.

    Returns:
        list[dict]: Parsed test case rows.
    """
    test_cases = []
    current_group = "Default Group"
    
    pattern = re.compile(r'^(ok|not ok)\s+(\d+)\s+([-+])\s+(\S+)\s+(\d+)\s+ms')
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("# parallel group"):
                group_match = re.search(r'# (parallel group \(.*?\))', line)
                if group_match:
                    current_group = group_match.group(1)
                else:
                    current_group = line[1:].split(":")[0].strip()
                continue
            
            match = pattern.match(line)
            if match:
                status = match.group(1)
                test_name = match.group(4)
                duration = int(match.group(5)) / 1000.0
                
                test_cases.append({
                    'name': test_name,
                    'classname': current_group,
                    'time': str(duration),
                    'status': status
                })
                
    return test_cases


def normalize_regression_paths(args):
    """Resolves regression.out and regression.diffs paths.

    This supports passing either a file path to regression.out or a directory
    that contains regression.out and regression.diffs.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        tuple[str, str, str]: (base_dir, regression_out, regression_diffs)
    """
    base_dir = args.base_dir
    if base_dir is None:
        base_dir = os.path.dirname(args.regression_out) or "."

    reg_out_candidate = resolve_path(base_dir, args.regression_out)
    if os.path.isdir(reg_out_candidate):
        base_dir = reg_out_candidate
        reg_out = os.path.join(base_dir, "regression.out")
        reg_diffs = resolve_path(base_dir, args.regression_diffs)
        return base_dir, reg_out, reg_diffs

    reg_out = reg_out_candidate
    reg_diffs = resolve_path(base_dir, args.regression_diffs)
    return base_dir, reg_out, reg_diffs

def get_out_file_steps(filepath):
    """
    Parses a PostgreSQL .out file and returns a list of dictionaries,
    each containing the SQL statement and its line range.
    """
    if not os.path.exists(filepath):
        return []
    
    steps = []
    current_sql = []
    start_line = 1
    
    sql_keywords = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
                    'ALTER', 'CALL', 'DO', '\\', 'BEGIN', 'COMMIT', 'ROLLBACK', '-- ')
    
    with open(filepath, 'r', errors='replace') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Heuristic for new command: starts with keyword at beginning of line
            is_new = any(line.startswith(kw) for kw in sql_keywords) and not line.startswith(' ')
            
            if is_new:
                if current_sql:
                    # Save previous step
                    steps.append({
                        'sql': "\n".join(current_sql).strip(),
                        'start': start_line,
                        'end': i # previous line
                    })
                current_sql = [line.rstrip()]
                start_line = i + 1
            elif current_sql:
                current_sql.append(line.rstrip())
        
        if current_sql:
            steps.append({
                'sql': "\n".join(current_sql).strip(),
                'start': start_line,
                'end': len(lines)
            })
            
    return steps

def create_junit_xml(test_cases, diffs, results_dir, output_path, expected_dir, fallback_expected_dir=None):
    """
    Creates the JUnit XML file with embedded steps and results.
    """
    testsuites = ET.Element('testsuites')
    testsuite = ET.SubElement(testsuites, 'testsuite', {
        'name': 'PostgreSQL Regression Tests',
        'tests': str(len(test_cases)),
        'failures': str(len([t for t in test_cases if t['status'] == 'not ok'])),
        'errors': '0',
        'skipped': '0'
    })
    
    for tc in test_cases:
        testcase = ET.SubElement(testsuite, 'testcase', {
            'name': tc['name'],
            'classname': tc['classname'],
            'time': tc['time']
        })
        
        sys_out = ET.SubElement(testcase, 'system-out')
        sys_err = ET.SubElement(testcase, 'system-err')
        actual_output = get_test_output(tc['name'], results_dir)
        # Always show the original (pre-conversion) output in system-out.
        sys_out.text = clean_xml_string(actual_output)
        
        # Find expected/actual files for both success and failure cases
        actual_file = os.path.join(results_dir, f"{tc['name']}.out")
        expected_file = os.path.join(expected_dir, f"{tc['name']}.out")
        if not os.path.exists(expected_file) and fallback_expected_dir:
            alt_expected = os.path.join(fallback_expected_dir, f"{tc['name']}.out")
            if os.path.exists(alt_expected):
                expected_file = alt_expected
        
        actual_steps = get_out_file_steps(actual_file)
        expected_steps = get_out_file_steps(expected_file)
        
        if tc['status'] == 'not ok':
            diff_content = diffs.get(tc['name'], "")
            
            failure = ET.SubElement(testcase, 'failure', {
                'message': 'Test failed',
                'type': 'Failure'
            })
            
            failure_lines = [f"[FAIL] {tc['name']}\n"]
            
            # Parse diff hunks to align failures with steps
            hunks = []
            if diff_content:
                # Find @@ -exp_start,exp_len +act_start,act_len @@
                hunk_pattern = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')
                current_hunk = None
                for line in diff_content.splitlines():
                    match = hunk_pattern.match(line)
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
            
            # For each hunk, map it to a step in actual_steps
            mismatching_steps = []
            for hunk in hunks:
                # Find the step that contains act_start
                target_step = None
                for step in actual_steps:
                    if step['start'] <= hunk['act_start'] <= step['end']:
                        target_step = step
                        break
                
                # Extract expected and actual results specifically for this hunk
                exp_val = []
                act_val = []
                for line in hunk['lines']:
                    if line.startswith('-') and not line.startswith('---'):
                        exp_val.append(line[1:])
                    elif line.startswith('+') and not line.startswith('+++'):
                        act_val.append(line[1:])

                sql_label = target_step['sql'] if target_step else f"(hunk at actual line {hunk['act_start']})"
                mismatching_steps.append({
                    'sql': sql_label,
                    'expected': "\n".join(exp_val).strip() or "(no expected output for this hunk)",
                    'actual': "\n".join(act_val).strip() or "(no actual output for this hunk)"
                })
            
            if mismatching_steps:
                # Add human-readable summary to the failure text
                for idx, m in enumerate(mismatching_steps[:10]):
                    # Keep STEP header and SQL block on separate lines for better rendering.
                    failure_lines.append(f"STEP {idx+1}:")
                    failure_lines.append(m['sql'])
                    failure_lines.append(f"EXPECTED:\n{m['expected']}")
                    failure_lines.append(f"ACTUAL:\n{m['actual']}")
                    failure_lines.append("-" * 40)
                
                if len(mismatching_steps) > 10:
                    failure_lines.append(f"... and {len(mismatching_steps) - 10} more mismatching steps.")
                
                # Add structured XML elements for each mismatching step
                # This allows the UI to show them in a tabbed or table format
                steps_elem = ET.SubElement(failure, 'steps')
                for idx, m in enumerate(mismatching_steps):
                    step_elem = ET.SubElement(steps_elem, 'step', {'index': str(idx+1)})
                    sql_elem = ET.SubElement(step_elem, 'sql')
                    sql_elem.text = clean_xml_string(m['sql'])
                    exp_elem = ET.SubElement(step_elem, 'expected')
                    exp_elem.text = clean_xml_string(m['expected'])
                    act_elem = ET.SubElement(step_elem, 'actual')
                    act_elem.text = clean_xml_string(m['actual'])
                    # For compatibility with some viewers that expect top-level expected/actual
                    if idx == 0:
                        comp_exp = ET.SubElement(failure, 'expected')
                        comp_exp.text = clean_xml_string(m['expected'])
                        comp_act = ET.SubElement(failure, 'actual')
                        comp_act.text = clean_xml_string(m['actual'])
            else:
                summary, _ = summarize_diff(diff_content)
                failure_lines.append(summary)

                # If we couldn't extract hunks/steps, still attach structured expected/actual
                # so the viewer can show something useful.
                exp_full = ""
                act_full = ""
                if os.path.exists(expected_file):
                    try:
                        with open(expected_file, 'r', errors='replace') as f:
                            exp_full = f.read().strip()
                    except:
                        exp_full = ""
                if os.path.exists(actual_file):
                    try:
                        with open(actual_file, 'r', errors='replace') as f:
                            act_full = f.read().strip()
                    except:
                        act_full = ""

                steps_elem = ET.SubElement(failure, 'steps')
                step_elem = ET.SubElement(steps_elem, 'step', {'index': '1'})
                sql_elem = ET.SubElement(step_elem, 'sql')
                sql_elem.text = clean_xml_string("(full output)")
                exp_elem = ET.SubElement(step_elem, 'expected')
                exp_elem.text = clean_xml_string(exp_full)
                act_elem = ET.SubElement(step_elem, 'actual')
                act_elem.text = clean_xml_string(act_full)

                # For compatibility with some viewers that expect top-level expected/actual
                comp_exp = ET.SubElement(failure, 'expected')
                comp_exp.text = clean_xml_string(exp_full)
                comp_act = ET.SubElement(failure, 'actual')
                comp_act.text = clean_xml_string(act_full)
            
            failure.text = clean_xml_string("\n".join(failure_lines))

            # A-mode: put step details in system-err (converted/derived view)
            steps_for_text = mismatching_steps
            if not steps_for_text:
                steps_for_text = [{
                    'sql': "(full output)",
                    'expected': exp_full if 'exp_full' in locals() else "",
                    'actual': act_full if 'act_full' in locals() else "",
                }]
            sys_err.text = clean_xml_string(_format_steps_text(steps_for_text))
        else:
            # For successful tests, add steps information
            # Match expected and actual steps by SQL statement
            all_steps = []
            exp_lines = []
            act_lines = []
            if os.path.exists(expected_file):
                try:
                    with open(expected_file, 'r', errors='replace') as f:
                        exp_lines = f.readlines()
                except:
                    exp_lines = []
            if os.path.exists(actual_file):
                try:
                    with open(actual_file, 'r', errors='replace') as f:
                        act_lines = f.readlines()
                except:
                    act_lines = []

            # If we couldn't detect steps, still include a single step with full content.
            if not actual_steps and (exp_lines or act_lines):
                all_steps.append({
                    'sql': "(full output)",
                    'expected': "".join(exp_lines).strip(),
                    'actual': "".join(act_lines).strip()
                })
            else:
                for act_step in actual_steps:
                    # Find matching expected step (best-effort)
                    exp_step = None
                    for es in expected_steps:
                        if es['sql'] == act_step['sql']:
                            exp_step = es
                            break

                    # Slice output blocks by detected ranges (best-effort)
                    expected_output = ""
                    if exp_step and exp_lines:
                        expected_output = "".join(exp_lines[exp_step['start']-1:exp_step['end']]).strip()
                    elif exp_lines:
                        expected_output = "".join(exp_lines[act_step['start']-1:act_step['end']]).strip()

                    actual_output_step = ""
                    if act_lines:
                        actual_output_step = "".join(act_lines[act_step['start']-1:act_step['end']]).strip()

                    all_steps.append({
                        'sql': act_step['sql'],
                        'expected': expected_output,
                        'actual': actual_output_step
                    })
            
            # Add steps information to successful test case
            if all_steps:
                steps_elem = ET.SubElement(testcase, 'steps')
                for idx, step in enumerate(all_steps):
                    step_elem = ET.SubElement(steps_elem, 'step', {'index': str(idx+1)})
                    sql_elem = ET.SubElement(step_elem, 'sql')
                    sql_elem.text = clean_xml_string(step['sql'])
                    exp_elem = ET.SubElement(step_elem, 'expected')
                    exp_elem.text = clean_xml_string(step['expected'])
                    act_elem = ET.SubElement(step_elem, 'actual')
                    act_elem.text = clean_xml_string(step['actual'])
                
                # For compatibility with some viewers that expect top-level expected/actual
                if all_steps:
                    comp_exp = ET.SubElement(testcase, 'expected')
                    comp_exp.text = clean_xml_string(all_steps[0]['expected'])
                    comp_act = ET.SubElement(testcase, 'actual')
                    comp_act.text = clean_xml_string(all_steps[0]['actual'])

            # A-mode: put step details in system-err (converted/derived view)
            sys_err.text = clean_xml_string(_format_steps_text(all_steps))

    xml_str = ET.tostring(testsuites, encoding='utf-8')
    try:
        reparsed = minidom.parseString(xml_str)
        pretty_xml_str = reparsed.toprettyxml(indent="  ")
    except Exception as e:
        pretty_xml_str = xml_str.decode('utf-8')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert PostgreSQL regression test results to JUnit XML format')
    parser.add_argument(
        'regression_out',
        help='Path to regression.out file or a directory containing regression.out',
    )
    parser.add_argument('regression_diffs', nargs='?', default='regression.diffs', 
                       help='Path to regression.diffs file (default: regression.diffs)')
    parser.add_argument('--base-dir', default=None,
                       help='Base directory for regression/expected/results paths')
    parser.add_argument('--mode', choices=['pg', 'ags'], default='ags',
                       help='Test mode: pg uses expected directory, ags uses ora_expected directory (default: ags)')
    
    args = parser.parse_args()
    
    base_dir, reg_out, reg_diffs = normalize_regression_paths(args)
    mode = args.mode
    
    results_dir = os.path.join(base_dir, "results")
    
    # Select expected directory based on mode
    if mode == 'pg':
        expected_dir_name = "expected"
    else:  # ags
        expected_dir_name = "ora_expected"
    
    expected_dir = os.path.join(base_dir, expected_dir_name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pg_test_result_make_check_{timestamp}.xml"
    
    results = parse_regression_out(reg_out)
    diff_map = parse_regression_diffs(reg_diffs)

    fallback_expected_dir_name = "expected" if expected_dir_name == "ora_expected" else "ora_expected"
    fallback_expected_dir = os.path.join(base_dir, fallback_expected_dir_name)

    create_junit_xml(results, diff_map, results_dir, output_file, expected_dir, fallback_expected_dir=fallback_expected_dir)
    print(f"Successfully converted results to {output_file}")
