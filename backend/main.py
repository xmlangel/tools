from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import os

from database import get_db, init_db, Job
from storage import init_storage, get_file_url, client, MINIO_BUCKET, list_files
from tasks import process_stt_job, process_translation_job
from minio.error import S3Error

app = FastAPI(title="YouTube STT & Translation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    init_storage()

# --- Pydantic Models ---
class STTRequest(BaseModel):
    url: str
    model: str = "base"

class TranslationRequest(BaseModel):
    text: Optional[str] = None
    file_path: Optional[str] = None # Path in MinIO
    api_url: str
    api_key: str
    model: str

class JobResponse(BaseModel):
    id: int
    type: str
    status: str
    progress: Optional[int] = 0
    input_data: Optional[str] = None
    created_at: str
    output_files: Optional[dict] = None
    error_message: Optional[str] = None

# --- Endpoints ---

@app.post("/api/stt", response_model=JobResponse)
def create_stt_job(request: STTRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(
        type="stt",
        input_data=request.url,
        model_name=request.model,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(process_stt_job, job.id, request.url, request.model)
    
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "created_at": str(job.created_at)
    }

@app.post("/api/translate", response_model=JobResponse)
def create_translation_job(
    request: TranslationRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    # Determine input text
    input_text = request.text
    if not input_text and request.file_path:
        # Download from MinIO
        try:
            response = client.get_object(MINIO_BUCKET, request.file_path)
            input_text = response.read().decode('utf-8')
            response.close()
            response.release_conn()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file from storage: {e}")
            
    if not input_text:
        raise HTTPException(status_code=400, detail="Either text or file_path must be provided")

    job = Job(
        type="translate",
        input_data=input_text[:100] + "...", # Store snippet
        model_name=request.model,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(
        process_translation_job, 
        job.id, 
        input_text, 
        request.api_url, 
        request.api_key, 
        request.model
    )
    
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "created_at": str(job.created_at)
    }

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    output = None
    if job.output_files:
        try:
            parsed_files = json.loads(job.output_files)
            output = {}
            for key, path in parsed_files.items():
                url = get_file_url(path)
                if url:
                    output[key] = url
        except Exception as e:
            print(f"Error processing output_files in get_job_status: {e}")

    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "input_data": job.input_data,
        "created_at": str(job.created_at),
        "output_files": output,
        "error_message": job.error_message
    }

@app.get("/api/jobs")
def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """최근 작업 목록 조회"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    
    result = []
    for job in jobs:
        output = None
        if job.output_files:
            try:
                parsed_files = json.loads(job.output_files)
                output = {}
                for key, path in parsed_files.items():
                    url = get_file_url(path)
                    if url:
                        output[key] = url
                    else:
                        print(f"Failed to generate URL for {path}")
            except Exception as e:
                print(f"Error processing output_files: {e}")
                output = None
        
        result.append({
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "progress": job.progress,
            "input_data": job.input_data,
            "created_at": str(job.created_at),
            "output_files": output,
            "error_message": job.error_message
        })
    
    return {"jobs": result}

@app.get("/api/files/{filename}")
def get_file(filename: str):
    """파일 다운로드 프록시"""
    try:
        # MinIO에서 파일 가져오기
        response = client.get_object(MINIO_BUCKET, filename)
        
        # 파일 내용 읽기
        file_data = response.read()
        
        # Content-Type 결정
        content_type = "application/octet-stream"
        if filename.endswith('.txt'):
            content_type = "text/plain"
        elif filename.endswith('.mp3'):
            content_type = "audio/mpeg"
        
        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    finally:
        response.close()
        response.release_conn()


@app.get("/api/files")
def list_all_files():
    """MinIO에 저장된 모든 파일 목록 조회"""
    files = list_files()
    return {"files": files}

@app.get("/api/download/{filename}")
def download_file(filename: str):
    """파일 다운로드 프록시"""
    try:
        # MinIO에서 파일 가져오기
        response = client.get_object(MINIO_BUCKET, filename)
        
        # 파일 내용 읽기
        file_data = response.read()
        
        # Content-Type 결정
        content_type = "application/octet-stream"
        if filename.endswith('.txt'):
            content_type = "text/plain; charset=utf-8"
        elif filename.endswith('.mp3'):
            content_type = "audio/mpeg"
        
        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
