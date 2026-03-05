"""
router/navigation.py
导航控制功能路由
包含小车指令执行、位置验证、导航状态查询等功能
"""

import asyncio
import time
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from src.smart_triager.car.typedef import CarAction, CarCommandsOutput
from src.car_control import execute_car_action, execute_car_actions_sequence, CarControlResponse
from src.logger import info, warning, error


# 创建导航路由
navigation_router = APIRouter(prefix="/navigation")


# ========== Pydantic模型定义 ==========

class ExecuteCommandRequest(BaseModel):
    """
    执行单个小车指令的请求体
    """
    action: CarAction = Field(..., description="小车动作指令")
    car_id: str = Field(default="default_car", description="小车标识符")
    command_index: Optional[int] = Field(None, description="命令索引，用于跟踪进度")


class ExecuteCommandsRequest(BaseModel):
    """
    执行多个小车指令的请求体
    """
    actions: List[CarAction] = Field(..., description="小车动作指令列表")
    car_id: str = Field(default="default_car", description="小车标识符")
    start_index: Optional[int] = Field(default=0, description="起始索引，用于断点续传")


class VerifyPositionRequest(BaseModel):
    """
    验证当前位置的请求体
    """
    expected_destination: str = Field(..., description="预期目的地节点ID")
    car_id: str = Field(default="default_car", description="小车标识符")
    image_data: Optional[str] = Field(None, description="Base64编码的图像数据（可选，如果通过JSON上传）")


class VerifyPositionResponse(BaseModel):
    """
    验证当前位置的响应体
    """
    success: bool = Field(..., description="验证是否成功")
    verified: bool = Field(..., description="当前位置是否与预期目的地匹配")
    confidence: float = Field(..., description="验证置信度 (0.0-1.0)")
    detected_text: Optional[str] = Field(None, description="检测到的文本（如果可用）")
    expected_text: Optional[str] = Field(None, description="预期文本（如果可用）")
    message: str = Field(..., description="验证结果消息")


class NavigationStatusResponse(BaseModel):
    """
    导航状态响应体
    """
    car_id: str = Field(..., description="小车标识符")
    is_active: bool = Field(..., description="导航是否正在进行")
    current_command_index: Optional[int] = Field(None, description="当前执行的命令索引")
    total_commands: Optional[int] = Field(None, description="总命令数")
    is_paused: bool = Field(..., description="导航是否暂停")
    verification_pending: bool = Field(..., description="是否有待验证的位置")
    last_verification_result: Optional[VerifyPositionResponse] = Field(None, description="上次验证结果")
    estimated_completion: Optional[float] = Field(None, description="预计完成进度 (0.0-1.0)")


# ========== 全局导航状态（内存存储） ==========

class NavigationState:
    """内存中的导航状态管理器"""
    def __init__(self):
        self.car_states = {}  # car_id -> 状态字典

    def get_state(self, car_id: str = "default_car") -> dict:
        """获取小车导航状态"""
        if car_id not in self.car_states:
            self.car_states[car_id] = {
                "is_active": False,
                "current_command_index": None,
                "total_commands": None,
                "is_paused": False,
                "verification_pending": False,
                "last_verification_result": None,
                "commands": None,
                "start_time": None,
            }
        return self.car_states[car_id]

    def start_navigation(self, commands: List[CarAction], car_id: str = "default_car"):
        """开始导航"""
        state = self.get_state(car_id)
        state.update({
            "is_active": True,
            "current_command_index": 0,
            "total_commands": len(commands),
            "is_paused": False,
            "verification_pending": False,
            "last_verification_result": None,
            "commands": commands,
            "start_time": time.time() if "time" in globals() else None,
        })
        info(f"[Navigation] Navigation started for {car_id}, {len(commands)} commands")

    def update_command_index(self, index: int, car_id: str = "default_car"):
        """更新当前命令索引"""
        state = self.get_state(car_id)
        state["current_command_index"] = index
        if state["total_commands"] and index >= state["total_commands"]:
            state["is_active"] = False
            info(f"[Navigation] Navigation completed for {car_id}")

    def pause_navigation(self, car_id: str = "default_car"):
        """暂停导航"""
        state = self.get_state(car_id)
        state["is_paused"] = True
        info(f"[Navigation] Navigation paused for {car_id}")

    def resume_navigation(self, car_id: str = "default_car"):
        """恢复导航"""
        state = self.get_state(car_id)
        state["is_paused"] = False
        info(f"[Navigation] Navigation resumed for {car_id}")

    def stop_navigation(self, car_id: str = "default_car"):
        """停止导航"""
        state = self.get_state(car_id)
        state.update({
            "is_active": False,
            "current_command_index": None,
            "is_paused": False,
            "verification_pending": False,
            "commands": None,
        })
        info(f"[Navigation] Navigation stopped for {car_id}")


# 全局导航状态实例
navigation_state = NavigationState()


# ========== API端点 ==========

@navigation_router.post("/execute_command/")
async def execute_command(
    request: ExecuteCommandRequest
):
    """
    执行单个小车指令

    请求体包含要执行的CarAction和小车标识符
    返回执行结果
    """
    info(f"[Navigation] Executing command for car {request.car_id}: {request.action}")

    try:
        # 执行小车动作
        success = await execute_car_action(request.action, request.car_id)

        # 更新导航状态（如果正在导航中）
        state = navigation_state.get_state(request.car_id)
        if state["is_active"] and request.command_index is not None:
            navigation_state.update_command_index(request.command_index + 1, request.car_id)

        if success:
            return JSONResponse(
                content={
                    "success": True,
                    "data": CarControlResponse(
                        success=True,
                        message=f"Command executed successfully: {request.action.orientation}, distance={request.action.distance}",
                        action_index=request.command_index,
                        car_id=request.car_id
                    ).model_dump()
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Failed to execute car command"
                },
                status_code=500
            )

    except ValueError as e:
        error(f"[Navigation] Invalid command: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Invalid command: {str(e)}"
            },
            status_code=400
        )
    except Exception as e:
        error(f"[Navigation] Failed to execute command: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/execute_commands/")
async def execute_commands(
    request: ExecuteCommandsRequest
):
    """
    执行多个小车指令

    按顺序执行CarAction列表，支持断点续传（start_index参数）
    """
    info(f"[Navigation] Executing {len(request.actions)} commands for car {request.car_id}, starting from index {request.start_index}")

    try:
        # 验证起始索引
        if request.start_index < 0 or request.start_index >= len(request.actions):
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Invalid start_index: {request.start_index}, must be between 0 and {len(request.actions)-1}"
                },
                status_code=400
            )

        # 只执行从start_index开始的指令
        actions_to_execute = request.actions[request.start_index:]

        # 执行指令序列
        results = await execute_car_actions_sequence(actions_to_execute, request.car_id)

        # 计算成功率
        success_count = sum(1 for r in results if r)
        total_count = len(results)

        # 更新导航状态
        if request.start_index == 0:  # 如果是新的导航任务
            navigation_state.start_navigation(request.actions, request.car_id)
        navigation_state.update_command_index(request.start_index + total_count, request.car_id)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "total_commands": total_count,
                    "successful_commands": success_count,
                    "failed_commands": total_count - success_count,
                    "start_index": request.start_index,
                    "end_index": request.start_index + total_count - 1,
                    "car_id": request.car_id
                }
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to execute commands: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/verify_position/")
async def verify_position(
    request: VerifyPositionRequest = None,
    image_file: Optional[UploadFile] = File(None),
    expected_destination: Optional[str] = Form(None),
    car_id: Optional[str] = Form("default_car")
):
    """
    验证当前位置

    支持两种方式上传图像：
    1. 通过JSON请求体（包含base64编码的图像数据）
    2. 通过multipart/form-data（文件上传）

    返回验证结果，包括是否匹配预期目的地和置信度
    """
    # 处理请求参数
    if request is not None:
        # 来自JSON请求体
        expected_dest = request.expected_destination
        car_id_val = request.car_id
        image_data = request.image_data
        info(f"[Navigation] Verifying position via JSON for car {car_id_val}, expected: {expected_dest}")
    else:
        # 来自form-data
        expected_dest = expected_destination
        car_id_val = car_id
        image_data = None
        info(f"[Navigation] Verifying position via form-data for car {car_id_val}, expected: {expected_dest}")

    if not expected_dest:
        return JSONResponse(
            content={
                "success": False,
                "error": "Missing expected_destination parameter"
            },
            status_code=400
        )

    try:
        # TODO: 实现真实的视觉验证系统
        # 当前为模拟实现，后续需要集成：
        # 1. 图像处理（黑框分割）
        # 2. OCR文本识别
        # 3. 目的地匹配

        info(f"[Navigation] Starting position verification for destination: {expected_dest}")

        # 模拟处理延迟
        await asyncio.sleep(0.2)

        # 模拟验证结果（当前总是成功）
        # 在实际实现中，这里应该调用视觉验证模块
        verified = True
        confidence = 0.95
        detected_text = f"模拟检测文本: {expected_dest}"
        expected_text = f"预期文本: {expected_dest}"

        # 创建验证响应
        verification_result = VerifyPositionResponse(
            success=True,
            verified=verified,
            confidence=confidence,
            detected_text=detected_text,
            expected_text=expected_text,
            message=f"Position verification {'successful' if verified else 'failed'}"
        )

        # 更新导航状态
        state = navigation_state.get_state(car_id_val)
        state["last_verification_result"] = verification_result
        state["verification_pending"] = False

        return JSONResponse(
            content={
                "success": True,
                "data": verification_result.model_dump()
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to verify position: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.get("/status/")
async def get_navigation_status(
    car_id: str = "default_car"
):
    """
    获取导航状态

    返回当前导航的详细信息，包括进度、状态等
    """
    try:
        state = navigation_state.get_state(car_id)

        # 计算预计完成进度
        estimated_completion = None
        if state["is_active"] and state["total_commands"] and state["current_command_index"] is not None:
            if state["total_commands"] > 0:
                estimated_completion = state["current_command_index"] / state["total_commands"]

        # 构建响应
        status_response = NavigationStatusResponse(
            car_id=car_id,
            is_active=state["is_active"],
            current_command_index=state["current_command_index"],
            total_commands=state["total_commands"],
            is_paused=state["is_paused"],
            verification_pending=state["verification_pending"],
            last_verification_result=state["last_verification_result"],
            estimated_completion=estimated_completion
        )

        return JSONResponse(
            content={
                "success": True,
                "data": status_response.model_dump()
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to get navigation status: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/start_navigation/")
async def start_navigation(
    commands: CarCommandsOutput,
    car_id: str = "default_car"
):
    """
    开始新的导航任务

    传入CarCommandsOutput（包含动作序列），开始导航
    """
    try:
        if not commands.actions:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "No commands provided"
                },
                status_code=400
            )

        # 开始导航
        navigation_state.start_navigation(commands.actions, car_id)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "message": f"Navigation started with {len(commands.actions)} commands",
                    "car_id": car_id,
                    "total_commands": len(commands.actions)
                }
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to start navigation: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/pause_navigation/")
async def pause_navigation(
    car_id: str = "default_car"
):
    """
    暂停当前导航
    """
    try:
        navigation_state.pause_navigation(car_id)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "message": "Navigation paused",
                    "car_id": car_id
                }
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to pause navigation: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/resume_navigation/")
async def resume_navigation(
    car_id: str = "default_car"
):
    """
    恢复暂停的导航
    """
    try:
        navigation_state.resume_navigation(car_id)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "message": "Navigation resumed",
                    "car_id": car_id
                }
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to resume navigation: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


@navigation_router.post("/stop_navigation/")
async def stop_navigation(
    car_id: str = "default_car"
):
    """
    停止当前导航
    """
    try:
        navigation_state.stop_navigation(car_id)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "message": "Navigation stopped",
                    "car_id": car_id
                }
            },
            status_code=200
        )

    except Exception as e:
        error(f"[Navigation] Failed to stop navigation: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal error: {str(e)}"
            },
            status_code=500
        )


__all__ = ["navigation_router"]