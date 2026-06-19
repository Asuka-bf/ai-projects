from fastapi import APIRouter
from app.models import Style
from app.routers.auth import get_current_user_id
from fastapi import Depends

router = APIRouter()


# 查询所有图片风格
@router.get("/styles")
async def get_styles(
    user_id: int = Depends(get_current_user_id),
):

    styles = await Style.all()
    return {
        "code": 200,
        "message": "查询成功",
        "data": [
            {
                "id": style.id,
                "name": style.name,
                "fengge": style.fengge,
                "create_time": (
                    style.create_time.isoformat() if style.create_time else None
                ),
            }
            for style in styles
        ],
    }
