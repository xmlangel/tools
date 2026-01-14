# API 문서

이 문서는 Backend FastAPI의 REST API 엔드포인트를 설명합니다.

## 📋 목차

- [기본 정보](#기본-정보)
- [인증](#인증)
- [사용자 관리](#사용자-관리)
- [YouTube STT](#youtube-stt)
- [파일 관리](#파일-관리)
- [작업 관리](#작업-관리)
- [LLM 설정](#llm-설정)
- [오류 코드](#오류-코드)

---

## 기본 정보

### Base URL

```
http://localhost:8000
```

프로덕션 환경에서는 적절한 도메인으로 변경하세요.

### API 문서

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 응답 형식

모든 API 응답은 JSON 형식입니다:

```json
{
  "success": true,
  "data": { ... },
  "message": "Success"
}
```

오류 응답:

```json
{
  "success": false,
  "error": "Error message",
  "detail": { ... }
}
```

---

## 인증

### JWT 토큰 기반 인증

대부분의 API는 JWT 토큰이 필요합니다.

#### 헤더 형식

```http
Authorization: Bearer <access_token>
```

### POST /api/auth/register

새 사용자 등록

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "홍길동"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "홍길동",
    "created_at": "2026-01-14T12:30:45+09:00"
  }
}
```

### POST /api/auth/login

로그인 및 토큰 발급

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### POST /api/auth/refresh

토큰 갱신

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

## 사용자 관리

### GET /api/users/me

현재 로그인한 사용자 정보 조회

**Headers:**

```http
Authorization: Bearer <access_token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "홍길동",
    "role": "user",
    "created_at": "2026-01-14T12:30:45+09:00",
    "storage_used": 2500000000,
    "storage_limit": 10000000000
  }
}
```

### PUT /api/users/me

사용자 정보 수정

**Request Body:**

```json
{
  "name": "김철수",
  "password": "new_password"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "김철수",
    "updated_at": "2026-01-14T13:00:00+09:00"
  }
}
```

---

## YouTube STT

### POST /api/stt/youtube

YouTube 동영상 STT 작업 생성

**Request Body:**

```json
{
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "model": "base",
  "language": "auto",
  "output_format": "txt",
  "include_timestamps": true
}
```

**Parameters:**

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| url | string | ✅ | - | YouTube URL |
| model | string | ❌ | base | Whisper 모델 (tiny/base/small/medium/large) |
| language | string | ❌ | auto | 언어 코드 또는 auto |
| output_format | string | ❌ | txt | 출력 형식 (txt/srt/vtt/json) |
| include_timestamps | boolean | ❌ | true | 타임스탬프 포함 여부 |

**Response:**

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "pending",
    "created_at": "2026-01-14T12:30:45+09:00",
    "video_info": {
      "title": "Rick Astley - Never Gonna Give You Up",
      "duration": 212,
      "thumbnail": "https://..."
    }
  }
}
```

### GET /api/stt/youtube/{job_id}

STT 작업 상태 조회

**Response:**

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "processing",
    "progress": 65,
    "created_at": "2026-01-14T12:30:45+09:00",
    "started_at": "2026-01-14T12:31:00+09:00",
    "estimated_completion": "2026-01-14T12:35:00+09:00"
  }
}
```

### GET /api/stt/youtube/{job_id}/result

STT 결과 다운로드

**Response (JSON):**

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "video_title": "Rick Astley - Never Gonna Give You Up",
    "detected_language": "en",
    "duration": 212,
    "transcript": "Never gonna give you up...",
    "segments": [
      {
        "start": 0.0,
        "end": 3.5,
        "text": "Never gonna give you up"
      }
    ]
  }
}
```

**Response (TXT):**

```
Content-Type: text/plain

[00:00.000] Never gonna give you up
[00:03.500] Never gonna let you down
...
```

---

## 파일 관리

### POST /api/files/upload

오디오 파일 업로드

**Request:**

```http
POST /api/files/upload
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <binary data>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "file_id": "file_xyz789",
    "filename": "audio.m4a",
    "size": 12500000,
    "mime_type": "audio/mp4",
    "uploaded_at": "2026-01-14T12:30:45+09:00"
  }
}
```

### POST /api/stt/file

업로드된 파일 STT 작업 생성

**Request Body:**

```json
{
  "file_id": "file_xyz789",
  "model": "base",
  "language": "auto",
  "output_format": "txt"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "job_id": "job_def456",
    "status": "pending",
    "file_info": {
      "filename": "audio.m4a",
      "size": 12500000,
      "duration": 1800
    }
  }
}
```

### GET /api/files

내 파일 목록 조회

**Query Parameters:**

- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20)
- `sort`: 정렬 기준 (created_at, size, name)
- `order`: 정렬 순서 (asc, desc)

**Response:**

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "file_id": "file_xyz789",
        "filename": "audio.m4a",
        "size": 12500000,
        "uploaded_at": "2026-01-14T12:30:45+09:00"
      }
    ],
    "total": 42,
    "page": 1,
    "limit": 20,
    "total_pages": 3
  }
}
```

### DELETE /api/files/{file_id}

파일 삭제

**Response:**

```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

---

## 작업 관리

### GET /api/jobs

내 작업 목록 조회

**Query Parameters:**

- `status`: 상태 필터 (pending, processing, completed, failed)
- `type`: 타입 필터 (youtube_stt, file_stt, translation)
- `page`: 페이지 번호
- `limit`: 페이지당 항목 수

**Response:**

```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "job_abc123",
        "type": "youtube_stt",
        "status": "completed",
        "title": "Rick Astley - Never Gonna Give You Up",
        "created_at": "2026-01-14T12:30:45+09:00",
        "completed_at": "2026-01-14T12:36:15+09:00",
        "processing_time": 330
      }
    ],
    "total": 67,
    "page": 1,
    "limit": 20
  }
}
```

### GET /api/jobs/{job_id}

작업 상세 정보

**Response:**

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "type": "youtube_stt",
    "status": "completed",
    "title": "Rick Astley - Never Gonna Give You Up",
    "created_at": "2026-01-14T12:30:45+09:00",
    "started_at": "2026-01-14T12:31:00+09:00",
    "completed_at": "2026-01-14T12:36:15+09:00",
    "processing_time": 315,
    "config": {
      "model": "base",
      "language": "auto",
      "detected_language": "en",
      "output_format": "txt"
    },
    "result": {
      "file_url": "/api/jobs/job_abc123/download",
      "file_size": 12500,
      "duration": 212
    }
  }
}
```

### DELETE /api/jobs/{job_id}

작업 취소 또는 삭제

**Response:**

```json
{
  "success": true,
  "message": "Job canceled successfully"
}
```

### POST /api/jobs/{job_id}/retry

실패한 작업 재시도

**Response:**

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "pending"
  }
}
```

---

## LLM 설정

### GET /api/llm/configs

LLM 설정 목록 조회

**Response:**

```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "id": "config_1",
        "name": "OpenWebUI Default",
        "base_url": "http://openwebui:3000",
        "model": "gpt-3.5-turbo",
        "is_active": true
      }
    ]
  }
}
```

### POST /api/llm/configs

새 LLM 설정 추가

**Request Body:**

```json
{
  "name": "Custom LLM",
  "base_url": "http://custom-llm:8080",
  "model": "custom-model",
  "api_key": "optional_api_key"
}
```

### PUT /api/llm/configs/{config_id}

LLM 설정 수정

### DELETE /api/llm/configs/{config_id}

LLM 설정 삭제

---

## 오류 코드

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 충돌 (예: 중복 이메일) |
| 422 | Unprocessable Entity | 유효성 검증 실패 |
| 429 | Too Many Requests | 요청 제한 초과 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | 서비스 일시 중단 |

### 애플리케이션 오류 코드

```json
{
  "success": false,
  "error": "INVALID_YOUTUBE_URL",
  "message": "The provided URL is not a valid YouTube URL",
  "detail": {
    "url": "invalid-url"
  }
}
```

주요 오류 코드:

| 코드 | 설명 |
|------|------|
| INVALID_YOUTUBE_URL | 잘못된 YouTube URL |
| VIDEO_NOT_FOUND | 동영상을 찾을 수 없음 |
| VIDEO_UNAVAILABLE | 동영상을 사용할 수 없음 (비공개, 삭제 등) |
| FILE_TOO_LARGE | 파일 크기 초과 |
| UNSUPPORTED_FORMAT | 지원하지 않는 파일 형식 |
| STORAGE_LIMIT_EXCEEDED | 저장 공간 초과 |
| JOB_NOT_FOUND | 작업을 찾을 수 없음 |
| JOB_ALREADY_COMPLETED | 이미 완료된 작업 |
| INVALID_TOKEN | 유효하지 않은 토큰 |
| TOKEN_EXPIRED | 만료된 토큰 |
| DUPLICATE_EMAIL | 중복된 이메일 |
| RATE_LIMIT_EXCEEDED | 요청 제한 초과 |

---

## 📚 사용 예제

### Python (requests)

```python
import requests

# 로그인
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={
        "email": "user@example.com",
        "password": "password"
    }
)
token = response.json()["data"]["access_token"]

# YouTube STT 작업 생성
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/stt/youtube",
    headers=headers,
    json={
        "url": "https://youtu.be/dQw4w9WgXcQ",
        "model": "base"
    }
)
job_id = response.json()["data"]["job_id"]

# 작업 상태 확인
response = requests.get(
    f"http://localhost:8000/api/stt/youtube/{job_id}",
    headers=headers
)
print(response.json())
```

### JavaScript (fetch)

```javascript
// 로그인
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const { data: { access_token } } = await loginResponse.json();

// YouTube STT 작업 생성
const sttResponse = await fetch('http://localhost:8000/api/stt/youtube', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    url: 'https://youtu.be/dQw4w9WgXcQ',
    model: 'base'
  })
});
const { data: { job_id } } = await sttResponse.json();

// 작업 상태 확인
const statusResponse = await fetch(
  `http://localhost:8000/api/stt/youtube/${job_id}`,
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);
const status = await statusResponse.json();
console.log(status);
```

### cURL

```bash
# 로그인
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.data.access_token')

# YouTube STT 작업 생성
JOB_ID=$(curl -X POST http://localhost:8000/api/stt/youtube \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"https://youtu.be/dQw4w9WgXcQ","model":"base"}' \
  | jq -r '.data.job_id')

# 작업 상태 확인
curl http://localhost:8000/api/stt/youtube/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 관련 문서

- [설치 가이드](./installation.md)
- [웹 애플리케이션 사용법](./web-application.md)
- [CLI 도구 사용법](./cli-tools.md)
- [개발 가이드](./development.md)
