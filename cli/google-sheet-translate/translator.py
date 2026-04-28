from src.config_loader import Config
from src.translation_manager import TranslationManager

"""
Google Sheets 자동 번역 도구의 메인 엔트리 포인트 파일입니다.
src 폴더 내부의 모듈들을 사용하여 번역 프로세스를 실행합니다.
"""

def main():
    print(">>> 프로젝트 설정을 로드하는 중...")
    config = Config()
    
    missing = config.validate()
    if missing:
        print(f"오류: .env 파일에 다음 설정이 누락되었습니다: {', '.join(missing)}")
        return

    print(">>> Google Sheets 서비스에 연결하는 중...")
    try:
        manager = TranslationManager(config)
        print(">>> 번역 작업을 시작합니다.\n")
        manager.process_all_columns()
        print("\n>>> 모든 작업이 완료되었습니다.")
    except Exception as e:
        print(f"\n[오류] 초기화 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
