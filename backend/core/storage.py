from minio import Minio
from minio.error import S3Error
import os
import io

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_EXTERNAL_ENDPOINT = os.getenv("MINIO_EXTERNAL_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "youtube-stt")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

# MinIO 클라이언트 (내부 통신용)
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def init_storage():
    """Ensure the bucket exists."""
    try:
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            print(f"Bucket '{MINIO_BUCKET}' created.")
        else:
            print(f"Bucket '{MINIO_BUCKET}' already exists.")
    except S3Error as e:
        print(f"Error initializing storage: {e}")

def upload_file(file_path, object_name):
    """Upload a file to MinIO."""
    try:
        client.fput_object(MINIO_BUCKET, object_name, file_path)
        return object_name
    except S3Error as e:
        print(f"Error uploading file: {e}")
        raise

def upload_stream(data: bytes, object_name: str, content_type: str = "application/octet-stream"):
    """Upload bytes to MinIO."""
    try:
        client.put_object(
            MINIO_BUCKET, 
            object_name, 
            io.BytesIO(data), 
            len(data), 
            content_type=content_type
        )
        return object_name
    except S3Error as e:
        print(f"Error uploading stream: {e}")
        raise

def get_file_url(object_name):
    """Get a download URL for the file (via backend proxy)."""
    # 백엔드 프록시를 통한 다운로드 URL 반환
    return f"http://localhost:8000/api/download/{object_name}"

def list_files():
    """List all files in the bucket."""
    try:
        objects = client.list_objects(MINIO_BUCKET)
        files = []
        for obj in objects:
            files.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None
            })
        return files
    except S3Error as e:
        print(f"Error listing files: {e}")
        return []

def get_file_stream(object_name):
    """Get a file stream from MinIO."""
    try:
        response = client.get_object(MINIO_BUCKET, object_name)
        return response
    except S3Error as e:
        print(f"Error getting file stream: {e}")
        raise

def get_file_content(object_name):
    """Get file content as string."""
    try:
        response = client.get_object(MINIO_BUCKET, object_name)
        content = response.read().decode('utf-8')
        response.close()
        return content
    except S3Error as e:
        print(f"Error getting file content: {e}")
        raise
