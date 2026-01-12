from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from core.storage import list_files, get_file_url, get_file_stream, get_file_content, upload_stream
import mimetypes
import urllib.parse

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename
        
        # Upload to MinIO
        # Determine content type
        content_type = file.content_type or "application/octet-stream"
        
        object_name = upload_stream(content, filename, content_type)
        
        return {
            "filename": object_name, 
            "size": len(content), 
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files")
def list_minio_files():
    files = list_files()
    return {"files": files}

@router.get("/view/{filename}")
async def view_file(filename: str):
    try:
        content = get_file_content(filename)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/download/{filename}")
async def download_file(filename: str):
    try:
        # URL 디코딩 (한글 파일명 등 처리)
        decoded_filename = urllib.parse.unquote(filename)
        
        file_stream = get_file_stream(decoded_filename)
        
        # MIME 타입 추론
        content_type, _ = mimetypes.guess_type(decoded_filename)
        if not content_type:
            content_type = "application/octet-stream"
            
        # Content-Disposition 헤더 설정 (다운로드 시 파일명 지정)
        # 파일명에 공백이나 특수문자가 있을 경우를 대비해 따옴표로 감싸거나 인코딩 처리
        encoded_filename = urllib.parse.quote(decoded_filename)
        
        return StreamingResponse(
            file_stream, 
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=404, detail=f"File not found: {e}")
