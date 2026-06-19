import os
import tempfile
import time
import requests
import json as _json
from xhs import XhsClient
from playwright.sync_api import sync_playwright
from xhs.help import sign as _builtin_sign
import re
import logging

logger = logging.getLogger("publish")


# 签名辅助类，专门用来绕过小红书签名风控的“签名生成器”，
# 核心目的是让自动化脚本能成功通过小红书的服务器验证。
# 小红书的接口防爬虫极严，所有请求必须带上 x-s 签名。这个签名是由一段极其复杂的 JavaScript 代码生成的。
class PlaywrightSigner:
    def __init__(self, a1: str, web_session: str):
        self.a1 = a1
        self.web_session = web_session

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(channel="chrome", headless=True)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
        )
        self.context.add_cookies(
            [
                {"name": "a1", "value": a1, "domain": ".xiaohongshu.com", "path": "/"},
                {
                    "name": "web_session",
                    "value": web_session,
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                },
            ]
        )
        self.page = self.context.new_page()
        self.page.goto(
            "https://www.xiaohongshu.com",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        try:
            self.page.wait_for_function(
                "window._webmsxyw != null && typeof window._webmsxyw === 'function'",
                timeout=20000,
            )
        except Exception:
            pass

    def sign(self, uri: str, data=None, a1: str = "", web_session: str = ""):
        """
        生成 x-s 签名。

        策略：
        - permit / upload 相关接口：JS 新版签名 + builtin 兜底（均可接受）
        - note 发布接口（/web_api/sns/v2/note）：必须用 builtin 旧版签名
         原因：_webmsxyw 对 note 返回的是 2025 年新版签名格式（XYW_前缀的 JWT），
            但 /web_api/sns/v2/note 端点只接受旧版签名，JS 签名会返回 406
        """
        # note 发布必须用内置签名
        if "/web_api/sns/v2/note" in uri:
            fallback_data = data if isinstance(data, dict) else None
            try:
                return _builtin_sign(uri, fallback_data, a1=self.a1)
            except Exception:
                return {}

        # 其他接口：JS 签名优先
        if isinstance(data, dict):
            js_data_arg = _json.dumps(data, separators=(",", ":"))
        elif isinstance(data, str):
            js_data_arg = data
        else:
            js_data_arg = '""'

        safe_uri = uri.replace("\\", "\\\\").replace("'", "\\'")

        raw = None
        try:
            raw = self.page.evaluate(
                f"(window._webmsxyw || function(){{}})('{safe_uri}', {js_data_arg})"
            )
        except Exception:
            pass

        if raw and isinstance(raw, dict):
            return {str(k).lower(): str(v) for k, v in raw.items()}

        # JS 失败则用 builtin 兜底
        fallback_data = data if isinstance(data, dict) else None
        try:
            return _builtin_sign(uri, fallback_data, a1=self.a1)
        except Exception:
            return {}

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass
        try:
            self.playwright.stop()
        except Exception:
            pass


# 下载网络图片到系统临时文件
# 小红书的 SDK 发笔记时，只接受本地电脑上的图片路径，不接受网页 URL。所以我们必须先把阿里云上的图下载到本地。
# 增加重试机制：国内网络连海外 OSS 时 SSL 握手偶发超时，重试可解决大部分临时性网络问题。
def download_image_to_temp(url: str, max_retries: int = 3) -> str | None:
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # 下载图片
            resp = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                stream=True,
                timeout=30,  # 从 15 秒增加到 30 秒，给 SSL 握手更多时间
            )
            # 检查响应状态
            resp.raise_for_status()
            # 获取图片的 Content-Type
            content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
            # 根据 Content-Type 获取图片后缀
            ext_map = {
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
                "image/bmp": ".bmp",
            }
            ext = ext_map.get(content_type.lower())
            # 如果 Content-Type 不匹配，则从 URL 路径推断扩展名
            if not ext:
                # 从 URL 路径推断扩展名
                m = re.search(r"\.([a-zA-Z]{3,4})$", url.split("?")[0])
                ext = f".{m.group(1).lower()}" if m else ".jpg"
            # 如果扩展名不匹配，则使用默认扩展名
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
                ext = ".jpg"
            # 创建临时文件
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            # 写入临时文件
            with os.fdopen(fd, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            # 返回临时文件路径
            return temp_path
        except Exception as e:
            last_error = e
            logger.warning(
                f"[download_image] 第 {attempt}/{max_retries} 次下载失败 "
                f"url={url[:80]}... err={type(e).__name__}: {e}"
            )
            if attempt < max_retries:
                time.sleep(1)  # 重试前等待 1 秒

    logger.error(
        f"[download_image] 全部 {max_retries} 次重试均失败 "
        f"url={url[:80]}... 最后错误: {type(last_error).__name__}: {last_error}"
    )
    return None


# 发布笔记
# a1: 小红书用户名唯一标识
# web_session: 小红书用户会话标识
# title: 笔记标题
# content: 笔记内容
# image_urls: 图片URL列表
def publish_xhs_note(
    a1: str,
    web_session: str,
    title: str,
    content: str,
    image_urls,
) -> dict:
    # Playwright 同步 API 必须在没有事件循环的线程中运行
    # 发布动作已通过 loop.run_in_executor 放到子线程，环境是干净的
    # 注意：不要在这里创建 asyncio event loop，否则 Playwright 会检测到并报错

    # 如果 image_urls 是字符串，则转换为列表
    if isinstance(image_urls, str):
        image_urls = [image_urls]
    # 验证图片是否为空
    if not image_urls:
        return {"success": False, "msg": "图片 URL 不能为空"}

    # 启动签名引擎
    try:
        signer = PlaywrightSigner(a1, web_session)
    except Exception as e:
        return {"success": False, "msg": f"签名引擎启动失败: {repr(e)}"}

    # 初始化小红书客户端
    cookie = f"a1={a1}; web_session={web_session};"
    try:
        client = XhsClient(cookie, sign=signer.sign)
    except Exception as e:
        signer.close()
        return {"success": False, "msg": f"客户端初始化失败: {repr(e)}"}

    # 下载图片到临时文件
    temp_paths: list[str] = []
    for url in image_urls:
        path = download_image_to_temp(url)
        if not path:
            # 如果下载失败，则删除临时文件
            for p in temp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
            signer.close()
            return {
                "success": False,
                "msg": f"图片下载失败（已重试3次），可能是网络波动，请稍后重试。图片地址: {url[:80]}...",
            }
        temp_paths.append(path)

    # 发布笔记
    try:
        note_info = client.create_image_note(
            title=title, desc=content, files=temp_paths
        )
        # 从返回结果中提取笔记 ID，构建笔记 URL
        note_id = note_info.get("id", "") or ""
        if note_id:
            note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        return {
            "success": True,
            "msg": "发布成功",
            "note_url": note_url,
            "data": note_info,
        }
    except Exception as e:
        return {"success": False, "msg": f"发布过程报错: {repr(e)}"}
    finally:
        signer.close()
        # 删除临时文件
        for p in temp_paths:
            try:
                os.remove(p)
            except Exception:
                pass


# CLI 入口：通过子进程隔离 Playwright
# 用法: python xhs_publish.py --cli '<json>' --output '<result_file_path>'
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", type=str, default=None, help="JSON publish params (subprocess mode)")
    parser.add_argument("--output", type=str, default=None, help="Output file path for result JSON (subprocess mode)")
    args = parser.parse_args()

    if args.cli and args.output:
        params = json.loads(args.cli)
        result = publish_xhs_note(**params)
        # Write directly to the file specified by parent process — no stdout pollution
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
    elif not args.cli:
        # Direct test — fill in your own credentials below
        res = publish_xhs_note(
            a1="your_a1_cookie_here",
            web_session="your_web_session_here",
            title="test title",
            content="test content",
            image_urls=[
                "https://example.com/image1.jpg",
                "https://example.com/image2.png",
            ],
        )
        print(res)
