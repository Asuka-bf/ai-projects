from tortoise import fields
from tortoise.models import Model


class User(Model):
    """用户表 t_users。"""

    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password = fields.CharField(max_length=255)
    name = fields.CharField(max_length=50)
    department = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_users"


class Section(Model):
    """板块表 t_sections。"""

    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    source_name = fields.CharField(max_length=255, null=True)  # 用户输入的标题/主题
    name = fields.CharField(max_length=100)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_sections"


class Title(Model):
    """标题表 t_titles。"""

    id = fields.IntField(pk=True)
    section_id = fields.IntField()
    title = fields.CharField(max_length=255)
    sort_order = fields.IntField()
    content = fields.TextField(null=True)  # 文章内容
    status = fields.CharField(
        max_length=255, null=True
    )  # 0:未生成/1:已生成/2:已发布/3:已废弃
    view_count = fields.CharField(max_length=255, null=True)
    like_count = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_titles"


class TitleImage(Model):
    """标题图片表 t_title_images。image_type: 0=正文图 1=封面图 2=缩略图"""

    id = fields.BigIntField(pk=True)
    user_id = fields.IntField(null=True)
    title_id = fields.IntField()
    image_url = fields.CharField(max_length=500)
    image_type = fields.SmallIntField(default=0)  # 0=正文图 1=封面图 2=缩略图
    sort_order = fields.IntField(default=0)
    file_size = fields.IntField(null=True)
    width = fields.IntField(null=True)
    height = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_title_images"


class Style(Model):
    """风格表 t_style。"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=True)
    fengge = fields.TextField(null=True)
    create_time = fields.DatetimeField(null=True)

    class Meta:
        table = "t_style"


class AIModel(Model):
    """AI 模型表 t_models。"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    type = fields.CharField(max_length=50)  # text=文本生成, image=图像生成
    version = fields.CharField(max_length=50, null=True)
    description = fields.TextField(null=True)
    status = fields.IntField(default=1)  # 1=可用, 0=停用
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_models"


class PublishRecord(Model):
    """
    发布记录表 t_publish_records。
        platform: 1=小红书 2=抖音 3=快手 4=微信公众号
        publish_status: 0=待发布 1=发布中 2=发布成功 3=发布失败 4=已删除
    """

    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)
    title_id = fields.IntField()
    xhs_id = fields.IntField()
    note_url = fields.CharField(max_length=255, null=True)
    platform = fields.SmallIntField()  # 1=小红书
    publish_status = fields.SmallIntField(default=0)
    publish_time = fields.DatetimeField(null=True)
    content = fields.TextField(null=True)
    view_count = fields.IntField(default=0)
    like_count = fields.IntField(default=0)
    comment_count = fields.IntField(default=0)
    share_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_publish_records"


class PublishImage(Model):
    """
    发布内容图片表 t_publish_images。
        image_type: 1=正文图 2=封面图 3=详情图
    """

    id = fields.IntField(pk=True)
    publish_id = fields.IntField()
    # 关联素材库或标题图片表中的图片 ID（例如 t_title_images.id）
    image_id = fields.IntField()
    image_type = fields.SmallIntField(default=1)
    sort_order = fields.IntField(default=1)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_publish_images"


class XhsAccount(Model):
    """
    小红书账号表 t_xhs_accounts。
    用于管理多个小红书账号的 cookie 登录凭证。
    """

    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)  # 所属用户
    name = fields.CharField(max_length=100, null=True)  # 账号昵称
    a1 = fields.CharField(max_length=255)  # cookie a1
    web_session = fields.CharField(max_length=255)  # cookie web_session
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_xhs_accounts"
