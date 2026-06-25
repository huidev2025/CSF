# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
FileSystemOps — 文件系统操作封装。

统一封装所有文件 I/O 操作，供 BackupEngine/Service 层使用。
所有相对路径自动拼接到 csf_lite_root，绝对路径直接使用。
"""

import os
import re
from pathlib import Path
from typing import Optional

from src.core.models import TreeNode


class FileSystemOps:
    """文件系统操作封装 — 统一路径管理与原子写入。"""

    def __init__(self, csf_lite_root: str, csf_clarity_dir: str):
        """DT-01: 初始化文件系统操作实例。

        Args:
            csf_lite_root: csf-lite/ 内核文件根目录
            csf_clarity_dir: csf-clarity/ 私有数据目录
        """
        self.csf_lite_root = Path(csf_lite_root).resolve()
        self.csf_clarity_dir = Path(csf_clarity_dir).resolve()

    # ── 路径解析 ──────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        """解析路径：绝对路径直接用，相对路径拼接到 csf_lite_root。"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.csf_lite_root / p

    # ── 基本读写（DT-02, DT-03）───────────────────────────

    def read_file(self, path: str) -> str:
        """DT-02: 读文件全文，UTF-8 编码。文件不存在 → FileNotFoundError。"""
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"文件不存在: {target}")
        return target.read_text(encoding='utf-8')

    def write_file(self, path: str, content: str):
        """DT-03: 写文件全文，原子写入（.tmp → rename），自动创建父目录。"""
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = target.with_suffix(target.suffix + '.tmp')
        try:
            tmp_path.write_text(content, encoding='utf-8')
            os.replace(str(tmp_path), str(target))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    # ── 目录操作（DT-04）──────────────────────────────────

    def ensure_dir(self, path: str):
        """DT-04: 确保目录存在。"""
        target = self._resolve(path)
        target.mkdir(parents=True, exist_ok=True)

    def list_dir(self, path: str) -> list[str]:
        """列出目录中的文件和子目录名（仅名称，不含路径）。目录不存在 → 返回空列表。"""
        target = self._resolve(path)
        if not target.exists() or not target.is_dir():
            return []
        return sorted([p.name for p in target.iterdir()])

    # ── 目录树（DT-05）───────────────────────────────────

    def list_tree(self, root: str, file_meta: Optional[dict] = None) -> TreeNode:
        """DT-05: 递归扫描目录，返回 TreeNode 树结构。

        排除：隐藏文件（.开头）和 .versions/ 目录。
        可选 file_meta dict 用于填充 description 字段。
        """
        if file_meta is None:
            file_meta = {}

        root_path = self._resolve(root)
        return self._build_tree(root_path, root_path, file_meta)

    # 文件树中排除的二进制/不可读文件后缀
    _BINARY_EXTS = {'.exe', '.dll', '.pyd', '.so', '.pyc', '.pyo',
                    '.db', '.sqlite', '.bin', '.dat',
                    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.bmp',
                    '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar'}

    def _build_tree(self, base: Path, current: Path,
                    file_meta: dict) -> TreeNode:
        """递归构建 TreeNode。排除隐藏文件、.versions/、二进制文件。"""
        name = current.name
        rel_path = str(current.relative_to(base)).replace('\\', '/')
        if rel_path == '.':
            rel_path = name

        is_dir = current.is_dir()

        if is_dir:
            children: list[TreeNode] = []
            try:
                entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                entries = []

            for entry in entries:
                # 排除隐藏文件、.versions/、二进制文件
                if entry.name.startswith('.') or entry.name == '.versions':
                    continue
                if entry.is_file() and entry.suffix.lower() in self._BINARY_EXTS:
                    continue
                children.append(self._build_tree(base, entry, file_meta))

            return TreeNode(
                name=name,
                path=rel_path,
                is_dir=True,
                children=children,
            )
        else:
            description = file_meta.get(rel_path)
            return TreeNode(
                name=name,
                path=rel_path,
                is_dir=False,
                description=description,
            )

    # ── Staging 操作（DT-06）──────────────────────────────

    def _staging_path(self) -> Path:
        """返回 staging/pending.md 的完整路径。"""
        return self.csf_lite_root / 'staging' / 'pending.md'

    def write_staging(self, content: str):
        """DT-06: 写 staging/pending.md。"""
        self.write_file(str(self._staging_path()), content)

    def read_staging(self) -> str:
        """DT-06: 读 staging/pending.md。"""
        return self.read_file(str(self._staging_path()))

    def delete_staging(self):
        """DT-06: 删除 staging/pending.md。"""
        target = self._staging_path()
        if target.exists():
            target.unlink()
