from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.release_note_service import convert_release_note, get_template, save_template

router = APIRouter()

class ConvertRequest(BaseModel):
    input_text: str
    openwebui_url: str
    api_key: str
    model: str

class TemplateRequest(BaseModel):
    system_prompt: str
    user_prompt_template: str

@router.post("/convert")
async def convert(request: ConvertRequest):
    try:
        result = convert_release_note(
            request.input_text,
            request.openwebui_url,
            request.api_key,
            request.model
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/template")
async def get_current_template():
    return get_template()

@router.post("/template")
async def update_template(request: TemplateRequest):
    success = save_template(request.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    return {"status": "success"}
