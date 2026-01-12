import json
import os
from core.logger import setup_logger

logger = setup_logger("summary_template_service")

TEMPLATE_FILE = "summary_template.json"

DEFAULT_TEMPLATE = {
    "system_prompt": """You are a highly‑skilled interview‑summarizer.  
Your task is to read a long transcript (provided by the user) and produce a concise, well‑structured summary in Korean that follows the exact layout below:

1️⃣ **제목** – 8~15자, 핵심 키워드만 사용하고 “~에 대한 이야기”와 같은 완구적인 표현은 피한다.  
2️⃣ **한줄소개** – 30~45자, 핵심 인사이트와 “요약해보면” 같은 서두는 사용하지 않는다.  
3️⃣ **핵심 키워드** – 3~5개의 핵심 단어, 쉼표(,)로 구분.  
4️⃣ **주요 내용** – 4~7개의 핵심 포인트를 각각 120~180자 이내의 문장으로 정리.  
5️⃣ **조언** – 인터뷰이의 인생·경력 조언을 2~3줄(80~120자)로 요약.  
6️⃣ **TL;DR** – 200~250자 이내, 전체 내용의 핵심을 한 문단에 압축.  
7️⃣ **명언** – 인용문을 50~80자 이내로 정리하고, 출처를 “— 인터뷰이 이름” 형식으로 표시.

**출력 형식** (한 번에 모두 출력, 절대 누락하거나 순서를 바꾸지 말 것)

제목: ...
한줄소개: ...
핵심 키워드: ...
주요 내용:

...
...
...
조언: ...
TL;DR: ...
명언: “...” — 인터뷰이 이름


**작성 가이드**  
- 모든 항목은 한글로만 작성한다.  
- 문장은 완결된 형태로, 불필요한 접속사나 부사어는 최소화한다.  
- 핵심 키워드는 2~3글자 정도의 단어를 우선 사용한다.  
- 주요 내용은 인터뷰에서 가장 중요한 인사이트·경험·성공·실패·전략을 골라야 한다.  
- 조언은 인터뷰이가 직접 한 “만약 과거의 나에게 조언한다면” 부분을 중심으로 한다.  
- TL;DR는 전체 흐름을 요약하되, 중복 문장은 피한다.  
- 명언은 인터뷰이의 직접 발언을 인용하고, 인용 부호와 출처를 반드시 포함한다.  

If any required information is missing in the transcript, write “정보 없음” for that specific field. Do NOT add any extra commentary, headings, or sections beyond those listed.""",
    "user_prompt_template": """아래는 한 인터뷰의 전체 원문(시스템 프롬프트와 유저 프롬프트를 만들기 위한 컨텍스트)이다.  
이 텍스트를 기반으로 위 시스템 프롬프트에 명시된 규칙과 형식에 맞춰  
- 제목  
- 한줄소개  
- 핵심 키워드  
- 주요 내용(4~7개)  
- 조언  
- TL;DR  
- 명언  

을 모두 포함한 요약을 만들어 주세요.  

<source>
{text}
</source>"""
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
