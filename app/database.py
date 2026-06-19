#注册Tortoise ORM的生命周期
from fastapi import FastAPI
from tortoise import Tortoise

#初始化Tortoise的连接
async def _init_Tortoise(config: dict,create_db:bool = False):
    await Tortoise.init(config=config,_create_db=create_db)

#关闭Tortoise的连接
async def _close_Tortoise():
    await Tortoise.close_connections()



#注册Tortoise连接
#app:fastapi 实例
#tortoise_config:Tortoise 配置
#generate_schemas: 是否生成数据库
def register_db(app:FastAPI,tortoise_config:dict,generate_schemas:bool=False): 
    @app.on_event("startup")
    async def startup_event():
        await _init_Tortoise(tortoise_config,generate_schemas)

    @app.on_event("shutdown")
    async def startup_event():
        await _close_Tortoise()
    

    return app