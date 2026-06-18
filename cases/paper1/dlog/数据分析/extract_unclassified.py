"""提取所有未分类 verbatim 并输出到文件"""
import re

INPUT = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_extracted_user_lines.txt"
OUTPUT = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_unclassified_review.txt"

CATEGORIES = [
    (["@agent", "Try Again"], "系统/工具操作", 10),
    (["出错", "错误", "没改", "不行", "你再检查", "不对", "删掉", "不是这样",
      "有问题", "似乎没改", "又出错", "出问题", "这不是", "搞错了",
      "检查一下", "再检查", "尾巴", "顺序是乱的", "超长", "这里有",
      "你又", "你这次", "不准确", "漏了", "忘了", "残留",
      "出了什么问题", "有错误", "存在错误", "不对啊", "又是",
      "怎么会", "为什么没有", "怎么没有"], "指出错误/纠偏", 9),
    (["你应该", "我的考虑", "太复杂", "不要把", "我真正想要", "我真正想要的",
      "你要考虑", "你先确认", "你要基于", "胃口太大", "这不是我",
      "你给", "为什么要", "这个表述", "这不是", "不是让你",
      "我的意思是", "我意识到", "我发现", "不能只是", "不是要你",
      "你先别", "你先不要", "你先读", "你需要先", "你先看看",
      "你要先", "你得先", "你最好", "你不应该", "你不能",
      "你不要", "你别", "这个不对", "这个不是", "这里不对",
      "你没有", "你还没", "你还", "你要注意", "你得注意",
      "你这个", "你这", "你这里", "你把", "你把我",
      "不是这样理解", "理解错了", "你理解错了", "你理解有",
      "我再强调", "我再重复", "我说的是", "我前面说的",
      "我说的不是", "我说的不是这个", "纠正", "纠偏",
      "跑偏了", "偏了", "扯远了", "说回来"], "业务纠偏/方向校准", 8),
    (["我觉得", "方法", "方法论", "Slice", "切片", "DDD", "规范", "理论",
      "公理", "第一性", "我认为", "我的判断", "我的观察",
      "我打算", "我想讨论", "我的想法", "我真正", "我想",
      "重新规划", "重构", "三元组",
      "原则", "结构", "机制", "协作", "世界观",
      "基本假设", "出发点", "立足点"], "方法探讨/理论讨论", 7),
    (["业务线", "解释", "我先描述", "先描述", "比如说", "例如",
      "简而言之", "换句话说", "举个例子", "我的意思是说",
      "从工程", "从语义", "我补充", "我解释", "实指",
      "在一个", "我补充一个", "补充一个事实"], "业务解释/知识传授", 6),
    (["非常好", "很好", "不错", "都同意", "默契", "我很满意",
      "作为一个骨架", "我觉得很好了", "都很好", "可以的",
      "可以了", "没问题", "没错误", "都对", "全都对",
      "很准确", "到位", "很好用", "这个好", "我喜欢",
      "都同意你的", "我都同意", "都没问题", "没有问题"], "肯定/认可", 5),
    (["阅读context", "继续", "开搞", "开始执行", "开始", "同意",
      "按推荐", "全按推荐", "可以", "好的", "好",
      "依建议", "按你的", "你来", "你定", "你主导",
      "收尾", "先做", "先处理", "推进", "启动",
      "继续推进", "执行", "确认", "是的", "对",
      "批准", "拍板", "就这样", "闭", "关",
      "下一步", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8",
      "A", "B", "C", "D", "P1", "P2", "P3"], "例行程序/方向指令", 4),
    (["闲聊", "好奇", "话题", "宋哥", "周末", "聊天", "开玩笑", "吐槽"], "闲聊/其他", 1),
]

def classify_line(text):
    text_lower = text.lower()
    for keywords, category, priority in sorted(CATEGORIES, key=lambda x: -x[2]):
        for kw in keywords:
            if kw.lower() in text_lower:
                return category
    return "未分类"

def get_phase(session):
    if session <= 214:
        return "升级前"
    elif session <= 252:
        return "升级中"
    else:
        return "升级后"

entries = []
with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        filename, linenum, text = parts
        m = re.search(r"_dlog_(\d+)", filename)
        if not m:
            continue
        session = int(m.group(1))
        cat = classify_line(text)
        if cat == "未分类":
            phase = get_phase(session)
            entries.append((session, phase, text))

# 统计
from collections import Counter
phase_counts = Counter(e[1] for e in entries)
print(f"Total unclassified: {len(entries)}")
print(f"升级前: {phase_counts.get('升级前', 0)}")
print(f"升级中: {phase_counts.get('升级中', 0)}")
print(f"升级后: {phase_counts.get('升级后', 0)}")

# 输出到文件
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(f"# 未分类 Verbatim 待核查列表\n\n")
    f.write(f"总计: {len(entries)} 条\n")
    f.write(f"升级前: {phase_counts.get('升级前', 0)} | 升级中: {phase_counts.get('升级中', 0)} | 升级后: {phase_counts.get('升级后', 0)}\n\n")
    f.write("---\n\n")
    
    current_phase = None
    for session, phase, text in sorted(entries, key=lambda x: ({"升级前":0,"升级中":1,"升级后":2}[x[1]], x[0])):
        if phase != current_phase:
            current_phase = phase
            f.write(f"\n## {current_phase}\n\n")
        f.write(f"- [#{session}] {text}\n")

print(f"Output: {OUTPUT}")
