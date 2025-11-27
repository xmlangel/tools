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
            "error": job.error_message,
            "youtube_url": job.youtube_url
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
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "input_data": job.input_data,
        "output": output,
        "error": job.error_message,
        "youtube_url": job.youtube_url,
        "created_at": job.created_at.isoformat() if job.created_at else None
    }

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}
    
    if job.status in ["pending", "processing"]:
        job.status = "cancelled"
        job.error_message = "Job cancelled by user"
        db.commit()
        return {"message": "Job cancelled"}
    
    return {"message": "Job is already completed or failed"}

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}
    
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
