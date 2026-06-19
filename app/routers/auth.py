"""登录认证：校验用户名密码，返回 JWT（密码明文比
对，不加密）。"""

import logging
import time
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from tortoise.exceptions import DoesNotExist
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_SECONDS
from app.models import User

# 日志记录器，用于记录错误日志
logger = logging.getLogger(__name__)

# 创建子路由，后驱挂载住路由
router = APIRouter()

# FastAPI的Bearer Token 的认证方案
# atuo_error=False 表示不自动抛出异常，方便后续处理
security = HTTPBearer(auto_error=False)


# 定义登录请求体的结构，必须有userName和password字段
class LoginBody(BaseModel):
    username: str = Field(alias="userName")
    password: str


# 生成Token的函数，传入用户ID，返回JWT字符串
def _make_token(sub: str, exp_seconds: int) -> str:
    # token包含的信息： 用户ID(sub)，签发时间，过期时间(exp)
    payload = {
        "sub": sub,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_seconds,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# 登录接口
@router.post("/login")
async def login(body: LoginBody):
    """校验用户名密码，用户名和密码不能为空"""
    username = (body.username or "").strip()
    if not username:
        return {"code": 400, "message": "请输入用户名", "data": None}
    if not body.password:
        return {"code": 400, "message": "请输入密码", "data": None}
    # 查询用户
    try:
        user = await User.get(username=username)
    except DoesNotExist:
        return {"code": 401, "message": "用户名或密码错误", "data": None}
    # 校验密码 匹配密码
    if user.password != body.password:
        return {"code": 401, "message": "用户名或密码错误", "data": None}

    # 生成Token
    try:
        user_id = str(user.id)
        access_token = _make_token(user_id, JWT_ACCESS_EXPIRE_SECONDS)
        user_name = getattr(user, "name", None) or user.username
        return {
            "code": 200,
            "message": "登录成功",
            "data": {
                "userId": user_id,
                "userName": user_name,
                "accessToken": access_token,
            },
        }
    except Exception as e:
        logger.exception("登录生成token失败: %s", e)
        return {"code": 500, "message": "登录失败", "data": None}


# 鉴权函数  用来解析令牌进行放权
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> int:
    # 如果请求头没有携带令牌的话 ，直接跑出401异常
    if not credentials or credentials.credentials is None:
        raise HTTPException(status_code=401, detail="未登录或token无效")
    # 解析令牌，获取用户ID 如果解析失败，抛出401异常
    try:
        payload = jwt.decode(
            credentials.credentials,  # 令牌
            JWT_SECRET,  # 密钥
            algorithms=[JWT_ALGORITHM],  # 算法
        )
        # 获取用户ID
        sub = payload.get("sub")
        # 如果用户id为空，抛出401异常
        if sub is None:
            raise HTTPException(status_code=401, detail="无效令牌")
        # 返回用户ID
        return int(sub)
    except Exception as e:  # 将报错的信息记录到日志e中，方便排查问题
        logger.exception("解析令牌失败:%s", e)
        raise HTTPException(
            status_code=401, detail="无效令牌或令牌已过期"
        )  # 给前端返回401错误，告诉它token无效
