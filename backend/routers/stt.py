from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
import json
from sqlalchemy.orm import Session
from core.database import get_db, Job
from services.stt_service import process_stt_job

router = APIRouter()

class STTRequest(BaseModel):
    url: str
    model: str = "base"

@router.post("/stt")
async def start_stt_job(request: STTRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(type="stt", input_data=request.url, model_name=request.model, youtube_url=request.url)
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
