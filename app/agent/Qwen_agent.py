from http import HTTPStatus
import os
import dashscope
from dashscope import MultiModalConversation, api_key
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 阿里百炼调用模型路径
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"


# 构建生成图片的提示词
# title:文章标题
# style_desecrtion:风格描述
# include_text:是否包含文字
def generate_cover_prompt(
    title: str, style_description: str, include_text: bool = False
) -> str:
    # 提示词部分
    prompt_parts = []
    # 1.风格描述
    prompt_parts.append(f"请以{style_description}的风格创作一张封面图片，")
    # 2.画面风格主题描述
    prompt_parts.append(f"画面主题围绕'{title}'展开，")
    # 3.是否包含文字 进行文字处理
    if include_text:
        prompt_parts.append(
            f"必须包含清晰准确的标题文字：{title}。"
            "文字要求：使用醒目的粗体无衬线字体，文字居中排列，"
            "文字颜色与背景形成强烈对比，文字边缘清晰锐利，"
            "无变形无模糊，确保每个汉字都完整正确显示，"
            "文字区域干净整洁，无干扰元素"
            "重要：标题文字必须完整、准确、清晰，"
            "不能出现错别字、缺字、乱码、字体变形或模糊"
        )
    else:
        prompt_parts.append(
            "画面中绝对不能出现任何文字，包括标题、数字、符号、字母。"
            "只使用图形、图标、插画和形状来表达主题。"
            "画面干净整洁，没有任何文字元素"
        )
    # 4.质量要求
    prompt_parts.append(
        "请确保生成的图片质量高，分辨率至少为1080x1080像素，"
        "画面清晰细腻，色彩丰富，构图合理，视觉效果吸引人。"
    )
    # 5.组装提示词
    full_prompt = "。".join(prompt_parts)
    # 返回组装后的提示词
    return full_prompt


# 使用图片,使用阿里云百炼生成图片,成功时返回图片URL，失败时抛出异常
# prompt: 提示词
# n:生成图片数量
# size：图片尺寸
# prompt_extend: 是否拓展提示词
# wartermark:是否加水印
# 模型名称
def generate_image(
    prompt: str,
    n: int = 1,
    size: str = "1080*1080",
    prompt_extend: bool = True,
    wartermark: bool = False,
    model: str = "qwen-image-2.0-pro",
) -> str | None:

    # 密钥
    api_key = os.getenv("QWEN_KEY")
    # 负向提示词
    negative_prompt = (
        "模糊，变形，扭曲，低质量，像素化，噪点，"
        "血腥暴力，色情，政治敏感，品牌标识，"
        "多余人脸，多余肢体，解剖错"
    )
    # 调用模型
    message = [{"role": "user", "content": [{"text": prompt}]}]

    response = MultiModalConversation.call(
        api_key=api_key,
        model=model,
        messages=message,
        watermark=wartermark,
        prompt_extend=prompt_extend,
        negative_prompt=negative_prompt,
        size=size,
        n=n,
    )
    # 解析模型返回数据
    if response.status_code != 200:
        error_msg = (
            f"Qwen生成失败: status_code={response.status_code}, "
            f"code={response.code}, message={response.message}"
        )
        print(error_msg)
        raise RuntimeError(error_msg)

    # 返回图片URL
    return response["output"]["choices"][0]["message"]["content"][0]["image"]


if __name__ == "__main__":
    # 测试生成图片
    prompt = generate_cover_prompt(
        title="人工智能的未来发展趋势",
        style_description="极简主义扁平化海报设计风格，整体采用非常清淡柔和的浅色调背景，背景由大面积的纯白色与少量浅粉色、浅紫色的圆形光晕渐变色块构成，营造出朦胧且科技感较弱的清新氛围，视觉中心采用经典的垂直居中排版布局，文字层级分明，顶部为主标题区域使用醒目的红色加粗无衬线字体，下方跟随黑色的副标题与深灰色的正文说明，字体均为现代简洁的无衬线黑体，底部排列着两行胶囊形状的白色标签，配以浅灰色的文字，整体画面留白充足，风格干净利落，具有典型的新媒体资讯或知识卡片的美学特征，色彩搭配为白色底色辅以淡粉淡紫装饰，字色为鲜红与深黑的强烈对比。",
        include_text=False,
    )

    image_url = generate_image(prompt)
    print(f"生成的图片URL: {image_url}")
