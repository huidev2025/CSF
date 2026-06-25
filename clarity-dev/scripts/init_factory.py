"""
Clarity 出厂初始化脚本。

用法：python scripts/init_factory.py

完成三件事：
1. 注入哨兵 — cos-context.md 添加 @SECTION/@TEMPLATE 标记
2. 创建出厂数据库 — 默认场景模板 + 出厂提示词 + 出厂基线
3. 建立目录结构 — csf-clarity/backups/prompts/templates + staging/

幂等：重复运行安全（哨兵已有的段不重复包裹，DB用IF NOT EXISTS）。
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# 确定路径
SCRIPT_DIR = Path(__file__).resolve().parent
CLARITY_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = CLARITY_DIR.parent  # 各种尝试/
CSF_LITE = PROJECT_ROOT / "csf-lite"
CSF_CLARITY = PROJECT_ROOT / "csf-clarity"

# 确保 clarity-app/src 在 sys.path
sys.path.insert(0, str(CLARITY_DIR))


# ============================================================
# Part 1: 哨兵注入
# ============================================================

def inject_sentinels():
    """为 cos-context.md 注入两层哨兵标记。"""
    context_path = CSF_LITE / "cos-context.md"
    text = context_path.read_text(encoding="utf-8")

    # 已有哨兵则跳过
    if "<!-- @SECTION:A -->" in text:
        print("[SKIP] cos-context.md 已有哨兵，跳过注入")
        return

    # 按 ## §X 标题切分
    # 我们精确知道各段的起止边界
    sections = {
        "A": {"start": "## §A 项目背景与角色", "end": "\n---\n\n## §B 任务窗口"},
        "B": {"start": "## §B 任务窗口", "end": "\n---\n\n## §C 上次会话"},
        "C": {"start": "## §C 上次会话", "end": "\n---\n\n## §D 下次会话"},
        "D": {"start": "## §D 下次会话", "end": "\n---\n\n## §收件箱"},
        "INBOX": {"start": "## §收件箱", "end": None},  # 文件末尾
    }

    result_parts = []
    cursor = 0

    for sec_id in ["A", "B", "C", "D", "INBOX"]:
        info = sections[sec_id]
        start_pos = text.index(info["start"])
        # 段前内容
        result_parts.append(text[cursor:start_pos])

        if info["end"] is None:
            # 最后一段：到文件末尾
            sec_content = text[start_pos:]
        else:
            end_pos = text.index(info["end"], start_pos)
            sec_content = text[start_pos:end_pos]

        # 段内注入 @TEMPLATE
        sec_with_template = inject_template_markers(sec_id, sec_content)

        # 外层包裹 @SECTION
        wrapped = f"<!-- @SECTION:{sec_id} -->\n{sec_with_template}\n<!-- @/SECTION:{sec_id} -->"
        result_parts.append(wrapped)

        if info["end"] is not None:
            cursor = start_pos + len(sec_content)
        else:
            cursor = len(text)

    context_path.write_text("".join(result_parts), encoding="utf-8")
    print("[OK] cos-context.md 哨兵注入完成")


def inject_template_markers(section_id: str, content: str) -> str:
    """为单个段注入 @TEMPLATE:FIXED / @TEMPLATE:PROJECT 标记。

    规则：
    - §A：加载链+引擎机构+触发索引+红线 = FIXED；
           项目与团队（项目名占位）+工作区布局 = PROJECT
    - §B：各段编写规范+任务窗口说明 = FIXED；全景图/红点/三元组/进度 = PROJECT
    - §C/§D/INBOX：全部 PROJECT（会话特定内容）
    """
    # 找到段标题行之后的内容
    lines = content.split("\n")

    if section_id == "A":
        return inject_section_a(lines)
    elif section_id == "B":
        return inject_section_b(lines)
    else:
        # §C/§D/INBOX：整段视为 PROJECT
        return f"<!-- @TEMPLATE:PROJECT -->\n{content}\n<!-- @/TEMPLATE:PROJECT -->"


def inject_section_a(lines: list[str]) -> str:
    """§A：大部分FIXED，项目名/描述和工作区布局为PROJECT。"""
    # 简化策略：§A几乎全是框架骨架，仅项目描述和布局为PROJECT
    # FIXED 从开头到"### 工作区布局"之前
    text = "\n".join(lines)

    # 找到工作区布局的起止位置，把它包为 PROJECT
    layout_start = text.index("### 工作区布局")
    # 工作区布局后面是"### 加载链"
    loading_start = text.index("### 加载链")

    before_layout = text[:layout_start]
    layout_section = text[layout_start:loading_start]
    after_layout = text[loading_start:]

    result = (
        f"<!-- @TEMPLATE:FIXED -->\n{before_layout}\n<!-- @/TEMPLATE:FIXED -->\n\n"
        f"<!-- @TEMPLATE:PROJECT -->\n{layout_section}\n<!-- @/TEMPLATE:PROJECT -->\n\n"
        f"<!-- @TEMPLATE:FIXED -->\n{after_layout}\n<!-- @/TEMPLATE:FIXED -->"
    )
    return result


def inject_section_b(lines: list[str]) -> str:
    """§B：编写规范为FIXED，其余为PROJECT。"""
    text = "\n".join(lines)

    # "### §B 各段编写规范" 是永驻FIXED结构
    fixed_start = text.index("### §B 各段编写规范")
    # FIXED 结束于 "### 定位" 之前
    project_start = text.index("### 定位", fixed_start)

    header = text[:fixed_start]
    fixed_content = text[fixed_start:project_start]
    project_content = text[project_start:]

    result = (
        f"{header}\n"
        f"<!-- @TEMPLATE:FIXED -->\n{fixed_content}\n<!-- @/TEMPLATE:FIXED -->\n\n"
        f"<!-- @TEMPLATE:PROJECT -->\n{project_content}\n<!-- @/TEMPLATE:PROJECT -->"
    )
    return result


# ============================================================
# Part 2: 出厂数据库
# ============================================================

def init_factory_database():
    """创建出厂数据库：默认场景模板 + 出厂提示词 + 出厂基线。"""
    from src.data.backup_db import BackupDB
    from src.data.template_store import TemplateStore
    from src.data.prompt_store import PromptStore
    from src.config import DB_PATH, TEMPLATES_DIR, PROMPTS_DIR

    # 确保目录存在
    CSF_CLARITY.mkdir(parents=True, exist_ok=True)
    (CSF_CLARITY / "backups").mkdir(exist_ok=True)
    (CSF_CLARITY / "templates").mkdir(exist_ok=True)
    (CSF_CLARITY / "prompts").mkdir(exist_ok=True)
    (CSF_LITE / "staging").mkdir(exist_ok=True)

    db = BackupDB(str(DB_PATH))
    db.init_db()

    tstore = TemplateStore(db, str(TEMPLATES_DIR))
    pstore = PromptStore(db, str(PROMPTS_DIR))

    # -- 默认场景模板 --
    existing = tstore.list_templates()
    if existing:
        print(f"[SKIP] 已有 {len(existing)} 个场景模板，跳过")
    else:
        tid = tstore.create_template("软件开发", "CSF标准软件开发模板：含FLDD规程、开发者通道、收件箱")
        for i, (sid, active, order, default_content) in enumerate([
            ("A", True, 0, None),
            ("B", True, 1, None),
            ("C", True, 2, None),
            ("D", True, 3, None),
            ("INBOX", True, 4, None),
        ]):
            tstore.upsert_section(tid, sid, active, order, default_content)
        print("[OK] 默认场景模板「软件开发」创建完成（5段）")

    # -- 出厂提示词 --
    factory_prompts = [
        # 开局
        ("标准开局", "开局", "适用于大多数会话的标准开局措辞", "阅读 cos-context，开局。"),
        ("聚焦式开局", "开局", "指定聚焦点的开局", "阅读 cos-context，聚焦在 ${聚焦点}。开局。"),
        # 收尾
        ("标准收尾", "收尾", "会话结束的标准收尾", "收尾。"),
        ("快速收尾", "收尾", "跳过后置验证的快速收尾", "88"),
        # 立项
        ("快速立项", "立项", "适用于小型任务的立项措辞", "为 ${任务名} 建立一个 TP。"),
        # 修复
        ("Bug修复", "修复", "Bug修复流程启动", "阅读 cos-context，这是一个 Bug 修复任务。Bug 描述：${描述}。"),
        # 复盘
        ("会话复盘", "复盘", "会话结束后复盘", "复盘本次会话。"),
    ]

    created = 0
    for title, category, desc, content in factory_prompts:
        existing_prompts = pstore.list_by_category(category)
        if not any(p["title"] == title for p in existing_prompts):
            pstore.create_prompt(title, category, desc, content)
            created += 1

    if created > 0:
        print(f"[OK] 出厂提示词创建完成（{created} 条）")
    else:
        print("[SKIP] 出厂提示词已存在")

    # -- 出厂基线 --
    # 对 cos-context.md 做一次出厂备份
    from src.core.sentinel_parser import SentinelParser
    from src.core.file_system_ops import FileSystemOps
    from src.core.backup_engine import BackupEngine
    from src.config import CSF_LITE_ROOT, STAGING_DIR

    fops = FileSystemOps(str(CSF_LITE), str(STAGING_DIR))
    parser = SentinelParser()
    engine = BackupEngine(db, fops, parser, str(CSF_CLARITY / "backups"), str(CSF_LITE))

    # 检查是否已有出厂基线
    try:
        engine.restore_baseline("v1-出厂基线")
        print("[SKIP] 出厂基线已存在")
    except Exception:
        try:
            # 备份 cos-context.md 的所有段
            doc = parser.parse(str(CSF_LITE / "cos-context.md"))
            for section in doc.sections:
                engine.backup_section(section.id, section.raw_content, "出厂版本")

            # 备份 core/ 核心文件
            for f in (CSF_LITE / "core").glob("*.md"):
                rel = str(f.relative_to(CSF_LITE)).replace("\\", "/")
                content = f.read_text(encoding="utf-8")
                engine.backup_file(rel, content, "出厂版本")

            # 创建基线
            engine.create_baseline("v1-出厂基线", "Clarity CSF Lite 出厂默认状态")
            print("[OK] 出厂基线「v1-出厂基线」创建完成")
        except Exception as e:
            print(f"[WARN] 出厂基线创建失败: {e}")


# ============================================================
# Main
# ============================================================

def main():
    print("=== Clarity 出厂初始化 ===\n")

    # 1. 哨兵注入
    print("[1/2] 哨兵注入...")
    inject_sentinels()
    print()

    # 2. 出厂数据库
    print("[2/2] 出厂数据库...")
    init_factory_database()
    print()

    print("=== 初始化完成 ===")
    print(f"  cos-context.md  → 哨兵就位")
    print(f"  场景模板        → 软件开发（5段）")
    print(f"  出厂提示词      → 7条（5场景）")
    print(f"  出厂基线        → v1-出厂基线")
    print(f"  csf-clarity/    → 目录结构就位")
    print()


if __name__ == "__main__":
    main()
