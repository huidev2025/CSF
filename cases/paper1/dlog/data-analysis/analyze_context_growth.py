"""
维度3: 上下文文件增长率分析
追踪 context.md 行数随会话编号的变化
"""
import os
import re
from collections import OrderedDict

OUTPUT = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_context_growth_analysis.md"

# ===== Context.md 快照来源 =====
# 手动收集各时间点的 context.md 文件路径，带时间/会话标记
SNAPSHOTS = [
    # (标签, 路径, 大约会话)
    ("SP-瘦身前 (约#136)", r"d:\huiDev\bang\bang-v3\plan\archive\2026-05-19-pre-workflow-refactor\CONTEXT.md", 136),
    ("SP-瘦身后 (约#141)", r"d:\huiDev\bang\bang-v3\plan\archive\2026-05-19-pre-context-refactor\CONTEXT.md", 141),
    ("升级前 (约#214, 旧体系末期)", r"d:\huiDev\bang\bang-v3\plan\CONTEXT.md", 214),
    ("CSF迁移初期 (约#256)", r"d:\huiDev\bang\bang-v3\plan-csf-v2\csf-iteration\Owner-notes\CSF-v2 备份 256\context.md", 256),
    ("升级后 (约#391, 当前)", r"d:\huiDev\bang\bang-v3\plan-csf-v2\context.md", 391),
]

def count_lines(filepath):
    """统计文件行数（排除空行）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [l for l in f.readlines() if l.strip()]
        return len(lines)
    except FileNotFoundError:
        return None

def count_sections(filepath):
    """统计章节数（## 开头的行）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return len(re.findall(r'^## ', content, re.MULTILINE))
    except FileNotFoundError:
        return None

def count_frontmatter_lines(filepath):
    """统计 frontmatter 行数（--- 之间的内容）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        m = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if m:
            return len([l for l in m.group(1).split('\n') if l.strip()])
        return 0
    except FileNotFoundError:
        return None

def main():
    results = []
    for label, path, session in SNAPSHOTS:
        lines = count_lines(path)
        sections = count_sections(path)
        fm_lines = count_frontmatter_lines(path)
        if lines is not None:
            results.append({
                'label': label,
                'session': session,
                'lines': lines,
                'sections': sections,
                'fm_lines': fm_lines,
                'path': path
            })
            print(f"[{label}] 行数: {lines}, 章节: {sections}, frontmatter: {fm_lines}")
        else:
            print(f"[{label}] 文件未找到: {path}")
    
    if not results:
        print("无有效快照")
        return
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write("# 上下文文件（context.md）增长率分析\n\n")
        f.write(f"方法：收集项目文件中不同时间点的 context.md 快照，统计非空行数\n\n")
        
        f.write("---\n\n## 一、快照数据\n\n")
        f.write("| 时间点 | 约会话 | 非空行数 | 章节数 | Frontmatter | 说明 |\n")
        f.write("|--------|--------|----------|--------|-------------|------|\n")
        
        for r in results:
            f.write(f"| {r['label']} | #{r['session']} | {r['lines']} | {r['sections']} | {r['fm_lines']} | `{r['path'].split(chr(92))[-1]}` |\n")
        
        # 计算增长率
        if len(results) >= 2:
            f.write("\n---\n\n## 二、增长分析\n\n")
            first = results[0]
            last = results[-1]
            pre_upgrade = [r for r in results if r['session'] <= 214]
            post_upgrade = [r for r in results if r['session'] >= 252]
            
            if pre_upgrade:
                pre_first = pre_upgrade[0]
                pre_last = pre_upgrade[-1]
                pre_sessions = pre_last['session'] - pre_first['session']
                pre_growth = pre_last['lines'] - pre_first['lines']
                pre_rate = pre_growth / pre_sessions if pre_sessions > 0 else 0
                f.write(f"**升级前**（#{pre_first['session']}→#{pre_last['session']}，{pre_sessions} 会话）：\n")
                f.write(f"- 行数：{pre_first['lines']} → {pre_last['lines']}（+{pre_growth}，平均 +{pre_rate:.1f} 行/会话）\n\n")
            
            if post_upgrade:
                post_first = post_upgrade[0]
                post_last = post_upgrade[-1]
                post_sessions = post_last['session'] - post_first['session']
                post_growth = post_last['lines'] - post_first['lines']
                post_rate = post_growth / post_sessions if post_sessions > 0 else 0
                f.write(f"**升级后**（#{post_first['session']}→#{post_last['session']}，{post_sessions} 会话）：\n")
                f.write(f"- 行数：{post_first['lines']} → {post_last['lines']}（{post_growth:+d}，平均 {post_rate:+.1f} 行/会话）\n\n")
            
            if pre_upgrade and post_upgrade:
                f.write(f"**对比**：升级前每会话增长 +{pre_rate:.1f} 行，升级后每会话增长 {post_rate:+.1f} 行\n")
                if pre_rate > 0 and post_rate <= 0:
                    f.write(f"\n✅ **基线-Log 分离使上下文文件从持续膨胀转为稳定（甚至缩减）。**\n")
        
        f.write("\n---\n\n## 三、Mermaid 时序图\n\n")
        f.write("```mermaid\n")
        f.write("gantt\n")
        f.write("    title context.md 非空行数变化\n")
        f.write("    dateFormat X\n")
        f.write("    axisFormat %s 会话\n")
        f.write("\n")
        for r in results:
            f.write(f"    section 行数\n")
            f.write(f"    {r['label']} :milestone, {r['session']}, 0\n")
        f.write("```\n\n")
        
        f.write("---\n\n## 四、方法说明\n\n")
        f.write("- 快照来源：项目文件中不同时间点保存的 context.md 副本\n")
        f.write("- 行数统计：排除空行后的有效内容行数\n")
        f.write("- 章节数：`## ` 开头的二级标题数量\n")
        f.write("- 局限：快照时间点有限（5个），无法捕捉连续变化；升级后的快照仅2个（#256和#391）\n")
        f.write("- 建议：如需更细粒度的数据，可从 git 历史或会话记录中的文件内容引用中提取更多快照\n")
    
    print(f"\n分析完成。输出: {OUTPUT}")

if __name__ == "__main__":
    main()
