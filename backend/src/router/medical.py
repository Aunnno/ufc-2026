"""
router/medical.py
医疗建议功能路由
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.medical.agent import get_medical_suggestion


medical_router = APIRouter(prefix="/medical")


class MedicalSuggestionRequest(BaseModel):
    """医疗建议请求体"""
    
    symptoms: str = Field(..., description="用户最近的症状")
    diagnosis: str = Field(..., description="医生给予用户的诊断结果")
    online_model: bool = Field(default=True, description="是否使用在线模型")


@medical_router.get("/suggest")
async def get_medical_suggestion_api(
    symptoms: str,
    diagnosis: str,
    online_model: bool = True
):
    """
    根据症状和诊断结果生成个性化的疗养建议
    
    Args:
        symptoms: 用户最近的症状
        diagnosis: 医生给予用户的诊断结果
        online_model: 是否使用在线模型
    
    Returns:
        JSON格式的建议：{"建议事项": [], "不建议事项": []}
    """
    
    try:
        suggestion = await get_medical_suggestion(symptoms, diagnosis, online_model)
        
        if suggestion:
            return JSONResponse(
                content={
                    "success": True,
                    "data": suggestion.model_dump()
                },
                status_code=200,
                media_type="application/json"
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "无法生成医疗建议"
                },
                status_code=500,
                media_type="application/json"
            )
            
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"内部错误: {str(e)}"
            },
            status_code=500,
            media_type="application/json"
        )