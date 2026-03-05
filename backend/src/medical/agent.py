"""
backend/src/medical/agent.py
医疗智能 Agent：根据症状和诊断结果生成个性化疗养建议
提供在线/离线接口
"""

from typing import Optional
from pydantic import BaseModel
from src.llm.online.client import get_online_client
from src.config import general
import json
import asyncio


class MedicalSuggestion(BaseModel):
    """医疗建议数据模型"""
    建议事项: list[str]
    不建议事项: list[str]


def _build_prompt(symptoms: str, diagnosis: str) -> str:
    """构建给 LLM 的详细 prompt，要求生成个性化的疗养建议"""
    prompt = """
你是专业的医疗助手，任务是根据患者的症状和医生的诊断结果，生成个性化的疗养建议。

## 要求：
1. 根据症状和诊断结果，提供具体、可执行的疗养建议
2. 建议要个性化，考虑患者的实际情况
3. 分为"建议事项"和"不建议事项"两部分
4. 每条建议要简洁明了，用中文表述
5. 建议要实用，便于患者执行
6. 避免使用过于专业的医学术语，用通俗易懂的语言

## 输出格式：
请返回严格的 JSON 格式：
{
    "建议事项": ["建议1", "建议2", "建议3", ...],
    "不建议事项": ["不建议1", "不建议2", "不建议3", ...]
}

## 输入信息：
患者症状：{symptoms}
医生诊断：{diagnosis}

请根据以上信息生成个性化的疗养建议。
""".format(symptoms=symptoms, diagnosis=diagnosis)

    return prompt


async def get_medical_suggestion_online(symptoms: str, diagnosis: str) -> Optional[MedicalSuggestion]:
    """使用在线模型获取医疗建议"""
    try:
        client = get_online_client()
        prompt = _build_prompt(symptoms, diagnosis)
        
        response = await client.chat.completions.create(
            model=general.ONLINE_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
        )

        content = response.choices[0].message.content or ""
        
        try:
            parsed = json.loads(content)
            return MedicalSuggestion(**parsed)
        except Exception:
            last_brace = content.rfind("{")
            if last_brace != -1:
                maybe = content[last_brace:]
                try:
                    parsed = json.loads(maybe)
                    return MedicalSuggestion(**parsed)
                except Exception:
                    pass
            return None
            
    except Exception:
        return None


def get_medical_suggestion_offline(symptoms: str, diagnosis: str) -> MedicalSuggestion:
    """离线模式：基于模板返回基本建议"""
    
    建议事项 = [
        "保证充足休息，避免劳累",
        "多喝水，保持身体水分",
        "饮食清淡，避免辛辣刺激食物",
        "按医嘱定时服药",
        "注意观察症状变化，如有加重及时就医"
    ]
    
    不建议事项 = [
        "不要自行停药或更改剂量",
        "避免剧烈运动",
        "不要饮酒或吸烟",
        "避免食用生冷食物",
        "不要随意使用非处方药"
    ]
    
    # 根据症状简单调整建议
    if "发烧" in symptoms or "发热" in symptoms:
        建议事项.append("注意体温变化，适当物理降温")
        不建议事项.append("不要过度捂汗")
    
    if "咳嗽" in symptoms:
        建议事项.append("保持室内空气流通")
        不建议事项.append("避免吸入刺激性气体")
    
    if "腹泻" in symptoms:
        建议事项.append("注意补充电解质")
        不建议事项.append("避免食用油腻食物")
    
    return MedicalSuggestion(
        建议事项=建议事项,
        不建议事项=不建议事项
    )


async def get_medical_suggestion(symptoms: str, diagnosis: str, online_model: bool = True) -> Optional[MedicalSuggestion]:
    """主接口：获取医疗建议"""
    if online_model:
        return await get_medical_suggestion_online(symptoms, diagnosis)
    else:
        return get_medical_suggestion_offline(symptoms, diagnosis)


__all__ = [
    "MedicalSuggestion",
    "get_medical_suggestion",
    "get_medical_suggestion_online",
    "get_medical_suggestion_offline"
]