# OpenWebUI 번역기 (translate_with_openwebui.py)
텍스트 파일을 읽어 문맥 단위로 나누어 OpenWebUI API로 전송하고, 전체 번역 결과를 저장하는 프로그램을 작성합니다. 긴 텍스트도 누락 없이 모두 번역되도록 청크(Chunk) 단위로 나누어 처리합니다.

## 기능 설명
전체 번역: 긴 텍스트 파일도 문맥 단위(약 2000자)로 나누어 끝까지 번역합니다.
OpenWebUI 연동: 사용자가 입력한 주소와 API 키를 사용하여 번역을 요청합니다.
자동 저장: 원본 파일명 뒤에 _translated.txt를 붙여서 저장합니다.

### 입력값 프로그램이 실행되면 다음 정보를 차례로 물어봅니다:
- 파일 경로: 번역할 텍스트 파일 (예: video_stt.txt)
    - OpenWebUI 주소: (예: http://localhost:3000 또는 외부 주소)
    - API Key: OpenWebUI 설정에서 발급받은 키
    - 모델 이름: 사용할 모델 (예: llama3, mistral 등 OpenWebUI에 등록된 이름)

### .env 파일을 통해 설정을 관리할 수 있습니다.

매번 입력할 필요 없이 파일 경로만 입력하면 됩니다.

#### 사용 방법
    설정 파일 생성 .env 파일을 만들고 아래 내용을 채워주세요.

```
OPENWEBUI_URL=http://localhost:3000
OPENWEBUI_API_KEY=sk-xxxxxxxxxxxx
OPENWEBUI_MODEL=llama3
```

```
python translate_with_openwebui.py
```

물론 .env 파일에 값이 없으면 기존처럼 직접 입력받는 모드로 작동합니다.

### OPENWEB UI 번역시도 다음과 같은 순서로 여러 경로를 자동으로 시도합니다:

```
1. /api/chat/completions (OpenWebUI 표준)
2. /v1/chat/completions (OpenAI 호환)
3. /api/v1/chat/completions
4. /chat/completions
5. /api/chat (구버전)
```

405 Method Not Allowed 오류가 발생하더라도, 올바른 경로를 찾아 자동으로 재시도하게 됩니다. 
