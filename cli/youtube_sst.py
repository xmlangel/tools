#!/usr/bin/env python3
"""
YouTube AI 음성 인식 자막 생성기 (STT)
자막이 없는 YouTube 영상의 음성을 다운로드하여 OpenAI Whisper AI로 텍스트로 변환합니다.
"""

import yt_dlp
import whisper
import os
import sys
import argparse
import warnings

# 경고 메시지 숨기기
warnings.filterwarnings("ignore")

def get_video_title(youtube_url):
    """
    YouTube 영상의 제목을 가져옵니다.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'youtube_video')
            # 파일명으로 사용할 수 없는 문자 제거
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            return safe_title
    except Exception as e:
        print(f"⚠️ 영상 제목을 가져올 수 없습니다. 기본 이름을 사용합니다: {str(e)}")
        return "youtube_video"

def download_audio(youtube_url, output_path="temp_audio"):
    """
    YouTube 영상에서 오디오만 추출하여 다운로드합니다.
    """
    print(f"📥 오디오 다운로드 시작: {youtube_url}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        final_path = output_path + ".mp3"
        if os.path.exists(final_path):
            print("✅ 오디오 다운로드 완료")
            return final_path
        else:
            raise Exception("오디오 파일 생성 실패")

    except Exception as e:
        print(f"❌ 오디오 다운로드 중 오류 발생: {str(e)}")
        raise

def transcribe_audio(audio_path, model_size="base", output_file="output.txt"):
    """
    다운로드한 오디오를 Whisper AI 모델을 사용하여 텍스트로 변환합니다.
    """
    print(f"\n🤖 Whisper AI 모델({model_size}) 로딩 중... (처음 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)")
    
    try:
        model = whisper.load_model(model_size)
        
        print("📝 음성 변환(STT) 진행 중... (영상 길이에 따라 시간이 소요됩니다)")
        result = model.transcribe(audio_path)
        
        text = result["text"].strip()
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print(f"\n✅ 변환 완료! 파일이 저장되었습니다: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ 음성 변환 중 오류 발생: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='자막이 없는 YouTube 영상을 AI로 분석하여 텍스트로 변환합니다.'
    )
    
    # URL을 선택적 인자로 변경 (nargs='?')
    parser.add_argument('url', nargs='?', help='YouTube 비디오 URL')
    parser.add_argument('-o', '--output', help='출력 파일 경로 (기본값: video_id_stt.txt)')
    parser.add_argument('-m', '--model', default='base', 
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper 모델 크기 (기본값: base). 클수록 정확하지만 느립니다.')
    parser.add_argument('--keep-audio', action='store_true', help='임시 오디오 파일을 삭제하지 않고 유지합니다.')
    
    args = parser.parse_args()
    
    # 인자 없이 실행된 경우 대화형 모드 실행
    if not args.url:
        print("=== YouTube AI 자막 생성기 (STT) ===")
        
        # 1. URL 입력
        while True:
            url_input = input("\nYouTube URL을 입력하세요: ").strip()
            if url_input:
                args.url = url_input
                break
            print("URL은 필수 입력값입니다.")
            
        # 2. 모델 선택
        print("\n사용할 AI 모델을 선택하세요:")
        print("1. tiny   (매우 빠름, 정확도 낮음)")
        print("2. base   (빠름, 보통 정확도)")
        print("3. small  (보통 속도, 좋은 정확도)")
        print("4. medium (느림, 높은 정확도) [기본값]")
        print("5. large  (매우 느림, 매우 높은 정확도)")
        
        model_map = {'1': 'tiny', '2': 'base', '3': 'small', '4': 'medium', '5': 'large'}
        model_input = input("선택 (1-5, 엔터치면 medium): ").strip()
        args.model = model_map.get(model_input, 'medium')
        print(f"선택된 모델: {args.model}")
        
        # 3. 오디오 유지 여부
        keep_input = input("\n임시 오디오 파일을 유지하시겠습니까? (Y/n): ").strip().lower()
        # 입력이 없거나(엔터) y로 시작하면 True, n으로 시작하면 False
        args.keep_audio = keep_input != 'n'
        
        print("\n" + "="*30 + "\n")

    # YouTube 영상 제목 가져오기
    print("\n📺 영상 정보 확인 중...")
    video_title = get_video_title(args.url)
    print(f"✅ 영상 제목: {video_title}")

    # 오디오 파일명 생성 (영상제목_mp3.mp3)
    audio_filename = f"{video_title}_mp3"
    final_audio_path = f"{audio_filename}.mp3"

    # 출력 파일명 자동 생성
    if not args.output:
        args.output = f"{video_title}_stt.txt"

    try:
        # 1. 오디오 다운로드 (파일이 이미 존재하면 건너뛰기)
        if os.path.exists(final_audio_path):
            print(f"\n✅ 기존 오디오 파일을 사용합니다: {final_audio_path}")
        else:
            final_audio_path = download_audio(args.url, audio_filename)

        # 2. AI 음성 인식
        transcribe_audio(final_audio_path, args.model, args.output)

        # 3. 오디오 파일 유지 여부 처리
        if not args.keep_audio and os.path.exists(final_audio_path):
            os.remove(final_audio_path)
            print("🧹 오디오 파일 삭제 완료")
        elif args.keep_audio:
            print(f"💾 오디오 파일 유지: {final_audio_path}")

    except Exception as e:
        print(f"\n❌ 작업 실패: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
