import json
from .google_sheets import GoogleSheetsClient
from .openwebui_translator import TranslatorClient

class TranslationManager:
    """
    시트 읽기, 번역 요청, 시트 쓰기 과정을 조율하는 매니저 클래스입니다.
    """
    def __init__(self, config):
        self.config = config
        self.sheets = GoogleSheetsClient(config.google_credentials_file)
        self.translator = TranslatorClient(
            config.openwebui_url, 
            config.openwebui_api_key, 
            config.openwebui_model
        )

    def process_all_columns(self):
        """
        설정된 모든 열(Column)에 대해 번역 작업을 수행합니다.
        """
        missing = self.config.validate()
        if missing:
            print(f"오류: 필수 설정값이 누락되었습니다: {', '.join(missing)}")
            return

        # 행 범위 유효성 검사
        try:
            start = int(self.config.start_row)
            end = int(self.config.end_row)
            if start > end:
                print(f"주의: 시작 행({start})이 종료 행({end})보다 큽니다. 범위를 확인해 주세요.")
                return
        except ValueError:
            print("오류: START_ROW 또는 END_ROW가 숫자가 아닙니다.")
            return

        for col in self.config.columns:
            self._process_column(col)

    def _process_column(self, col):
        """
        개별 열의 데이터를 처리합니다.
        """
        range_name = f"{self.config.sheet_name}!{col}{self.config.start_row}:{col}{self.config.end_row}"
        print(f"\n--- {col}열 작업 시작 ({range_name}) ---")
        
        try:
            # 1. 시트에서 원문 읽기
            values = self.sheets.get_values(self.config.google_sheet_id, range_name)
        except Exception as e:
            self._handle_sheet_error(e)
            return

        if not values:
            print(f"  {range_name} 범위에 데이터가 없습니다.")
            return

        updated_rows = []
        for row in values:
            original = row[0] if row else ""
            if not original.strip():
                updated_rows.append([""])
                continue
            
            # 2. 제외 문구 확인 (완전히 일치할 경우 번역 건너뜀)
            if original.strip() in self.config.exclude_phrases:
                print(f"  제외 대상 발견: {original} (번역 생략)")
                updated_rows.append([original])
                continue

            # 3. 번역 수행
            print(f"  번역 중: {original[:50]}...")
            translated = self.translator.translate(original)
            
            # 4. 결과 포맷팅 (원문 + 번역문)
            if translated:
                updated_rows.append([f"{original}\n{translated}"])
            else:
                updated_rows.append([original])

        try:
            # 5. 시트에 결과 쓰기
            res = self.sheets.update_values(self.config.google_sheet_id, range_name, updated_rows)
            print(f"  성공: {res.get('updatedCells')}개의 셀이 업데이트되었습니다.")
        except Exception as e:
            print(f"  [Error] 시트 업데이트 실패: {e}")

    def _handle_sheet_error(self, e):
        """
        시트 접근 시 발생하는 일반적인 오류(권한 등)를 처리합니다.
        """
        if "permission" in str(e).lower():
            print("  [권한 오류] 구글 시트를 아래 서비스 계정 이메일과 공유해 주세요.")
            try:
                with open(self.config.google_credentials_file) as f:
                    email = json.load(f).get('client_email')
                    print(f"  초대할 이메일: {email}")
            except: pass
        else:
            print(f"  [Error] 시트 접근 실패: {e}")
