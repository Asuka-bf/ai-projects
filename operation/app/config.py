import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "bf-operation")  # 数据库名称

# 密码中若含 @、# 等需 URL 编码 ---处理数据库连接字符串
_encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = f"mysql://{DB_USER}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# JWT配置
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_SECONDS = 7 * 24 * 60 * 60  # 七天（秒）


# Tortoise ORM 配置，连接数据库
# "connections": 连接数据库字符串
# "apps": 应用配置
# "app.models": 模型文件路径
# "aerich.models": Aerich 模型文件路径，Aerich 会创建和管理自己的迁移表
# "default_connection": 默认连接
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}
