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
    """
    Parses regression.out and returns a list of test case dictionaries.
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

def create_junit_xml(test_cases, diffs, results_dir, output_path, expected_dir, ora_expected_dir):
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
        
        actual_output = clean_xml_string(get_test_output(tc['name'], results_dir))
        sys_out = ET.SubElement(testcase, 'system-out')
        sys_out.text = actual_output
        
        if tc['status'] == 'not ok':
            diff_content = diffs.get(tc['name'], "")
            
            # Find expected/actual files
            actual_file = os.path.join(results_dir, f"{tc['name']}.out")
            expected_file = os.path.join(expected_dir, f"{tc['name']}.out")
            if not os.path.exists(expected_file):
                expected_file = os.path.join(ora_expected_dir, f"{tc['name']}.out")
            
            actual_steps = get_out_file_steps(actual_file)
            expected_steps = get_out_file_steps(expected_file)
            
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
                
                if target_step:
                    # Find corresponding expected step (usually same SQL)
                    exp_step = None
                    for es in expected_steps:
                        if es['sql'] == target_step['sql']:
                            exp_step = es
                            break
                    
                    # Extract expected and actual results specifically for this step hunk
                    # For simplicity, we can just show the hunk content or the whole step
                    exp_val = []
                    act_val = []
                    for line in hunk['lines']:
                        if line.startswith('-'): exp_val.append(line[1:])
                        elif line.startswith('+'): act_val.append(line[1:])
                    
                    mismatching_steps.append({
                        'sql': target_step['sql'],
                        'expected': "\n".join(exp_val).strip() or "(no expected output for this hunk)",
                        'actual': "\n".join(act_val).strip() or "(no actual output for this hunk)"
                    })
            
            if mismatching_steps:
                # Add human-readable summary to the failure text
                for idx, m in enumerate(mismatching_steps[:10]):
                    failure_lines.append(f"STEP {idx+1}: {m['sql']}")
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
            
            failure.text = clean_xml_string("\n".join(failure_lines))

    xml_str = ET.tostring(testsuites, encoding='utf-8')
    try:
        reparsed = minidom.parseString(xml_str)
        pretty_xml_str = reparsed.toprettyxml(indent="  ")
    except Exception as e:
        pretty_xml_str = xml_str.decode('utf-8')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_to_junit.py <regression.out> [regression.diffs]")
        sys.exit(1)
    
    reg_out = sys.argv[1]
    reg_diffs = sys.argv[2] if len(sys.argv) > 2 else "regression.diffs"
    
    base_dir = os.path.dirname(reg_out) or "."
    results_dir = os.path.join(base_dir, "results")
    expected_dir = os.path.join(base_dir, "expected")
    ora_expected_dir = os.path.join(base_dir, "ora_expected")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pg_test_result_make_check_{timestamp}.xml"
    
    results = parse_regression_out(reg_out)
    diff_map = parse_regression_diffs(reg_diffs)
    create_junit_xml(results, diff_map, results_dir, output_file, expected_dir, ora_expected_dir)
    print(f"Successfully converted results to {output_file}")
