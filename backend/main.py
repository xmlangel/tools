from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from routers import stt, translation, jobs, settings, files

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 구체적인 도메인으로 제한하는 것이 좋습니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 초기화
@app.on_event("startup")
def on_startup():
    init_db()

# 라우터 등록
app.include_router(stt.router, prefix="/api", tags=["stt"])
app.include_router(translation.router, prefix="/api", tags=["translation"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(files.router, prefix="/api", tags=["files"])

@app.get("/")
def read_root():
    return {"message": "YouTube STT & Translation API"}
