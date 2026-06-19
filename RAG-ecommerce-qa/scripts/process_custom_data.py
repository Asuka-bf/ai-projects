"""
处理自定义对话数据
格式：1\t顾客：xxx\t客服：xxx
"""

import json
import re
import os


def process_custom_data(input_file: str, output_file: str):
    """
    处理自定义对话数据

    Args:
        input_file: 输入文件路径
        output_file: 输出 JSON 文件路径
    """
    qa_pairs = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 分割标签和对话
            parts = line.split('\t')
            if len(parts) < 2:
                continue

            label = parts[0].strip()

            # 只处理正样本（label=1）
            if label != '1':
                continue

            # 提取对话内容
            conversation = '\t'.join(parts[1:])

            # 分离顾客和客服
            # 格式：顾客：xxx\t客服：xxx
            customer_match = re.search(r'顾客[：:](.+?)(?:\t|$)', conversation)
            service_match = re.search(r'客服[：:](.+?)(?:\t|$)', conversation)

            if customer_match and service_match:
                question = customer_match.group(1).strip()
                answer = service_match.group(1).strip()

                # 简单分类
                category = classify_question(question)

                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "conversation_history": [],
                    "full_conversation": [f"顾客：{question}", f"客服：{answer}"]
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

    return qa_pairs


def classify_question(question: str) -> str:
    """根据关键词对问题进行分类"""
    category_keywords = {
        "物流配送": ["发货", "快递", "物流", "配送", "运费", "邮费", "包邮", "到货", "几天到", "什么时候到", "什么时候能收到"],
        "退换货": ["退货", "换货", "退款", "退换", "退回", "退了", "不要了", "申请退", "售后", "补发"],
        "订单支付": ["下单", "付款", "支付", "拍下", "拍了", "订单", "价格", "多少钱", "便宜", "优惠", "打折", "改价", "便宜点"],
        "优惠活动": ["优惠券", "券", "活动", "满减", "买一送一", "赠品", "送什么", "试吃", "返现", "返钱", "折扣"],
        "产品咨询": ["质量", "怎么样", "好用吗", "效果", "材质", "尺寸", "大小", "颜色", "型号", "规格", "包装", "日期", "一样的吗"],
        "账户服务": ["发票", "收藏", "关注", "会员", "积分", "地址", "修改", "备注", "客服", "投诉"],
        "售前咨询": ["有货吗", "有吗", "库存", "现货", "预售", "什么时候有", "补货", "上新"],
        "售后服务": ["坏了", "破损", "少发", "漏发", "错了", "问题", "怎么处理", "怎么办", "解决"],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in question:
                return category

    return "其他"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法：python process_custom_data.py <输入文件> [输出文件]")
        print("示例：python process_custom_data.py data.txt data/custom_qa.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/custom_qa.json"

    process_custom_data(input_file, output_file)
