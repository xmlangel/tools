from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, Job
from core.storage import get_file_content
from services.translation_service import process_translation_job

router = APIRouter()

class TranslationRequest(BaseModel):
    input_file: str
    target_lang: str
    openwebui_url: str
    api_key: str
    model: str
    youtube_url: str = None  # Optional YouTube URL from original STT job

@router.post("/translate")
async def start_translation_job(request: TranslationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Get file content from MinIO
    try:
        file_content = get_file_content(request.input_file)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")

    # 2. Create Job
    job = Job(
        type="translate", 
        input_data=request.input_file, 
        model_name=request.model,
        youtube_url=request.youtube_url  # Store YouTube URL if provided
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 3. Start Background Task
    background_tasks.add_task(
        process_translation_job, 
        job.id, 
        file_content, 
        request.openwebui_url, 
        request.api_key, 
        request.model,
        request.input_file
    )

    return {"job_id": job.id, "status": "pending"}
