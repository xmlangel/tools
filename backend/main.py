from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from core.storage import init_storage
from core.init_default_user import create_default_user
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from routers import files, jobs, stt, translation, settings, release_note, auth, users, llm_configs, summary_template

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("backend")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    # exc.body can be FormData which is not JSON serializable
    body = exc.body
    if hasattr(body, "dict"): # For Pydantic models
        body = body.dict()
    elif hasattr(body, "_list"): # For FormData
        body = dict(body)
    
    # Still, let's be safe and only return errors in content
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# 데이터베이스 및 스토리지 초기화
@app.on_event("startup")
def on_startup():
    init_db()
    init_storage()
    create_default_user()  # 기본 관리자 계정 생성

# Include Routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(stt.router, prefix="/api", tags=["stt"])
app.include_router(translation.router, prefix="/api", tags=["translation"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(release_note.router, prefix="/api/release-note", tags=["release-note"])
app.include_router(llm_configs.router, prefix="/api", tags=["llm-configs"])
app.include_router(summary_template.router, prefix="/api", tags=["summary-template"])

@app.get("/")
def read_root():
    return {"message": "YouTube STT & Translation API"}
