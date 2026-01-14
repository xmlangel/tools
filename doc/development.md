# 개발 가이드

이 문서는 YouTube STT & Translation Tools 프로젝트의 개발 환경 설정 및 개발 컨벤션을 설명합니다.

## 📋 목차

- [개발 환경 설정](#개발-환경-설정)
- [프로젝트 구조](#프로젝트-구조)
- [Git 컨벤션](#git-컨벤션)
- [코드 스타일](#코드-스타일)
- [테스트](#테스트)

---

## 개발 환경 설정

### Backend 개발

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend 개발

```bash
cd frontend
npm install

# 개발 서버 실행
npm run dev
```

---

## 프로젝트 구조

```
tools/
├── backend/              # FastAPI Backend
│   ├── core/            # 핵심 설정
│   ├── routers/         # API 라우터
│   ├── services/        # 비즈니스 로직
│   └── models/          # 데이터 모델
├── frontend/            # React Frontend
│   ├── src/
│   │   ├── components/  # 재사용 컴포넌트
│   │   ├── features/    # 기능별 모듈
│   │   └── pages/       # 페이지
├── doc/                 # 문서
└── docker-compose.yml   # Docker 설정
```

---

## Git 컨벤션

### 커밋 메시지 규칙

**중요:** 모든 커밋 메시지는 **한국어(Hangul)**로 작성해야 합니다.

```
<type>: <subject>

<body>
```

**타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 리팩토링
- `test`: 테스트 추가
- `chore`: 빌드/설정 변경

**예시:**
```
feat: YouTube 동영상 업로드 기능 추가

- 파일 업로드 API 구현
- MinIO 스토리지 연동
- 프론트엔드 업로드 UI 추가
```

---

## 코드 스타일

### Python (Backend)

- PEP 8 준수
- Type hints 사용
- Docstring 작성 (Google style)

### JavaScript (Frontend)

- ESLint 규칙 준수
- Functional components 사용
- Hooks 활용

---

## 테스트

### Backend 테스트

```bash
pytest tests/
```

### Frontend 테스트

```bash
npm run test
```

---

## 📚 관련 문서

- [설치 가이드](./installation.md)
- [API 문서](./api.md)
