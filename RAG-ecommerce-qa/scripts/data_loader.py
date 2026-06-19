"""
电商对话数据集处理脚本
将淘宝客服对话数据集转换为 RAG 知识库可用的 Q&A 格式
"""

import json
import os
import re
from collections import defaultdict


# 分类关键词映射
CATEGORY_KEYWORDS = {
    "物流配送": ["发货", "快递", "物流", "配送", "运费", "邮费", "包邮", "到货", "几天到", "什么时候到", "发什么快递", "韵达", "圆通", "中通", "申通", "EMS", "顺丰"],
    "退换货": ["退货", "换货", "退款", "退换", "退回", "退了", "不要了", "申请退", "售后", "补发", "换一个"],
    "订单支付": ["下单", "付款", "支付", "拍下", "拍了", "订单", "价格", "多少钱", "便宜", "优惠", "打折", "改价"],
    "优惠活动": ["优惠券", "券", "活动", "满减", "买一送一", "赠品", "送什么", "试吃", "返现", "返钱", "折扣"],
    "产品咨询": ["质量", "怎么样", "好用吗", "效果", "材质", "尺寸", "大小", "颜色", "型号", "规格", "包装", "日期"],
    "账户服务": ["发票", "收藏", "关注", "会员", "积分", "地址", "修改", "备注", "客服", "投诉"],
    "售前咨询": ["有货吗", "有吗", "库存", "现货", "预售", "什么时候有", "补货", "上新"],
    "售后服务": ["坏了", "破损", "少发", "漏发", "错了", "问题", "怎么处理", "怎么办", "解决"],
}


def classify_question(question: str, conversation: list) -> str:
    """根据关键词对问题进行分类"""
    # 合并所有对话内容进行匹配
    all_text = question + " " + " ".join(conversation)

    scores = defaultdict(int)
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                scores[category] += 1

    if scores:
        return max(scores, key=scores.get)
    return "其他"


def clean_text(text: str) -> str:
    """清理文本：去除词语间空格，还原为正常中文"""
    # 去除词语间的空格（中文分词后的空格）
    text = text.replace(" ", "")
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def process_dialogue_file(file_path: str, max_samples: int = None) -> list:
    """
    处理对话数据文件

    Args:
        file_path: 数据文件路径
        max_samples: 最大采样数量（None 表示全部）

    Returns:
        处理后的 Q&A 列表
    """
    qa_pairs = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            label = parts[0]
            # 只保留正样本（label=1）
            if label != '1':
                continue

            conversation_raw = parts[1:-1]
            response_raw = parts[-1]

            # 清理文本
            conversation = [clean_text(c) for c in conversation_raw]
            response = clean_text(response_raw)

            # 过滤太短的对话
            if len(response) < 2:
                continue

            # 提取最后一轮用户问题
            last_question = conversation[-1] if conversation else ""

            # 分类
            category = classify_question(last_question, conversation)

            qa_pairs.append({
                "question": last_question,
                "answer": response,
                "category": category,
                "conversation_history": conversation[:-1] if len(conversation) > 1 else [],
                "full_conversation": conversation + [response],
            })

            if max_samples and len(qa_pairs) >= max_samples:
                break

    return qa_pairs


def save_dataset(qa_pairs: list, output_path: str):
    """保存处理后的数据集"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)


def print_statistics(qa_pairs: list):
    """打印数据集统计信息"""
    print(f"\n{'='*50}")
    print(f"数据集统计")
    print(f"{'='*50}")
    print(f"总 Q&A 对数: {len(qa_pairs)}")

    # 分类统计
    categories = defaultdict(int)
    for qa in qa_pairs:
        categories[qa['category']] += 1

    print(f"\n分类分布:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / len(qa_pairs) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # 示例
    print(f"\n示例:")
    for qa in qa_pairs[:3]:
        print(f"  Q: {qa['question'][:50]}...")
        print(f"  A: {qa['answer'][:50]}...")
        print(f"  分类: {qa['category']}")
        print()


if __name__ == "__main__":
    # 配置
    # 通过环境变量设置数据目录，不设置则使用默认路径
    DATA_DIR = os.getenv("ECOMMERCE_DATA_DIR", r"D:\Google\E-commerce dataset")
    OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce_qa.json")
    MAX_SAMPLES = 8000  # 采样数量，可调整

    # 处理训练集
    train_file = os.path.join(DATA_DIR, "train.txt")
    if not os.path.exists(train_file):
        print(f"错误: 数据文件不存在: {train_file}")
        print(f"请设置环境变量 ECOMMERCE_DATA_DIR 指向数据所在目录")
        print(f"例如: set ECOMMERCE_DATA_DIR=D:\\your\\data\\path")
        exit(1)

    print(f"正在处理数据文件: {train_file}")
    print(f"最大采样数: {MAX_SAMPLES}")

    qa_pairs = process_dialogue_file(train_file, max_samples=MAX_SAMPLES)
    save_dataset(qa_pairs, OUTPUT_PATH)
    print_statistics(qa_pairs)
    print(f"\n数据已保存到: {OUTPUT_PATH}")
