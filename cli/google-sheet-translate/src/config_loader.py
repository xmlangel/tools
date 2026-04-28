import os
from dotenv import load_dotenv

class Config:
    """
    환경 변수(.env)를 로드하고 프로젝트 설정을 관리하는 클래스입니다.
    """
    def __init__(self):
        # .env 파일로부터 환경 변수를 로드합니다.
        load_dotenv()
        
        # OpenWebUI(LLM) API 관련 설정
        self.openwebui_url = os.getenv("OPENWEBUI_URL")
        self.openwebui_api_key = os.getenv("OPENWEBUI_API_KEY")
        self.openwebui_model = os.getenv("OPENWEBUI_MODEL", "llama3")
        
        # Google Sheets 관련 설정
        self.google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.google_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "config/key.json")
        self.sheet_name = os.getenv("SHEET_NAME", "Sheet1")
        
        # 번역할 범위 설정 (열, 시작 행, 끝 행)
        self.column_raw = os.getenv("COLUMN", "A")
        self.start_row = os.getenv("START_ROW", "1")
        self.end_row = os.getenv("END_ROW", "100")
        
        # 번역에서 제외할 문구 (쉼표로 구분)
        self.exclude_phrases_raw = os.getenv("EXCLUDE_PHRASES", "")

    @property
    def exclude_phrases(self):
        """
        제외할 문구들을 리스트로 반환합니다.
        """
        if not self.exclude_phrases_raw:
            return []
        return [p.strip() for p in self.exclude_phrases_raw.split(',')]

    @property
    def columns(self):
        """
        쉼표로 구분된 열 이름들을 리스트로 변환하여 반환합니다.
        예: "A,B" -> ["A", "B"]
        """
        return [c.strip() for c in self.column_raw.split(',')]

    def validate(self):
        """
        필수 설정값이 누락되었는지 확인합니다.
        누락된 설정 항목의 리스트를 반환합니다.
        """
        missing = []
        if not self.openwebui_url: missing.append("OPENWEBUI_URL")
        if not self.openwebui_api_key: missing.append("OPENWEBUI_API_KEY")
        if not self.google_sheet_id: missing.append("GOOGLE_SHEET_ID")
        return missing
