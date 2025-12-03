from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from routers import files, jobs, stt, translation, settings, release_note, auth, users

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 초기화
@app.on_event("startup")
def on_startup():
    init_db()

# Include Routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(stt.router, prefix="/api", tags=["stt"])
app.include_router(translation.router, prefix="/api", tags=["translation"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(release_note.router, prefix="/api/release-note", tags=["release-note"])

@app.get("/")
def read_root():
    return {"message": "YouTube STT & Translation API"}
