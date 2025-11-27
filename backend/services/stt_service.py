import os
import json
import yt_dlp
import whisper
from sqlalchemy.orm import Session
from core.database import Job, SessionLocal
from core.storage import upload_file, upload_stream

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
