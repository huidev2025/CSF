# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
ContextService V6 — 标签2 v6 服务层骨架。

STB-1 DT-01.6~01.10：
- cos-context.md 的 @SECTION 哨兵解析 → SectionData 列表
- section_meta.json 读写
- 版本列表扫描
- 草稿文件读写

V6 关键差异：不依赖 sentinel_parser 的 Section/ContextDoc 旧模型，
仅复用其 _SECTION_START/_SECTION_END/_find_pairs 正则工具。
"""

import json
import logging
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.models import (
    SectionData, VersionEntry, DraftState, TemplateData,
)
from src.core.sentinel_parser import _SECTION_START, _SECTION_END, _find_pairs

logger = logging.getLogger(__name__)


# ── @SOURCE 哨兵正则 ─────────────────────────────────────────

_SOURCE_SENTINEL = re.compile(r'<!--\s*@SOURCE:v(\d+)\s*-->')

# 段标题提取（第一个 # 或 ## 或 ### 行）
_HEADING = re.compile(r'^#{1,3}\s+(.+)$', re.MULTILINE)


# ── DT-01.6: ContextService ──────────────────────────────────

class ContextService:
    """标签2 v6 上下文服务。

    负责解析 cos-context.md 中的 @SECTION 哨兵对，
    读取 section_meta.json 说明，扫描版本列表，管理草稿文件。
    """

    def __init__(
        self,
        cos_context_path: str,
        sections_dir: str,
        section_meta_path: str,
        draft_path: str,
        staging_path: str,
        templates_dir: str,
    ):
        """DT-01.6：接收6个路径参数，存储为实例属性。"""
        self.cos_context_path = cos_context_path
        self.sections_dir = sections_dir
        self.section_meta_path = section_meta_path
        self.draft_path = draft_path
        self.staging_path = staging_path
        self.templates_dir = templates_dir

    # ── DT-01.7: 加载基线段列表 ─────────────────────────────

    def load_baseline_sections(self) -> list[SectionData]:
        """解析 cos-context.md 中所有 @SECTION 哨兵对 → SectionData 列表。

        提取逻辑：
        1. 读 cos-context.md 全文
        2. 用 _find_pairs 找所有 @SECTION 哨兵对
        3. 逐对提取：段标题（首行#标题）、@SOURCE版本号、正文内容
        4. 从 section_meta.json 读取对应说明
        5. 按文档出现顺序分配 1-based 序号

        Returns:
            SectionData 列表（按文档顺序）。无哨兵对时返回空列表。
        """
        try:
            text = Path(self.cos_context_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            return []

        # 找所有 @SECTION 哨兵对
        pairs = _find_pairs(text, _SECTION_START, _SECTION_END)

        if not pairs:
            return []

        # 读 section_meta.json（容錯：文件不存在用空dict）
        meta = self.read_section_meta()

        sections: list[SectionData] = []
        for order, (start_pos, end_pos, sid) in enumerate(pairs, start=1):
            # 提取哨兵行之间的完整文本
            raw = text[start_pos:end_pos]

            # 提取段标题：第一个 # 标题行
            title = sid  # fallback
            heading_match = _HEADING.search(raw)
            if heading_match:
                title = heading_match.group(1).strip()

            # 提取 @SOURCE 版本号
            source_version: Optional[int] = None
            source_match = _SOURCE_SENTINEL.search(raw)
            if source_match:
                source_version = int(source_match.group(1))

            # 提取正文内容（去掉哨兵行本身）
            # 开哨兵行之后 → 闭哨兵行之前
            inner_start = raw.find('-->') + 3
            inner_end = raw.rfind('<!-- @/SECTION')
            if inner_end == -1:
                inner_end = len(raw)
            content = raw[inner_start:inner_end].strip('\n')

            # 从 section_meta.json 取 description
            entry = meta.get(title, '')
            if isinstance(entry, dict):
                description = entry.get('description', '')
            else:
                description = entry if isinstance(entry, str) else ''

            sections.append(SectionData(
                title=title,
                section_id=sid,
                source_version=source_version,
                content=content,
                description=description,
                order=order,
            ))

        return sections

    # ── DT-01.8: 加载版本列表 ───────────────────────────────

    def load_version_list(self, section_title: str) -> list[VersionEntry]:
        """扫描 sections/.versions/{段名}.v*.md → VersionEntry 列表。

        文件名格式：{段标题}.v{N}.md
        解析文件内的 YAML frontmatter（---...---）获取 description/created_at。
        空目录返回空列表不报错。按版本号倒序排列。

        Args:
            section_title: 段标题（如"§B 任务窗口"）

        Returns:
            VersionEntry 列表（版本号倒序）。无版本文件时返回空列表。
        """
        versions_dir = Path(self.sections_dir) / '.versions'
        if not versions_dir.is_dir():
            return []

        entries: list[VersionEntry] = []

        # 扫描匹配 {section_title}.v*.md 的文件
        # 安全处理文件名中的特殊字符
        pattern = f"{section_title}.v*.md"
        for file_path in versions_dir.glob(pattern):
            # 从文件名提取版本号
            name = file_path.name
            ver_match = re.search(r'\.v(\d+)\.md$', name)
            if not ver_match:
                continue
            version = int(ver_match.group(1))

            # 解析 YAML frontmatter
            description = ""
            created_at = ""
            baselines: list[str] = []
            try:
                raw = file_path.read_text(encoding='utf-8')
                fm = _parse_yaml_frontmatter(raw)
                description = fm.get('description', '')
                created_at = fm.get('created_at', '')
                baselines_str = fm.get('baselines', '')
                if baselines_str:
                    baselines = [
                        b.strip() for b in baselines_str.split(',') if b.strip()
                    ]
            except Exception:
                pass

            entries.append(VersionEntry(
                section_title=section_title,
                version=version,
                description=description,
                created_at=created_at,
                file_path=str(file_path),
                baselines=baselines,
            ))

        # 按版本号倒序
        entries.sort(key=lambda e: e.version, reverse=True)
        return entries

    # ── DT-01.9: section_meta.json 读写 ─────────────────────

    def read_section_meta(self) -> dict:
        """读取 section_meta.json → dict。文件不存在返回空dict。"""
        try:
            raw = Path(self.section_meta_path).read_text(encoding='utf-8')
            return json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write_section_meta(self, data: dict) -> None:
        """写入 section_meta.json（覆盖）。自动创建父目录。"""
        path = Path(self.section_meta_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    # ── DT-04.1: 模板服务层 ────────────────────────────────

    def load_templates(self) -> list[TemplateData]:
        """DT-04.1：扫描 templates/ 目录 → 解析所有模板JSON。

        空目录返回空列表不报错。
        """
        templates_dir = Path(self.templates_dir)
        if not templates_dir.is_dir():
            return []

        result: list[TemplateData] = []
        for fpath in templates_dir.glob('*.json'):
            try:
                raw = fpath.read_text(encoding='utf-8')
                data = json.loads(raw)
                result.append(TemplateData(
                    name=data.get('name', fpath.stem),
                    sections=data.get('sections', []),
                    created_at=data.get('created_at', ''),
                ))
            except (json.JSONDecodeError, Exception):
                logger.warning('[模板] 解析失败: %s', fpath.name)
        return result

    def read_template(self, name: str) -> Optional[TemplateData]:
        """DT-04.1：按模板名读取单个模板JSON。"""
        fpath = Path(self.templates_dir) / f'{name}.json'
        if not fpath.exists():
            return None
        try:
            raw = fpath.read_text(encoding='utf-8')
            data = json.loads(raw)
            return TemplateData(
                name=data.get('name', name),
                sections=data.get('sections', []),
                created_at=data.get('created_at', ''),
            )
        except (json.JSONDecodeError, Exception):
            return None

    def write_template(self, template: TemplateData) -> None:
        """DT-04.1：序列化模板为JSON写入 templates/{name}.json。

        自动创建父目录。
        """
        templates_dir = Path(self.templates_dir)
        templates_dir.mkdir(parents=True, exist_ok=True)
        fpath = templates_dir / f'{template.name}.json'
        data = {
            'name': template.name,
            'sections': template.sections,
            'created_at': template.created_at,
        }
        fpath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def delete_template(self, name: str) -> None:
        """DT-04.1：删除模板JSON文件。不影响段库版本。"""
        fpath = Path(self.templates_dir) / f'{name}.json'
        if fpath.exists():
            fpath.unlink()

    def rename_template(self, old_name: str, new_name: str) -> None:
        """重命名模板：读取→以新名写入→删除旧文件。

        Raises:
            FileNotFoundError: 旧模板不存在
            ValueError: 新名称为空或已存在
        """
        if not new_name or not new_name.strip():
            raise ValueError('模板名不能为空')
        new_name = new_name.strip()
        if new_name == old_name:
            return
        old_path = Path(self.templates_dir) / f'{old_name}.json'
        new_path = Path(self.templates_dir) / f'{new_name}.json'
        if not old_path.exists():
            raise FileNotFoundError(f'模板不存在: {old_name}')
        if new_path.exists():
            raise ValueError(f'模板 "{new_name}" 已存在')
        tpl = self.read_template(old_name)
        if tpl is None:
            raise FileNotFoundError(f'模板读取失败: {old_name}')
        tpl.name = new_name
        self.write_template(tpl)
        old_path.unlink()
        logger.info('[模板] 重命名: %s → %s', old_name, new_name)

    # ── DT-04.6: 导入上下文 ─────────────────────────────────

    def import_context(self, file_path: str) -> TemplateData:
        """DT-04.6：解析 .md 文件中的 @SECTION 哨兵对 → 段入库 → 生成模板。

        对每个段：
        - 段库中无同标题段 → 保存为 v1
        - 段库中已有同标题段 → 取 max+1 保存

        模板名 = {源文件名}（导入）

        Args:
            file_path: 要导入的 .md 文件路径

        Returns:
            生成的 TemplateData

        Raises:
            ValueError: 文件中无任何 @SECTION 哨兵对
        """
        src = Path(file_path)
        if not src.exists():
            raise ValueError(f'文件不存在: {file_path}')

        text = src.read_text(encoding='utf-8')

        # 查找所有 @SECTION 哨兵对
        pairs = _find_pairs(text, _SECTION_START, _SECTION_END)
        if not pairs:
            raise ValueError(
                f'文件中未找到任何 @SECTION 标记，无法导入。'
            )

        versions_dir = Path(self.sections_dir) / '.versions'
        versions_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        template_sections: list[dict] = []
        parse_errors: list[str] = []

        for _, _, sid in pairs:
            # 重新提取该段内容（因为 text 可能被前面的更新改变位置）
            # 这里用一次性提取所有段的方式
            pass

        # 重新扫描所有对（一次性处理）
        failed_sections: list[str] = []
        for start_pos, end_pos, sid in pairs:
            try:
                raw = text[start_pos:end_pos]

                # 提取段标题
                heading_match = _HEADING.search(raw)
                title = sid
                if heading_match:
                    title = heading_match.group(1).strip()

                # 提取 @SOURCE 版本号
                source_version: Optional[int] = None
                source_match = _SOURCE_SENTINEL.search(raw)
                if source_match:
                    source_version = int(source_match.group(1))

                # 提取正文（哨兵对之间的内容）
                inner_start = raw.find('-->') + 3
                inner_end = raw.rfind('<!-- @/SECTION')
                if inner_end == -1:
                    inner_end = len(raw)
                content = raw[inner_start:inner_end].strip('\n')

                # 提取描述（从 section_meta 或 YAML frontmatter）
                description = ''
                # 尝试从 @DESC 哨兵提取
                desc_match = re.search(
                    r'<!--\s*@DESC.*?-->\s*\n(.*?)\n\s*<!--\s*@/DESC',
                    raw, re.DOTALL,
                )
                if desc_match:
                    description = desc_match.group(1).strip()

                # 确定版本号
                existing_versions = list(
                    versions_dir.glob(f'{title}.v*.md')
                )
                if existing_versions:
                    max_ver = 0
                    for f in existing_versions:
                        ver_match = re.search(r'\.v(\d+)\.md$', f.name)
                        if ver_match:
                            max_ver = max(max_ver, int(ver_match.group(1)))
                    new_ver = max_ver + 1
                else:
                    new_ver = 1

                # 写入版本文件
                ver_path = versions_dir / f'{title}.v{new_ver}.md'
                yaml_header = (
                    f'---\n'
                    f'description: {description}\n'
                    f'created_at: {now}\n'
                    f'version: {new_ver}\n'
                    f'---\n\n'
                )
                content_block = (
                    f'<!-- @SEC:CONTENT -->\n'
                    f'{content}\n'
                    f'<!-- @/SEC:CONTENT -->\n'
                )
                ver_path.write_text(
                    yaml_header + content_block, encoding='utf-8',
                )

                template_sections.append({
                    'title': title,
                    'version': new_ver,
                })
                logger.info(
                    '[导入] %s → v%d（%d字）',
                    title, new_ver, len(content),
                )

            except Exception as e:
                failed_sections.append(f'{sid}: {e}')
                logger.warning('[导入] 段解析失败 %s: %s', sid, e)

        if not template_sections:
            raise ValueError(
                '所有段解析均失败，无法生成模板。'
            )

        # 生成模板
        src_name = src.stem
        template_name = f'{src_name}（导入）'
        template = TemplateData(
            name=template_name,
            sections=template_sections,
            created_at=now,
        )
        self.write_template(template)

        if failed_sections:
            logger.warning(
                '[导入] 部分段解析失败: %s', ', '.join(failed_sections),
            )

        return template

    # ── DT-04.7: 导出上下文 ─────────────────────────────────

    def export_context(self, template_name: str, output_path: str) -> None:
        """DT-04.7：按模板引用从段库拼装完整 context .md 文件。

        对每个段引用：
        - 从段库版本文件提取 @SEC:CONTENT 哨兵对之间的正文
        - 提取 YAML frontmatter 中的 description
        - 拼接为 @SECTION 哨兵对 + @SOURCE 哨兵 + 正文 + 说明

        异常处理：
        - 部分版本已删除 → 输出占位标记，弹窗提示后继续
        - 所有引用版本均已删除 → 抛异常中止

        Args:
            template_name: 模板名
            output_path: 输出文件路径

        Raises:
            ValueError: 模板不存在或所有版本均已删除
        """
        template = self.read_template(template_name)
        if not template:
            raise ValueError(f'模板不存在: {template_name}')

        versions_dir = Path(self.sections_dir) / '.versions'
        missing_sections: list[str] = []
        output_parts: list[str] = []

        for sec_ref in template.sections:
            title = sec_ref.get('title', '')
            version = sec_ref.get('version', 0)

            ver_path = versions_dir / f'{title}.v{version}.md'
            if not ver_path.exists():
                missing_sections.append(
                    f'{title}（原引用 v{version}，该版本已被删除）'
                )
                output_parts.append(
                    f'<!-- @SECTION 缺失（原引用 v{version}，'
                    f'该版本已被删除） -->\n'
                    f'## {title}\n\n'
                    f'> ⚠️ 该版本已被删除，无法恢复内容。\n\n'
                )
                continue

            try:
                raw = ver_path.read_text(encoding='utf-8')

                # 提取 YAML frontmatter
                fm: dict = {}
                body = raw
                if raw.startswith('---'):
                    fm_end = raw.find('---', 3)
                    if fm_end != -1:
                        fm = _parse_yaml_frontmatter(raw)
                        body = raw[fm_end + 3:].lstrip('\n')

                description = fm.get('description', '')

                # 提取 @SEC:CONTENT 之间的正文
                content_match = re.search(
                    r'<!--\s*@SEC:CONTENT\s*-->\s*\n(.*?)\n\s*<!--\s*@/SEC:CONTENT',
                    body, re.DOTALL,
                )
                if content_match:
                    content = content_match.group(1)
                else:
                    content = body.strip()

                # 确定 section_id
                section_id = fm.get('section_id', title)

                # 拼装段输出
                desc_block = ''
                if description:
                    desc_block = (
                        f'\n<!-- @DESC -->\n{description}\n<!-- @/DESC -->\n'
                    )

                section_block = (
                    f'<!-- @SECTION:{section_id} -->\n'
                    f'<!-- @SOURCE:v{version} -->\n'
                    f'## {title}\n'
                    f'{desc_block}'
                    f'\n{content}\n'
                    f'<!-- @/SECTION:{section_id} -->\n'
                )
                output_parts.append(section_block)

            except Exception as e:
                missing_sections.append(f'{title} v{version}: {e}')
                output_parts.append(
                    f'<!-- @SECTION 解析失败（{title} v{version}） -->\n'
                    f'## {title}\n\n'
                    f'> ⚠️ 版本文件解析失败: {e}\n\n'
                )

        if not output_parts:
            raise ValueError(
                f'模板 "{template_name}" 中所有引用的版本均已删除，无法导出。'
            )

        # 写入输出文件
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text('\n'.join(output_parts), encoding='utf-8')

        if missing_sections:
            logger.warning(
                '[导出] 部分段缺失: %s', ', '.join(missing_sections),
            )

    # ── DT-01.10: 草稿文件读写 ──────────────────────────────

    def read_draft(self) -> Optional[DraftState]:
        """读取草稿文件（staging/draft_tag2.json）→ DraftState。

        文件不存在返回 None。JSON解析失败返回 None。
        自动注入 _persist 回调：后续 add_change/remove_change/clear 会即时写盘。
        """
        try:
            raw = Path(self.draft_path).read_text(encoding='utf-8')
            data = json.loads(raw)
            state = DraftState(
                baseline_sections=data.get('baseline_sections', []),
                baseline_order=data.get('baseline_order', {}),
                changes=[
                    _dict_to_draft_change(c)
                    for c in data.get('changes', [])
                ],
            )
            state._persist = lambda: self.write_draft(state)
            return state
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def write_draft(self, state: DraftState) -> None:
        """写入草稿文件（staging/draft_tag2.json）。自动创建父目录。"""
        path = Path(self.draft_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'baseline_sections': state.baseline_sections,
            'baseline_order': state.baseline_order,
            'changes': [
                {
                    'change_type': c.change_type,
                    'section_title': c.section_title,
                    'to_version': c.to_version,
                    'from_version': c.from_version,
                    'new_order': c.new_order,
                }
                for c in state.changes
            ],
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    # ── DT-02.2: staging 文件读写 ────────────────────────────

    def write_staging(self, content: str) -> None:
        """写入 staging 指令文件。

        若 staging 文件已存在→先删除→删除失败则抛异常中止→写入新文件。
        自动创建父目录。
        """
        path = Path(self.staging_path)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                raise OSError(f'无法删除已有staging文件: {self.staging_path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def read_staging(self) -> Optional[str]:
        """读取 staging 文件内容。不存在返回 None。"""
        try:
            return Path(self.staging_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            return None

    def delete_staging(self) -> None:
        """删除 staging 文件。不存在则静默跳过。"""
        path = Path(self.staging_path)
        if path.exists():
            path.unlink()

    # ── DT-03.9: save_to_current_context ───────────────────

    def save_to_current_context(
        self, section_title: str, description: str
    ) -> None:
        """DT-03.9：保存说明到当前上下文。

        仅更新 section_meta.json 中该段的 description 字段。
        不再向 cos-context.md 写入 @DESC 哨兵（浪费 AI 上下文）。
        不产生新版本号。

        Args:
            section_title: 段标题（如"§B 任务窗口"）
            description: 编辑后的说明文本
        """
        # 同步 section_meta.json
        meta = self.read_section_meta()
        if section_title not in meta:
            meta[section_title] = {}
        elif not isinstance(meta[section_title], dict):
            meta[section_title] = {'description': meta[section_title]}
        meta[section_title]['description'] = description
        self.write_section_meta(meta)

    # ── DT-03.10: save_as_library_version ──────────────────

    def save_as_library_version(
        self,
        section_title: str,
        content: str,
        description: str,
        source_version: Optional[int] = None,
    ) -> int:
        """DT-03.10：保存为段库版本。

        - source_version 非 None → 覆写已有版本文件
          （YAML frontmatter更新description，正文保持不变——只读不修改）
        - source_version 为 None → 扫描 max+1 → 写入新版本文件
          （YAML frontmatter + @SEC:CONTENT哨兵对包裹正文）

        Args:
            section_title: 段标题
            content: 段正文
            description: 版本说明
            source_version: 要覆写的版本号（None=新建）

        Returns:
            实际版本号
        """
        versions_dir = Path(self.sections_dir) / '.versions'
        versions_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        if source_version is not None:
            # 覆写已有版本
            ver = source_version
            ver_path = versions_dir / f'{section_title}.v{ver}.md'
            # 只更新 YAML frontmatter 中的 description，正文保持不变
            if ver_path.exists():
                existing_raw = ver_path.read_text(encoding='utf-8')
                # 提取正文（跳过 frontmatter）
                fm_end = existing_raw.find('---', 3)
                body = existing_raw[fm_end + 3:].lstrip('\n') if fm_end != -1 else existing_raw
            else:
                body = content

            yaml_header = (
                f'---\n'
                f'description: {description}\n'
                f'created_at: {now}\n'
                f'---\n\n'
            )
            ver_path.write_text(yaml_header + body, encoding='utf-8')
            return ver

        # 新建版本：扫描 max+1
        max_ver = 0
        pattern = f'{section_title}.v*.md'
        for f in versions_dir.glob(pattern):
            ver_match = re.search(r'\.v(\d+)\.md$', f.name)
            if ver_match:
                max_ver = max(max_ver, int(ver_match.group(1)))

        new_ver = max_ver + 1
        ver_path = versions_dir / f'{section_title}.v{new_ver}.md'

        yaml_header = (
            f'---\n'
            f'description: {description}\n'
            f'created_at: {now}\n'
            f'version: {new_ver}\n'
            f'---\n\n'
        )
        content_block = (
            f'<!-- @SEC:CONTENT -->\n'
            f'{content}\n'
            f'<!-- @/SEC:CONTENT -->\n'
        )
        ver_path.write_text(yaml_header + content_block, encoding='utf-8')
        return new_ver

    # ── DT-03.11: delete_version ───────────────────────────

    def delete_version(
        self, section_title: str, version: int
    ) -> None:
        """DT-03.11：删除版本（含两重约束检查）。

        约束1：至少保留一个版本（该段版本总数>1）
        约束2：出厂模板锁定段不允许删除版本
        不满足 → 抛 VersionDeleteError（含具体原因）

        Args:
            section_title: 段标题
            version: 要删除的版本号

        Raises:
            VersionDeleteError: 约束不满足
        """
        versions_dir = Path(self.sections_dir) / '.versions'

        # 约束1：检查版本总数
        existing = list(versions_dir.glob(f'{section_title}.v*.md'))
        if len(existing) <= 1:
            raise VersionDeleteError(
                f'至少保留一个版本。"{section_title}" 仅有 {len(existing)} 个版本。',
                reason='min_one_version',
            )

        # 约束2：检查出厂模板锁定段
        # 读取该版本的 baselines 字段（从YAML frontmatter）
        ver_path = versions_dir / f'{section_title}.v{version}.md'
        if ver_path.exists():
            raw = ver_path.read_text(encoding='utf-8')
            fm = _parse_yaml_frontmatter(raw)
            baselines_str = fm.get('baselines', '')
            baselines = [
                b.strip() for b in baselines_str.split(',') if b.strip()
            ]
            # 检查是否有出厂基线模板名（以 'csf-' 开头或标记为factory）
            for bl in baselines:
                if bl.startswith('csf-') or 'factory' in bl.lower():
                    raise VersionDeleteError(
                        f'出厂模板锁定段不允许删除版本。'
                        f'版本 v{version} 关联出厂基线: {bl}',
                        reason='factory_locked',
                    )

        # 执行删除
        if ver_path.exists():
            ver_path.unlink()

    # ── DT-03.12: copy_version ─────────────────────────────

    def copy_version(
        self, section_title: str, version: int
    ) -> int:
        """DT-03.12：复制版本。

        读取源版本文件完整内容 → 取 max(已有版本号)+1 →
        写入新版本文件（YAML frontmatter 中 version 更新为新号，
        created_at 更新为当前时间，description 保持不变）。

        Args:
            section_title: 段标题
            version: 源版本号

        Returns:
            新版本号
        """
        versions_dir = Path(self.sections_dir) / '.versions'
        src_path = versions_dir / f'{section_title}.v{version}.md'

        if not src_path.exists():
            raise FileNotFoundError(
                f'源版本文件不存在: {src_path}'
            )

        raw = src_path.read_text(encoding='utf-8')

        # 取 max+1
        max_ver = 0
        for f in versions_dir.glob(f'{section_title}.v*.md'):
            ver_match = re.search(r'\.v(\d+)\.md$', f.name)
            if ver_match:
                max_ver = max(max_ver, int(ver_match.group(1)))

        new_ver = max_ver + 1
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        # 解析原 frontmatter，更新 version 和 created_at
        fm = _parse_yaml_frontmatter(raw)
        fm_end = raw.find('---', 3)
        body = raw[fm_end + 3:].lstrip('\n') if fm_end != -1 else raw

        fm['version'] = str(new_ver)
        fm['created_at'] = now
        if 'description' not in fm:
            fm['description'] = ''

        # 重建 YAML frontmatter
        yaml_lines = ['---']
        for key in ['description', 'created_at', 'version']:
            if key in fm:
                yaml_lines.append(f'{key}: {fm[key]}')
        yaml_lines.append('---')
        yaml_lines.append('')

        new_path = versions_dir / f'{section_title}.v{new_ver}.md'
        new_path.write_text('\n'.join(yaml_lines) + body, encoding='utf-8')
        return new_ver

    # ── DT-03.13: detect_version_changes ───────────────────

    def detect_version_changes(self) -> list[tuple[str, int, int]]:
        """DT-03.13：版本变化检测与 @DESC 同步。

        标签2获得焦点时调用。遍历 cos-context.md 中每个 @SECTION 块的
        @SOURCE 版本号 → 与 section_meta.json 中对应段的 source_version
        比较 → 返回变化的段列表。

        对每个变化的段：
        - 读取目标版本的 description
        - 在前面插入 @DESC:v{N} 标记（旧描述块保留下方）
        - 更新 section_meta.json 的 source_version

        source_version 首次不存在 → 取当前 @SOURCE 值写入，不触发说明拷贝。

        Returns:
            [(段标题, 旧版本, 新版本), ...] 变化的段列表
        """
        cos_path = Path(self.cos_context_path)
        if not cos_path.exists():
            return []

        text = cos_path.read_text(encoding='utf-8')
        pairs = _find_pairs(text, _SECTION_START, _SECTION_END)
        meta = self.read_section_meta()
        changed: list[tuple[str, int, int]] = []

        for _, _, sid in pairs:
            # 重新定位该段（因为 text 可能被前面的更新改变）
            # 这里用重新读取的方式，但我们一次性处理所有段
            pass

        # 重新获取所有段信息
        meta_changed = False
        # 从头到尾扫描一遍，逐个段处理
        for start_pos, end_pos, sid in pairs:
            raw = text[start_pos:end_pos]

            # 找到段标题
            heading_match = _HEADING.search(raw)
            title = sid
            if heading_match:
                title = heading_match.group(1).strip()

            # 找到 @SOURCE 版本号
            source_match = _SOURCE_SENTINEL.search(raw)
            new_source_ver: Optional[int] = None
            if source_match:
                new_source_ver = int(source_match.group(1))

            # 从 section_meta.json 读取旧 source_version
            entry = meta.get(title, '')
            if not isinstance(entry, dict):
                entry = {}
            old_source_ver = entry.get('source_version')

            if old_source_ver is None:
                # 首次记录 → 不触发说明拷贝，仅写入
                if new_source_ver is not None:
                    if title not in meta or not isinstance(meta.get(title), dict):
                        meta[title] = {}
                    meta[title]['source_version'] = new_source_ver
                    meta_changed = True
                continue

            if new_source_ver is not None and new_source_ver != old_source_ver:
                changed.append((title, old_source_ver, new_source_ver))

                # 读取目标版本的 description
                ver_desc = self._load_version_description(
                    title, new_source_ver
                )
                if ver_desc:
                    # 在前面插入 @DESC:v{N} 标记
                    new_desc = (
                        f'<!-- @DESC:v{new_source_ver} -->\n'
                        f'{ver_desc}\n\n'
                    )
                    old_desc = entry.get('description', '')
                    entry['description'] = new_desc + old_desc

                entry['source_version'] = new_source_ver
                meta[title] = entry
                meta_changed = True

        if meta_changed:
            self.write_section_meta(meta)

        return changed

    def _load_version_description(
        self, section_title: str, version: int
    ) -> Optional[str]:
        """加载指定版本的 description（从YAML frontmatter）。"""
        versions_dir = Path(self.sections_dir) / '.versions'
        ver_path = versions_dir / f'{section_title}.v{version}.md'
        if not ver_path.exists():
            return None
        try:
            raw = ver_path.read_text(encoding='utf-8')
            fm = _parse_yaml_frontmatter(raw)
            return fm.get('description', '')
        except Exception:
            return None


# ── VersionDeleteError ──────────────────────────────────────

class VersionDeleteError(Exception):
    """版本删除约束异常。"""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


# ── 内部辅助 ─────────────────────────────────────────────────

def _parse_yaml_frontmatter(text: str) -> dict:
    """从Markdown文本中提取YAML frontmatter（---...---）→ dict。

    简单解析：逐行读 key: value，不支持嵌套/引用/多行字符串。
    容忍格式错误，返回尽量多的已解析字段。
    """
    # 找 frontmatter 块
    if not text.startswith('---'):
        return {}
    end_idx = text.find('---', 3)
    if end_idx == -1:
        return {}
    fm_text = text[3:end_idx]

    result: dict = {}
    for line in fm_text.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            result[key] = val
    return result


def _dict_to_draft_change(d: dict) -> 'DraftChange':
    """从 dict 构造 DraftChange（避免循环导入）。"""
    from src.core.models import DraftChange
    return DraftChange(
        change_type=d.get('change_type', ''),
        section_title=d.get('section_title', ''),
        to_version=d.get('to_version'),
        from_version=d.get('from_version'),
        new_order=d.get('new_order'),
    )
