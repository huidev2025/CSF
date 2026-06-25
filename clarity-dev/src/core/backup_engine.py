# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
BackupEngine — 纯文件备份引擎（V2）。

替代 V1 的 SQLite 方案，全部基于文件系统：
- 段版本快照：sections/.versions/{段名}.v{N}.md
- 文件备份：backups/files/{path}/v{NNN}.md
- 基线管理：backups/baselines/{基线名}.md

所有文件 I/O 通过 FileSystemOps 实例完成，不直接操作文件系统。
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.core.models import VersionMeta
from src.core.file_system_ops import FileSystemOps


# 版本号正则 — 匹配两种模式：
#   段版本快照: xxx.v12.md  (.v{N}.md)
#   文件备份:    v001.md     (v{NNN}.md)
_VERSION_RE = re.compile(r'(?:\.v|^v)(\d+)\.md$')

# YAML frontmatter 分隔符
_YAML_SEP = '---'


class BackupEngine:
    """纯文件备份引擎 — 版本快照 / 文件备份 / 基线管理。"""

    def __init__(self, fs: FileSystemOps, sections_dir: str, backups_dir: str):
        """DT-07: 初始化备份引擎。

        Args:
            fs: FileSystemOps 实例，所有 I/O 通过它完成
            sections_dir: csf-clarity/sections/ 目录路径
            backups_dir: csf-clarity/backups/ 目录路径
        """
        self.fs = fs
        self.sections_dir = sections_dir
        self.backups_dir = backups_dir

    # ── 内部工具 ──────────────────────────────────────────

    @staticmethod
    def _now_iso() -> str:
        """当前 UTC 时间 ISO 8601 格式。"""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _extract_version(filename: str) -> Optional[int]:
        """从文件名提取版本号：xxx.v3.md → 3，xxx.md → None。"""
        m = _VERSION_RE.search(filename)
        return int(m.group(1)) if m else None

    @staticmethod
    def _parse_frontmatter(text: str) -> tuple[dict, str]:
        """解析 YAML frontmatter。返回 (frontmatter_dict, 正文)。"""
        if not text.startswith(_YAML_SEP):
            return {}, text

        parts = text.split(_YAML_SEP, 2)
        if len(parts) < 3:
            return {}, text

        try:
            import yaml
            fm = yaml.safe_load(parts[1]) or {}
        except Exception:
            fm = {}
        return fm, parts[2]

    @staticmethod
    def _build_frontmatter(meta: dict) -> str:
        """构建 YAML frontmatter 字符串。"""
        import yaml
        yaml_str = yaml.dump(meta, allow_unicode=True, default_flow_style=False,
                             sort_keys=False).strip()
        return f'{_YAML_SEP}\n{yaml_str}\n{_YAML_SEP}'

    @staticmethod
    def _read_content_after_frontmatter(text: str) -> str:
        """读取 YAML frontmatter 之后的内容。"""
        if not text.startswith(_YAML_SEP):
            return text
        parts = text.split(_YAML_SEP, 2)
        return parts[2] if len(parts) >= 3 else text

    @staticmethod
    def _join(*parts: str) -> str:
        """路径拼接，使用 os.path.join 保证跨平台正确。"""
        return os.path.join(*parts)

    def _scan_versions_dir(self, dir_path: str) -> list[str]:
        """扫描目录下匹配 *.v*.md 的文件名列表（仅名称不含路径）。"""
        try:
            all_files = self.fs.list_dir(dir_path)
        except Exception:
            return []
        return [f for f in all_files if _VERSION_RE.search(f)]

    # ── 段版本快照（DT-08）────────────────────────────────

    def save_section_version(self, section_name: str, content: str,
                             description: Optional[str] = None) -> VersionMeta:
        """DT-08: 保存段版本快照。v4: 移除 note，仅保留 description。"""
        versions_dir = self._join(self.sections_dir, '.versions')
        self.fs.ensure_dir(versions_dir)

        # 扫描现有版本
        existing = self._scan_versions_dir(versions_dir)
        section_versions = [
            self._extract_version(f)
            for f in existing
            if f.startswith(section_name + '.v') or f.startswith(section_name.replace('.md', '') + '.v')
        ]
        max_ver = max(section_versions) if section_versions else 0
        new_ver = max_ver + 1

        # 纯段名（去掉 .md 后缀）
        clean_name = section_name.replace('.md', '')
        storage_name = f'{clean_name}.v{new_ver}.md'
        storage_path = self._join(versions_dir, storage_name)

        # YAML frontmatter（v4: 移除 note，仅保留 description）
        meta = {
            'section_id': clean_name,
            'version': new_ver,
            'description': description or '',
            'created_at': self._now_iso(),
            'baselines': [],
        }
        full_content = self._build_frontmatter(meta) + '\n' + content

        self.fs.write_file(storage_path, full_content)

        return VersionMeta(
            target_type='section',
            target_id=clean_name,
            version=new_ver,
            storage_path=storage_path,
            description=description,
            created_at=meta['created_at'],
            baselines=[],
        )

    # ── 文件备份（DT-09）──────────────────────────────────

    def save_file_backup(self, file_path: str, content: str,
                         description: str = '') -> VersionMeta:
        """DT-09: 保存文件备份。

        ① file_path 为相对路径（如 'core/守则.md'），拒绝含 '..' 的路径
        ② 扫描 backups/files/{file_path}/ 确定最大编号
        ③ 写入 v{NNN+1:03d}.md
        ④ 返回 VersionMeta

        v3 (DT-18): 新增 description 字段写入 YAML frontmatter。
        """
        # 防路径穿越
        if '..' in file_path:
            raise ValueError(f'路径含非法字符: {file_path}')

        backup_dir = self._join(self.backups_dir, 'files', file_path)
        self.fs.ensure_dir(backup_dir)

        existing = self._scan_versions_dir(backup_dir)
        nums = [self._extract_version(f) for f in existing]
        nums = [n for n in nums if n is not None]
        max_num = max(nums) if nums else 0
        new_num = max_num + 1

        storage_name = f'v{new_num:03d}.md'
        storage_path = self._join(backup_dir, storage_name)

        meta = {
            'file_path': file_path,
            'version': new_num,
            'description': description,
            'created_at': self._now_iso(),
            'baselines': [],
        }
        full_content = self._build_frontmatter(meta) + '\n' + content

        self.fs.write_file(storage_path, full_content)

        return VersionMeta(
            target_type='file',
            target_id=file_path,
            version=new_num,
            storage_path=storage_path,
            description=description,
            created_at=meta['created_at'],
            baselines=[],
        )

    # ── 版本历史（DT-10）──────────────────────────────────

    def scan_version_history(self, target_path: str) -> list[VersionMeta]:
        """DT-10: 扫描目录下所有版本快照，返回 VersionMeta 列表（降序）。

        target_path: 目录路径，如 sections_dir/.versions/ 或
                     backups_dir/files/core/守则.md/
        """
        files = self._scan_versions_dir(target_path)
        result: list[VersionMeta] = []

        for fname in files:
            full_path = self._join(target_path, fname)
            try:
                text = self.fs.read_file(full_path)
            except FileNotFoundError:
                continue

            fm, _ = self._parse_frontmatter(text)
            ver = self._extract_version(fname) or 0
            result.append(VersionMeta(
                target_type=fm.get('section_id') and 'section' or fm.get('file_path') and 'file' or 'section',
                target_id=fm.get('section_id') or fm.get('file_path') or fname,
                version=ver,
                storage_path=full_path,
                description=(
                    fm.get('description', '') or
                    fm.get('note', '')  # 向后兼容：旧版本YAML有note无description → 自动迁移
                ),
                created_at=fm.get('created_at', ''),
                baselines=fm.get('baselines', []),
            ))

        result.sort(key=lambda v: v.version, reverse=True)
        return result

    # ── 更新备份说明（DT-19）──────────────────────────────

    def update_backup_description(self, storage_path: str,
                                  description: str) -> None:
        """DT-19: 更新备份文件的 YAML description 字段。

        ① 读备份文件
        ② 解析 YAML frontmatter
        ③ 修改 description 字段
        ④ 写回文件

        Raises:
            FileNotFoundError: 备份文件不存在
        """
        text = self.fs.read_file(storage_path)
        fm, body = self._parse_frontmatter(text)
        fm['description'] = description
        updated = self._build_frontmatter(fm) + '\n' + body
        self.fs.write_file(storage_path, updated)

    # ── 版本恢复（DT-11）──────────────────────────────────

    def restore_version(self, storage_path: str) -> str:
        """DT-11: 读取指定版本文件，返回 YAML frontmatter 之后的内容。"""
        text = self.fs.read_file(storage_path)
        return self._read_content_after_frontmatter(text).lstrip('\n')

    # ── 基线管理（DT-12, DT-13, DT-14）────────────────────

    def create_baseline(self, name: str) -> dict:
        """DT-12: 创建基线清单文件。返回基线元信息 dict。"""
        baselines_dir = self._join(self.backups_dir, 'baselines')
        self.fs.ensure_dir(baselines_dir)

        baseline_path = self._join(baselines_dir, f'{name}.md')
        created_at = self._now_iso()

        meta = {
            'name': name,
            'created_at': created_at,
        }
        content = self._build_frontmatter(meta) + '\n## 包含的版本快照\n\n'
        self.fs.write_file(baseline_path, content)

        return {
            'name': name,
            'created_at': created_at,
            'version_count': 0,
        }

    def add_to_baseline(self, baseline_name: str,
                        version_meta: VersionMeta):
        """DT-13: 向基线添加版本快照引用。

        ① 读基线清单文件
        ② 追加版本快照行
        ③ 更新 version_meta 的 baselines 字段
        ④ 写回版本快照文件的 YAML frontmatter
        """
        baselines_dir = self._join(self.backups_dir, 'baselines')
        baseline_path = self._join(baselines_dir, f'{baseline_name}.md')

        # 读基线文件
        text = self.fs.read_file(baseline_path)
        fm, body = self._parse_frontmatter(text)

        # 追加版本快照引用行
        new_line = f'| {version_meta.target_id} | {version_meta.storage_path} |\n'
        updated_body = body.rstrip('\n') + '\n' + new_line

        # 更新基线文件
        updated_text = self._build_frontmatter(fm) + '\n' + updated_body
        self.fs.write_file(baseline_path, updated_text)

        # 更新 version_meta 的 baselines 字段
        if baseline_name not in version_meta.baselines:
            version_meta.baselines.append(baseline_name)

        # 读版本快照文件，更新其 YAML frontmatter
        try:
            ver_text = self.fs.read_file(version_meta.storage_path)
            ver_fm, ver_body = self._parse_frontmatter(ver_text)
            if 'baselines' not in ver_fm:
                ver_fm['baselines'] = []
            if baseline_name not in ver_fm['baselines']:
                ver_fm['baselines'].append(baseline_name)
            updated_ver = self._build_frontmatter(ver_fm) + '\n' + ver_body
            self.fs.write_file(version_meta.storage_path, updated_ver)
        except FileNotFoundError:
            pass

    def restore_baseline(self, name: str) -> dict[str, str]:
        """DT-14: 恢复基线——将基线中所有版本快照写回原文件。

        返回 {原文件路径: 恢复后的内容} 映射。
        """
        baselines_dir = self._join(self.backups_dir, 'baselines')
        baseline_path = self._join(baselines_dir, f'{name}.md')

        try:
            text = self.fs.read_file(baseline_path)
        except FileNotFoundError:
            raise FileNotFoundError(f'基线不存在: {name}')

        _, body = self._parse_frontmatter(text)

        # 解析版本快照引用行
        # 格式: | target_id | storage_path |
        restored: dict[str, str] = {}
        for line in body.strip().split('\n'):
            line = line.strip()
            if not line.startswith('|') or not line.endswith('|'):
                continue
            parts = [p.strip() for p in line.strip('|').split('|')]
            if len(parts) >= 2:
                target_id, storage_path = parts[0], parts[1]
                content = self.restore_version(storage_path)
                self.fs.write_file(target_id, content)
                restored[target_id] = content

        return restored

    # ── IT-11b 新增：备份删除 ────────────────────────────

    def delete_backup(self, storage_path: str) -> None:
        """IT-11b DT-10: 删除单个备份文件。

        Raises:
            FileNotFoundError: 备份文件不存在
        """
        target = Path(storage_path)
        if not target.exists():
            raise FileNotFoundError(f'备份文件不存在: {storage_path}')
        target.unlink()

    # ── IT-11b 新增：基线列表/详情/删除 ─────────────────

    def list_baselines(self) -> list[dict]:
        """IT-11b DT-15: 列出所有基线及其元信息。

        返回列表，每项 dict: {name, note, created_at, file_count}
        """
        baselines_dir = self._join(self.backups_dir, 'baselines')
        try:
            self.fs.ensure_dir(baselines_dir)
            files = self.fs.list_dir(baselines_dir)
        except Exception:
            return []

        result = []
        for fname in files:
            if not fname.endswith('.md'):
                continue
            name = fname[:-3]  # 去掉 .md
            try:
                text = self.fs.read_file(self._join(baselines_dir, fname))
            except Exception:
                continue
            fm, body = self._parse_frontmatter(text)
            # 计算文件数（| target | path | 行）
            file_count = 0
            for line in body.strip().split('\n'):
                line = line.strip()
                if line.startswith('|') and line.endswith('|'):
                    parts = [p.strip() for p in line.strip('|').split('|')]
                    if len(parts) >= 2:
                        file_count += 1

            result.append({
                'name': name,
                'note': fm.get('note', ''),
                'created_at': fm.get('created_at', ''),
                'file_count': file_count,
                'is_factory': name == 'v1-出厂基线',
            })

        result.sort(key=lambda b: b['created_at'], reverse=True)
        return result

    def get_baseline_files(self, name: str) -> list[dict]:
        """IT-11b DT-15: 获取基线中的文件清单。

        返回每项: {target_id, storage_path, version, description}

        Raises:
            FileNotFoundError: 基线不存在
        """
        baselines_dir = self._join(self.backups_dir, 'baselines')
        baseline_path = self._join(baselines_dir, f'{name}.md')

        try:
            text = self.fs.read_file(baseline_path)
        except FileNotFoundError:
            raise FileNotFoundError(f'基线不存在: {name}')

        _, body = self._parse_frontmatter(text)
        files = []
        for line in body.strip().split('\n'):
            line = line.strip()
            if not line.startswith('|') or not line.endswith('|'):
                continue
            parts = [p.strip() for p in line.strip('|').split('|')]
            if len(parts) >= 2:
                target_id, storage_path = parts[0], parts[1]
                # 尝试从备份文件读取 version 和 description
                version = 0
                description = ''
                try:
                    ver_text = self.fs.read_file(storage_path)
                    fm, _ = self._parse_frontmatter(ver_text)
                    version = fm.get('version', 0)
                    description = fm.get('description', '')
                except Exception:
                    pass
                files.append({
                    'target_id': target_id,
                    'storage_path': storage_path,
                    'version': version,
                    'description': description,
                })
        return files

    def delete_baseline(self, name: str) -> None:
        """IT-11b DT-15: 删除基线清单文件。

        Raises:
            ValueError: 尝试删除出厂基线
            FileNotFoundError: 基线不存在
        """
        if name == 'v1-出厂基线':
            raise ValueError('出厂基线不可删除')

        baselines_dir = self._join(self.backups_dir, 'baselines')
        baseline_path = self._join(baselines_dir, f'{name}.md')

        target = Path(baseline_path)
        if not target.exists():
            raise FileNotFoundError(f'基线不存在: {name}')
        target.unlink()
