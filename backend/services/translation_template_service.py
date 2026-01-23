import json
import os
from core.logger import setup_logger

logger = setup_logger("translation_template_service")

TEMPLATE_FILE = "translation_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": "You are a professional {source_lang} ({src_lang_code}) to {target_lang} ({tgt_lang_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities. Produce only the {target_lang} translation, without any additional explanations or commentary.",
    "user_prompt_template": "Please translate the following {source_lang} text into {target_lang}:\n\n{text}"
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
