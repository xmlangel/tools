from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, Settings
from typing import Optional

router = APIRouter()

class SettingsModel(BaseModel):
    openwebui_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    stt_model: Optional[str] = None

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(Settings).all()
    return {s.key: s.value for s in settings}

@router.post("/settings")
def save_settings(settings: SettingsModel, db: Session = Depends(get_db)):
    data = settings.dict(exclude_unset=True)
    for key, value in data.items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
        else:
            new_setting = Settings(key=key, value=value)
            db.add(new_setting)
    db.commit()
    return {"status": "success"}
