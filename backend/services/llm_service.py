import requests
from core.logger import setup_logger

logger = setup_logger("llm_service")

def send_llm_request(api_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Sends a request to an OpenWebUI (or OpenAI compatible) API.
    
    Args:
        api_url (str): The base URL of the API (e.g., http://localhost:3000).
        api_key (str): The API key for authentication.
        model (str): The model name to use.
        system_prompt (str): The system instruction.
        user_prompt (str): The user input prompt.
        temperature (float): Sampling temperature.

    Returns:
        str: The generated text content.
    """
    base_url = api_url.rstrip('/')
    target_url = f"{base_url}/api/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }

    try:
        logger.info(f"Sending LLM request to {target_url} (Model: {model})")
        response = requests.post(target_url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        elif 'message' in result:
             return result['message']['content'].strip()
        else:
            logger.warning(f"Unexpected response format: {result}")
            return f"[Error] Unexpected response format"
            
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        raise e
