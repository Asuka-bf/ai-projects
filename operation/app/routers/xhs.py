# 小红书账号管理 API
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from app.models import XhsAccount
from app.routers.auth import get_current_user_id

router = APIRouter(prefix="/xhs", tags=["xhs"])

# 添加小红书账号请求体
class AddAccountBody(BaseModel):
    name: str = ""              # 账号名称
    a1: str                     # cookie a1
    web_session: str            # cookie web_session

# 添加小红书账号
@router.post("/accounts")
async def add_account(body: AddAccountBody, user_id: int = Depends(get_current_user_id)):
    # 验证 a1 和 web_session 不能为空
    if not body.a1.strip() or not body.web_session.strip():
        raise HTTPException(status_code=400, detail="a1 和 web_session 不能为空")
    # 验证 web_session 是否已存在
    exists = await XhsAccount.filter(user_id=user_id, web_session=body.web_session).first()
    if exists:
        raise HTTPException(status_code=409, detail="该 web_session 的账号已存在")
    # 创建账号
    account = await XhsAccount.create(
        user_id=user_id,
        name=body.name or "",
        a1=body.a1.strip(),
        web_session=body.web_session.strip(),
    )
    return {"code": 200, "message": "添加成功", "data": {"id": account.id}}

# 修改小红书账号请求体
class UpdateAccountBody(BaseModel):
    account_id: int             # 必填：要修改的账号 ID
    name: str | None = None
    a1: str | None = None
    web_session: str | None = None

# 修改小红书账号
@router.put("/accounts")
async def update_account(body: UpdateAccountBody, user_id: int = Depends(get_current_user_id)):
    # 验证账号是否存在
    account = await XhsAccount.filter(id=body.account_id, user_id=user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    # 更新账号信息
    update_fields = {}
    if body.name is not None:
        update_fields["name"] = body.name
    if body.a1 is not None:
        update_fields["a1"] = body.a1.strip()
    if body.web_session is not None:
        update_fields["web_session"] = body.web_session.strip()

    # 如果更新字段不为空，则更新账号信息
    if update_fields:
        await account.update_from_dict(update_fields).save()

    return {"code": 200, "message": "修改成功", "data": {"id": account.id}}

# 删除小红书账号
@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int = Path(..., description="账号 ID"),
    user_id: int = Depends(get_current_user_id),
):
    # 验证账号是否存在
    account = await XhsAccount.filter(id=account_id, user_id=user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    # 删除账号
    await account.delete()
    return {"code": 200, "message": "删除成功"}

# 查询当前用户的所有小红书账号
@router.get("/accounts")
async def list_accounts(
    user_id: int = Depends(get_current_user_id)
):
    # 查询账号
    accounts = await XhsAccount.filter(user_id=user_id).order_by("created_at")
    return {
        "code": 200,
        "message": "ok",
        "data": [
            {
                "id": account.id,
                "name": account.name or "",
                "a1": account.a1,
                "web_session": account.web_session,
                "created_at": account.created_at.isoformat()
            }
            for account in accounts
        ]
    }
