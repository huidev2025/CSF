"""
维度2: 会话启动成本分析
统计每个会话启动时 AI Read 的文件数量，对比升级前后
"""
import re
import os
from collections import defaultdict

LOG_DIR = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_dlog_各阶段的尝试记录\01-Github copilot 帮找v3 csf v2的诞生"
OUTPUT = r"D:\OneDrive\Research & Notes\ObsidianNotes\_Projects\_02_CSF\_paper_1_索引病和语义空间管理\dlog\_startup_cost_analysis.md"

PRE_END = 214
TRANS_END = 252

def get_phase(session):
    if session <= PRE_END:
        return "升级前"
    elif session <= TRANS_END:
        return "升级中"
    else:
        return "升级后"

def count_startup_reads(filepath):
    """统计会话启动时的 Read 操作数"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 找到第一个 User: 行
    first_user_idx = None
    for i, line in enumerate(lines):
        if line.startswith('User: '):
            first_user_idx = i
            break
    
    if first_user_idx is None:
        return 0, 0
    
    # 找到第一个 User: 之后的 GitHub Copilot: 响应块
    # 统计该块中的 Read [ 操作数
    read_count = 0
    search_count = 0
    in_response = False
    for i in range(first_user_idx + 1, min(first_user_idx + 500, len(lines))):
        line = lines[i]
        if line.startswith('User: '):
            break  # 下一个 User: 出现，启动块结束
        if line.startswith('GitHub Copilot:'):
            in_response = True
            continue
        if in_response:
            if line.strip().startswith('Read ['):
                read_count += 1
            elif line.strip().startswith('Searched '):
                search_count += 1
    
    return read_count, search_count

def main():
    results = []
    for fname in sorted(os.listdir(LOG_DIR)):
        if not fname.startswith('_dlog_') or not fname.endswith('.md'):
            continue
        m = re.search(r'_dlog_(\d+)', fname)
        if not m:
            continue
        session = int(m.group(1))
        filepath = os.path.join(LOG_DIR, fname)
        read_count, search_count = count_startup_reads(filepath)
        phase = get_phase(session)
        results.append({
            'session': session,
            'phase': phase,
            'reads': read_count,
            'searches': search_count,
            'total_ops': read_count + search_count
        })
    
    # 按阶段统计
    phase_stats = defaultdict(lambda: {'sessions': [], 'reads': [], 'total': []})
    for r in results:
        phase_stats[r['phase']]['sessions'].append(r['session'])
        phase_stats[r['phase']]['reads'].append(r['reads'])
        phase_stats[r['phase']]['total'].append(r['total_ops'])
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write("# 会话启动成本分析\n\n")
        f.write(f"数据源：{len(results)} 个会话记录文件\n")
        f.write("方法：统计每个会话首次 `User:` 输入后 AI 响应块中的 `Read [` 和 `Searched ` 操作数\n\n")
        
        f.write("---\n\n## 一、按阶段汇总\n\n")
        f.write("| 阶段 | 会话数 | 平均启动 Read | 平均启动 Search | 平均启动总操作 | 中位数 Read | 范围 Read |\n")
        f.write("|------|--------|---------------|-----------------|---------------|-------------|----------|\n")
        
        for phase in ["升级前", "升级中", "升级后"]:
            stats = phase_stats[phase]
            if not stats['reads']:
                continue
            avg_read = sum(stats['reads']) / len(stats['reads'])
            avg_search = sum(stats.get('searches', [0]*len(stats['reads']))) / len(stats['reads']) if 'searches' in stats else 0
            avg_total = sum(stats['total']) / len(stats['total'])
            med_read = sorted(stats['reads'])[len(stats['reads'])//2]
            min_read = min(stats['reads'])
            max_read = max(stats['reads'])
            f.write(f"| {phase} | {len(stats['sessions'])} | {avg_read:.1f} | {avg_search:.1f} | {avg_total:.1f} | {med_read} | {min_read}–{max_read} |\n")
        
        f.write("\n---\n\n## 二、关键对比：升级前 vs 升级后\n\n")
        
        pre_reads = phase_stats["升级前"]['reads']
        post_reads = phase_stats["升级后"]['reads']
        pre_avg = sum(pre_reads) / len(pre_reads) if pre_reads else 0
        post_avg = sum(post_reads) / len(post_reads) if post_reads else 0
        change = (post_avg - pre_avg) / pre_avg * 100 if pre_avg > 0 else 0
        
        f.write(f"| 指标 | 升级前 | 升级后 | 变化 |\n")
        f.write(f"|------|--------|--------|------|\n")
        f.write(f"| 平均启动 Read 操作 | {pre_avg:.1f} | {post_avg:.1f} | {change:+.0f}% |\n")
        
        pre_total = sum(phase_stats["升级前"]['total']) / len(phase_stats["升级前"]['total']) if phase_stats["升级前"]['total'] else 0
        post_total = sum(phase_stats["升级后"]['total']) / len(phase_stats["升级后"]['total']) if phase_stats["升级后"]['total'] else 0
        total_change = (post_total - pre_total) / pre_total * 100 if pre_total > 0 else 0
        f.write(f"| 平均启动总操作 | {pre_total:.1f} | {post_total:.1f} | {total_change:+.0f}% |\n")
        
        f.write("\n---\n\n## 三、逐会话数据\n\n")
        f.write("| 会话 | 阶段 | Read数 | Search数 |\n")
        f.write("|------|------|--------|----------|\n")
        for r in sorted(results, key=lambda x: x['session']):
            f.write(f"| #{r['session']} | {r['phase']} | {r['reads']} | {r['searches']} |\n")
        
        f.write("\n---\n\n## 四、方法说明\n\n")
        f.write("- 每个会话文件以第一个 `User: ` 行作为会话起点\n")
        f.write("- 统计该起点后、下一个 `User: ` 出现前的所有 `Read [` 和 `Searched ` 操作\n")
        f.write("- 这近似于 AI 在'开局'阶段为重建语境而读取的文件数\n")
        f.write("- 局限：部分会话可能有多个轮次，本分析仅统计首轮启动操作\n")
    
    print(f"分析完成。输出: {OUTPUT}")
    print(f"升级前平均启动Read: {pre_avg:.1f}")
    print(f"升级后平均启动Read: {post_avg:.1f}")
    print(f"变化: {change:+.0f}%")

if __name__ == "__main__":
    main()
