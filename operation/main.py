# 启动项目
from importlib import reload
from multiprocessing import allow_connection_pickling
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from app.config import TORTOISE_ORM
from app.routers import v1_router, auther_router
from app.database import register_db
import uvicorn

# 创建FastAPI实例
app = FastAPI()

# 前后端分离
# 配置跨域请求   CORS中间件
app.add_middleware(
    CORSMiddleware,
    # 允许跨域的前端地址
    allow_origins=["*"],
    # 允许携带Cookie
    allow_credentials=True,
    # 允许的请求方法
    allow_methods=["*"],
    # 允许的请求头
    allow_headers=["*"],
)

# 注册路由
app.include_router(v1_router)
# 注册登录路由
app.include_router(auther_router)


# 连接数据库
register_db(app, TORTOISE_ORM, generate_schemas=False)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
