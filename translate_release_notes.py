#!/usr/bin/env python3
"""
릴리즈 노트 한글 번역기
generate_release_notes.py로 생성된 릴리즈 노트를 LLM을 사용하여 한글로 번역합니다.
OpenWebUI API를 통해 기술 문서에 적합한 자연스러운 번역을 제공합니다.
"""

import requests
import json
import os
import sys
import argparse
import time
import re
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class ReleaseNotesTranslator:
    """릴리즈 노트 번역을 위한 클래스"""

    def __init__(self, api_url, api_key, model):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model

        # 시도할 엔드포인트 목록
        self.endpoints = [
            f"{self.api_url}/api/chat/completions",
            f"{self.api_url}/v1/chat/completions",
            f"{self.api_url}/api/v1/chat/completions",
            f"{self.api_url}/chat/completions",
            f"{self.api_url}/api/chat"
        ]

        # 사용자가 전체 경로를 입력한 경우
        if 'chat/completions' in api_url or api_url.endswith('/chat'):
            self.endpoints.insert(0, api_url)

    def read_file(self, file_path):
        """릴리즈 노트 파일을 읽습니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {str(e)}")
            sys.exit(1)

    def save_file(self, file_path, content):
        """번역된 내용을 파일에 저장합니다."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 번역 결과 저장 완료: {file_path}")
        except Exception as e:
            print(f"❌ 파일 저장 실패: {str(e)}")

    def split_by_sections(self, markdown_text):
        """
        릴리즈 노트를 의미 있는 섹션 단위로 나눕니다.
        날짜별(##) 또는 타입별(###) 섹션으로 분리하여 문맥을 유지합니다.
        """
        sections = []
        current_section = []
        lines = markdown_text.split('\n')

        for line in lines:
            # ## 또는 ### 헤더를 만나면 새 섹션 시작
            if line.startswith('## ') or line.startswith('### '):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = [line]
                else:
                    current_section = [line]
            else:
                current_section.append(line)

        # 마지막 섹션 추가
        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def translate_section(self, section_text, section_index, total_sections):
        """개별 섹션을 번역합니다."""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 릴리즈 노트 특화 프롬프트
        prompt = f"""
다음은 소프트웨어 릴리즈 노트의 일부입니다. 기술 문서로서 정확하고 자연스럽게 한글로 번역해주세요.

**번역 규칙:**
1. 마크다운 형식은 그대로 유지 (##, ###, -, *, `, [ ], 등)
2. 커밋 해시 ([`abc123`])는 번역하지 말고 그대로 유지
3. 기술 용어는 아래 가이드를 따름:
   - Features → 새로운 기능
   - Bug Fixes → 버그 수정
   - Performance → 성능 개선
   - Refactoring → 리팩토링
   - Documentation → 문서
   - Tests → 테스트
   - Chores → 기타 작업
   - Build System → 빌드 시스템
   - CI/CD → CI/CD
4. 날짜 형식 유지 (YYYY-MM-DD)
5. 이모지는 그대로 유지
6. 코드, 파일명, 함수명 등 기술적 식별자는 그대로 유지
7. 자연스러운 한국어 문장으로 번역 (직역보다는 의역)

**번역할 내용:**

{section_text}

**번역된 결과만 출력하세요. 설명이나 추가 코멘트는 하지 마세요.**
"""

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional technical translator specializing in software documentation. Translate accurately while maintaining technical terminology and markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        last_error = None

        for target_url in self.endpoints:
            try:
                response = requests.post(target_url, headers=headers, json=data, timeout=180)

                if response.status_code in [404, 405]:
                    last_error = f"{response.status_code} {response.reason}"
                    continue

                response.raise_for_status()
                result = response.json()

                # 응답 형식 처리
                if 'choices' in result and len(result['choices']) > 0:
                    translated = result['choices'][0]['message']['content'].strip()
                    return self.clean_translation(translated)
                elif 'message' in result:
                    translated = result['message']['content'].strip()
                    return self.clean_translation(translated)
                else:
                    print(f"⚠️ 예상치 못한 응답 형식: {result}")
                    return section_text

            except Exception as e:
                last_error = str(e)
                continue

        print(f"❌ 섹션 [{section_index}/{total_sections}] 번역 실패: {last_error}")
        return f"[번역 실패]\n{section_text}"

    def clean_translation(self, translated_text):
        """번역 결과를 정리합니다."""
        # LLM이 추가한 불필요한 설명 제거
        cleaned = translated_text

        # "번역 결과:", "번역:", "Translation:" 등의 prefix 제거
        patterns = [
            r'^번역\s*결과\s*:\s*',
            r'^번역\s*:\s*',
            r'^Translation\s*:\s*',
            r'^\*\*번역\*\*\s*:\s*',
        ]

        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        return cleaned.strip()

    def translate_release_notes(self, input_file, output_file=None):
        """릴리즈 노트 전체를 번역합니다."""

        print(f"\n📖 릴리즈 노트 읽는 중: {input_file}")
        original_text = self.read_file(input_file)

        # 섹션별로 분리
        sections = self.split_by_sections(original_text)
        print(f"✂️ 릴리즈 노트를 {len(sections)}개의 섹션으로 나누었습니다.")

        # 섹션별로 번역
        translated_sections = []
        print("\n🚀 번역 시작...\n")

        for i, section in enumerate(sections, 1):
            # 헤더 추출 (진행상황 표시용)
            header_match = re.search(r'^#{1,3}\s+(.+)$', section, re.MULTILINE)
            header = header_match.group(1) if header_match else "섹션"

            print(f"[{i}/{len(sections)}] 번역 중: {header[:50]}...")
            translated = self.translate_section(section, i, len(sections))
            translated_sections.append(translated)

            # API 부하 방지
            if i < len(sections):
                time.sleep(1)

        # 번역된 섹션 합치기
        final_translation = '\n\n'.join(translated_sections)

        # 출력 파일명 결정
        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_ko.md"

        # 저장
        self.save_file(output_file, final_translation)

        print("\n✨ 번역 완료!")
        return output_file


def main():
    """메인 함수"""
    print("=== 릴리즈 노트 한글 번역기 ===\n")

    parser = argparse.ArgumentParser(
        description='릴리즈 노트를 LLM을 사용하여 한글로 번역합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 사용 (환경변수 사용)
  python translate_release_notes.py RELEASE_NOTES.md

  # 모든 옵션 지정
  python translate_release_notes.py RELEASE_NOTES.md \\
    --url http://localhost:3000 \\
    --key sk-xxx \\
    --model llama3 \\
    --output RELEASE_NOTES_ko.md

  # 환경변수 설정 (.env 파일)
  OPENWEBUI_URL=http://localhost:3000
  OPENWEBUI_API_KEY=sk-xxx
  OPENWEBUI_MODEL=llama3

번역 특징:
  - 마크다운 형식 유지
  - 기술 용어의 정확한 번역
  - 커밋 해시, 코드 등 식별자 보존
  - 섹션 단위 번역으로 문맥 유지
        """
    )

    parser.add_argument(
        'input_file',
        nargs='?',
        help='번역할 릴리즈 노트 파일 (Markdown)'
    )

    parser.add_argument(
        '-o', '--output',
        help='출력 파일 경로 (기본값: 입력파일명_ko.md)'
    )

    parser.add_argument(
        '--url',
        help='OpenWebUI API 주소 (환경변수: OPENWEBUI_URL)'
    )

    parser.add_argument(
        '--key',
        help='API Key (환경변수: OPENWEBUI_API_KEY)'
    )

    parser.add_argument(
        '--model',
        help='사용할 LLM 모델 (환경변수: OPENWEBUI_MODEL)'
    )

    args = parser.parse_args()

    # 설정 가져오기 (인자 > 환경변수 > 대화형)
    input_file = args.input_file
    api_url = args.url or os.getenv('OPENWEBUI_URL')
    api_key = args.key or os.getenv('OPENWEBUI_API_KEY')
    model = args.model or os.getenv('OPENWEBUI_MODEL')

    # 대화형 입력
    if not input_file:
        while True:
            input_file = input("번역할 릴리즈 노트 파일 경로: ").strip()
            if os.path.exists(input_file):
                break
            print("❌ 파일이 존재하지 않습니다. 다시 입력해주세요.")

    if not os.path.exists(input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {input_file}")
        sys.exit(1)

    if not api_url:
        api_url = input("OpenWebUI 주소 (기본값: http://localhost:3000): ").strip()
        if not api_url:
            api_url = "http://localhost:3000"

    if not api_key:
        api_key = input("API Key: ").strip()
        if not api_key:
            print("❌ API Key는 필수입니다.")
            sys.exit(1)

    if not model:
        model = input("LLM 모델 (예: llama3, gpt-4, qwen2.5): ").strip()
        if not model:
            print("❌ 모델 이름은 필수입니다.")
            sys.exit(1)

    # 설정 확인
    print(f"\n⚙️  설정:")
    print(f"   - 입력 파일: {input_file}")
    print(f"   - API URL: {api_url}")
    print(f"   - Model: {model}")
    print(f"   - API Key: {'*' * 5}{api_key[-4:] if len(api_key) > 4 else '****'}")

    # 번역 실행
    translator = ReleaseNotesTranslator(api_url, api_key, model)
    output_file = translator.translate_release_notes(input_file, args.output)

    print(f"\n📄 번역된 파일: {output_file}")


if __name__ == "__main__":
    main()
