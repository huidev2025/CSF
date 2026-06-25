# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
SpecsService V2 — 规范文件服务：浏览/编辑/备份/恢复/全局基线。

纯文件驱动，通过 FileSystemOps + BackupEngine 完成所有 I/O。
file_meta.json 独立存储文件说明，与正文解耦。
"""

import json
import os
from pathlib import Path
from typing import Optional

from src.core.models import TreeNode, VersionMeta
from src.core.file_system_ops import FileSystemOps
from src.core.backup_engine import BackupEngine


# ── 出厂文件判定常量 ──────────────────────────────────────

FACTORY_ROOTS = (
    'core/',
    'protocols/',
    'knowledge/methods/',
    'knowledge/redlines/',
    'knowledge/crafts/',
    'cos-context.md',
    'dev-context.md',
    'README.md',
    'QUICKSTART.md',
)

COS_CONTEXT_WARNING = '⚠️ 建议通过标签2（会话上下文）编辑此文件'


class SpecsService:
    """规范文件服务 — 文件树/编辑/版本/备份/基线。"""

    # ── DT-01 ──────────────────────────────────────────────

    def __init__(self, fs: FileSystemOps, backup: BackupEngine,
                 csf_lite_root: str, csf_clarity_dir: str):
        """DT-01: 初始化，加载 file_meta.json。

        Args:
            fs: FileSystemOps 实例
            backup: BackupEngine 实例
            csf_lite_root: csf-lite/ 目录绝对路径
            csf_clarity_dir: csf-clarity/ 目录绝对路径
        """
        self.fs = fs
        self.backup = backup
        self.csf_lite_root = Path(csf_lite_root).resolve()
        self.csf_clarity_dir = Path(csf_clarity_dir).resolve()
        self._file_meta: dict[str, str] = {}

        # 加载 file_meta.json
        meta_path = self.csf_clarity_dir / 'file_meta.json'
        if meta_path.exists():
            try:
                self._file_meta = json.loads(meta_path.read_text('utf-8'))
            except (json.JSONDecodeError, OSError):
                self._file_meta = {}

    # ── 内部：file_meta 持久化 ─────────────────────────────

    def _save_file_meta(self):
        """DT-11: 原子写入 file_meta.json。"""
        meta_path = self.csf_clarity_dir / 'file_meta.json'
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = meta_path.with_suffix('.tmp')
        tmp.write_text(
            json.dumps(self._file_meta, ensure_ascii=False, indent=2),
            encoding='utf-8')
        os.replace(str(tmp), str(meta_path))

    # ── 内部：出厂文件判定 ─────────────────────────────────

    @staticmethod
    def _is_factory(rel_path: str) -> bool:
        """判断文件是否为出厂文件。"""
        # 精确匹配
        if rel_path in FACTORY_ROOTS:
            return True
        # 前缀匹配
        for root in FACTORY_ROOTS:
            if root.endswith('/') and rel_path.startswith(root):
                return True
        return False

    @staticmethod
    def _rule_name(rel_path: str) -> str:
        """DT-03/IT-03d: 从相对路径提取规则名称。core/守则.md → 守则"""
        return Path(rel_path).stem

    @staticmethod
    def _get_description(rel_path: str, file_meta: dict) -> Optional[str]:
        """获取文件说明，cos-context.md 特殊处理。v4: 键迁移为规则名。"""
        if rel_path == 'cos-context.md':
            return COS_CONTEXT_WARNING
        return file_meta.get(SpecsService._rule_name(rel_path))

    # ── DT-02: 文件树 ──────────────────────────────────────

    def get_file_tree(self) -> TreeNode:
        """DT-02: 获取完整文件树，含 is_factory 和 description。"""
        tree = self.fs.list_tree(str(self.csf_lite_root))

        def _post_process(node: TreeNode):
            if not node.is_dir:
                node.is_factory = self._is_factory(node.path)
                node.description = self._get_description(
                    node.path, self._file_meta)
            for child in node.children:
                _post_process(child)

        _post_process(tree)
        return tree

    # ── IT-03e DT-01: 全文搜索 ─────────────────────────────

    def search_files(self, query: str) -> list[str]:
        """DT-01: 全文搜索 csf-lite/ 下所有 .md 文件正文。

        Args:
            query: 搜索关键词（不区分大小写）

        Returns:
            匹配文件相对路径列表（按路径排序）。
            空 query 返回空列表（UI 层用空列表 = 不执行过滤，显示完整树）。
        """
        if not query or not query.strip():
            return []

        q = query.lower()
        matched: list[str] = []

        tree = self.get_file_tree()

        def _search(node: TreeNode):
            if not node.is_dir:
                try:
                    content = self.fs.read_file(node.path)
                except Exception:
                    return
                if q in content.lower():
                    matched.append(node.path)
            for child in node.children:
                _search(child)

        _search(tree)
        matched.sort()
        return matched

    # ── DT-03: 打开文件 ────────────────────────────────────

    def open_file(self, rel_path: str) -> dict:
        """DT-03: 打开文件，返回 content/description/is_factory/path。

        Raises:
            FileNotFoundError: 文件不存在
        """
        content = self.fs.read_file(rel_path)
        description = self._get_description(rel_path, self._file_meta)
        is_factory = self._is_factory(rel_path)

        return {
            'content': content,
            'description': description or '',
            'is_factory': is_factory,
            'path': rel_path,
        }

    # ── DT-04: 保存文件（随手保存，不产生版本）──────────────

    def save_file(self, rel_path: str, content: str):
        """DT-04: 直接写入文件，不产生版本备份。"""
        self.fs.write_file(rel_path, content)

    # ── DT-05: 保存新版本（里程碑保存）─────────────────────

    def save_new_version(self, rel_path: str, content: str,
                         description: str = '') -> VersionMeta:
        """DT-05: 保存新版本 — 先备份再写当前文件。

        v4 (IT-03d): description 可选。留空时取正文前30字符截断为前20字作回退摘要。
        """
        if not description or not description.strip():
            # 取正文前30字符，回溯到非空白字符边界作为前20字摘要
            raw = content[:30]
            desc = raw.rstrip()
            if not desc:
                desc = content[:20].strip() or '(无内容)'
            description = desc

        # 先备份当前内容（含 description）
        vm = self.backup.save_file_backup(rel_path, content, description)

        # 再写当前文件
        self.fs.write_file(rel_path, content)

        # 保存后同步更新当前版本的 file_meta 说明（v4: 键为规则名）
        if description:
            self._file_meta[self._rule_name(rel_path)] = description
            self._save_file_meta()

        return vm

    # ── DT-06: 新建文件 ────────────────────────────────────

    def new_file(self, rel_path: str, content: str = "",
                 parent_dir: str = "") -> str:
        """DT-06: 创建新文件并在 file_meta 注册空说明。

        v3 (DT-20): 新增 parent_dir 参数实现智能目录。
        v4 (IT-03d): 新增同名检查——规则名已在 file_meta 中存在则拦截。

        Raises:
            ValueError: 同名规则已存在
        """
        # 智能目录：有 parent_dir 则拼接
        if parent_dir:
            rel_path = str(Path(parent_dir) / rel_path).replace('\\', '/')

        # v4: 同名检查
        rule_name = self._rule_name(rel_path)
        if rule_name in self._file_meta:
            raise ValueError(f'同名规则已存在: {rule_name}')

        self.fs.write_file(rel_path, content)
        self._file_meta[self._rule_name(rel_path)] = ""
        self._save_file_meta()
        return rel_path

    # ── DT-07: 删除文件 ────────────────────────────────────

    def delete_file(self, rel_path: str):
        """DT-07: 删除文件及 file_meta 条目。出厂文件不可删除。

        Raises:
            ValueError: 出厂文件
            FileNotFoundError: 文件不存在
        """
        if self._is_factory(rel_path):
            raise ValueError(f'出厂文件不可删除: {rel_path}')

        target = self.fs._resolve(rel_path)
        if not target.exists():
            raise FileNotFoundError(f'文件不存在: {rel_path}')

        target.unlink()

        # 清理 file_meta（v4: 键为规则名）
        self._file_meta.pop(self._rule_name(rel_path), None)
        self._save_file_meta()

    # ── DT-08: 版本历史 ────────────────────────────────────

    def get_version_history(self, rel_path: str) -> list[VersionMeta]:
        """DT-08: 获取文件的所有备份版本（降序）。"""
        backup_dir = str(Path(self.backup.backups_dir) / 'files' / rel_path)
        versions = self.backup.scan_version_history(backup_dir)
        versions.sort(key=lambda v: v.version, reverse=True)
        return versions

    # ── DT-09: 恢复版本 ────────────────────────────────────

    def restore_version(self, storage_path: str) -> str:
        """DT-09: 恢复指定版本的内容（纯正文，不含frontmatter）。"""
        return self.backup.restore_version(storage_path)

    # ── DT-10: 全局基线 ────────────────────────────────────

    def create_global_baseline(self, name: str) -> dict:
        """DT-10: 创建全局基线清单文件。v4: 移除 note 参数。"""
        return self.backup.create_baseline(name)

    # ── DT-11: 更新文件说明 ─────────────────────────────────

    def update_file_description(self, rel_path: str, description: str):
        """DT-11: 更新文件说明并持久化到 file_meta.json。v4: 键为规则名。"""
        self._file_meta[self._rule_name(rel_path)] = description
        self._save_file_meta()

    # ══════════════════════════════════════════════════════════
    # IT-11b DT-10: 删除
    # ══════════════════════════════════════════════════════════

    def delete_current_version(self, rel_path: str) -> dict:
        """DT-10: 删除当前版本——删源文件+file_meta条目。

        返回 {fallback_type, fallback_path, fallback_label}
        - fallback_type: 'backup' | 'factory_baseline' | 'none'
        - fallback_path: 自动打开的文件路径（备份storage_path 或 出厂源文件abs路径）
        - fallback_label: 视图标题文本

        Raises:
            ValueError: 出厂文件不可删除当前版本
            FileNotFoundError: 文件不存在
        """
        if self._is_factory(rel_path):
            raise ValueError(f'出厂文件的当前版本不可删除: {rel_path}')

        target = self.fs._resolve(rel_path)
        if not target.exists():
            raise FileNotFoundError(f'文件不存在: {rel_path}')

        # 先查最新备份
        versions = self.get_version_history(rel_path)

        # 删除源文件
        target.unlink()

        # 清理 file_meta（v4: 键为规则名）
        self._file_meta.pop(self._rule_name(rel_path), None)
        self._save_file_meta()

        if versions:
            # 有备份 → 打开最新备份
            latest = versions[0]
            return {
                'fallback_type': 'backup',
                'fallback_path': latest.storage_path,
                'fallback_version': latest.version,
                'fallback_description': latest.description or '',
                'fallback_label': f'{rel_path} · v{latest.version}（历史版本）',
            }
        else:
            # 无备份 → 检查是否有出厂基线可恢复
            factory_path = self.csf_lite_root / rel_path
            if not factory_path.exists():
                # 出厂文件被删？尝试从出厂基线恢复
                try:
                    factory_versions = [
                        v for v in self.get_version_history(rel_path)
                        if 'v1-出厂基线' in (v.baselines or [])
                    ]
                    # 上面已经查过版本历史为空，这里不再重复
                    pass
                except Exception:
                    pass

            return {
                'fallback_type': 'none',
                'fallback_path': '',
                'fallback_version': 0,
                'fallback_description': '',
                'fallback_label': '该文件已被删除',
            }

    def delete_backup_version(self, storage_path: str,
                              rel_path: str) -> None:
        """DT-10: 删除单个备份版本。

        Raises:
            FileNotFoundError: 备份文件不存在
        """
        self.backup.delete_backup(storage_path)

    # ══════════════════════════════════════════════════════════
    # IT-11b DT-11: 应用为当前版本
    # ══════════════════════════════════════════════════════════

    def apply_version(self, storage_path: str, rel_path: str,
                      backup_first: bool = False) -> dict:
        """DT-11: 将历史版本应用为当前版本。v4: 移除 backup_note 参数。

        Args:
            storage_path: 备份文件路径
            rel_path: 目标文件相对路径
            backup_first: 是否先备份当前版本

        Returns:
            {version, description, rel_path}
        """
        # 读取备份内容
        content = self.backup.restore_version(storage_path)

        # 读取备份的 description
        try:
            text = self.fs._resolve(storage_path).read_text(encoding='utf-8')
        except Exception:
            text = ''
        fm, _ = self.backup._parse_frontmatter(text)
        description = fm.get('description', '')

        # 如需先备份当前版本
        if backup_first:
            try:
                current_content = self.fs.read_file(rel_path)
                self.backup.save_file_backup(
                    rel_path, current_content,
                    self._file_meta.get(self._rule_name(rel_path), ''))
            except FileNotFoundError:
                pass  # 当前文件不存在（可能已被删除），跳过备份

        # 写回 csf-lite
        self.fs.write_file(rel_path, content)

        # 同步 description 到 file_meta（v4: 键为规则名）
        if description:
            self._file_meta[self._rule_name(rel_path)] = description
            self._save_file_meta()

        return {
            'rel_path': rel_path,
            'description': description,
        }

    # ══════════════════════════════════════════════════════════
    # IT-11b DT-14: 全局备份重做
    # ══════════════════════════════════════════════════════════

    def global_backup_all(self, name: str,
                          progress_callback=None) -> dict:
        """DT-14: 备份文件树中所有文件（出厂+用户），归入新基线。v4: note→name。

        Args:
            name: 基线名称
            progress_callback: callable(current, total, filename)
                              返回 False 则中止

        Returns:
            {name, file_count, created_at}
        """
        tree = self.get_file_tree()

        # 收集所有文件
        all_files: list[str] = []

        def _collect(node: TreeNode):
            if not node.is_dir:
                all_files.append(node.path)
            for child in node.children:
                _collect(child)

        _collect(tree)
        total = len(all_files)

        # 创建基线
        baseline = self.backup.create_baseline(name)

        for i, rel_path in enumerate(all_files):
            if progress_callback:
                cont = progress_callback(i + 1, total, rel_path)
                if cont is False:
                    break

            try:
                content = self.fs.read_file(rel_path)
                description = self._file_meta.get(self._rule_name(rel_path), '')
                vm = self.backup.save_file_backup(
                    rel_path, content, description)
                self.backup.add_to_baseline(name, vm)
            except FileNotFoundError:
                continue  # 文件可能在扫描后被删除

        return {
            'name': name,
            'file_count': total,
            'created_at': baseline['created_at'],
        }

    # ══════════════════════════════════════════════════════════
    # IT-11b DT-15: 基线管理
    # ══════════════════════════════════════════════════════════

    def baseline_list(self) -> list[dict]:
        """DT-15: 列出所有基线。"""
        return self.backup.list_baselines()

    def baseline_get_files(self, name: str) -> list[dict]:
        """DT-15: 获取基线内文件清单。"""
        return self.backup.get_baseline_files(name)

    def baseline_delete(self, name: str) -> None:
        """DT-15: 删除基线。"""
        self.backup.delete_baseline(name)

    def baseline_restore(self, name: str, backup_first: bool = False,
                         progress_callback=None) -> dict:
        """DT-15: 批量恢复基线。

        Args:
            name: 基线名称
            backup_first: 是否先备份所有当前文件
            progress_callback: callable(current, total, filename)

        Returns:
            {restored_count, total_count}
        """
        files = self.backup.get_baseline_files(name)
        total = len(files)

        if backup_first:
            # 先备份所有当前文件
            for i, f in enumerate(files):
                try:
                    current = self.fs.read_file(f['target_id'])
                    self.backup.save_file_backup(
                        f['target_id'], current,
                        f'恢复基线「{name}」前的自动备份',
                        self._file_meta.get(self._rule_name(f['target_id']), ''))
                except FileNotFoundError:
                    pass

        restored = 0
        for i, f in enumerate(files):
            if progress_callback:
                cont = progress_callback(i + 1, total, f['target_id'])
                if cont is False:
                    break

            try:
                content = self.backup.restore_version(f['storage_path'])
                self.fs.write_file(f['target_id'], content)
                if f.get('description'):
                    self._file_meta[self._rule_name(f['target_id'])] = f['description']
                restored += 1
            except Exception:
                continue

        if restored > 0:
            self._save_file_meta()

        return {'restored_count': restored, 'total_count': total}

    def baseline_export(self, name: str, export_dir: str,
                        progress_callback=None) -> str:
        """DT-15: 导出基线到指定目录。

        按原目录结构导出 + _baseline_manifest.json。

        Returns:
            manifest 文件路径
        """
        files = self.backup.get_baseline_files(name)
        total = len(files)
        export_root = Path(export_dir)

        manifest = {
            'baseline_name': name,
            'exported_at': BackupEngine._now_iso(),
            'file_count': total,
            'files': [],
        }

        for i, f in enumerate(files):
            if progress_callback:
                cont = progress_callback(i + 1, total, f['target_id'])
                if cont is False:
                    break

            try:
                content = self.backup.restore_version(f['storage_path'])
                dest = export_root / f['target_id']
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding='utf-8')
                manifest['files'].append({
                    'path': f['target_id'],
                    'version': f.get('version', 0),
                    'description': f.get('description', ''),
                })
            except Exception:
                continue

        manifest_path = export_root / '_baseline_manifest.json'
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding='utf-8')

        return str(manifest_path)

    # ══════════════════════════════════════════════════════════
    # IT-11b DT-16: 未应用规则
    # ══════════════════════════════════════════════════════════

    def get_unapplied_rules(self) -> list[dict]:
        """DT-16: 扫描所有文件的非当前版本备份，跨文件集中展示。

        返回 [{file_name, version, storage_path, description_first_line}]
        """
        import re as _re

        result = []
        backups_files_dir = Path(self.backup.backups_dir) / 'files'

        if not backups_files_dir.exists():
            return result

        # 遍历 backups/files/ 下所有子目录
        for root, dirs, files in os.walk(str(backups_files_dir)):
            for fname in files:
                if not fname.endswith('.md'):
                    continue
                storage_path = str(Path(root) / fname)

                # 提取相对路径
                rel = str(Path(storage_path).relative_to(
                    str(backups_files_dir)))
                # 去掉最后的 /vNNN.md → 得到文件路径
                file_rel = str(Path(rel).parent).replace('\\', '/')
                if file_rel == '.':
                    continue

                try:
                    text = Path(storage_path).read_text(encoding='utf-8')
                except Exception:
                    continue

                fm, _ = self.backup._parse_frontmatter(text)
                version = fm.get('version', 0)
                description = fm.get('description', '')

                # 提取说明首行
                desc_first = ''
                if description:
                    desc_lines = description.strip().split('\n')
                    desc_first = desc_lines[0] if desc_lines else ''

                result.append({
                    'file_name': file_rel,
                    'version': version,
                    'storage_path': storage_path,
                    'description_first_line': desc_first,
                })

        # 按文件名+版本号排序
        result.sort(key=lambda r: (r['file_name'], -r['version']))
        return result
