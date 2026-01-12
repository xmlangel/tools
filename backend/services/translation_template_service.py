import json
import os
from core.logger import setup_logger

logger = setup_logger("translation_template_service")

TEMPLATE_FILE = "translation_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": "You are a professional translator. Translate the input text into {target_lang}. Ensure the output is strictly in {target_lang}. Return ONLY the translated text. Do not include any explanations, introductory text, or closing remarks.",
    "user_prompt_template": """Translate the following text into {target_lang}. Maintain the original tone and context. The output MUST be in {target_lang}. Output ONLY the translation.

[Source Text Start]
{text}
[Source Text End]"""
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
