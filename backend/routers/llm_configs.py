from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, LLMConfig
from typing import List, Optional
import datetime

router = APIRouter()

class LLMConfigBase(BaseModel):
    name: str
    openwebui_url: str
    api_key: str
    model: str
    is_default: bool = False

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    openwebui_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_default: Optional[bool] = None

class LLMConfigResponse(LLMConfigBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

@router.get("/llm-configs", response_model=List[LLMConfigResponse])
def get_llm_configs(db: Session = Depends(get_db)):
    return db.query(LLMConfig).all()

@router.post("/llm-configs", response_model=LLMConfigResponse)
def create_llm_config(config: LLMConfigCreate, db: Session = Depends(get_db)):
    db_config = db.query(LLMConfig).filter(LLMConfig.name == config.name).first()
    if db_config:
        raise HTTPException(status_code=400, detail="Config with this name already exists")
    
    if config.is_default:
        db.query(LLMConfig).filter(LLMConfig.is_default == True).update({LLMConfig.is_default: False})

    new_config = LLMConfig(**config.dict())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config

@router.put("/llm-configs/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(config_id: int, config: LLMConfigUpdate, db: Session = Depends(get_db)):
    db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    update_data = config.dict(exclude_unset=True)

    if update_data.get("is_default"):
        db.query(LLMConfig).filter(LLMConfig.id != config_id).filter(LLMConfig.is_default == True).update({LLMConfig.is_default: False})

    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.delete("/llm-configs/{config_id}")
def delete_llm_config(config_id: int, db: Session = Depends(get_db)):
    db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    db.delete(db_config)
    db.commit()
    return {"status": "success"}
