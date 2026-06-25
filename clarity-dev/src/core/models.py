# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
Core Layer 数据模型 — V2。

定义 Clarity V2 核心层共用的数据结构：
- TemplateBlock: 段内模板块（FIXED/PROJECT）         [DT-03]
- Section: context 文档的一个段                       [DT-03]
- ContextDoc: 完整的 context 文档模型                 [DT-03]
- TreeNode: 文件系统树节点                            [DT-04]
- VersionMeta: 版本元数据（无 id，纯文件驱动）         [DT-05]
- SectionFile: 段文件模型（@SEC:CONTENT / @SEC:NOTES） [DT-06]
- StagingOp / StagingDoc: staging 操作模型            [DT-07]
- Template / TemplateSectionRef: 模板模型             [DT-08]
- Prompt: 提示词模型 v3（极简，无版本管理）            [IT-13a]
- SectionData: 标签2 v6 在役段数据                   [STB-1 DT-01.1]
- VersionEntry: 标签2 v6 版本条目                     [STB-1 DT-01.2]
- DraftChange: 标签2 v6 单条草稿变更                  [STB-1 DT-01.3]
- DraftState: 标签2 v6 草稿状态容器                   [STB-1 DT-01.4]
- TemplateData: 标签2 v6 模板数据                     [STB-1 DT-01.5]
"""

from dataclasses import dataclass, field
from typing import Optional


# ── DT-03 ───────────────────────────────────────────────────

@dataclass
class TemplateBlock:
    """段内模板块 — 区分框架固定内容与项目可变内容。

    Attributes:
        type: 'FIXED'（CSF 框架骨架，模板切换时保留）
              或 'PROJECT'（项目相关，模板切换时替换）
        content: 块的完整文本内容（含原始 Markdown）
    """
    type: str          # 'FIXED' | 'PROJECT'
    content: str


@dataclass
class Section:
    """context 文档的一个段。

    Attributes:
        id: 段标识符，对应 @SECTION:X 的 X（如 'A', 'B', 'C', 'D', 'INBOX'）
        title: 段标题（如 '项目背景与角色'）
        fixed_blocks: 框架固定内容块列表（模板切换时保留）
        project_blocks: 项目可变内容块列表（模板切换时替换）
        raw_content: 段的完整原始文本（含哨兵标记）
        is_active: 段是否激活（False 表示已移出）
    """
    id: str
    title: str
    fixed_blocks: list[TemplateBlock] = field(default_factory=list)
    project_blocks: list[TemplateBlock] = field(default_factory=list)
    raw_content: str = ""
    is_active: bool = True


@dataclass
class ContextDoc:
    """完整的 context 文档模型。

    Attributes:
        sections: 所有段的列表（按文档出现顺序）
        template_name: 当前使用的场景模板名称（None 表示无模板）
    """
    sections: list[Section] = field(default_factory=list)
    template_name: Optional[str] = None


# ── DT-04 ───────────────────────────────────────────────────

@dataclass
class TreeNode:
    """文件系统树节点。

    Attributes:
        name: 文件/目录名
        path: 相对于 csf-lite 根目录的完整路径
        is_dir: 是否为目录
        children: 子节点列表（仅目录有）
        is_factory: 是否为出厂文件（不可删除）
        description: 文件说明（标签3 文件说明区使用）  ← V2 新增
    """
    name: str
    path: str
    is_dir: bool
    children: list['TreeNode'] = field(default_factory=list)
    is_factory: bool = False
    description: Optional[str] = None  # V2 新增


# ── DT-05 ───────────────────────────────────────────────────

@dataclass
class VersionMeta:
    """版本元数据 — V2 纯文件驱动，无数据库 id。

    V1→V2 关键差异：去掉 id 字段，版本号从文件名提取。

    Attributes:
        target_type: 'section' | 'file'
        target_id: 段名（如 'B'）/ 文件路径
        version: 版本号（从文件名提取，如 .v3.md → 3）
        storage_path: 备份/快照文件存储路径
        ⚠️ note字段已废除（v4），统一使用description
        description: 版本说明（v3 新增，比备注更丰富）
        created_at: ISO 8601 创建时间
        baselines: 该版本参与过的基线名称列表
        content: 版本内容全文（可选，按需加载）
    """
    target_type: str              # 'section' | 'file'
    target_id: str                # 段名 / 文件路径
    version: int                  # 从文件名提取
    storage_path: str
    created_at: str
    description: Optional[str] = None   # v4: note已废除，description为唯一说明字段
    baselines: list[str] = field(default_factory=list)
    content: Optional[str] = None


# ── DT-06 ───────────────────────────────────────────────────

@dataclass
class SectionFile:
    """段文件模型 — 对应 @SEC:CONTENT 和 @SEC:NOTES 分区。

    Attributes:
        name: 段文件名（如 '项目背景与角色.md'）
        content: @SEC:CONTENT 区的实际内容
        notes: @SEC:NOTES 区的版本注释
        version: 段文件关联的版本元数据（当前版本）
    """
    name: str
    content: str
    notes: str
    version: Optional[VersionMeta] = None


# ── DT-07 ───────────────────────────────────────────────────

@dataclass
class StagingOp:
    """staging 单条操作指令 — v3。

    Attributes:
        op: 操作类型 — 'change_version' | 'deactivate' | 'activate' | 'change_template' | 'reorder'
        target: 操作目标（段名 / 模板名）
        position: 插入位置（可选，activate 时用）
        adapt: 是否自适应（默认 False）
        content: 操作附带内容（change_version/activate/change_template 时为段/模板内容）
        template: change_template 操作的目标模板名（v3 新增）
        sequence: reorder 操作的段顺序列表（v3 新增，如 '§C, §B, §A, §D'）
    """
    op: str  # 'change_version' | 'deactivate' | 'activate' | 'change_template' | 'reorder'
    target: str  # 段名 / 模板名
    position: Optional[str] = None
    adapt: bool = False
    content: Optional[str] = None
    template: Optional[str] = None  # v3: change_template 操作的目标模板名
    sequence: Optional[str] = None  # v3: reorder 操作的段顺序列表


@dataclass
class StagingDoc:
    """staging 文档 — pending.md 的完整模型。

    Attributes:
        status: 'pending' | 'processing'（三态生命周期，完成后删除文件）
        ops: 操作指令列表
    """
    status: str  # 'pending' | 'processing'
    ops: list[StagingOp] = field(default_factory=list)


# ── DT-08 ───────────────────────────────────────────────────

@dataclass
class TemplateSectionRef:
    """模板中的段引用 — 模板不拥有段，只是引用集合。

    Attributes:
        section_name: 段文件名
        version: 引用的段版本号
        order: 在 context 中的排列顺序
        is_active: 该段在模板中是否激活
    """
    section_name: str
    version: int
    order: int
    is_active: bool = True


@dataclass
class Template:
    """模板模型 — 段版本引用的集合。

    Attributes:
        name: 模板名称（如 '默认开发模板'）
        description: 模板用途说明
        sections: 段引用列表
    """
    name: str
    description: str
    sections: list[TemplateSectionRef] = field(default_factory=list)


# ── DT-09 / IT-13a ──────────────────────────────────────────

@dataclass
class Prompt:
    """提示词模型 v3 — 极简：一个 .md 文件 = 一条提示词。

    v2→v3 关键差异：去掉 category（分组由目录决定）、去掉 versions（无版本管理）。
    新增 created_at（ISO 8601 时间戳）。

    Attributes:
        description: 提示词说明（导航区显示此字段）
        content: 提示词正文（Markdown）
        created_at: ISO 8601 创建时间戳
    """
    description: str
    content: str
    created_at: str


# ── STB-1 DT-01.1~01.5: 标签2 v6 数据模型 ──────────────────

@dataclass
class SectionData:
    """标签2 v6 — cos-context.md中的一个在役段。

    Attributes:
        title: 段标题（如"§B 任务窗口"）
        section_id: 段标识符（如"B"），来自@SECTION哨兵
        source_version: @SOURCE哨兵值（如9），无哨兵则为None
        content: 段正文（含Markdown标记，去掉了哨兵行但保留内部@TEMPLATE块）
        description: 来自section_meta.json的说明文本
        order: 在context中的出现序号（1-based）
    """
    title: str
    section_id: str
    source_version: Optional[int] = None
    content: str = ""
    description: str = ""
    order: int = 0


@dataclass
class VersionEntry:
    """标签2 v6 — 段库中的一个版本条目。

    Attributes:
        section_title: 段标题（如"§B 任务窗口"）
        version: 版本号（从文件名提取，如.v3.md→3）
        description: YAML frontmatter中的description字段
        created_at: ISO 8601创建时间
        file_path: 版本文件路径（sections/.versions/{段名}.v{N}.md）
        baselines: 引用此版本的模板名列表
    """
    section_title: str
    version: int
    description: str = ""
    created_at: str = ""
    file_path: str = ""
    baselines: list[str] = field(default_factory=list)


@dataclass
class DraftChange:
    """标签2 v6 — 单条草稿变更。

    Attributes:
        change_type: 变更类型 — "swap_version" | "remove" | "add" | "reorder"
        section_title: 目标段标题
        to_version: swap_version/add时的目标版本号
        from_version: swap_version时的来源版本号
        new_order: reorder时的段标题顺序列表
    """
    change_type: str  # "swap_version" | "remove" | "add" | "reorder"
    section_title: str
    to_version: Optional[int] = None
    from_version: Optional[int] = None
    new_order: Optional[list[str]] = None


@dataclass
class DraftState:
    """标签2 v6 — 草稿状态容器。

    Attributes:
        baseline_sections: 基线段标题列表（基线时的段顺序）
        baseline_order: 基线段标题→序号映射
        changes: 草稿变更列表（按应用顺序）
        _persist: 可选持久化回调，每次变更后自动调用
    """
    baseline_sections: list[str] = field(default_factory=list)
    baseline_order: dict[str, int] = field(default_factory=dict)
    changes: list[DraftChange] = field(default_factory=list)
    _persist: object = field(default=None, repr=False, compare=False)

    # ── DT-02.1: 变更方法 ──────────────────────────────────

    def is_dirty(self) -> bool:
        """是否有未提交的草稿变更。"""
        return len(self.changes) > 0

    def add_change(self, change: DraftChange) -> None:
        """追加一条草稿变更并即时写盘。

        冲突规则（DT-02.5/02.8）：
        - swap_version：同段同类型已有 → 覆盖（后装载覆盖前装载）
        - remove + add 同段：add 覆盖 remove（撤下后又添加 → 保留add）
        - add + remove 同段：两条抵消 → 都删掉
        - reorder：始终追加，不覆盖（每次重排独立记录）
        """
        # ── 冲突处理 ──
        if change.change_type == 'swap_version':
            # 同段已有 swap_version → 覆盖
            self.changes = [
                c for c in self.changes
                if not (c.change_type == 'swap_version'
                        and c.section_title == change.section_title)
            ]
        elif change.change_type == 'add':
            # 同段已有 remove → 抵消删除
            removed = [
                c for c in self.changes
                if not (c.change_type == 'remove'
                        and c.section_title == change.section_title)
            ]
            if len(removed) < len(self.changes):
                # 有remove被抵消，同时删掉add（不加入）
                self.changes = removed
                self._try_persist()
                return
            # 同段已有 add → 覆盖
            self.changes = [
                c for c in self.changes
                if not (c.change_type == 'add'
                        and c.section_title == change.section_title)
            ]
        elif change.change_type == 'remove':
            # 同段已有 add → 抵消删除
            added = [
                c for c in self.changes
                if not (c.change_type == 'add'
                        and c.section_title == change.section_title)
            ]
            if len(added) < len(self.changes):
                # 有add被抵消，同时删掉remove（不加入）
                self.changes = added
                self._try_persist()
                return
            # 同段已有 remove → 不重复添加
            for c in self.changes:
                if c.change_type == 'remove' and c.section_title == change.section_title:
                    return

        self.changes.append(change)
        self._try_persist()

    def remove_change(self, section_title: str, change_type: str) -> bool:
        """撤回单条变更：按段标题+变更类型删除对应变更并即时写盘。

        Returns: True 如果找到并删除了变更，False 如果未找到。
        """
        for i, c in enumerate(self.changes):
            if c.change_type == change_type and c.section_title == section_title:
                del self.changes[i]
                self._try_persist()
                return True
        return False

    def clear(self) -> None:
        """清空所有草稿变更并即时写盘。"""
        self.changes.clear()
        self._try_persist()

    def _try_persist(self) -> None:
        """如果设置了持久化回调，调用它。"""
        if self._persist is not None and callable(self._persist):
            self._persist()

    # ── DT-02.2: staging 序列化 ─────────────────────────────

    def to_staging_md(self, baseline_sections: list) -> str:
        """将草稿序列化为 staging 指令 Markdown。

        格式（设计§3.3）：
        ## 换版本
        | 段 | 目标版本 |
        |...|...|

        ## 撤下
        - §段名

        ## 添加
        - §段名 v{N}

        ## 重排
        - 新顺序：§A, §B, §C...

        无变更的段不输出。
        """
        from src.core.models import SectionData  # noqa: F811

        lines: list[str] = []

        # 收集各类型变更
        swaps = [c for c in self.changes if c.change_type == 'swap_version']
        removes = [c for c in self.changes if c.change_type == 'remove']
        adds = [c for c in self.changes if c.change_type == 'add']
        reorders = [c for c in self.changes if c.change_type == 'reorder']

        # 换版本
        if swaps:
            lines.append('## 换版本')
            lines.append('| 段 | 目标版本 |')
            lines.append('|---|---|')
            for c in swaps:
                lines.append(f'| {c.section_title} | v{c.to_version} |')
            lines.append('')

        # 撤下
        if removes:
            lines.append('## 撤下')
            for c in removes:
                lines.append(f'- {c.section_title}')
            lines.append('')

        # 添加
        if adds:
            lines.append('## 添加')
            for c in adds:
                lines.append(f'- {c.section_title} v{c.to_version}')
            lines.append('')

        # 重排
        if reorders:
            lines.append('## 重排')
            # 使用最新的 reorder（最后一条）
            latest = reorders[-1]
            if latest.new_order:
                lines.append(f'- {", ".join(latest.new_order)}')
            lines.append('')

        return '\n'.join(lines).strip()


@dataclass
class TemplateData:
    """标签2 v6 — 模板数据。

    Attributes:
        name: 模板名称
        sections: 段引用列表，每项{"title": str, "version": int}
        created_at: ISO 8601创建时间
    """
    name: str
    sections: list[dict] = field(default_factory=list)
    created_at: str = ""
