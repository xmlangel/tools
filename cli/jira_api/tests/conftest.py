import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def record_junit_case(record_property, description, step, actual, expected):
    """JUnit XML에 테스트 메타데이터를 기록합니다.

    Args:
        record_property (callable): pytest 제공 프로퍼티 기록 함수.
        description (str): 테스트 설명.
        step (str): 수행 단계.
        actual (str): 실제 결과.
        expected (str): 기대 결과.
    """
    record_property("description", description)
    record_property("step", step)
    record_property("actual", actual)
    record_property("expected", expected)
