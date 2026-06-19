import os
import alibabacloud_oss_v2 as oss
from dotenv import load_dotenv
import uuid
import requests
from urllib.parse import urlparse
import io

# 读取环境变量
load_dotenv()
access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
region = os.getenv("OSS_REGION")
bucket = os.getenv("OSS_BUCKET")
endpoint = os.getenv("OSS_ENDPOINT")

# 初始化阿里云OSS客户端
cfg = oss.config.load_default()
cfg.region = region
cfg.credentials_provider = oss.credentials.StaticCredentialsProvider(
    access_key_id=access_key_id, access_key_secret=access_key_secret
)
client = oss.Client(cfg)


# 上传本地图片


# local_path:本地图片文件的路径
def upload_local_image(local_path: str) -> str:
    # 检查本地文件是否存在
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"本地文件不存在: {local_path}")

    # 自动设置图片类型
    # 获取文件拓展名
    ext = os.path.splitext(local_path)[1].lower()

    # 根据文件拓展名设置Content-Type
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }

    content_type = content_type_map.get(ext, "image/jpeg")

    try:
        # 设置文件的上传路径 #文件名
        original_name = os.path.basename(local_path)

        # 原始后缀
        ext = os.path.splitext(original_name)[1].lower()
        # 随机码 八位
        random_code = uuid.uuid4().hex[:8]
        oss_key = f"images/{os.path.splitext(original_name)[0]}_{random_code}{ext}"

        # 创建一个上传请求体对象
        # bucket:存储空间
        # key: 上传后的文件名和路径
        request = oss.PutObjectRequest(
            bucket=bucket, key=oss_key, content_type=content_type
        )

        # 上传文件
        result = client.put_object_from_file(request=request, filepath=local_path)

        # 拼接出图片上传成功后的访问地址
        # success：验证是否上传成功 #key:上传后的文件名和路径 #url：上传后的文件访问路径 #etag：上传后的文件的ETage：唯一标识符
        return {
            "success": True,
            "key": oss_key,
            "url": f"https://{endpoint}/{oss_key}",
            "etag": result.etag,
        }
    except Exception as e:
        print(f"上传文件失败: {str(e)}")
        raise


######从网络URL下载图片并上传到OSS
def upload_image_from_url(image_url: str) -> str:
    try:
        # 下载文件
        response = requests.get(image_url, timeout=30)
        # 检查HTTP请求是否成功
        response.raise_for_status()
        # 从URL中提取文件名(如果没有则用默认)
        parsed = urlparse(image_url)
        original_name = os.path.basename(parsed.path) or "downloaded_image.png"
        # 原始后缀
        ext = os.path.splitext(original_name)[1].lower()
        # 随机码八位
        random_code = uuid.uuid4().hex[:8]
        oss_key = f"images/{os.path.splitext(original_name)[0]}_{random_code}{ext}"
        # 获取响应头中的Content-Type，如果不是图片类型,设置为图片类型
        content_type = response.headers.get("Content-Type", "image/jpeg")
        if "image" not in content_type:
            content_type = "image/jpeg"

        # 直接上传二进制内容(无需保存到本地)
        request = oss.PutObjectRequest(
            bucket=bucket,
            key=oss_key,
            body=io.BytesIO(response.content),
            content_type=content_type,
        )

        # 上传文件
        result = client.put_object(request)
        # 拼接出这个图片上传成功后的访问地址
        # success：验证上传是否成功 #key:获取上传后的文件名和路径 #url：上传后的文件访问地址 #etag：上传后的文件的ETag，唯一标识符
        return {
            "success": True,
            "key": oss_key,
            "url": f"https://{endpoint}/{oss_key}",
            "etag": result.etag,
        }

    except requests.exceptions.RequestException as e:
        print(f"下载网络图片失败: {str(e)}")
        raise

    except Exception as e:
        print(f"上传文件失败: {str(e)}")
        raise


if __name__ == "__main__":
    # result = upload_local_image(local_path="D:/test.png")
    result = upload_image_from_url(
        image_url="https://bf-operation-sgp.oss-ap-southeast-1.aliyuncs.com/images/test_0082379e.png"
    )
    print(result)
