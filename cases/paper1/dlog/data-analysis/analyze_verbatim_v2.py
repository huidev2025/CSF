"""
Owner Verbatim 分类统计 v2 - 增加纠偏类详细输出
"""
import re
import os
from collections import defaultdict

INPUT_FILE = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_extracted_user_lines.txt"
OUTPUT_FILE = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_verbatim_analysis_v2.md"

PRE_END = 214
TRANS_END = 252

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
      "重新规划", "重构", "三元组", "目的.*方法.*资源",
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
    (["闲聊", "好奇", "话题", "宋哥", "周末", "聊天",
      "开玩笑", "吐槽"], "闲聊/其他", 1),
]

def extract_session_num(filename):
    m = re.search(r'_dlog_(\d+)', filename)
    return int(m.group(1)) if m else 0

def get_phase(session_num):
    if session_num <= PRE_END:
        return "升级前 (#136-#214)"
    elif session_num <= TRANS_END:
        return "升级中 (#215-#252)"
    else:
        return "升级后 (#253-#395)"

def classify_line(text):
    text_lower = text.lower()
    for keywords, category, priority in sorted(CATEGORIES, key=lambda x: -x[2]):
        for kw in keywords:
            if kw.lower() in text_lower:
                return category
    return "未分类"

def main():
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
    
    for entry in entries:
        entry['category'] = classify_line(entry['text'])
    
    phases = ["升级前 (#136-#214)", "升级中 (#215-#252)", "升级后 (#253-#395)"]
    
    phase_cat_count = defaultdict(lambda: defaultdict(int))
    phase_entries = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        phase_cat_count[entry['phase']][entry['category']] += 1
        phase_entries[entry['phase']][entry['category']].append(entry)
    
    phase_total = defaultdict(int)
    phase_session_set = defaultdict(set)
    for entry in entries:
        phase_total[entry['phase']] += 1
        phase_session_set[entry['phase']].add(entry['session'])
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Owner Verbatim 分类统计分析 v2\n\n")
        f.write(f"> 数据：139 文件，{len(entries)} 条 `User:` 行\n")
        f.write(f"> 会话范围：#136 – #395\n\n")
        
        f.write("---\n\n## 一、总览\n\n")
        f.write("| 阶段 | 会话数 | Verbatim 总数 | 平均/session |\n")
        f.write("|------|--------|---------------|-------------|\n")
        for phase in phases:
            total = phase_total[phase]
            n_sessions = len(phase_session_set[phase])
            f.write(f"| {phase} | {n_sessions} | {total} | {total/n_sessions:.1f} |\n")
        
        f.write("\n---\n\n## 二、分类统计\n\n")
        f.write("| 类别 | 升级前 | 升级中 | 升级后 | 总计 |\n")
        f.write("|------|--------|--------|--------|------|\n")
        
        ordered_cats = ["指出错误/纠偏", "业务纠偏/方向校准", "方法探讨/理论讨论", 
                       "业务解释/知识传授", "肯定/认可", "例行程序/方向指令",
                       "系统/工具操作", "闲聊/其他", "未分类"]
        
        for cat in ordered_cats:
            row = [cat]
            for phase in phases:
                row.append(str(phase_cat_count[phase].get(cat, 0)))
            row.append(str(sum(phase_cat_count[p].get(cat, 0) for p in phases)))
            f.write(f"| {' | '.join(row)} |\n")
        
        total_all = sum(phase_total.values())
        f.write(f"| **总计** | **{phase_total[phases[0]]}** | **{phase_total[phases[1]]}** | **{phase_total[phases[2]]}** | **{total_all}** |\n")
        
        f.write("\n---\n\n## 三、关键指标：纠偏密度\n\n")
        
        n_pre = len(phase_session_set[phases[0]])
        n_post = len(phase_session_set[phases[2]])
        
        corr_pre = phase_cat_count[phases[0]].get("指出错误/纠偏", 0) + phase_cat_count[phases[0]].get("业务纠偏/方向校准", 0)
        corr_post = phase_cat_count[phases[2]].get("指出错误/纠偏", 0) + phase_cat_count[phases[2]].get("业务纠偏/方向校准", 0)
        
        f.write("| 指标 | 升级前 | 升级后 | 变化 |\n")
        f.write("|------|--------|--------|------|\n")
        f.write(f"| 指出错误 | {phase_cat_count[phases[0]].get('指出错误/纠偏', 0)} | {phase_cat_count[phases[2]].get('指出错误/纠偏', 0)} | {(phase_cat_count[phases[2]].get('指出错误/纠偏', 0) / n_post):.1f}/session vs {(phase_cat_count[phases[0]].get('指出错误/纠偏', 0) / n_pre):.1f}/session |\n")
        f.write(f"| 业务纠偏 | {phase_cat_count[phases[0]].get('业务纠偏/方向校准', 0)} | {phase_cat_count[phases[2]].get('业务纠偏/方向校准', 0)} | {(phase_cat_count[phases[2]].get('业务纠偏/方向校准', 0) / n_post):.1f}/session vs {(phase_cat_count[phases[0]].get('业务纠偏/方向校准', 0) / n_pre):.1f}/session |\n")
        f.write(f"| **纠偏合计** | **{corr_pre}** | **{corr_post}** | **{corr_pre/n_pre:.1f}/session → {corr_post/n_post:.1f}/session ({(corr_post/n_post)/(corr_pre/n_pre)*100-100:+.0f}%)** |\n")
        
        # ===== 完整纠偏类列表 =====
        f.write("\n---\n\n## 四、升级前 · 指出错误/纠偏（全部 33 条）\n\n")
        for e in phase_entries[phases[0]].get("指出错误/纠偏", []):
            f.write(f"- [#{e['session']}] {e['text']}\n")
        
        f.write("\n---\n\n## 五、升级前 · 业务纠偏/方向校准（全部 14 条）\n\n")
        for e in phase_entries[phases[0]].get("业务纠偏/方向校准", []):
            f.write(f"- [#{e['session']}] {e['text']}\n")
        
        f.write("\n---\n\n## 六、升级后 · 指出错误/纠偏（全部 11 条）\n\n")
        for e in phase_entries[phases[2]].get("指出错误/纠偏", []):
            f.write(f"- [#{e['session']}] {e['text']}\n")
        
        f.write("\n---\n\n## 七、升级后 · 业务纠偏/方向校准（全部 6 条）\n\n")
        for e in phase_entries[phases[2]].get("业务纠偏/方向校准", []):
            f.write(f"- [#{e['session']}] {e['text']}\n")
        
        # ===== 补充统计：升级后纠偏类按会话分布 =====
        f.write("\n---\n\n## 八、升级后纠偏类按会话分布\n\n")
        post_corr_by_session = defaultdict(list)
        for e in phase_entries[phases[2]].get("指出错误/纠偏", []):
            post_corr_by_session[e['session']].append(('指出错误', e['text']))
        for e in phase_entries[phases[2]].get("业务纠偏/方向校准", []):
            post_corr_by_session[e['session']].append(('业务纠偏', e['text']))
        
        for sess in sorted(post_corr_by_session.keys()):
            items = post_corr_by_session[sess]
            f.write(f"### #{sess}（{len(items)} 条）\n\n")
            for cat, text in items:
                f.write(f"- [{cat}] {text}\n")
            f.write("\n")
        
        f.write("\n---\n\n## 附：分类方法\n\n")
        f.write("基于关键词匹配自动分类。分类优先级从上到下递减。\n")
        f.write("> ⚠️ 自动分类可能漏掉不含关键词的隐含纠偏（如讽刺、反问等）。建议抽检。\n")
    
    print(f"v2 分析完成。输出: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
