import json
import os
from core.logger import setup_logger

logger = setup_logger("translation_template_service")

TEMPLATE_FILE = "translation_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": "You are a professional translator. Your task is to translate text into {target_lang}. CRITICAL: All output must be in {target_lang} language only. Do not use any other language in your response. Return ONLY the translated text in {target_lang}. Do not include any explanations, notes, or comments.",
    "user_prompt_template": """Translate the following text into {target_lang}.

IMPORTANT INSTRUCTIONS:
- Output language: {target_lang} ONLY
- Do NOT output in any other language
- Maintain the original meaning and tone
- Preserve paragraph breaks and structure from the original text
- Add a line break after each sentence for better readability
- Return ONLY the translation, nothing else

[Source Text Start]
{text}
[Source Text End]

Provide the translation in {target_lang}:"""
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
