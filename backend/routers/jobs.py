from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db, Job
import json

router = APIRouter()

@router.get("/jobs")
def get_jobs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for job in jobs:
        output = json.loads(job.output_files) if job.output_files else {}
        result.append({
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "progress": job.progress,
            "input": job.input_data,
            "output": output,
            "created_at": job.created_at,
            "error": job.error_message
        })
    
    return {"jobs": result}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}
    
    output = json.loads(job.output_files) if job.output_files else {}
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "output": output,
        "error": job.error_message
    }
