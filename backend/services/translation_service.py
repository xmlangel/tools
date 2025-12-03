import json
import time
from sqlalchemy.orm import Session
from core.database import Job, SessionLocal
from core.storage import upload_stream
from core.logger import setup_logger
from services.llm_service import send_llm_request
from services.translation_template_service import get_template, DEFAULT_TEMPLATE

logger = setup_logger("translation_service")

def split_text(text, chunk_size=2000):
    chunks = []
    current_chunk = ""
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(paragraph) > chunk_size:
                chunks.append(paragraph + "\n")
                current_chunk = ""
            else:
                current_chunk = paragraph + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def translate_chunk(text, api_url, api_key, model):
    template = get_template()
    system_prompt = template.get("system_prompt", DEFAULT_TEMPLATE["system_prompt"])
    user_prompt_template = template.get("user_prompt_template", DEFAULT_TEMPLATE["user_prompt_template"])
    
    user_prompt = user_prompt_template.replace("{text}", text)
    
    try:
        return send_llm_request(api_url, api_key, model, system_prompt, user_prompt, temperature=0.3)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"[Translation Failed] {text}"

def process_translation_job(job_id: int, text_content: str, api_url: str, api_key: str, model: str, original_filename: str):
    logger.info(f"Starting Translation job {job_id} with model {model} for file {original_filename}")
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        job.status = "processing"
        job.progress = 10
        db.commit()

        chunks = split_text(text_content)
        logger.info(f"Job {job_id}: Split text into {len(chunks)} chunks")
        translated_parts = []
        
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            # Check for cancellation
            db.refresh(job)
            if job.status == "cancelled":
                logger.info(f"Job {job_id}: Cancelled by user")
                return

            logger.info(f"Job {job_id}: Translating chunk {i+1}/{total_chunks} ({len(chunk)} chars)...")
            translated = translate_chunk(chunk, api_url, api_key, model)
            translated_parts.append(translated)
            
            # 진행률 업데이트 (10% ~ 90%)
            progress = 10 + int((i + 1) / total_chunks * 80)
            job.progress = progress
            db.commit()
            
            time.sleep(0.5)
            
        final_translation = "\n\n".join(translated_parts)
        
        # Upload to MinIO
        # Generate output filename: original_filename_translation.txt
        name_without_ext = original_filename.rsplit('.', 1)[0]
        output_filename = f"{name_without_ext}_translation.txt"
        
        logger.info(f"Job {job_id}: Uploading result to MinIO as {output_filename}")
        upload_stream(final_translation.encode('utf-8'), output_filename, "text/plain")
        
        job.status = "completed"
        job.progress = 100
        job.output_files = json.dumps({"translated_text": output_filename})
        db.commit()
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    finally:
        db.close()
