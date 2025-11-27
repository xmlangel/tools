from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, Job
from services.stt_service import process_stt_job

router = APIRouter()

class STTRequest(BaseModel):
    url: str
    model: str = "base"

@router.post("/stt")
async def start_stt_job(request: STTRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = Job(type="stt", input_data=request.url, model_name=request.model)
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_stt_job, job.id, request.url, request.model)

    return {"job_id": job.id, "status": "pending"}
