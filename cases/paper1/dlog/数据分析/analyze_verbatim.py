"""
Owner Verbatim 分类统计脚本
读取提取的 User: 行，按阶段和类别统计
"""
import re
import os
from collections import defaultdict, Counter

# ===== 配置 =====
INPUT_FILE = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_extracted_user_lines.txt"
OUTPUT_FILE = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_verbatim_analysis.md"

# 阶段分界
PRE_END = 214       # 升级前: #136-#214
TRANS_END = 252     # 升级中: #215-#252
# 升级后: #253-#395

# ===== 分类规则 =====
# 每条规则是 (关键词列表, 类别名, 优先级)
# 优先级高的先匹配（防止误分类）
CATEGORIES = [
    # 系统操作（最高优先级，因为 @agent 等很明确）
    (["@agent", "Try Again"], "系统/工具操作", 10),
    
    # 指出错误/纠偏
    (["出错", "错误", "没改", "不行", "你再检查", "不对", "删掉", "不是这样",
      "有问题", "似乎没改", "又出错", "出问题", "这不是", "搞错了",
      "检查一下", "再检查", "尾巴", "顺序是乱的", "超长", "这里有",
      "你又", "你这次", "不准确", "漏了", "忘了", "残留"], "指出错误/纠偏", 9),
    
    # 业务纠偏/方向校准
    (["你应该", "我的考虑", "太复杂", "不要把", "我真正想要", "我真正想要的",
      "你要考虑", "你先确认", "你要基于", "胃口太大", "这不是我",
      "你给", "为什么要", "这个表述", "这不是", "不是让你",
      "我的意思是", "我意识到", "我发现", "不能只是", "不是要你",
      "你先别", "你先不要", "你先读", "你需要先", "你先看看",
      "你要先", "你得先", "你最好", "你不应该", "你不能",
      "你不要", "你别", "这个不对", "这个不是", "这里不对",
      "你没有", "你还没", "你还"], "业务纠偏/方向校准", 8),
    
    # 方法探讨
    (["我觉得", "方法", "方法论", "Slice", "切片", "DDD", "规范", "理论",
      "公理", "第一性", "我认为", "我的判断", "我的观察",
      "我打算", "我想讨论", "我的想法", "我真正", "我想",
      "重新规划", "重构", "三元组", "目的.*方法.*资源",
      "原则", "结构", "机制", "协作"], "方法探讨/理论讨论", 7),
    
    # 业务解释
    (["业务线", "解释", "我先描述", "先描述", "比如说", "例如",
      "简而言之", "换句话说", "举个例子", "我的意思是说",
      "从工程", "从语义", "我补充", "我解释", "实指",
      "在一个"], "业务解释/知识传授", 6),
    
    # 肯定/确认
    (["非常好", "很好", "不错", "都同意", "默契", "我很满意",
      "作为一个骨架", "我觉得很好了", "都很好", "可以的",
      "可以了", "没问题", "没错误", "都对", "全都对",
      "很准确", "到位", "很好用", "这个好", "我喜欢"], "肯定/认可", 5),
    
    # 例行程序/方向指令
    (["阅读context", "继续", "开搞", "开始执行", "开始", "同意",
      "按推荐", "全按推荐", "可以", "好的", "好",
      "依建议", "按你的", "你来", "你定", "你主导",
      "收尾", "先做", "先处理", "推进", "启动",
      "继续推进", "执行", "确认", "是的", "对",
      "批准", "拍板", "就这样", "闭", "关",
      "下一步", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8",
      "A", "B", "C", "D", "P1", "P2", "P3"], "例行程序/方向指令", 4),
    
    # 闲聊
    (["闲聊", "好奇", "话题", "宋哥", "周末", "聊天",
      "开玩笑", "吐槽"], "闲聊/其他", 1),
]

def extract_session_num(filename):
    """从文件名提取会话编号"""
    m = re.search(r'_dlog_(\d+)', filename)
    return int(m.group(1)) if m else 0

def get_phase(session_num):
    """确定会话所属阶段"""
    if session_num <= PRE_END:
        return "升级前 (#136-#214)"
    elif session_num <= TRANS_END:
        return "升级中 (#215-#252)"
    else:
        return "升级后 (#253-#395)"

def classify_line(text):
    """基于关键词对单行进行分类，返回 (类别, 置信度)"""
    text_lower = text.lower()
    for keywords, category, priority in sorted(CATEGORIES, key=lambda x: -x[2]):
        for kw in keywords:
            if kw.lower() in text_lower:
                return category
    return "未分类", 

def main():
    # 读取数据
    entries = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|', 2)
            if len(parts) < 3:
                continue
            filename, linenum, text = parts
            session_num = extract_session_num(filename)
            if session_num == 0:
                continue
            entries.append({
                'filename': filename,
                'line': int(linenum) if linenum.isdigit() else 0,
                'text': text,
                'session': session_num,
                'phase': get_phase(session_num)
            })
    
    # 分类
    for entry in entries:
        entry['category'] = classify_line(entry['text'])
    
    # 统计
    phases = ["升级前 (#136-#214)", "升级中 (#215-#252)", "升级后 (#253-#395)"]
    
    # 各类别统计
    all_categories = [c[1] for c in CATEGORIES] + ["未分类"]
    
    # 按阶段 x 类别 统计
    phase_cat_count = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        phase_cat_count[entry['phase']][entry['category']] += 1
    
    # 按阶段统计总数
    phase_total = defaultdict(int)
    for entry in entries:
        phase_total[entry['phase']] += 1
    
    # 按阶段 x 会话 统计（用于计算平均每条会话的各类verbatim数）
    phase_session_set = defaultdict(set)
    for entry in entries:
        phase_session_set[entry['phase']].add(entry['session'])
    
    # ===== 输出 Markdown =====
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Owner Verbatim 分类统计分析\n\n")
        f.write(f"> 自动生成日期：2026-06-18\n")
        f.write(f"> 数据来源：139 个会话记录文件，共 {len(entries)} 条 Owner verbatim (`User:` 行)\n")
        f.write(f"> 会话范围：#136 – #395\n\n")
        
        f.write("---\n\n")
        
        # 阶段定义
        f.write("## 阶段划分\n\n")
        f.write("| 阶段 | 会话范围 | 会话数 | Verbatim 总数 | 平均每会话 verbatim |\n")
        f.write("|------|----------|--------|---------------|---------------------|\n")
        for phase in phases:
            total = phase_total[phase]
            n_sessions = len(phase_session_set[phase])
            avg = total / n_sessions if n_sessions > 0 else 0
            f.write(f"| {phase} | #{min(phase_session_set[phase]) if phase_session_set[phase] else '?'}–#{max(phase_session_set[phase]) if phase_session_set[phase] else '?'} | {n_sessions} | {total} | {avg:.1f} |\n")
        
        f.write("\n---\n\n")
        
        # 主统计表
        f.write("## 分类统计表\n\n")
        f.write("| 类别 | 升级前 | 升级中 | 升级后 | 总计 | 备注 |\n")
        f.write("|------|--------|--------|--------|------|------|\n")
        
        # 把"指出错误"和"业务纠偏"放在最前面（最关键的指标）
        ordered_cats = ["指出错误/纠偏", "业务纠偏/方向校准", "方法探讨/理论讨论", 
                       "业务解释/知识传授", "肯定/认可", "例行程序/方向指令",
                       "系统/工具操作", "闲聊/其他", "未分类"]
        
        totals_by_cat = defaultdict(int)
        for cat in ordered_cats:
            row = [cat]
            for phase in phases:
                count = phase_cat_count[phase].get(cat, 0)
                row.append(str(count))
                totals_by_cat[cat] += count
            row.append(str(totals_by_cat[cat]))
            # 备注
            note = ""
            f.write(f"| {' | '.join(row)} | {note} |\n")
        
        # 总计行
        total_all = sum(totals_by_cat.values())
        f.write(f"| **总计** |")
        for phase in phases:
            f.write(f" **{phase_total[phase]}** |")
        f.write(f" **{total_all}** | |\n")
        
        f.write("\n---\n\n")
        
        # 关键对比：纠偏类 verbatim
        f.write("## 关键对比：纠偏类 Verbatim（指出错误 + 业务纠偏）\n\n")
        correction_pre = phase_cat_count[phases[0]].get("指出错误/纠偏", 0) + phase_cat_count[phases[0]].get("业务纠偏/方向校准", 0)
        correction_trans = phase_cat_count[phases[1]].get("指出错误/纠偏", 0) + phase_cat_count[phases[1]].get("业务纠偏/方向校准", 0)
        correction_post = phase_cat_count[phases[2]].get("指出错误/纠偏", 0) + phase_cat_count[phases[2]].get("业务纠偏/方向校准", 0)
        
        n_pre = len(phase_session_set[phases[0]])
        n_trans = len(phase_session_set[phases[1]])
        n_post = len(phase_session_set[phases[2]])
        
        f.write("| 阶段 | 纠偏类总数 | 会话数 | 平均每会话纠偏 |\n")
        f.write("|------|-----------|--------|----------------|\n")
        f.write(f"| 升级前 | {correction_pre} | {n_pre} | {correction_pre/n_pre:.1f} |\n")
        f.write(f"| 升级中 | {correction_trans} | {n_trans} | {correction_trans/n_trans:.1f} |\n")
        f.write(f"| 升级后 | {correction_post} | {n_post} | {correction_post/n_post:.1f} |\n")
        
        f.write("\n---\n\n")
        
        # 每会话平均各类别对比
        f.write("## 每会话平均各类别 Verbatim 数\n\n")
        f.write("| 类别 | 升级前 | 升级后 | 变化 |\n")
        f.write("|------|--------|--------|------|\n")
        for cat in ordered_cats:
            pre_avg = phase_cat_count[phases[0]].get(cat, 0) / n_pre if n_pre > 0 else 0
            post_avg = phase_cat_count[phases[2]].get(cat, 0) / n_post if n_post > 0 else 0
            if pre_avg + post_avg > 0:
                change = f"{(post_avg - pre_avg):+.1f} ({(post_avg/pre_avg - 1)*100:+.0f}%)" if pre_avg > 0 else "新增"
            else:
                change = "-"
            f.write(f"| {cat} | {pre_avg:.1f} | {post_avg:.1f} | {change} |\n")
        
        f.write("\n---\n\n")
        
        # 典型样本
        f.write("## 各类别典型样本（各取5条）\n\n")
        samples_by_cat = defaultdict(list)
        for entry in entries:
            if len(samples_by_cat[entry['category']]) < 5:
                samples_by_cat[entry['category']].append(entry)
        
        for cat in ordered_cats:
            samples = samples_by_cat.get(cat, [])
            if samples:
                f.write(f"### {cat}\n\n")
                for s in samples:
                    text_short = s['text'][:120] + ('...' if len(s['text']) > 120 else '')
                    f.write(f"- [#{s['session']}] {text_short}\n")
                f.write("\n")
        
        # 分类方法说明
        f.write("---\n\n")
        f.write("## 分类方法说明\n\n")
        f.write("采用关键词匹配自动分类，分类规则及优先级如下：\n\n")
        for keywords, category, priority in sorted(CATEGORIES, key=lambda x: -x[2]):
            f.write(f"- **{category}** (优先级 {priority}): `{', '.join(keywords[:8])}` {'...' if len(keywords) > 8 else ''}\n")
        f.write("\n> ⚠️ 自动分类有误差。关键类别（指出错误、业务纠偏）已使用较严格的关键词匹配，但可能漏掉隐含的纠偏语义。建议人工抽检。\n")
    
    print(f"分析完成。输出文件: {OUTPUT_FILE}")
    print(f"总计 {len(entries)} 条 verbatim")
    print(f"升级前: {phase_total[phases[0]]} 条 ({len(phase_session_set[phases[0]])} sessions)")
    print(f"升级中: {phase_total[phases[1]]} 条 ({len(phase_session_set[phases[1]])} sessions)")
    print(f"升级后: {phase_total[phases[2]]} 条 ({len(phase_session_set[phases[2]])} sessions)")
    print(f"纠偏类 (升级前/升级后): {correction_pre} / {correction_post}")

if __name__ == "__main__":
    main()
