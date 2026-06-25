# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
SentinelParser V2 — 哨兵解析器。

支持三种文件类型的解析：
- cos-context.md（context 文档）
- csf-clarity/sections/*.md（段文件）
- csf-lite/staging/pending.md（staging 指令）

V2 哨兵体系（9种）：
  @SECTION:X       段边界
  @TEMPLATE:FIXED   框架固定内容
  @TEMPLATE:PROJECT 项目可变内容
  @SEC:CONTENT      段文件内容区
  @SEC:NOTES        段文件笔记区
  @STG:CONTENT      staging 内容嵌入
  @STAGING:N        staging 操作块
  @MSG:N            异步消息块
  @MSG:NEXT:N       消息编号计数器
"""

import re
from pathlib import Path
from typing import Optional

from src.core.models import (
    TemplateBlock, Section, ContextDoc,
    SectionFile, StagingOp, StagingDoc,
    VersionMeta,
)


# ── 正则模式（DT-01, DT-03）─────────────────────────────────

# @SECTION:A / @/SECTION:A
_SECTION_START = re.compile(r'<!--\s*@SECTION:(\w+(?::\w+)?)\s*-->')
_SECTION_END = re.compile(r'<!--\s*@/SECTION:(\w+(?::\w+)?)\s*-->')

# @TEMPLATE:FIXED / @TEMPLATE:PROJECT
_TEMPLATE_START = re.compile(r'<!--\s*@TEMPLATE:(FIXED|PROJECT)\s*-->')
_TEMPLATE_END = re.compile(r'<!--\s*@/TEMPLATE:(FIXED|PROJECT)\s*-->')

# @SEC:CONTENT / @/SEC:CONTENT
_SEC_CONTENT_START = re.compile(r'<!--\s*@SEC:CONTENT\s*-->')
_SEC_CONTENT_END = re.compile(r'<!--\s*@/SEC:CONTENT\s*-->')

# @SEC:NOTES / @/SEC:NOTES
_SEC_NOTES_START = re.compile(r'<!--\s*@SEC:NOTES\s*-->')
_SEC_NOTES_END = re.compile(r'<!--\s*@/SEC:NOTES\s*-->')

# @STG:CONTENT:START / @STG:CONTENT:END
_STG_CONTENT_START = re.compile(r'<!--\s*@STG:CONTENT:START\s*-->')
_STG_CONTENT_END = re.compile(r'<!--\s*@STG:CONTENT:END\s*-->')

# @STAGING:N op="..." target="..." / @/STAGING:N
_STAGING_OP_START = re.compile(
    r'<!--\s*@STAGING:(\d+)\s+op="(\w+)"\s+target="([^"]*)"'
    r'(?:\s+position="([^"]*)")?(?:\s+adapt="([^"]*)")?\s*-->'
)
_STAGING_OP_END = re.compile(r'<!--\s*@/STAGING:(\d+)\s*-->')

# @MSG:N / @/MSG:N
_MSG_START = re.compile(r'<!--\s*@MSG:(\d+)\s*-->')
_MSG_END = re.compile(r'<!--\s*@/MSG:(\d+)\s*-->')

# @MSG:NEXT:N
_MSG_NEXT = re.compile(r'<!--\s*@MSG:NEXT:(\d+)\s*-->')

# 段标题提取
_HEADING = re.compile(r'^#{1,3}\s+(.+)$', re.MULTILINE)


# ── 内部辅助（DT-01）────────────────────────────────────────

def _find_pairs(text: str, start_pattern: re.Pattern,
                end_pattern: re.Pattern) -> list[tuple[int, int, str]]:
    """扫描文本，匹配哨兵对，返回 (内容起始位置, 内容结束位置, 哨兵标识符) 列表。"""
    pairs = []
    open_stack: list[tuple[int, str]] = []  # (start_pos, sentinel_id)

    # 收集所有匹配点
    all_matches: list[tuple[int, bool, str]] = []  # (pos, is_start, id)
    for m in start_pattern.finditer(text):
        all_matches.append((m.start(), True, m.group(1)))
    for m in end_pattern.finditer(text):
        all_matches.append((m.end(), False, m.group(1)))
    all_matches.sort(key=lambda x: x[0])

    for pos, is_start, sid in all_matches:
        if is_start:
            open_stack.append((pos, sid))
        else:
            # 找最近的匹配开哨兵
            for i in range(len(open_stack) - 1, -1, -1):
                if open_stack[i][1] == sid:
                    start_pos, _ = open_stack.pop(i)
                    pairs.append((start_pos, pos, sid))
                    break

    return pairs


def _parse_template_blocks(text: str) -> list[TemplateBlock]:
    """从文本中解析 @TEMPLATE:FIXED/PROJECT 块。"""
    blocks: list[TemplateBlock] = []
    pairs = _find_pairs(text, _TEMPLATE_START, _TEMPLATE_END)

    # 同时需要知道每个块的 type (FIXED/PROJECT)
    type_matches: list[tuple[int, int, str]] = []  # (start, end, type)
    for m in _TEMPLATE_START.finditer(text):
        type_matches.append((m.start(), m.end(), m.group(1)))

    for start_pos, end_pos, sid in pairs:
        # 找到对应的开哨兵 type
        block_type = 'FIXED'  # fallback
        for ts, te, t in type_matches:
            if ts >= start_pos and ts < start_pos + 50:
                block_type = t
                break

        content = text[start_pos:end_pos - len(f'<!-- @/TEMPLATE:{sid} -->')]
        # 去掉开哨兵行
        content_start = content.find('-->') + 3
        if content_start > 2:
            content = content[content_start:]
        blocks.append(TemplateBlock(type=block_type, content=content.strip('\n')))

    return blocks


def _parse_sections(text: str) -> list[Section]:
    """从 context 文本中解析所有 @SECTION 段。"""
    sections: list[Section] = []

    # 找所有 @SECTION 开哨兵位置
    section_starts: list[tuple[int, str]] = []  # (pos, id)
    for m in _SECTION_START.finditer(text):
        section_starts.append((m.start(), m.group(1)))

    # 找所有 @/SECTION 闭哨兵位置
    section_ends: dict[str, list[int]] = {}
    for m in _SECTION_END.finditer(text):
        sid = m.group(1)
        section_ends.setdefault(sid, []).append(m.end())

    for i, (start_pos, sid) in enumerate(section_starts):
        # 找对应的闭哨兵
        end_pos: Optional[int] = None
        if sid in section_ends and section_ends[sid]:
            # 取该 id 的第一个未使用的闭哨兵
            for ep in section_ends[sid]:
                if ep > start_pos:
                    end_pos = ep
                    section_ends[sid].remove(ep)
                    break

        if end_pos is None:
            # 回退：用下一个 @SECTION 的起始作为隐式闭合
            if i + 1 < len(section_starts):
                end_pos = section_starts[i + 1][0]
            else:
                end_pos = len(text)

        # 提取段内容（含哨兵行）
        raw_content = text[start_pos:end_pos]

        # 提取段标题
        title = sid
        heading_match = _HEADING.search(raw_content)
        if heading_match:
            title = heading_match.group(1).strip()

        # 提取内部文本（去掉哨兵行）
        inner_start = raw_content.find('-->') + 3
        inner_end = raw_content.rfind('<!-- @/SECTION')
        if inner_end == -1:
            inner_end = len(raw_content)
        inner = raw_content[inner_start:inner_end].strip('\n')

        # 解析内部的 FIXED/PROJECT 块
        fixed_blocks = _parse_template_blocks(inner)
        project_blocks: list[TemplateBlock] = []
        # 分离 FIXED 和 PROJECT
        actual_fixed: list[TemplateBlock] = []
        for b in fixed_blocks:
            if b.type == 'FIXED':
                actual_fixed.append(b)
            else:
                project_blocks.append(b)

        section = Section(
            id=sid,
            title=title,
            fixed_blocks=actual_fixed,
            project_blocks=project_blocks,
            raw_content=raw_content.strip('\n'),
            is_active=True,
        )
        sections.append(section)

    return sections


# ── 公开 API ────────────────────────────────────────────────

class SentinelParser:
    """V2 哨兵解析器 — 支持 context / 段文件 / staging 三种文件类型。"""

    # ── Context 解析（DT-02）─────────────────────────────────

    def parse_context(self, file_path: str) -> ContextDoc:
        """解析 cos-context.md → ContextDoc。"""
        text = Path(file_path).read_text(encoding='utf-8')
        return self.parse_context_text(text)

    def parse_context_text(self, text: str) -> ContextDoc:
        """从文本解析 context → ContextDoc。"""
        sections = _parse_sections(text)
        return ContextDoc(sections=sections)

    def assemble_context(self, doc: ContextDoc) -> str:
        """将 ContextDoc 序列化回 Markdown 字符串（哨兵对完整保留）。
        跳过 is_active=False 的段。"""
        parts: list[str] = []
        for section in doc.sections:
            if section.is_active:
                parts.append(section.raw_content)
        return '\n\n'.join(parts)

    def get_section(self, doc: ContextDoc, section_id: str) -> Optional[Section]:
        """从 ContextDoc 中获取指定 id 的段。"""
        for s in doc.sections:
            if s.id == section_id:
                return s
        return None

    def replace_section(self, doc: ContextDoc, section_id: str,
                        new_content: str) -> str:
        """替换指定段的内容，返回新的完整 Markdown。"""
        parts: list[str] = []
        for s in doc.sections:
            if s.id == section_id:
                parts.append(new_content)
            else:
                parts.append(s.raw_content)
        return '\n\n'.join(parts)

    # ── 段文件解析（DT-04）───────────────────────────────────

    def parse_section_file(self, file_path: str) -> SectionFile:
        """解析段文件 → SectionFile。"""
        path = Path(file_path)
        name = path.name
        text = path.read_text(encoding='utf-8')

        # 提取 @SEC:CONTENT 区
        content = ''
        cm = _SEC_CONTENT_START.search(text)
        if cm:
            content_start = cm.end()
            cem = _SEC_CONTENT_END.search(text, cm.end())
            if cem:
                content = text[content_start:cem.start()].strip('\n')
            else:
                # 容忍无闭哨兵：取到文本末尾或 @SEC:NOTES
                nm = _SEC_NOTES_START.search(text, cm.end())
                content = text[content_start:nm.start() if nm else len(text)].strip('\n')

        # 提取 @SEC:NOTES 区
        notes = ''
        nm = _SEC_NOTES_START.search(text)
        if nm:
            notes_start = nm.end()
            nem = _SEC_NOTES_END.search(text, nm.end())
            if nem:
                notes = text[notes_start:nem.start()].strip('\n')
            else:
                notes = text[notes_start:].strip('\n')

        # 版本号推断
        version: Optional[VersionMeta] = None
        ver_match = re.search(r'\.v(\d+)\.md$', name)
        if ver_match:
            version = VersionMeta(
                target_type='section',
                target_id=name.replace('.md', ''),
                version=int(ver_match.group(1)),
                storage_path=str(path),
                created_at='',
            )

        return SectionFile(
            name=name,
            content=content,
            notes=notes,
            version=version,
        )

    # ── Staging 解析（DT-05, DT-06）──────────────────────────

    def parse_staging(self, file_path: str) -> StagingDoc:
        """解析 pending.md → StagingDoc。"""
        text = Path(file_path).read_text(encoding='utf-8')

        # 解析 status 行
        status = 'pending'
        status_match = re.search(r'^status:\s*(\w+)', text, re.MULTILINE)
        if status_match:
            status = status_match.group(1)

        # 解析 @STAGING:N 操作块
        ops: list[StagingOp] = []

        # 找所有 STAGING 对
        staging_pairs = _find_pairs(text, _STAGING_OP_START, _STAGING_OP_END)

        for start_pos, end_pos, sid in staging_pairs:
            # 重新匹配开哨兵获取属性
            block_text = text[start_pos:end_pos]
            op_match = _STAGING_OP_START.search(block_text)
            if not op_match:
                continue

            op_num = op_match.group(1)
            op_type = op_match.group(2)
            op_target = op_match.group(3)
            op_position = op_match.group(4) or None
            op_adapt_str = op_match.group(5) or 'false'
            op_adapt = op_adapt_str.lower() == 'true'

            # 在块内找 @STG:CONTENT:START / @STG:CONTENT:END
            op_content: Optional[str] = None
            csm = _STG_CONTENT_START.search(block_text)
            if csm:
                cem = _STG_CONTENT_END.search(block_text, csm.end())
                if cem:
                    op_content = block_text[csm.end():cem.start()].strip('\n')

            ops.append(StagingOp(
                op=op_type,
                target=op_target,
                position=op_position,
                adapt=op_adapt,
                content=op_content,
            ))

        return StagingDoc(status=status, ops=ops)

    def parse_staging_status(self, file_path: str) -> Optional[str]:
        """轻量读取 pending.md 的 status 行。返回 'pending' / 'processing' / None。"""
        try:
            text = Path(file_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            return None
        status_match = re.search(r'^status:\s*(\w+)', text, re.MULTILINE)
        if status_match:
            return status_match.group(1)
        return None

    # ── MSG 计数器（DT-07）───────────────────────────────────

    def parse_msg_counter(self, text: str) -> int:
        """从文本中提取 @MSG:NEXT:N 的 N 值。找不到返回 0。"""
        match = _MSG_NEXT.search(text)
        if match:
            return int(match.group(1))
        return 0
