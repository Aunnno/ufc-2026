"""
router/user.py
用户管理功能路由
"""

import uuid
import pickle
import face_recognition
import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from src.user.typedef import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserResponse,
    UploadFaceResponse,
    RecognizeFaceResponse
)
from src.user.database import UserDatabase
from src.config.general import BACKEND_ROOT_DIR


user_router = APIRouter(prefix="/user")

# 初始化数据库
db = UserDatabase(str(BACKEND_ROOT_DIR / "user_data.db"))

# 人脸图片保存路径
FACE_IMAGE_PATH = BACKEND_ROOT_DIR / "assets" / "face.jpg"


@user_router.get("/create")
async def create_user(name: str):
    """
    创建新用户
    
    Args:
        name: 用户姓名
        
    Returns:
        CreateUserResponse: 包含用户ID的响应
    """
    # 生成唯一用户ID
    user_id = str(uuid.uuid4())
    
    # 创建用户
    success = db.create_user(user_id, name)
    
    if not success:
        return JSONResponse(
            content={"success": False, "error": "创建用户失败，用户ID可能已存在"},
            status_code=500
        )
    
    return JSONResponse(
        content={
            "success": True,
            "data": CreateUserResponse(user_id=user_id).model_dump()
        },
        status_code=200
    )


@user_router.get("/get")
async def get_user(id: str):
    """
    获取用户数据
    
    Args:
        id: 用户ID
        
    Returns:
        GetUserResponse: 用户数据
    """
    user_data = db.get_user(id)
    
    if not user_data:
        return JSONResponse(
            content={"success": False, "error": "用户不存在"},
            status_code=404
        )
    
    return JSONResponse(
        content={
            "success": True,
            "data": GetUserResponse(
                id=user_data.id,
                name=user_data.name,
                medicine=user_data.medicine
            ).model_dump()
        },
        status_code=200
    )


@user_router.post("/upload_face_img")
async def upload_face_img(file: UploadFile = File(...)):
    """
    上传人脸图片
    
    Args:
        file: 上传的人脸图片文件
        
    Returns:
        UploadFaceResponse: 上传结果
    """
    try:
        # 确保assets目录存在
        assets_dir = BACKEND_ROOT_DIR / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # 保存图片文件
        with open(FACE_IMAGE_PATH, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return JSONResponse(
            content={
                "success": True,
                "data": UploadFaceResponse(
                    success=True,
                    message="人脸图片上传成功"
                ).model_dump()
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "data": UploadFaceResponse(
                    success=False,
                    message=f"上传失败: {str(e)}"
                ).model_dump()
            },
            status_code=500
        )


@user_router.get("/recognize_face")
async def recognize_face():
    """
    识别人脸
    
    Returns:
        RecognizeFaceResponse: 识别结果
    """
    try:
        # 检查图片文件是否存在
        if not FACE_IMAGE_PATH.exists():
            return JSONResponse(
                content={
                    "success": False,
                    "data": RecognizeFaceResponse(
                        user_id="",
                        success=False
                    ).model_dump()
                },
                status_code=404
            )
        
        # 读取图片
        image = cv2.imread(str(FACE_IMAGE_PATH))
        if image is None:
            return JSONResponse(
                content={
                    "success": False,
                    "data": RecognizeFaceResponse(
                        user_id="",
                        success=False
                    ).model_dump()
                },
                status_code=500
            )
        
        # 转换颜色空间
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 检测人脸
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return JSONResponse(
                content={
                    "success": False,
                    "data": RecognizeFaceResponse(
                        user_id="",
                        success=False
                    ).model_dump()
                },
                status_code=404
            )
        
        # 提取人脸特征
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            return JSONResponse(
                content={
                    "success": False,
                    "data": RecognizeFaceResponse(
                        user_id="",
                        success=False
                    ).model_dump()
                },
                status_code=500
            )
        
        # 获取所有人脸数据
        all_users = db.get_all_users()
        
        # 尝试匹配每个人脸
        for user in all_users:
            if user.face_data:
                try:
                    # 反序列化人脸数据（使用pickle）
                    import pickle
                    stored_encoding = pickle.loads(user.face_data)
                    if stored_encoding is not None:
                        # 比较人脸特征
                        matches = face_recognition.compare_faces(
                            [stored_encoding], 
                            face_encodings[0], 
                            tolerance=0.6
                        )
                        
                        if True in matches:
                            return JSONResponse(
                                content={
                                    "success": True,
                                    "data": RecognizeFaceResponse(
                                        user_id=user.id,
                                        success=True
                                    ).model_dump()
                                },
                                status_code=200
                            )
                except Exception as e:
                    print(f"处理用户 {user.id} 的人脸数据时出错: {e}")
                    continue
        
        # 未找到匹配的用户
        return JSONResponse(
            content={
                "success": False,
                "data": RecognizeFaceResponse(
                    user_id="",
                    success=False
                ).model_dump()
            },
            status_code=404
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "data": RecognizeFaceResponse(
                    user_id="",
                    success=False
                ).model_dump()
            },
            status_code=500
        )


@user_router.post("/register_face")
async def register_face(user_id: str):
    """
    注册人脸数据（将上传的人脸图片与用户关联）
    
    Args:
        user_id: 用户ID
        
    Returns:
        JSONResponse: 注册结果
    """
    try:
        # 检查用户是否存在
        user = db.get_user(user_id)
        if not user:
            return JSONResponse(
                content={"success": False, "error": "用户不存在"},
                status_code=404
            )
        
        # 检查人脸图片是否存在
        if not FACE_IMAGE_PATH.exists():
            return JSONResponse(
                content={"success": False, "error": "请先上传人脸图片"},
                status_code=400
            )
        
        # 读取图片并提取人脸特征
        image = cv2.imread(str(FACE_IMAGE_PATH))
        if image is None:
            return JSONResponse(
                content={"success": False, "error": "无法读取人脸图片"},
                status_code=500
            )
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return JSONResponse(
                content={"success": False, "error": "未检测到人脸"},
                status_code=400
            )
        
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            return JSONResponse(
                content={"success": False, "error": "无法提取人脸特征"},
                status_code=500
            )
        
        # 将人脸特征序列化为字节（使用pickle）
        import pickle
        face_data_bytes = pickle.dumps(face_encodings[0])
        
        # 更新用户的人脸数据
        success = db.update_user_face_data(user_id, face_data_bytes)
        
        if not success:
            return JSONResponse(
                content={"success": False, "error": "更新人脸数据失败"},
                status_code=500
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "人脸注册成功"
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": f"注册失败: {str(e)}"},
            status_code=500
        )


@user_router.post("/update_medicine")
async def update_medicine(user_id: str, medicine: str):
    """
    更新用户药物列表
    
    Args:
        user_id: 用户ID
        medicine: 药物列表字符串，用逗号分隔
        
    Returns:
        JSONResponse: 更新结果
    """
    try:
        # 解析药物列表
        medicine_list = [m.strip() for m in medicine.split(",") if m.strip()]
        
        # 更新药物列表
        success = db.update_user_medicine(user_id, medicine_list)
        
        if not success:
            return JSONResponse(
                content={"success": False, "error": "用户不存在或更新失败"},
                status_code=404
            )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "药物列表更新成功"
            },
            status_code=200
        )
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": f"更新失败: {str(e)}"},
            status_code=500
        )