import requests

class TranslatorClient:
    """
    OpenWebUI API를 사용하여 텍스트 번역을 수행하는 클래스입니다.
    (OpenAI API와 호환되는 인터페이스를 사용합니다.)
    """
    def __init__(self, url, api_key, model):
        self.url = url
        self.api_key = api_key
        self.model = model

    def translate(self, text):
        """
        주어진 영문 텍스트를 한글로 번역합니다.
        번역 스타일은 기술 문서 매뉴얼 형식(명사형 종결)을 따릅니다.
        """
        if not text or not text.strip():
            return ""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 번역 스타일 및 역할을 정의하는 시스템 프롬프트
        system_prompt = (
            "You are a professional technical translator. "
            "Translate the following English text to Korean in a concise manual style "
            "(using '명사형 종결 어미' like ~사용, ~함, ~기). "
            "Output ONLY the translation, nothing else."
        )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3 # 일관된 번역을 위해 낮은 온도를 사용합니다.
        }
        
        try:
            # API 요청 및 결과 반환
            response = requests.post(f"{self.url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"  [Error] 번역 중 오류 발생: {e}")
            return None
