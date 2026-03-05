from fastapi import APIRouter
from src.router.triager import triager_router
from src.router.voice import voice_router
from src.router.mapping import map_router
from src.router.user import user_router
from src.router.qrcode import qrcode_router
from src.router.medical import medical_router

api_router = APIRouter(prefix="/api")
api_router.include_router(triager_router)
api_router.include_router(voice_router)
api_router.include_router(map_router)
api_router.include_router(user_router)
api_router.include_router(qrcode_router)
api_router.include_router(medical_router)
