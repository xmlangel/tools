#!/usr/bin/env python3
"""
YouTube 자막 다운로더
YouTube 링크에서 자막을 다운로드하여 텍스트 파일로 저장합니다.
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
import sys
import argparse


def extract_video_id(youtube_url):
    """
    YouTube URL에서 비디오 ID를 추출합니다.
    
    지원하는 URL 형식:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError("유효하지 않은 YouTube URL입니다.")


def download_subtitle(youtube_url, output_file=None, language='ko'):
    """
    YouTube 비디오의 자막을 다운로드하여 텍스트 파일로 저장합니다.
    
    Args:
        youtube_url (str): YouTube 비디오 URL
        output_file (str): 저장할 파일 경로 (기본값: video_id.txt)
        language (str): 자막 언어 코드 (기본값: 'ko' 한국어)
    
    Returns:
        str: 저장된 파일 경로
    """
    try:
        # 비디오 ID 추출
        video_id = extract_video_id(youtube_url)
        print(f"비디오 ID: {video_id}")
        
        # 자막 다운로드 시도
        try:
            # 지정된 언어로 자막 가져오기
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            print(f"{language} 자막을 찾았습니다.")
        except:
            # 지정된 언어가 없으면 사용 가능한 자막 확인
            print(f"{language} 자막을 찾을 수 없습니다. 사용 가능한 자막을 확인합니다...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 자동 생성 자막이라도 가져오기
            try:
                transcript = transcript_list.find_transcript([language]).fetch()
                print(f"{language} 자동 생성 자막을 찾았습니다.")
            except:
                # 첫 번째 사용 가능한 자막 가져오기
                available_transcripts = list(transcript_list)
                if not available_transcripts:
                    raise Exception("사용 가능한 자막이 없습니다.")
                
                first_transcript = available_transcripts[0]
                transcript = first_transcript.fetch()
                print(f"{first_transcript.language} 자막을 사용합니다.")
        
        # 텍스트 포맷으로 변환
        formatter = TextFormatter()
        text_formatted = formatter.format_transcript(transcript)
        
        # 출력 파일명 설정
        if output_file is None:
            output_file = f"{video_id}.txt"
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_formatted)
        
        print(f"\n자막이 성공적으로 저장되었습니다: {output_file}")
        print(f"총 {len(transcript)}개의 자막 항목이 저장되었습니다.")
        
        return output_file
        
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(
        description='YouTube 비디오의 자막을 다운로드하여 텍스트 파일로 저장합니다.',
        epilog='예시: python youtube_subtitle_downloader.py https://www.youtube.com/watch?v=VIDEO_ID'
    )
    
    parser.add_argument('url', help='YouTube 비디오 URL')
    parser.add_argument('-o', '--output', help='출력 파일 경로 (기본값: video_id.txt)')
    parser.add_argument('-l', '--language', default='ko', 
                        help='자막 언어 코드 (기본값: ko)')
    
    args = parser.parse_args()
    
    try:
        download_subtitle(args.url, args.output, args.language)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
