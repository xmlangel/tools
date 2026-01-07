from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
import json
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
        request.input_file,
        request.target_lang
    )

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

@router.get("/template")
async def get_current_template():
    from services.translation_template_service import get_template
    return get_template()

class TemplateRequest(BaseModel):
    system_prompt: str
    user_prompt_template: str

@router.post("/template")
async def update_template(request: TemplateRequest):
    from services.translation_template_service import save_template
    success = save_template(request.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    return {"status": "success"}

class SimpleTranslationRequest(BaseModel):
    text: str
    target_lang: str
    openwebui_url: str
    api_key: str
    model: str
    system_prompt: str = None

@router.post("/translate/simple")
async def simple_translation(request: SimpleTranslationRequest):
    from services.translation_service import translate_chunk, split_text
    
    # Split text if it's too long, though for "simple" we might just process it.
    # But to be safe and consistent, let's split and join.
    chunks = split_text(request.text)
    translated_parts = []
    
    for chunk in chunks:
        # We can't use background tasks here easily if we want to return the result synchronously.
        # So we'll do it synchronously. This might timeout for very large texts.
        translated = translate_chunk(
            chunk, 
            request.openwebui_url, 
            request.api_key, 
            request.model, 
            request.target_lang,
            request.system_prompt
        )
        translated_parts.append(translated)
    
    final_translation = "\n\n".join(translated_parts)
    return {"translated_text": final_translation}
