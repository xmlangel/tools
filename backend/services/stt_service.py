import os
import json
import yt_dlp
import whisper
from sqlalchemy.orm import Session
from core.database import Job, SessionLocal
from core.storage import upload_file, upload_stream
from core.logger import setup_logger

logger = setup_logger("stt_service")

def get_video_title(youtube_url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'youtube_video')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            return safe_title.replace(' ', '_')
    except Exception as e:
        logger.error(f"Error getting title: {e}")
        return "youtube_video"

def download_audio(youtube_url, output_path):
    logger.info(f"Downloading audio from {youtube_url} to {output_path}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    logger.info("Download complete")
    return output_path + ".mp3"

def process_stt_job(job_id: int, youtube_url: str, model_size: str):
    logger.info(f"Starting STT job {job_id} for URL: {youtube_url} with model: {model_size}")
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        job.status = "processing"
        job.progress = 10
        db.commit()

        # 1. Download Audio
        logger.info(f"Job {job_id}: Fetching video title...")
        video_title = get_video_title(youtube_url)
        base_filename = f"{job_id}_{video_title}"
        temp_audio_path = f"/tmp/{base_filename}"
        
        job.progress = 20
        db.commit()
        
        logger.info(f"Job {job_id}: Downloading audio...")
        final_audio_path = download_audio(youtube_url, temp_audio_path)
        
        # Upload Audio to MinIO
        audio_object_name = f"{base_filename}.mp3"
        logger.info(f"Job {job_id}: Uploading audio to MinIO as {audio_object_name}...")
        upload_file(final_audio_path, audio_object_name)
        
        job.progress = 50
        db.commit()

        # Check for cancellation
        db.refresh(job)
        if job.status == "cancelled":
            logger.info(f"Job {job_id}: Cancelled by user")
            return

        # 2. Transcribe
        logger.info(f"Job {job_id}: Loading Whisper model ({model_size})...")
        model = whisper.load_model(model_size)
        job.progress = 60
        db.commit()
        
        logger.info(f"Job {job_id}: Transcribing audio...")
        result = model.transcribe(final_audio_path)
        text = result["text"].strip()
        logger.info(f"Job {job_id}: Transcription complete. Length: {len(text)} chars")
        
        job.progress = 90
        db.commit()

        # Upload Text to MinIO
        text_object_name = f"{base_filename}.txt"
        logger.info(f"Job {job_id}: Uploading text to MinIO as {text_object_name}...")
        upload_stream(text.encode('utf-8'), text_object_name, "text/plain")

        # Cleanup local files
        if os.path.exists(final_audio_path):
            os.remove(final_audio_path)
            logger.info(f"Job {job_id}: Cleaned up local file {final_audio_path}")

        # Update Job
        job.status = "completed"
        job.progress = 100
        job.output_files = json.dumps({"audio": audio_object_name, "text": text_object_name})
        db.commit()
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    finally:
        db.close()
