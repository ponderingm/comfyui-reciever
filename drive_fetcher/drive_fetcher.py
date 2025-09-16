import os
import sys
import time
import io
from typing import List
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from datetime import datetime  # 追加

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/creds/service_account.json')
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/downloads')
QUERY = os.environ.get('DRIVE_QUERY', "mimeType contains 'image/'")
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '60'))
FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')  # Optional: 指定フォルダのみ監視
ARCHIVE_FOLDER_ID = os.environ.get('ARCHIVE_FOLDER_ID')  # アーカイブ先フォルダID


def get_service():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"[drive_fetcher] Credentials not found at {CREDENTIALS_PATH}", file=sys.stderr)
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def build_query() -> str:
    parts: List[str] = [QUERY]
    if FOLDER_ID:
        parts.append(f"'{FOLDER_ID}' in parents")
    return " and ".join(parts)


def list_images(service):
    q = build_query()
    resp = service.files().list(q=q, spaces='drive', fields='files(id, name, mimeType, size)', pageSize=100).execute()
    return resp.get('files', [])


def download_and_archive(service, file_obj):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_id = file_obj['id']
    original_name = file_obj['name']  # 元の名前保持
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    local_name = f"{timestamp}_{original_name}"
    dest = os.path.join(DOWNLOAD_DIR, local_name)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"[drive_fetcher] Downloading {local_name}: {int(status.progress()*100)}%")
    fh.close()
    print(f"[drive_fetcher] Downloaded: {dest}")
    # Move to archive folder
    if ARCHIVE_FOLDER_ID:
        try:
            file = service.files().get(fileId=file_id, fields='parents').execute()
            prev_parents = ",".join(file.get('parents', []))
            service.files().update(
                fileId=file_id,
                addParents=ARCHIVE_FOLDER_ID,
                removeParents=prev_parents
            ).execute()
            print(f"[drive_fetcher] Moved to archive folder (remote name unchanged): {original_name}")
        except Exception as e:
            print(f"[drive_fetcher] Error moving to archive: {e}", file=sys.stderr)
    else:
        print(f"[drive_fetcher] ARCHIVE_FOLDER_ID not set, skipping move.")


def main():
    service = get_service()
    print("[drive_fetcher] Started. Monitoring Drive for images...")
    while True:
        try:
            files = list_images(service)
            if files:
                print(f"[drive_fetcher] Found {len(files)} image(s)")
            for f in files:
                download_and_archive(service, f)
        except Exception as e:
            print(f"[drive_fetcher] Error: {e}", file=sys.stderr)
        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
