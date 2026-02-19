#!/usr/bin/env python3
import io
import os
import sys
import pickle
import argparse
import re
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from tqdm import tqdm

# 권한 범위 설정 (읽기 및 쓰기 권한)
SCOPES = ['https://www.googleapis.com/auth/drive']

# 파일 이름과 기본 폴더 ID 설정
CLIENT_SECRET_FILE = 'client_secrit.json'
TOKEN_FILE = 'token.json'
SERVICE_ACCOUNT_FILE = 'service_account.json'
DEFAULT_FOLDER_ID = '0ADwzHDbRBoXBUk9PVA'
DOWNLOAD_DIR = 'downloads'

def extract_folder_id(input_str):
    """URL에서 폴더 ID를 추출하거나, 그대로 반환"""
    if 'drive.google.com' in input_str:
        # URL 형태 (예: .../folders/ID 또는 ...?id=ID)
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', input_str)
        if match:
            return match.group(1)
        match = re.search(r'id=([a-zA-Z0-9_-]+)', input_str)
        if match:
            return match.group(1)
    return input_str

def get_service():
    """Google Drive API 서비스 인증 및 생성"""
    creds = None
    
    # 1. 서비스 계정 파일이 있으면 최우선으로 사용 (SSH/서버 환경 권장)
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"✅ 인증 방식: 서비스 계정 ({SERVICE_ACCOUNT_FILE})")
        return build('drive', 'v3', credentials=service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES))

    # 2. 기존 토큰 파일 확인 (사용자 계정 인증)
    if os.path.exists(TOKEN_FILE):
        print(f"✅ 인증 방식: 기존 사용자 토큰 ({TOKEN_FILE})")
        with open(TOKEN_FILE, 'rb') as token:
            try:
                # pickle 로드 시도 (구버전 호환)
                creds = pickle.load(token)
            except Exception:
                # pickle 로드 실패 시 json으로 시도
                from google.oauth2.credentials import Credentials
                try:
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                except Exception:
                    creds = None

    # 유효한 자격 증명이 없으면 새로 로그인
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        
        # 새로운 자격 증명 저장
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def download_file(service, file_id, file_name, file_size, current_path):
    """파일 다운로드 함수 (중복 체크 및 진행률 표시 포함)"""
    
    # 저장 경로 확인 및 생성
    if not os.path.exists(current_path):
        os.makedirs(current_path)
        
    file_path = os.path.join(current_path, file_name)
    
    # 기존 파일 체크 (이름과 크기 비교)
    if os.path.exists(file_path):
        local_size = os.path.getsize(file_path)
        if local_size == int(file_size):
            print(f"     [Skip] 이미 존재함: {file_name}")
            return
        else:
            print(f"     [Update] 크기 다름 (로컬:{local_size} vs 드라이브:{file_size}): {file_name}")

    request = service.files().get_media(fileId=file_id)
    
    # 파일 쓰기 모드
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    
    # tqdm 진행률 표시줄 설정
    pbar = tqdm(total=int(file_size), unit='B', unit_scale=True, desc=file_name)
    
    max_retries = 5
    while done is False:
        retry_count = 0
        while retry_count < max_retries:
            try:
                status, done = downloader.next_chunk()
                if status:
                    pbar.update(int(status.resumable_progress - pbar.n))
                break # 성공 시 루프 탈출
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    pbar.close()
                    fh.close()
                    raise e
                time.sleep(2 ** retry_count) # 지수 백오프
    
    pbar.close()
    fh.close()

def escape_query_string(s):
    """구글 드라이브 쿼리문에서 사용되는 문자열의 특수문자(홀따옴표, 백슬래시) 이스케이프"""
    return s.replace("\\", "\\\\").replace("'", "\\'")

def execute_with_retry(request, max_retries=5):
    """API 실행 시 지수 백오프를 적용한 재시도 로직"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            return request.execute()
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            # 500 계열 에러나 특정 일시적 오류인 경우 재시도
            wait_time = 2 ** retry_count
            print(f"     ⚠️ API 오류 발생 ({e}). {wait_time}초 후 재시도 ({retry_count}/{max_retries})...")
            time.sleep(wait_time)

def get_or_create_folder(service, folder_name, parent_id):
    """구글 드라이브에서 폴더를 찾거나 없으면 생성"""
    escaped_name = escape_query_string(folder_name)
    query = f"name = '{escaped_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    
    results = execute_with_retry(service.files().list(
        q=query, 
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ))
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = execute_with_retry(service.files().create(
            body=file_metadata, 
            fields='id',
            supportsAllDrives=True
        ))
        print(f"📁 새 폴더 생성됨: {folder_name} (ID: {folder['id']})")
        return folder['id']

def upload_file(service, local_path, parent_id):
    """파일 업로드 (중복 체크 포함)"""
    file_name = os.path.basename(local_path)
    file_size = os.path.getsize(local_path)
    
    # 드라이브에서 동일 이름/크기 파일 확인
    escaped_name = escape_query_string(file_name)
    query = f"name = '{escaped_name}' and '{parent_id}' in parents and trashed = false"
    
    results = execute_with_retry(service.files().list(
        q=query, 
        fields="files(id, name, size)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ))
    items = results.get('files', [])
    
    for item in items:
        if int(item.get('size', 0)) == file_size:
            print(f"     [Skip] 드라이브에 이미 동일 파일 존재: {file_name}")
            return item['id']

    print(f"📤 업로드 중: {file_name} ({file_size} bytes)")
    
    file_metadata = {
        'name': file_name,
        'parents': [parent_id]
    }
    media = MediaFileUpload(local_path, resumable=True)
    
    request = service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id',
        supportsAllDrives=True
    )
    
    response = None
    pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name)
    
    max_retries = 5
    while response is None:
        retry_count = 0
        while retry_count < max_retries:
            try:
                status, response = request.next_chunk()
                if status:
                    pbar.update(int(status.resumable_progress - pbar.n))
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    pbar.close()
                    raise e
                wait_time = 2 ** retry_count
                print(f"     ⚠️ 업로드 중 오류 ({e}). {wait_time}초 후 재시도...")
                time.sleep(wait_time)
    
    pbar.close()
    return response.get('id')

def upload_directory(service, local_path, parent_id, recursive=True):
    """디렉토리 내용을 드라이브에 업로드"""
    if not os.path.isdir(local_path):
        print(f"❌ 오류: '{local_path}'는 디렉토리가 아닙니다.")
        return

    print(f"📂 로컬 탐색 중: {local_path}")
    
    for item_name in os.listdir(local_path):
        # .git 이나 venv 같은 폴더 제외 (선택 사항)
        if item_name in ['.git', 'venv', '__pycache__', '.ipynb_checkpoints']:
            continue
            
        full_path = os.path.join(local_path, item_name)
        
        if os.path.isdir(full_path):
            if recursive:
                new_drive_folder_id = get_or_create_folder(service, item_name, parent_id)
                upload_directory(service, full_path, new_drive_folder_id, recursive=True)
        else:
            try:
                upload_file(service, full_path, parent_id)
            except Exception as e:
                print(f"     ❌ 업로드 실패 ({item_name}): {e}")

def list_and_download_files(service, folder_id, current_path, recursive=False):
    """지정된 폴더의 모든 파일을 나열하고 다운로드"""
    
    # 현재 로컬 경로가 없으면 생성
    if not os.path.exists(current_path):
        os.makedirs(current_path)

    print(f"📂 폴더 탐색 중: {current_path} (ID: {folder_id})")
    
    query = f"'{folder_id}' in parents and trashed = false"
    
    # 폴더 내 파일 검색 (페이지네이션 처리)
    page_token = None
    while True:
        results = execute_with_retry(service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, size, mimeType)",
            pageToken=page_token,
            supportsAllDrives=True,  # 공유 드라이브 지원
            includeItemsFromAllDrives=True  # 공유 드라이브 항목 포함
        ))

        items = results.get('files', [])

        print(f"   -> 검색 결과: {len(items)}개 항목 발견")

        if not items:
            print("   ⚠️ 주의: 폴더가 비어 있거나, 접근 권한이 없습니다.")
            print("      (서비스 계정을 사용하는 경우, 해당 이메일로 폴더를 '공유'했는지 확인하세요.)")
            break

        for item in items:
            print(f"   - 발견: {item['name']} ({item['mimeType']})")
            
            # 폴더인 경우
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                if recursive:
                    new_folder_path = os.path.join(current_path, item['name'])
                    list_and_download_files(service, item['id'], new_folder_path, recursive=True)
                else:
                    print(f"     [Skip] 하위 폴더 (재귀 옵션 필요): {item['name']}")
                continue
                
            # Google Docs/Sheets 등의 파일은 바이너리로 직접 다운로드 불가하므로 export 필요
            if 'google-apps' in item['mimeType']:
                print(f"     [Skip] Google 문서 (내보내기 필요): {item['name']}")
                continue

            file_size = item.get('size', 0) # 크기 정보가 없는 경우 0
            try:
                download_file(service, item['id'], item['name'], file_size, current_path)
            except Exception as download_err:
                print(f"     ❌ 다운로드 실패 ({item['name']}): {download_err}")

        page_token = results.get('nextPageToken')
        if not page_token:
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Google Drive 폴더 다운로더/업로더',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  1. 다운로드 (기본):
     python google_deive_files_api.py -r -f "FOLDER_ID" -o "./downloads"

  2. 업로드 (현재 폴더를 드라이브 폴더로):
     python google_deive_files_api.py -u -r -f "FOLDER_ID" -o "./local_folder"

  3. 구글 드라이브 URL 사용:
     python google_deive_files_api.py -f "https://drive.google.com/drive/folders/FOLDER_ID"

  4. 백그라운드 실행 (nohup):
     nohup python google_deive_files_api.py -r > download.log 2>&1 &
"""
    )
    parser.add_argument('-u', '--upload', action='store_true', help='업로드 모드로 실행 (기본값: 다운로드 모드)')
    parser.add_argument('-r', '--recursive', action='store_true', help='하위 폴더를 포함하여 재귀적으로 처리')
    parser.add_argument('-f', '--folder', type=str, help='대상 구글 드라이브 폴더 ID 또는 URL')
    parser.add_argument('-o', '--output', type=str, help=f'저장 또는 업로드할 로컬 경로 (기본값: {DOWNLOAD_DIR})')
    args = parser.parse_args()

    # 경로 설정
    local_path = args.output if args.output else DOWNLOAD_DIR

    folder_input = args.folder
    if not folder_input:
        mode_str = "업로드" if args.upload else "다운로드"
        print(f"💡 구글 드라이브 폴더 ID가 지정되지 않았습니다. (기본값: {DEFAULT_FOLDER_ID})")
        try:
            choice = input(f"👉 {mode_str} 진행(Enter), 취소(n), 또는 새로운 ID/URL 입력: ").strip()
            if choice.lower() == 'n':
                print("👋 작업을 종료합니다.")
                sys.exit(0)
            folder_input = choice if choice else DEFAULT_FOLDER_ID
        except EOFError:
            print("🤖 비대화형 환경 탐지: 기본값을 자동으로 사용합니다.")
            folder_input = DEFAULT_FOLDER_ID

    target_id = extract_folder_id(folder_input)

    try:
        service = get_service()
        
        # 현재 로그인된 사용자 정보 확인
        try:
            about = execute_with_retry(service.about().get(fields="user"))
            user_email = about['user']['emailAddress']
            print(f"👤 현재 로그인된 계정: {user_email}")
        except:
            print("👤 로그인 정보 확인 불가 (권한 부족 또는 서비스 계정)")

        if args.upload:
            print(f"🚀 업로드 시작 (로컬: {local_path} -> 드라이브 ID: {target_id})")
            if not os.path.exists(local_path):
                print(f"❌ 오류: 로컬 경로 '{local_path}'가 존재하지 않습니다.")
                sys.exit(1)
            upload_directory(service, local_path, target_id, recursive=args.recursive)
        else:
            print(f"🚀 다운로드 시작 (드라이브 ID: {target_id} -> 로컬: {local_path})")
            list_and_download_files(service, target_id, local_path, recursive=args.recursive)
            
        print("\n✨ 모든 작업이 완료되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

# ==========================================
# 사용법 가이드 (Usage Guide)
# ==========================================
# 1. 다운로드 모드 (Download Mode)
#    - 특정 드라이브 폴더의 내용을 로컬로 가져옵니다.
#    - 예: python google_deive_files_api.py -r -f "FOLDER_ID" -o "./downloads"
#
# 2. 업로드 모드 (Upload Mode) - [신규]
#    - 로컬의 파일/폴더를 구글 드라이브의 특정 폴더로 업로드합니다.
#    - 중복 체크: 동일한 이름과 크기를 가진 파일이 드라이브에 있으면 건너뜁니다.
#    - 예: python google_deive_files_api.py -u -r -f "FOLDER_ID" -o "./my_data"
#
# 3. 주요 옵션 설명:
#    - -u, --upload    : 업로드 모드 활성화 (기본값은 다운로드)
#    - -r, --recursive : 하위 폴더까지 재귀적으로 처리
#    - -f, --folder    : 구글 드라이브 폴더 ID 또는 전체 URL
#    - -o, --output    : 로컬 경로 (다운로드 시 저장 위치 / 업로드 시 소스 위치)
#
# 4. 주의사항:
#    - 권한 오류(403) 발생 시 기존 'token.json' 파일을 삭제하고 재인증하세요.
#    - 서비스 계정 사용 시, 업로드 대상 드라이브 폴더에 서비스 계정 이메일을 '편집자'로 공유해야 합니다.
# ==========================================
