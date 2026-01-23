from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
import json
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db, Job
from core.storage import get_file_content, upload_stream
from services.translation_service import process_translation_job, translate_chunk, split_text
from services.translation_template_service import get_template, save_template
from services.translation_file_service import extract_text_from_file
import uuid
import datetime

router = APIRouter()

LANG_NAMES_KO = {
    'ko': '한국어',
    'en': '영어',
    'ja': '일본어',
    'zh': '중국어',
    'auto': '자동감지'
}

class TranslationRequest(BaseModel):
    input_file: str
    target_lang: str
    src_lang: str = 'en'
    provider: str
    api_url: str
    api_key: str
    model: str
    youtube_url: Optional[str] = None  # Optional YouTube URL from original STT job

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
        request.provider,
        request.api_url, 
        request.api_key, 
        request.model,
        request.input_file,
        request.target_lang,
        request.src_lang
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

@router.get("/translate/template")
async def get_current_template():
    return get_template()

class TemplateRequest(BaseModel):
    system_prompt: str
    user_prompt_template: str

@router.post("/translate/template")
async def update_template(request: TemplateRequest):
    success = save_template(request.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    return {"status": "success"}

class SimpleTranslationRequest(BaseModel):
    text: str
    target_lang: str
    src_lang: str = 'en'
    provider: str
    api_url: str
    api_key: str
    model: str
    system_prompt: str = None

@router.post("/translate/simple")
async def simple_translation(request: SimpleTranslationRequest, db: Session = Depends(get_db)):
    
    # Split text if it's too long, though for "simple" we might just process it.
    # But to be safe and consistent, let's split and join.
    chunks = split_text(request.text)
    translated_parts = []
    
    for chunk in chunks:
        # We can't use background tasks here easily if we want to return the result synchronously.
        # So we'll do it synchronously. This might timeout for very large texts.
        translated = translate_chunk(
            chunk, 
            request.provider,
            request.api_url, 
            request.api_key, 
            request.model, 
            request.target_lang,
            request.src_lang,
            request.system_prompt
        )
        translated_parts.append(translated)
    
    final_translation = "\n\n".join(translated_parts)

    # 1. Store in MinIO as a job
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:8]
    input_filename = f"simple_in_{timestamp}_{uid}.txt"
    output_filename = f"simple_out_{timestamp}_{uid}.txt"

    # Consolidate input and output as requested by user with dynamic header
    src_name = LANG_NAMES_KO.get(request.src_lang, request.src_lang)
    tgt_name = LANG_NAMES_KO.get(request.target_lang, request.target_lang)
    header = f"# 텍스트입력, {src_name}, {tgt_name}"
    
    consolidated_content = f"{header}\n{request.text}\n\n#번역결과\n{final_translation}"

    upload_stream(request.text.encode('utf-8'), input_filename, "text/plain")
    upload_stream(consolidated_content.encode('utf-8'), output_filename, "text/plain")

    # 2. Create Job Record
    job = Job(
        type="translate",
        status="completed",
        progress=100,
        input_data=input_filename,
        output_files=json.dumps({
            "translated_text": output_filename
        }),
        model_name=request.model,
        source_type="text",
        original_filename="Simple Translation Tab"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "translated_text": final_translation,
        "job": {
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "progress": job.progress,
            "input": job.input_data,
            "output": json.loads(job.output_files),
            "created_at": job.created_at,
            "error": job.error_message
        }
    }

@router.post("/translate/file")
async def translate_file(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    src_lang: str = Form(...),
    provider: str = Form(...),
    api_url: str = Form(...),
    api_key: Optional[str] = Form(None),
    model: str = Form(...),
    system_prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        filename = file.filename
        
        # Extract text from file
        try:
            text = extract_text_from_file(content, filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Split and translate
        chunks = split_text(text)
        translated_parts = []
        
        for chunk in chunks:
            translated = translate_chunk(
                chunk, 
                provider,
                api_url, 
                api_key, 
                model, 
                target_lang,
                src_lang,
                system_prompt
            )
            translated_parts.append(translated)
        
        final_translation = "\n\n".join(translated_parts)
        
        # 1. Store in MinIO
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = str(uuid.uuid4())[:8]
        # Use original filename but add prefix/timestamp to avoid collisions
        safe_name = filename.replace(' ', '_')
        input_object = f"upload_{timestamp}_{uid}_{safe_name}"
        output_object = f"translated_{timestamp}_{uid}_{safe_name}"
        if not output_object.endswith('.txt'):
            output_object += '.txt'

        # Consolidate input and output as requested by user with dynamic header
        src_name = LANG_NAMES_KO.get(src_lang, src_lang)
        tgt_name = LANG_NAMES_KO.get(target_lang, target_lang)
        header = f"# 텍스트입력, {src_name}, {tgt_name}"
        
        consolidated_content = f"{header}\n{text}\n\n#번역결과\n{final_translation}"

        upload_stream(text.encode('utf-8'), input_object, "text/plain")
        upload_stream(consolidated_content.encode('utf-8'), output_object, "text/plain")

        # 2. Create Job record
        job = Job(
            type="translate",
            status="completed",
            progress=100,
            input_data=input_object,
            output_files=json.dumps({
                "translated_text": output_object
            }),
            model_name=model,
            source_type="upload",
            original_filename=filename
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        return {
            "original_text": text,
            "translated_text": final_translation,
            "filename": filename,
            "job": {
                "id": job.id,
                "type": job.type,
                "status": job.status,
                "progress": job.progress,
                "input": job.input_data,
                "output": json.loads(job.output_files),
                "created_at": job.created_at,
                "error": job.error_message
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
