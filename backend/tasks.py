import os
import json
import yt_dlp
import whisper
import requests
import time
from sqlalchemy.orm import Session
from database import Job, SessionLocal
from storage import upload_file, upload_stream

# --- STT Logic ---

def get_video_title(youtube_url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'youtube_video')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            return safe_title.replace(' ', '_')
    except Exception as e:
        print(f"Error getting title: {e}")
        return "youtube_video"

def download_audio(youtube_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    return output_path + ".mp3"

def process_stt_job(job_id: int, youtube_url: str, model_size: str):
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    try:
        job.status = "processing"
        job.progress = 10
        db.commit()

        # 1. Download Audio
        video_title = get_video_title(youtube_url)
        base_filename = f"{job_id}_{video_title}"
        temp_audio_path = f"/tmp/{base_filename}"
        
        job.progress = 20
        db.commit()
        
        final_audio_path = download_audio(youtube_url, temp_audio_path)
        
        # Upload Audio to MinIO
        audio_object_name = f"{base_filename}.mp3"
        upload_file(final_audio_path, audio_object_name)
        
        job.progress = 50
        db.commit()

        # 2. Transcribe
        model = whisper.load_model(model_size)
        job.progress = 60
        db.commit()
        
        result = model.transcribe(final_audio_path)
        text = result["text"].strip()
        
        job.progress = 90
        db.commit()

        # Upload Text to MinIO
        text_object_name = f"{base_filename}.txt"
        upload_stream(text.encode('utf-8'), text_object_name, "text/plain")

        # Cleanup local files
        if os.path.exists(final_audio_path):
            os.remove(final_audio_path)

        # Update Job
        job.status = "completed"
        job.progress = 100
        job.output_files = json.dumps({"audio": audio_object_name, "text": text_object_name})
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        print(f"STT Job failed: {e}")
    finally:
        db.close()

# --- Translation Logic ---

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
