# user/typedef.py
# 用户数据模型定义
#

from typing import List
from pydantic import BaseModel, Field


class UserData(BaseModel):
    """
    用户数据结构
    """
    
    id: str = Field(..., description="用户的唯一ID")
    name: str = Field(..., description="用户姓名")
    medicine: List[str] = Field(default_factory=list, description="用户需要服用的药物列表")
    face_data: bytes = Field(default=b"", description="人脸识别二进制数据")


class CreateUserRequest(BaseModel):
    """
    创建用户请求
    """
    
    name: str = Field(..., description="用户姓名")


class CreateUserResponse(BaseModel):
    """
    创建用户响应
    """
    
    user_id: str = Field(..., description="创建的用户ID")


class GetUserResponse(BaseModel):
    """
    获取用户响应
    """
    
    id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户姓名")
    medicine: List[str] = Field(..., description="药物列表")


class UploadFaceResponse(BaseModel):
    """
    上传人脸图片响应
    """
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


class RecognizeFaceResponse(BaseModel):
    """
    识别人脸响应
    """
    
    user_id: str = Field(..., description="识别出的用户ID")
    success: bool = Field(..., description="是否识别成功")