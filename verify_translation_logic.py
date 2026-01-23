import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mocking some dependencies to test translate_chunk without full backend
from unittest import mock
from unittest.mock import MagicMock

# Mock the database/template service
mock_template = {
    "system_prompt": "You are a professional {source_lang} ({src_lang_code}) to {target_lang} ({tgt_lang_code}) translator. Produce only the {target_lang} translation.",
    "user_prompt_template": "Translate this {source_lang} text to {target_lang}: {text}"
}

with mock.patch('services.translation_template_service.get_template', return_value=mock_template):
    from services.translation_service import translate_chunk
    
    # Test cases: (text, src, target)
    test_cases = [
        ("Hello, how are you?", "auto", "auto"),
        ("안녕하세요, 어떻게 지내세요?", "auto", "auto"),
        ("Hello, how are you?", "en", "auto"),
        ("안녕하세요, 어떻게 지내세요?", "ko", "auto"),
        ("Hello, how are you?", "auto", "ko"),
    ]
    
    print("--- Testing Translation Prompt Logic ---")
    for text, src, target in test_cases:
        print(f"\n[Case] Src: {src}, Target: {target}, Text: {text}")
        
        # We'll mock send_llm_request to just see the prompts
        with mock.patch('services.translation_service.send_llm_request') as mock_llm:
            translate_chunk(text, "mock_provider", "http://mock", "key", "model", target_lang=target, src_lang=src)
            
            # Extract arguments passed to send_llm_request
            args, kwargs = mock_llm.call_args
            system_prompt = args[4]
            user_prompt = args[5]
            
            print(f"System Prompt: {system_prompt}")
            print(f"User Prompt: {user_prompt[:100]}...")
