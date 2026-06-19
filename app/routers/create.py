# 生成运营内容所用的API
import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from fastapi import APIRouter, Body, Depends, File, Path as PathParam, Query
from pydantic import BaseModel
from app.agent.coze_agent import search_hot_topics, concent_creation
from app.models import Section, Title, Style, TitleImage, PublishRecord, PublishImage, XhsAccount
from app.routers.auth import get_current_user_id
from datetime import datetime
from app.agent.Qwen_agent import generate_cover_prompt, generate_image
from app.until.upload import upload_image_from_url, upload_local_image
from fastapi import UploadFile
import logging
import subprocess
import functools
import sys

# 创建路由实例
router = APIRouter(prefix="/create", tags=["create"])


# 定义请求体的模型(根据主题生成相应的题目)
class CreateByThemeBody(BaseModel):
    theme: str  # 主题


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


# 根据主题调用agent生成题目
@router.post("/start")
async def create_by_theme(
    body: CreateByThemeBody, user_id: int = Depends(get_current_user_id)
):
    # 验证输入主题是否为空
    theme = (body.theme or "").strip()
    if not theme:
        return {"code": 400, "message": "请输入主题", "data": None}

    # 调用Coze生成模块与标题
    try:
        raw = search_hot_topics(theme)
    except Exception as e:
        return {"code": 500, "message": f"agent调用失败: {e}", "data": None}
    # 解析COze返回的JSON

    try:
        data = _extract_json(raw)
    except Exception as e:
        return {"code": 500, "message": f"解析JSON失败:{e}", "data": None}
    # 验证返回格式是否正确
    if not isinstance(data, dict):
        return {"code": 500, "message": "agent返回格式异常", "data": None}

    # 存储板块数据
    sections_out = []
    # 遍历返回的板块与标题
    for section_name, title_list in data.items():
        # 验证板块名称和标题列表是否为空
        if not section_name or not isinstance(title_list, list):
            continue

        # 讲板块数据写入数据库中
        section = await Section.create(
            user_id=user_id,
            source_name=theme if theme else None,
            name=section_name,
            created_at=datetime.now(),
        )

        # 存储标题数据
        title_out = []
        # 遍历标题数据 遍历标题列表和排序序号
        for sort_order, title_text in enumerate(title_list, start=1):
            # 验证标题是否为字符串
            if not isinstance(title_text, str):
                title_text = str(title_text)
            # 将标题数据写入数据库中
            title_row = await Title.create(
                section_id=section.id,
                title=title_text,
                sort_order=sort_order,
                created_at=datetime.now(),
            )
            # 存储标题数据
            title_out.append(
                {
                    "id": title_row.id,
                    "title": title_row.title,
                    "content": title_row.content,
                    "status": title_row.status,
                    "sort_order": title_row.sort_order,
                    "created_at": title_row.created_at,
                }
            )
        # 存储板块数据
        sections_out.append(
            {
                "id": section.id,
                "name": section.name,
                "created_at": section.created_at,
                "titles": title_out,
            }
        )
    # 返回结果
    return {"code": 200, "message": "创建成功", "data": {"sections": sections_out}}


# 检索当前用户已有的主题列表，可选择关键词进行过滤---对应主页的下面的功能模块
@router.get("/themes")
async def list_themes(
    keyword: str | None = Query(None), user_id: int = Depends(get_current_user_id)
):

    # 从数据库查找该用户的所有生成过的主题
    sections = await Section.filter(user_id=user_id).values_list(
        "source_name", flat=True
    )

    # 去重操作 得到主题数据
    themes = list(set(s for s in sections if s))

    # 如果有关键词，就进行过滤
    if keyword:
        kw = (keyword or "").lower()
        themes = [t for t in themes if kw in t.lower()]

        # 对主题列表进行一个排序
    themes.sort()
    # 返回结果
    return {"code": 200, "message": "查询成功", "data": {"themes": themes}}


# 根据主题名加载用户已经生成的标题 ，返回格式与/strat一致，便于前端复用
@router.get("/load")
async def load_by_theme(
    theme: str = Query(...), user_id: int = Depends(get_current_user_id)  # 必填
):

    # 验证主题是否为空
    if not theme:
        return {"code": 400, "message": "请输入主题 主题不能为空", "data": None}

    # 根据用户 + 主题查询板块
    sections = await Section.filter(user_id=user_id, source_name=theme).order_by("id")

    # 提取板块的ID列表
    section_ids = [section.id for section in sections]

    # 根据板块ID列表查询对应的标题数据
    titles_map = await Title.filter(section_id__in=section_ids).order_by(
        "section_id", "sort_order"
    )

    # 封装成一个新列表
    # 创建一个字典, key是板块ID，value是该板块下的标题列表
    titles_by_sec = {}
    # 遍历标题列表，把标题按照板块ID分类存储到字典中
    for title in titles_map:
        titles_by_sec.setdefault(title.section_id, []).append(title)

    # 创建一个新列表，用于存储板块数据
    sections_out = []

    # 遍历板块列表，将板块数据封装成一个列表
    for section in sections:
        titles_out = [
            {
                "id": title.id,
                "title": title.title,
                "content": title.content,
                "status": title.status,
                "sort_order": title.sort_order,
                "created_at": title.created_at,
            }
            for title in titles_by_sec.get(section.id, [])  # 获取该板块下的所有标题
        ]
        sections_out.append(
            {
                "id": section.id,
                "name": section.name,
                "created_at": section.created_at,
                "titles": titles_out,
            }
        )
    # 返回列表数据
    return {
        "code": 200,
        "message": "查询成功",
        "data": {"sections": sections_out},
    }


# 请求体，根据标题生成内容
class CreateCopyBody(BaseModel):
    title_text: str  # 标题
    title_id: int | None = None  # 标题ID


# 根据标题调用agent生成文案，返回生成的文案
@router.post("/copy")
async def create_copy(
    body: CreateCopyBody, user_id: int = Depends(get_current_user_id)
):

    # 验证标题文本是否为空
    title_text = (body.title_text or "").strip()
    if not title_text:
        return {"code": 400, "message": "请输入标题文本,传入标题", "data": None}
    # 调用智能体COZE生成文案
    try:
        content = concent_creation(title_text)
    except Exception as e:
        return {"code": 500, "message": f"agent调用失败: {e}", "data": None}
    # 如果传入了标题ID，就把文案写入到该标题的content字段中，并将状态更新为1(已完成)
    if body.title_id:
        title = await Title.get(id=body.title_id).first()
        if title:
            title.content = content if content else None
            title.status = "1"
            await title.save()

    # 返回结果

    return {"code": 200, "message": "创建成功", "data": {"content": content}}


#########重置文案的功能模块############


# 查询数据库中的标题详情
@router.get("/title/{title_id}")
async def get_title_detail(
    title_id: int = PathParam(..., description="标题ID"),
    user_id: int = Depends(get_current_user_id),
):

    # 根据标题ID查询标题
    title = await Title.get(id=title_id).first()
    # 验证标题是否存在，且属于当前用户 如果标题不存在返回错误信息
    if not title:
        return {"code": 404, "message": "标题不存在", "data": None}

    # 根据标题ID查询对应的板块数据
    section = await Section.get(id=title.section_id).first()
    # 如果标题不存在。返回错误信息
    if not section:
        return {"code": 404, "message": "标题对应的板块不存在", "data": None}

    # 返回标题的信息
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "id": title.id,
            "title": title.title,
            "content": title.content,
            "status": title.status,
            "view_count": title.view_count,
            "like_count": title.like_count,
        },
    }


# 请求体 用于保存文案
class SaveCopyBody(BaseModel):
    content: str = ""  # 文案内容


# 保存文案,用于文案编导步骤，编辑文案后保存到数据库
@router.post("/save-copy")
async def save_copy(
    title_id: int = Query(..., description="标题ID"),
    body: SaveCopyBody = Body(...),
    user_id: int = Depends(get_current_user_id),
):

    # 根据标题ID查询标题
    title = await Title.get(id=title_id).first()
    # 验证标题是否存在，且属于当前用户 如果标题不存在或是不属于当前用户,返回错误信息
    if not title:
        return {"code": 403, "message": "标题无权访问", "data": None}

    # 更新标题的文案 也就是content字段
    title.content = body.content if body.content else None
    await title.save(update_fields=["content"])

    # 返回结果
    return {"code": 200, "message": "保存成功", "data": {"id": title.id}}


# 获取风格列表
@router.get("/styles")
async def get_style_list(user_id: int = Depends(get_current_user_id)):
    # 从数据库中所有风格
    styles = await Style.all().order_by("id")
    list_out = [
        {
            "id": style.id,
            "name": style.name or "",
            "fengge": style.fengge or "",
            "create_time": (
                style.create_time.strftime("%Y-%m-%d %H:%M:%S")
                if style.create_time
                else None
            ),
        }
        for style in styles
    ]
    # 返回风格列表
    return {"code": 200, "message": "成功", "data": {"styles": list_out}}


# 生成封面请求体
class GenerateCoverBody(BaseModel):
    title_id: int
    prompt: str


# 生成封面图
# 调用AI agent 生成封面图,将图片上传到阿里云的OSS,将封面图数据写入数据库
@router.post("/cover")
async def generate_cover(
    body: GenerateCoverBody, user_id: int = Depends(get_current_user_id)
):
    # 获取标题ID和风格提示词
    title_id = body.title_id
    prompt = (body.prompt or "").strip()

    # 验证风格提示词是否为空
    if not prompt:
        return {"code": 400, "message": "请传入风格提示词", "data": None}

    # 验证标题是否真实存在
    title = await Title.get(id=title_id).first()
    if not title:
        return {"code": 404, "message": "标题不存在", "data": None}

    # 验证标题所属板块是否属于当前的用户
    section = await Section.get(id=title.section_id).first()
    if not section or section.user_id != user_id:
        return {"code": 403, "message": "无权操作该标题", "data": None}

    # 调用qwen_agent生成的封面图
    try:
        # 构建提示词
        prompt = generate_cover_prompt(
            title=title.title, style_description=prompt, include_text=True
        )
        # 生成图片
        image_url = generate_image(prompt=prompt)
    except Exception as e:
        return {"code": 500, "message": f"生成封面图失败: {e}", "data": None}

    if not image_url:
        return {
            "code": 500,
            "message": f"图片生成未返回结果(image_url={repr(image_url)})",
            "data": None,
        }

    # 上传图片到OSS（用线程池避免阻塞事件循环）
    try:
        loop = asyncio.get_running_loop()
        upload_result = await loop.run_in_executor(
            None, upload_image_from_url, image_url
        )
        oss_url = upload_result["url"]
    except Exception as e:
        return {"code": 500, "message": f"上传封面图失败: {e}", "data": None}

    # 将封面图数据写入数据库
    # 查询该标题是否有封面图
    title_image = await TitleImage.create(
        user_id=user_id,
        title_id=title_id,
        image_url=oss_url,
        image_type=1,  # 封面图
        created_at=datetime.now(),
    )

    # 返回结果
    return {
        "code": 200,
        "message": "封面生成成功",
        "data": {
            "image_url": oss_url,
            "image_id": title_image.id,
        },
    }


# 上传封面图功能
# 接受前端上传的图片文件，上传到阿里云OSS，并将封面数据写入数据库
@router.post("/cover/upload")
async def upload_cover_image(
    file: UploadFile = File(...),
    title_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
):
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"code": 400, "message": "请上传图片文件", "data": None}

    # 获取文件后缀
    suffix = Path(file.filename).suffix

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        # 获取临时文件路径
        tmp_path = tmp.name

        # 读取文件内容并写入临时文件
        content = await file.read()
        tmp.write(content)

    # 上传到阿里云的OSS仓库（用线程池避免阻塞事件循环导致MySQL断连）
    try:
        loop = asyncio.get_running_loop()
        upload_result = await loop.run_in_executor(None, upload_local_image, tmp_path)
        oss_url = upload_result["url"]
    finally:
        # 删除临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # 查询该标题是否已有封面图
    existing = await TitleImage.filter(
        title_id=title_id,
        image_type=1,  # 封面图
    ).first()

    if existing:
        # 已有封面图的情况，进行修改
        existing.image_url = oss_url
        await existing.save()
        image_id = existing.id
    else:
        # 没有封面图的情况，进行新增
        created = await TitleImage.create(
            user_id=user_id,
            title_id=title_id,
            image_url=oss_url,
            image_type=1,  # 封面图
            sort_order=0,
        )
        image_id = created.id

    # 返回结果
    return {
        "code": 200,
        "message": "上传成功",
        "data": {
            "image_url": oss_url,
            "image_id": image_id,
        },
    }


# 上传正文图功能
# 接受前端上传的正文图片文件，上传到阿里云OSS，并将正文面数据写入数据库
@router.post("/image/upload")
async def upload_content_image(
    file: UploadFile = File(...),
    title_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
):
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        return {"code": 400, "message": "请上传图片文件", "data": None}

    # 获取文件后缀
    suffix = Path(file.filename).suffix

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        # 获取临时文件路径
        tmp_path = tmp.name

        # 读取文件内容并写入临时文件
        content = await file.read()
        tmp.write(content)

    # 上传到阿里云的OSS仓库（用线程池避免阻塞事件循环导致MySQL断连）
    try:
        loop = asyncio.get_running_loop()
        upload_result = await loop.run_in_executor(None, upload_local_image, tmp_path)
        oss_url = upload_result["url"]
    finally:
        # 删除临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    # 将正文图片数据保存到数据库
    # 查询该标题是否已有封面图
    # 查询该标题是否已有该位置的正文图（按 sort_order 递增）
    max_order_row = (
        await TitleImage.filter(
            title_id=title_id,
            image_type=0,  # 正文图
        )
        .order_by("-sort_order")
        .first()
    )
    next_order = (max_order_row.sort_order + 1) if max_order_row else 1

    # 新增正文图记录
    created = await TitleImage.create(
        user_id=user_id,
        title_id=title_id,
        image_url=oss_url,
        image_type=0,  # 正文图
        sort_order=next_order,
        created_at=datetime.now(),
    )

    # 返回结果
    return {
        "code": 200,
        "message": "上传成功",
        "data": {
            "image_url": oss_url,
            "image_id": created.id,
        },
    }


# 获取标题正文图列表
@router.get("/images/{title_id}")
async def get_title_images(
    title_id: int = PathParam(..., description="标题ID"),
    user_id: int = Depends(get_current_user_id),
):

    images = await TitleImage.filter(
        title_id=title_id, image_type=0  # 正文图
    ).order_by("sort_order")
    return {
        "code": 200,
        "message": "成功",
        "data": {
            "images": [
                {
                    "id": image.id,
                    "image_url": image.image_url,
                    "sort_order": image.sort_order,
                }
                for image in images
            ]
        },
    }

    # 删除正文图


@router.delete("/image/{image_id}")
async def delete_content_image(
    image_id: int = PathParam(..., description="图片 ID"),
    user_id: int = Depends(get_current_user_id),
):
    image_row = await TitleImage.filter(
        id=image_id, user_id=user_id, image_type=0
    ).first()
    if not image_row:
        return {"code": 404, "message": "图片不存在或无权限", "data": None}
    await image_row.delete()
    return {"code": 200, "message": "删除成功", "data": None}


# 请求体，修改标题与文案
class UpdateTitleBody(BaseModel):
    title: str = ""
    content: str = ""

# 发布前最后一次修改标题和文案
@router.put("/title/{title_id}")
async def update_title(
    title_id: int = PathParam(..., description="标题ID"),
    body: UpdateTitleBody = Body(...),
    user_id: int = Depends(get_current_user_id)
):
    # 根据标题ID查询标题
    title = await Title.get(id=title_id).first()

    # 如果标题不存在，返回错误信息
    if not title:
        return {"code": 404, "message": "标题不存在", "data": None}

    # 验证标题所属板块是否属于当前用户
    section = await Section.get(id=title.section_id).first()
    if not section or section.user_id != user_id:
        return {"code": 403, "message": "无权操作该标题", "data": None}

    # 更新标题和文案
    title.title = (body.title or "").strip() or title.title
    title.content = (body.content or "").strip() or title.content

    # 保存更新
    await title.save()

    return {"code": 200, "message": "成功", "data": {"id": title_id}}


# ========== 小红书发布相关 ==========

# 发布请求体
class PublishXhsBody(BaseModel):
    title_id: int              # 标题 ID
    account_ids: list[int]     # 选中的小红书账号 ID 列表


logger = logging.getLogger("publish")


# 脚本路径（绝对路径，避免工作目录不同导致找不到文件）
_SCRIPT_DIR = Path(__file__).resolve().parent
_XHS_PUBLISH_SCRIPT = str(_SCRIPT_DIR.parent / "until" / "xhs_publish.py")


def _cleanup_result_file(path: str):
    """删除子进程结果临时文件"""
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


# 发布笔记到小红书
# 使用子进程隔离 Playwright：sync_playwright 底层依赖 greenlet，
# 在 Windows 子线程中会触发 NotImplementedError，因此用独立进程彻底隔离。
# 子进程本质就是 "uv run python xhs_publish.py --cli" — 跟之前直连测试一模一样。
@router.post("/publish")
async def publish_title(
    body: PublishXhsBody,
    user_id: int = Depends(get_current_user_id),
):
    # 验证账号列表不能为空
    if not body.account_ids:
        return {"code": 400, "message": "请选择至少一个发布账号", "data": None}

    # 验证标题是否存在
    title_row = await Title.filter(id=body.title_id).first()
    if not title_row:
        return {"code": 404, "message": "标题不存在", "data": None}

    # 验证标题所属板块属于当前用户
    section = await Section.filter(id=title_row.section_id).first()
    if not section or section.user_id != user_id:
        return {"code": 403, "message": "无权限发布该标题", "data": None}

    # 获取标题对应的所有图片（正文图 + 封面图）
    title_images = await TitleImage.filter(title_id=body.title_id).order_by("sort_order")
    if not title_images:
        return {"code": 400, "message": "该标题下没有图片，请先上传图片", "data": None}

    # 构建图片 URL 列表
    image_urls = [img.image_url for img in title_images]
    note_title = title_row.title or ""
    note_content = title_row.content or ""

    results = []

    for account_id in body.account_ids:
        # 查询小红书账号
        account_row = await XhsAccount.filter(id=account_id, user_id=user_id).first()
        if not account_row:
            results.append({
                "account_id": account_id,
                "account_name": "",
                "success": False,
                "msg": "账号不存在或无权限",
            })
            continue

        # 构建子进程参数
        publish_params = {
            "a1": account_row.a1,
            "web_session": account_row.web_session,
            "title": note_title,
            "content": note_content,
            "image_urls": image_urls,
        }

        # 子进程 = 直连方式：python xhs_publish.py --cli '<json>' --output '<result_file>'
        # subprocess.run 只是启动进程等结果，不涉及 Playwright/greenlet
        # 结果写入临时文件，stdout 被忽略，彻底避免 Playwright 日志污染
        fd, result_path = tempfile.mkstemp(suffix=".json", prefix="xhs_result_")
        os.close(fd)  # 让子进程打开写入

        sync_func = functools.partial(
            subprocess.run,
            [
                sys.executable, _XHS_PUBLISH_SCRIPT,
                "--cli", json.dumps(publish_params, ensure_ascii=False),
                "--output", result_path,
            ],
            capture_output=True,
            timeout=300,
        )
        try:
            loop = asyncio.get_running_loop()
            proc_result = await loop.run_in_executor(None, sync_func)
        except subprocess.TimeoutExpired:
            logger.error(f"[publish] 子进程超时 (5min) account={account_id}")
            _cleanup_result_file(result_path)
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": False,
                "msg": "发布超时（超过5分钟），请检查网络后重试",
            })
            continue
        except Exception as e:
            logger.error(f"[publish] 子进程启动失败 account={account_id}: {e}")
            _cleanup_result_file(result_path)
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": False,
                "msg": f"子进程启动失败: {e}",
            })
            continue

        # 解析子进程输出：忽略 stdout（可能被 Playwright 污染），直接读结果文件
        err_msg = proc_result.stderr.decode("utf-8", errors="replace")[:500] if proc_result.stderr else ""

        if proc_result.returncode != 0:
            logger.error(
                f"[publish] 子进程异常退出 account={account_id} "
                f"code={proc_result.returncode} stderr={err_msg}"
            )
            _cleanup_result_file(result_path)
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": False,
                "msg": f"子进程异常 (exit={proc_result.returncode}): {err_msg}",
            })
            continue

        # 从 API 指定的输出文件读取结果
        publish_result = None
        try:
            if os.path.isfile(result_path):
                with open(result_path, "r", encoding="utf-8") as f:
                    publish_result = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"[publish] 读取结果文件失败 account={account_id}: {e}")
        finally:
            _cleanup_result_file(result_path)

        if publish_result is None:
            logger.error(
                f"[publish] 子进程无有效结果 account={account_id} "
                f"stderr={err_msg[:200]}"
            )
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": False,
                "msg": f"子进程未返回有效结果: {err_msg[:200] or '结果文件为空或不存在'}",
            })
            continue

        logger.info(f"[publish] account={account_id} result={publish_result}")

        if publish_result.get("success"):
            # 创建发布成功记录
            record = await PublishRecord.create(
                user_id=user_id,
                title_id=body.title_id,
                xhs_id=account_id,
                note_url=publish_result.get("note_url", ""),
                platform=1,          # 小红书
                publish_status=2,    # 发布成功
                publish_time=datetime.now(),
                content=note_content,
            )
            # 创建发布图片关联记录
            for img in title_images:
                await PublishImage.create(
                    publish_id=record.id,
                    image_id=img.id,
                    image_type=1 if img.image_type == 1 else (3 if img.image_type == 0 else 1),
                    sort_order=img.sort_order,
                )
            # 更新标题状态为已发布
            title_row.status = "2"
            await title_row.save()
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": True,
                "msg": "发布成功",
                "publish_id": record.id,
                "note_url": publish_result.get("note_url", ""),
            })
        else:
            # 创建发布失败记录
            await PublishRecord.create(
                user_id=user_id,
                title_id=body.title_id,
                xhs_id=account_id,
                platform=1,
                publish_status=3,    # 发布失败
                content=note_content,
            )
            results.append({
                "account_id": account_id,
                "account_name": account_row.name,
                "success": False,
                "msg": publish_result.get("msg", "发布失败"),
            })

    # 统计成功/失败数量
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count
    message = f"发布完成：成功 {success_count} 个，失败 {fail_count} 个"

    return {"code": 200, "message": message, "data": {"results": results}}
