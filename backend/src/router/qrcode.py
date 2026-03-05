"""
router/qrcode.py
二维码识别功能 路由
"""

import io
import numpy as np
from typing import Optional

from fastapi import APIRouter, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src import logger

try:
    import cv2
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


qrcode_router = APIRouter(prefix="/qrcode")


class DecodeQRCodeResponse(BaseModel):
    """
    二维码识别响应模型
    """
    success: bool = Field(..., description="识别是否成功")
    data: Optional[str] = Field(None, description="二维码内容，失败时为None")
    error: Optional[str] = Field(None, description="错误信息，成功时为None")


@qrcode_router.post("/")
@qrcode_router.post("")  # 支持无斜杠路径
async def decode_qrcode(file: bytes = File(...)):
    """
    识别二维码图片
    
    Args:
        file: 上传的图片文件字节
        
    Returns:
        JSONResponse: 包含识别结果的响应
    """
    
    if not QRCODE_AVAILABLE:
        logger.error("[QRCode] 二维码识别库未安装")
        return JSONResponse(
            content=DecodeQRCodeResponse(
                success=False,
                data=None,
                error="二维码识别功能不可用，请安装依赖库"
            ).model_dump(),
            status_code=500
        )
    
    try:
        # 记录请求信息
        logger.info(f"[QRCode] 收到二维码识别请求，文件大小: {len(file)} 字节")
        
        # 检查文件大小
        if len(file) == 0:
            logger.error("[QRCode] 上传的文件为空")
            return JSONResponse(
                content=DecodeQRCodeResponse(
                    success=False,
                    data=None,
                    error="上传的文件为空"
                ).model_dump(),
                status_code=400
            )
        
        # 将字节转换为OpenCV图像
        nparr = np.frombuffer(file, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("[QRCode] 无法解码图像文件")
            return JSONResponse(
                content=DecodeQRCodeResponse(
                    success=False,
                    data=None,
                    error="无法解码图像文件，请检查图片格式"
                ).model_dump(),
                status_code=400
            )
        
        # 记录图像信息
        logger.info(f"[QRCode] 图像尺寸: {image.shape}, 类型: {image.dtype}")
        
        # 使用OpenCV的二维码检测器
        qr_detector = cv2.QRCodeDetector()
        
        # 解码二维码
        decoded_text, points, straight_qrcode = qr_detector.detectAndDecode(image)
        
        # 检查解码结果
        if not decoded_text:
            logger.warning("[QRCode] 未检测到二维码或二维码内容为空")
            return JSONResponse(
                content=DecodeQRCodeResponse(
                    success=False,
                    data=None,
                    error="未检测到二维码"
                ).model_dump(),
                status_code=404
            )
        
        # 获取二维码内容
        qr_content = decoded_text
        
        # 记录成功信息
        logger.info(f"[QRCode] 二维码识别成功，内容: {qr_content}")
        if points is not None:
            logger.info(f"[QRCode] 检测到二维码位置点")
        
        # 返回成功响应
        return JSONResponse(
            content=DecodeQRCodeResponse(
                success=True,
                data=qr_content,
                error=None
            ).model_dump(),
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"[QRCode] 二维码识别失败: {e}")
        return JSONResponse(
            content=DecodeQRCodeResponse(
                success=False,
                data=None,
                error=f"二维码识别失败: {str(e)}"
            ).model_dump(),
            status_code=500
        )