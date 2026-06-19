from fastapi import APIRouter

# 从app/router/目录下导入所有子路由
from app.routers import test, auth, create, xhs

# 创建一个主路由器 ，专门挂在所有V1版本的API
v1_router = APIRouter(prefix="/v1")  # 在所有这个router中的接口都自动加/v1前缀
v1_router.include_router(test.router)
v1_router.include_router(create.router)
v1_router.include_router(xhs.router)
# 登录路由器
auther_router = APIRouter(tags=["suth"])
auther_router.include_router(auth.router)
