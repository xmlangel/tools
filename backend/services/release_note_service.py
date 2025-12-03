import json
import os
from core.logger import setup_logger
from services.llm_service import send_llm_request

logger = setup_logger("release_note_service")

TEMPLATE_FILE = "release_note_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": "너는 스티브 잡스 같은 통찰력을 가진 'IT 제품 전문 마케터'야. 개발팀이 준 건조한 '기능 업데이트' 내용을, 고객이 듣고 설레할 만한 '고객 혜택 중심'의 릴리즈 노트로 바꿔줘.",
    "user_prompt_template": """
[변환 공식]
1. 기능(Feature): 무엇이 바뀌었나? (사실 위주)
2. 장점(Advantage): 기술적으로 무엇이 더 좋아졌나?
3. 혜택(Benefit): 결국 고객의 삶(돈/시간/감정)이 어떻게 나아졌나? (★이걸 매력적인 헤드라인으로 뽑아줘)

[입력: 개발팀 전달 사항]
{input_text}

[출력 양식]
헤드라인: (Benefit을 강조한 한 줄 카피)
상세 설명: (고객이 얻게 될 변화를 중심으로 2~3문장)
FAB 분석:
- Feature: ...
- Advantage: ...
- Benefit: ...
"""
}

def get_template():
    if os.path.exists(TEMPLATE_FILE):
        try:
            with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
    return DEFAULT_TEMPLATE

def save_template(template_data):
    try:
        with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save template: {e}")
        return False

def convert_release_note(input_text, api_url, api_key, model):
    template = get_template()
    system_prompt = template.get("system_prompt", DEFAULT_TEMPLATE["system_prompt"])
    user_prompt_template = template.get("user_prompt_template", DEFAULT_TEMPLATE["user_prompt_template"])
    
    user_prompt = user_prompt_template.replace("{input_text}", input_text)
    
    try:
        return send_llm_request(api_url, api_key, model, system_prompt, user_prompt, temperature=0.7)
    except Exception as e:
        logger.error(f"Release note conversion failed: {e}")
        raise e
