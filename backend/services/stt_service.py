import os
import json
import yt_dlp
import whisper
import re
from sqlalchemy.orm import Session
from core.database import Job, SessionLocal, LLMConfig
from core.storage import upload_file, upload_stream
from core.logger import setup_logger
from services.summary_service import generate_summary
from services.translation_service import translate_chunk, split_text

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

def clean_vtt_content(content):
    lines = content.splitlines()
    text = []
    seen = set()
    # Simple timestamp matcher: 00:00:00.000 --> 00:00:00.000
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}')
    
    for line in lines:
        line = line.strip()
        if not line or line == "WEBVTT":
            continue
        if timestamp_pattern.search(line):
            continue
        if line.isdigit() and "-->" not in line: 
             continue
             
        # Remove HTML-like tags
        clean_line = re.sub(r'<[^>]+>', '', line)
        if clean_line and clean_line not in seen:
            text.append(clean_line)
            seen.add(clean_line)
            
    return " ".join(text)

def download_manual_subtitle(youtube_url, base_path):
    # Check logical existence first
    ydl_opts_check = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    target_lang = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            subtitles = info.get('subtitles', {})
            # Priorities: en, en-US, en-GB
            for lang in ['en', 'en-US', 'en-GB']:
                if lang in subtitles:
                    target_lang = lang
                    break
    except Exception as e:
        logger.error(f"Error checking subtitles: {e}")
        return None

    if not target_lang:
        return None
        
    logger.info(f"Found manual subtitles for language: {target_lang}")
    
    # Download
    ydl_opts_dl = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': [target_lang],
        'subtitlesformat': 'vtt',
        'outtmpl': base_path, # yt-dlp will append .lang.vtt
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
            ydl.download([youtube_url])
            
        expected_file = f"{base_path}.{target_lang}.vtt"
        if os.path.exists(expected_file):
            with open(expected_file, 'r', encoding='utf-8') as f:
                content = f.read()
            os.remove(expected_file)
            return clean_vtt_content(content)
    except Exception as e:
        logger.error(f"Error downloading subtitle: {e}")
        return None
        
    return None

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

        # 2. Check for manual subtitles first
        logger.info(f"Job {job_id}: Checking for existing subtitles...")
        subtitle_text = download_manual_subtitle(youtube_url, temp_audio_path.replace('.mp3', ''))
        
        text = ""
        if subtitle_text:
             logger.info(f"Job {job_id}: Used existing manual subtitles. Skipping Whisper.")
             text = subtitle_text
             job.progress = 90 # Jump progress
        else:
            # 3. Transcribe with Whisper (Fallback)
            logger.info(f"Job {job_id}: No suitable subtitles found. Loading Whisper model ({model_size})...")
            model = whisper.load_model(model_size)
            job.progress = 60
            db.commit()
            
            logger.info(f"Job {job_id}: Transcribing audio...")
            result = model.transcribe(final_audio_path)
            text = result["text"].strip()
            
        logger.info(f"Job {job_id}: Transcription/Subtitle extraction complete. Length: {len(text)} chars")
        
        job.progress = 90

        db.commit()

        # Upload Text to MinIO
        text_object_name = f"{base_filename}.txt"
        logger.info(f"Job {job_id}: Uploading text to MinIO as {text_object_name}...")
        upload_stream(text.encode('utf-8'), text_object_name, "text/plain")
        
        # 4. Generate Summary
        logger.info(f"Job {job_id}: Generating summary...")
        summary_text = generate_summary(text)
        summary_object_name = f"{base_filename}_summary.txt"
        
        logger.info(f"Job {job_id}: Uploading summary to MinIO as {summary_object_name}...")
        upload_stream(summary_text.encode('utf-8'), summary_object_name, "text/plain")

        # 5. Generate Korean Translation
        translation_object_name = None
        try:
            logger.info(f"Job {job_id}: Generating Korean translation...")
            
            # Get default LLM config
            llm_config = db.query(LLMConfig).filter(LLMConfig.is_default == True).first()
            if not llm_config:
                # If no default, try to get any config
                llm_config = db.query(LLMConfig).first()
            
            if llm_config:
                # Split text into chunks for translation
                chunks = split_text(text)
                logger.info(f"Job {job_id}: Split text into {len(chunks)} chunks for translation")
                
                translated_parts = []
                for i, chunk in enumerate(chunks):
                    logger.info(f"Job {job_id}: Translating chunk {i+1}/{len(chunks)}...")
                    translated = translate_chunk(
                        chunk,
                        llm_config.openwebui_url,
                        llm_config.api_key,
                        llm_config.model,
                        target_lang='ko'
                    )
                    translated_parts.append(translated)
                
                final_translation = "\n\n".join(translated_parts)
                
                # Upload translation to MinIO
                translation_object_name = f"{base_filename}_translation.txt"
                logger.info(f"Job {job_id}: Uploading translation to MinIO as {translation_object_name}...")
                upload_stream(final_translation.encode('utf-8'), translation_object_name, "text/plain")
                logger.info(f"Job {job_id}: Translation completed successfully")
            else:
                logger.warning(f"Job {job_id}: No LLM configuration found. Skipping translation.")
        except Exception as e:
            logger.error(f"Job {job_id}: Translation failed: {e}", exc_info=True)
            # Continue even if translation fails

        # Cleanup local files
        if os.path.exists(final_audio_path):
            os.remove(final_audio_path)
            logger.info(f"Job {job_id}: Cleaned up local file {final_audio_path}")

        # Update Job
        job.status = "completed"
        job.progress = 100
        
        output_data = {
            "audio": audio_object_name, 
            "text": text_object_name,
            "summary": summary_object_name
        }
        
        if translation_object_name:
            output_data["translation"] = translation_object_name
        
        job.output_files = json.dumps(output_data)
        db.commit()
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    finally:
        db.close()
