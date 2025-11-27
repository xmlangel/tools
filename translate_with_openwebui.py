#!/usr/bin/env python3
"""
OpenWebUI 텍스트 번역기
텍스트 파일을 읽어 OpenWebUI API를 통해 한국어로 번역합니다.
긴 텍스트도 문맥 단위로 나누어 전체를 번역합니다.
"""

import requests
import json
import os
import sys
import argparse
import time
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def read_file(file_path):
    """파일을 읽어서 내용을 반환합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {str(e)}")
        sys.exit(1)

def save_file(file_path, content):
    """내용을 파일에 저장합니다."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 번역 결과 저장 완료: {file_path}")
    except Exception as e:
        print(f"❌ 파일 저장 실패: {str(e)}")

def split_text(text, chunk_size=2000):
    """
    텍스트를 문맥이 끊기지 않도록 문단/문장 단위로 나눕니다.
    단순히 글자수로 자르면 문장이 잘릴 수 있으므로, 개행문자나 마침표를 기준으로 자릅니다.
    """
    chunks = []
    current_chunk = ""
    
    # 문단 단위로 먼저 분리
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n"
        else:
            # 현재 청크가 꽉 찼으면 저장하고 초기화
            if current_chunk:
                chunks.append(current_chunk)
            
            # 만약 한 문단이 chunk_size보다 크다면 강제로 나눔 (드문 경우)
            if len(paragraph) > chunk_size:
                # 이 부분은 더 정교하게 할 수 있지만, 일단은 그냥 넣음
                chunks.append(paragraph + "\n")
                current_chunk = ""
            else:
                current_chunk = paragraph + "\n"
    
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def translate_chunk(text, api_url, api_key, model):
    """OpenWebUI API를 호출하여 텍스트 조각을 번역합니다."""
    
    # 시도해볼 엔드포인트 목록
    base_url = api_url.rstrip('/')
    endpoints = [
        f"{base_url}/api/chat/completions",  # OpenWebUI 표준
        f"{base_url}/v1/chat/completions",   # OpenAI 호환
        f"{base_url}/api/v1/chat/completions",
        f"{base_url}/chat/completions",
        f"{base_url}/api/chat"               # 일부 구버전
    ]
    
    # 사용자가 이미 전체 경로를 입력했을 경우를 대비
    if 'chat/completions' in api_url or api_url.endswith('/chat'):
        endpoints.insert(0, api_url)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"""
    다음 텍스트를 한국어로 번역해줘. 
    문맥을 고려해서 자연스럽게 번역하고, 번역된 결과만 출력해. 
    설명이나 잡담은 하지 마.
    
    [텍스트 시작]
    {text}
    [텍스트 끝]
    """
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional translator. Translate the following text into Korean naturally."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    last_error = None
    
    for target_url in endpoints:
        try:
            # print(f"Trying: {target_url}") # 디버깅용
            response = requests.post(target_url, headers=headers, json=data, timeout=120)
            
            # 404나 405는 경로 문제이므로 다음 경로 시도
            if response.status_code in [404, 405]:
                last_error = f"{response.status_code} {response.reason}"
                continue
                
            response.raise_for_status()
            
            result = response.json()
            
            # 응답 형식 처리
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            # /api/chat 엔드포인트의 경우 (Ollama 스타일)
            elif 'message' in result:
                return result['message']['content'].strip()
            else:
                print(f"⚠️ 예상치 못한 응답 형식 ({target_url}): {result}")
                return text 
                
        except Exception as e:
            last_error = str(e)
            continue
            
    print(f"❌ 모든 API 경로 시도 실패. 마지막 오류: {last_error}")
    return f"[번역 실패]\n{text}"

def main():
    print("=== OpenWebUI 텍스트 번역기 ===")
    
    # 1. 설정 입력 (인자가 없으면 대화형)
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', help='번역할 텍스트 파일 경로')
    parser.add_argument('--url', help='OpenWebUI 주소')
    parser.add_argument('--key', help='API Key')
    parser.add_argument('--model', help='사용할 모델 이름')
    
    args = parser.parse_args()
    
    file_path = args.file
    
    # 환경 변수 또는 인자에서 설정 가져오기
    api_url = args.url or os.getenv('OPENWEBUI_URL')
    api_key = args.key or os.getenv('OPENWEBUI_API_KEY')
    model = args.model or os.getenv('OPENWEBUI_MODEL')
    
    # 대화형 입력 (값이 없는 경우에만)
    if not file_path:
        while True:
            file_path = input("\n번역할 텍스트 파일 경로를 입력하세요: ").strip()
            if os.path.exists(file_path):
                break
            print("❌ 파일이 존재하지 않습니다. 다시 입력해주세요.")
            
    if not api_url:
        api_url = input("OpenWebUI 주소 (기본값: http://localhost:3000): ").strip()
        if not api_url:
            api_url = "http://localhost:3000"
            
    if not api_key:
        api_key = input("API Key를 입력하세요: ").strip()
        
    if not model:
        model = input("사용할 모델 이름을 입력하세요 (예: llama3, gpt-4): ").strip()
        if not model:
            print("모델 이름은 필수입니다.")
            sys.exit(1)
            
    print(f"\n⚙️  설정 확인:")
    print(f"   - URL: {api_url}")
    print(f"   - Model: {model}")
    print(f"   - API Key: {'*' * 5}{api_key[-4:] if api_key and len(api_key) > 4 else '****'}")

    # 2. 파일 읽기 및 분할
    print(f"\n📖 파일 읽는 중: {file_path}")
    original_text = read_file(file_path)
    
    chunks = split_text(original_text)
    print(f"✂️ 전체 텍스트를 {len(chunks)}개의 조각으로 나누었습니다.")
    
    # 3. 순차적 번역
    translated_parts = []
    
    print("\n🚀 번역 시작...")
    for i, chunk in enumerate(chunks):
        print(f"[{i+1}/{len(chunks)}] 번역 중... ({len(chunk)}자)")
        translated_text = translate_chunk(chunk, api_url, api_key, model)
        translated_parts.append(translated_text)
        # API 부하 방지를 위해 살짝 대기
        time.sleep(0.5)
        
    # 4. 결과 합치기 및 저장
    final_translation = "\n\n".join(translated_parts)
    
    output_path = os.path.splitext(file_path)[0] + "_translated.txt"
    save_file(output_path, final_translation)
    
    print("\n✨ 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()
