from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleSheetsClient:
    """
    Google Sheets API와의 상호작용을 담당하는 클라이언트 클래스입니다.
    """
    def __init__(self, credentials_file):
        """
        서비스 계정 키 파일을 사용하여 인증을 수행하고 시트 서비스 객체를 생성합니다.
        """
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=self.scopes)
        # 구글 시트 API v4 서비스 빌드
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet = self.service.spreadsheets()

    def get_values(self, spreadsheet_id, range_name):
        """
        지정된 스프레드시트의 특정 범위에서 값을 읽어옵니다.
        """
        result = self.sheet.values().get(
            spreadsheetId=spreadsheet_id, 
            range=range_name
        ).execute()
        return result.get('values', [])

    def update_values(self, spreadsheet_id, range_name, values):
        """
        지정된 스프레드시트의 특정 범위에 새로운 값들을 기록합니다.
        """
        body = {'values': values}
        return self.sheet.values().update(
            spreadsheetId=spreadsheet_id, 
            range=range_name,
            valueInputOption='RAW', 
            body=body
        ).execute()
