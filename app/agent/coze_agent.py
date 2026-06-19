import sys
import os

# 任何包都可以导入该文件下的内容
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from cozepy import COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message

# 读取环境变量
load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".env",
    )
)


# 热点选题搜索
def search_hot_topics(question: str) -> str:
    # Coze的令牌
    token = os.getenv("COZE_TOKEN")
    # 创建Coze实例
    coze = Coze(auth=TokenAuth(token), base_url=COZE_CN_BASE_URL)

    # BOTID
    bot_id = os.getenv("BOT_ID_TOPIC")
    # USERID
    user_id = os.getenv("USER_ID")

    # 向扣子机器人发消息并等待完整回答
    chat_poll = coze.chat.create_and_poll(
        bot_id=bot_id,
        user_id=user_id,
        additional_messages=[
            Message.build_user_question_text(
                question
            )  # 把纯文本包装成扣子机器人需要的message（信息）对象
        ],
    )

    print(f"chat status: {chat_poll.chat.status}")  #######调试用#########

    # 提取最终的结果
    final_answer = ""
    for message in chat_poll.messages:
        print(
            f"type: {message.type}, content: {message.content[:100] if message.content else ''}"
        )  #######调试用#########
        if message.type == "answer":
            final_answer += message.content
    return final_answer


# 文案生成功能
def concent_creation(title_text: str) -> str:
    # Coze的令牌
    token = os.getenv("COZE_TOKEN")
    # 创建Coze实例
    coze = Coze(auth=TokenAuth(token), base_url=COZE_CN_BASE_URL)

    # BOTID
    bot_id = os.getenv("BOT_ID_CONCENT")
    # USERID
    user_id = os.getenv("USER_ID")

    # 向扣子机器人发消息并等待完整回答
    chat_poll = coze.chat.create_and_poll(
        bot_id=bot_id,
        user_id=user_id,
        additional_messages=[
            Message.build_user_question_text(
                title_text
            )  # 把纯文本包装成扣子机器人需要的message（信息）对象
        ],
    )

    print(f"chat status: {chat_poll.chat.status}")  #######调试用#########

    # 提取最终的结果
    final_answer = ""
    for message in chat_poll.messages:
        print(
            f"type: {message.type}, content: {message.content[:100] if message.content else ''}"
        )  #######调试用#########
        if message.type == "answer":
            final_answer += message.content
    return final_answer


# 测试一下 测试

if __name__ == "__main__":
    title_text = "agent"
    answer = concent_creation(title_text)
    print(answer)
