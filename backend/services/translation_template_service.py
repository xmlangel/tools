import json
import os
from core.logger import setup_logger

logger = setup_logger("translation_template_service")

TEMPLATE_FILE = "translation_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": "You are a professional translator. Translate the following text into {target_lang} naturally.",
    "user_prompt_template": """다음 텍스트를 {target_lang}로 번역해줘. 문맥을 고려해서 자연스럽게 번역하고, 번역된 결과만 출력해. 설명이나 잡담은 하지 마.

[텍스트 시작]
{text}
[텍스트 끝]"""
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
