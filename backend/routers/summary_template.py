from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.summary_template_service import get_template, save_template

router = APIRouter()

@router.get("/summary/template")
async def get_current_summary_template():
    return get_template()

class TemplateRequest(BaseModel):
    system_prompt: str
    user_prompt_template: str

@router.post("/summary/template")
async def update_summary_template(request: TemplateRequest):
    success = save_template(request.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    return {"status": "success"}
