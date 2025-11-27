import json
import requests
import time
from sqlalchemy.orm import Session
from core.database import Job, SessionLocal
from core.storage import upload_stream

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
    base_url = api_url.rstrip('/')
    # Try standard OpenAI compatible endpoint first as it's most common for OpenWebUI
    target_url = f"{base_url}/api/chat/completions" 
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"다음 텍스트를 한국어로 번역해줘. 문맥을 고려해서 자연스럽게 번역하고, 번역된 결과만 출력해. 설명이나 잡담은 하지 마.\n\n[텍스트 시작]\n{text}\n[텍스트 끝]"
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional translator. Translate the following text into Korean naturally."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(target_url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        elif 'message' in result:
             return result['message']['content'].strip()
        else:
            return text
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[Translation Failed] {text}"

def process_translation_job(job_id: int, text_content: str, api_url: str, api_key: str, model: str):
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    try:
        job.status = "processing"
        job.progress = 10
        db.commit()

        chunks = split_text(text_content)
        translated_parts = []
        
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            translated = translate_chunk(chunk, api_url, api_key, model)
            translated_parts.append(translated)
            
            # 진행률 업데이트 (10% ~ 90%)
            progress = 10 + int((i + 1) / total_chunks * 80)
            job.progress = progress
            db.commit()
            
            time.sleep(0.5)
            
        final_translation = "\n\n".join(translated_parts)
        
        # Upload to MinIO
        output_filename = f"translation_{job_id}.txt"
        upload_stream(final_translation.encode('utf-8'), output_filename, "text/plain")
        
        job.status = "completed"
        job.progress = 100
        job.output_files = json.dumps({"translated_text": output_filename})
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
