import requests
from core.logger import setup_logger

logger = setup_logger("llm_service")

def send_llm_request(provider: str, api_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Sends a request to an LLM API (OpenWebUI or Ollama).
    
    Args:
        provider (str): The provider type ('openwebui' or 'ollama').
        api_url (str): The base URL of the API (e.g., http://localhost:3000 or http://localhost:11434).
        api_key (str): The API key for authentication (may be empty for Ollama).
        model (str): The model name to use.
        system_prompt (str): The system instruction.
        user_prompt (str): The user input prompt.
        temperature (float): Sampling temperature.

    Returns:
        str: The generated text content.
    """
    if provider == "ollama":
        return _send_ollama_request(api_url, api_key, model, system_prompt, user_prompt, temperature)
    else:  # openwebui or default
        return _send_openwebui_request(api_url, api_key, model, system_prompt, user_prompt, temperature)

def _send_openwebui_request(api_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Sends a request to OpenWebUI (OpenAI-compatible API).
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
        logger.info(f"Sending OpenWebUI request to {target_url} (Model: {model})")
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
        logger.error(f"OpenWebUI request failed: {e}")
        raise e

def _send_ollama_request(api_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Sends a request to Ollama API.
    """
    base_url = api_url.rstrip('/')
    target_url = f"{base_url}/api/generate"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add API key header if provided (Ollama may not always require it)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Combine system and user prompts for Ollama
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    data = {
        "model": model,
        "prompt": combined_prompt,
        "temperature": temperature,
        "stream": False
    }

    try:
        logger.info(f"Sending Ollama request to {target_url} (Model: {model})")
        response = requests.post(target_url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if 'response' in result:
            return result['response'].strip()
        else:
            logger.warning(f"Unexpected Ollama response format: {result}")
            return f"[Error] Unexpected response format"
            
    except Exception as e:
        logger.error(f"Ollama request failed: {e}")
        raise e
