"""
处理品牌知识问答数据集
格式：query：xxx\t答案：xxx\tBC
"""

import json
import re
import os


def process_brand_data(input_file: str, output_file: str):
    """
    处理品牌知识问答数据

    Args:
        input_file: 输入文件路径
        output_file: 输出 JSON 文件路径
    """
    qa_pairs = []

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # 按行分割
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 查找包含 query 和 答案 的行
        # 格式：...	query：xxx	答案：xxx	BC
        if 'query：' in line and '答案：' in line:
            # 提取 query 和答案
            parts = line.split('\t')

            query_part = None
            answer_part = None

            for part in parts:
                part = part.strip()
                if part.startswith('query：') or part.startswith('query:'):
                    query_part = part.replace('query：', '').replace('query:', '').strip()
                elif part.startswith('答案：') or part.startswith('答案:'):
                    answer_part = part.replace('答案：', '').replace('答案:', '').strip()

            if query_part and answer_part:
                # 分类
                category = classify_brand_question(query_part)

                qa_pairs.append({
                    "question": query_part,
                    "answer": answer_part,
                    "category": category,
                    "conversation_history": [],
                    "full_conversation": [f"问：{query_part}", f"答：{answer_part}"]
                })

    # 保存为 JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

    print(f"处理完成！共 {len(qa_pairs)} 条数据")
    print(f"保存到：{output_file}")

    # 统计分类
    from collections import Counter
    categories = Counter(qa['category'] for qa in qa_pairs)
    print("\n分类统计：")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    # 显示前5条
    print("\n前5条数据：")
    for qa in qa_pairs[:5]:
        print(f"  Q: {qa['question']}")
        print(f"  A: {qa['answer'][:50]}...")
        print()

    return qa_pairs


def classify_brand_question(question: str) -> str:
    """根据关键词对品牌问题进行分类"""
    category_keywords = {
        "产品咨询": ["产品", "商品", "有哪些", "包括", "系列", "款式", "型号"],
        "品牌信息": ["品牌", "创立", "发源地", "历史", "成立", "创办"],
        "业务范围": ["业务", "主营", "经营范围", "做什么", "销售"],
        "价格咨询": ["价格", "多少钱", "贵不贵", "便宜"],
        "购买渠道": ["哪里买", "门店", "官网", "旗舰店"],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in question:
                return category

    return "品牌知识"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法：python process_brand_data.py <输入文件> [输出文件]")
        print("示例：python process_brand_data.py brand_data.txt data/brand_qa.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/brand_qa.json"

    process_brand_data(input_file, output_file)
