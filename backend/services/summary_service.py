from core.logger import setup_logger
from services.llm_service import send_llm_request
from services.summary_template_service import get_template, DEFAULT_TEMPLATE
from core.database import SessionLocal, LLMConfig
import json

logger = setup_logger("summary_service")

def generate_summary(text):
    db = SessionLocal()
    try:
        # 1. Get Default LLM Config
        llm_config = db.query(LLMConfig).filter(LLMConfig.is_default == True).first()
        if not llm_config:
            # If no default, try to get any config
            llm_config = db.query(LLMConfig).first()
            
        if not llm_config:
            logger.warning("No LLM configuration found. Skipping summary.")
            return "No LLM configuration available to generate summary."

        # 2. Get Summary Template
        template = get_template()
        system_prompt = template.get("system_prompt", DEFAULT_TEMPLATE["system_prompt"])
        user_prompt_template = template.get("user_prompt_template", DEFAULT_TEMPLATE["user_prompt_template"])
        
        # 3. Prepare Prompt
        # Limit text length if needed to avoid context window issues, 
        # but for now we assume the text fits or the model handles it.
        # Maybe truncate if extremely long, but let's try full text first.
        user_prompt = user_prompt_template.replace("{text}", text)
        
        logger.info(f"Generating summary with model {llm_config.model}...")
        
        # 4. Call LLM
        summary = send_llm_request(
            llm_config.openwebui_url,
            llm_config.api_key,
            llm_config.model,
            system_prompt,
            user_prompt,
            temperature=0.3
        )
        return summary

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return f"Error generating summary: {str(e)}"
    finally:
        db.close()
