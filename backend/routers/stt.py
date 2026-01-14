from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
import json
import os
import shutil
from sqlalchemy.orm import Session
from core.database import get_db, Job
from services.stt_service import process_stt_job, process_uploaded_file_job

router = APIRouter()

class STTRequest(BaseModel):
    url: str
    model: str = "base"

@router.post("/stt")
async def start_stt_job(request: STTRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(type="stt", input_data=request.url, model_name=request.model, youtube_url=request.url, source_type="youtube")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_stt_job, job.id, request.url, request.model)

    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "input": job.input_data,
        "output": {},
        "created_at": job.created_at,
        "error": job.error_message,
        "youtube_url": job.youtube_url
    }

@router.post("/stt/upload")
async def start_stt_upload_job(
    file: UploadFile = File(...),
    model: str = Form("base"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    # Validate file extension
    allowed_extensions = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".aac", ".mp4", ".webm"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    # Create job record
    job = Job(
        type="stt",
        input_data=file.filename,
        model_name=model,
        source_type="upload",
        original_filename=file.filename
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Save uploaded file temporarily
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{job.id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        job.status = "failed"
        job.error_message = f"Failed to save uploaded file: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    
    # Start background processing
    background_tasks.add_task(process_uploaded_file_job, job.id, temp_file_path, model)
    
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "input": job.input_data,
        "output": {},
        "created_at": job.created_at,
        "error": job.error_message,
        "source_type": job.source_type,
        "original_filename": job.original_filename
    }
