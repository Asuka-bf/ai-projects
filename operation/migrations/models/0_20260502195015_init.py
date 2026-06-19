from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `t_models` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `type` VARCHAR(50) NOT NULL,
    `version` VARCHAR(50),
    `description` LONGTEXT,
    `status` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='AI 模型表 t_models。';
CREATE TABLE IF NOT EXISTS `t_publish_images` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `publish_id` INT NOT NULL,
    `image_id` INT NOT NULL,
    `image_type` SMALLINT NOT NULL DEFAULT 1,
    `sort_order` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='发布内容图片表 t_publish_images。';
CREATE TABLE IF NOT EXISTS `t_publish_records` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT,
    `title_id` INT NOT NULL,
    `platform` SMALLINT NOT NULL,
    `publish_status` SMALLINT NOT NULL DEFAULT 0,
    `publish_time` DATETIME(6),
    `content` LONGTEXT,
    `view_count` INT NOT NULL DEFAULT 0,
    `like_count` INT NOT NULL DEFAULT 0,
    `comment_count` INT NOT NULL DEFAULT 0,
    `share_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='发布记录表 t_publish_records。';
CREATE TABLE IF NOT EXISTS `t_sections` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `source_name` VARCHAR(255),
    `name` VARCHAR(100) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='板块表 t_sections。';
CREATE TABLE IF NOT EXISTS `t_style` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255),
    `fengge` LONGTEXT,
    `create_time` DATETIME(6)
) CHARACTER SET utf8mb4 COMMENT='风格表 t_style。';
CREATE TABLE IF NOT EXISTS `t_titles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `section_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `sort_order` INT NOT NULL,
    `content` LONGTEXT,
    `status` VARCHAR(255),
    `view_count` VARCHAR(255),
    `like_count` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='标题表 t_titles。';
CREATE TABLE IF NOT EXISTS `t_title_images` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT,
    `title_id` INT NOT NULL,
    `image_url` VARCHAR(500) NOT NULL,
    `image_type` SMALLINT NOT NULL DEFAULT 0,
    `sort_order` INT NOT NULL DEFAULT 0,
    `file_size` INT,
    `width` INT,
    `height` INT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='标题图片表 t_title_images。image_type: 0=正文图 1=封面图 2=缩略图';
CREATE TABLE IF NOT EXISTS `t_users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `department` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='用户表 t_users。';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "KVy2XLpq1lViNSAcllO+jy8ut/9Tr+Vw=="
)
