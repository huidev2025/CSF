# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
PromptStore — 提示词纯文件持久化（V3）。

v2→v3 关键差异：去掉版本管理（无 .versions/ 目录、无版本快照）、
分组即目录（单一真相源）、文件名=说明的安全化、收藏用 _favorites.json。
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from src.core.models import Prompt

# 文件名非法字符正则（Windows + Linux 交集）
_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*]')


class PromptStore:
    """提示词纯文件持久化 v3 — 分组扫描 + 文件读写 + 收藏管理。"""

    def __init__(self, prompts_dir: str):
        """初始化，保存 prompts/ 根目录路径（不自动创建目录）。"""
        self.prompts_dir = Path(prompts_dir)

    # ══════════════════════════════════════════════════════════
    # DT-02 · 分组扫描
    # ══════════════════════════════════════════════════════════

    def get_groups(self) -> list[str]:
        """扫描 prompts_dir/ 下所有子目录名作为分组列表。

        规则：
        - 仅返回子目录（排除文件）
        - 排除隐藏目录（以 . 开头，如 .versions/）
        - 排除 _favorites.json（它是文件，自然被排除）
        - 优先使用 _group_order.json 排序；不在排序文件中的分组按字母排末尾
        - 若 prompts_dir/ 不存在 → 返回空列表 []
        """
        if not self.prompts_dir.exists():
            return []
        # 扫描磁盘上的实际分组
        disk_groups = set(
            d.name for d in self.prompts_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        )
        if not disk_groups:
            return []
        # 加载保存的排序
        saved_order = self._load_group_order()
        # 按保存顺序排列，不在保存列表中的按字母排末尾
        ordered = [g for g in saved_order if g in disk_groups]
        new_groups = sorted(disk_groups - set(ordered))
        ordered.extend(new_groups)
        return ordered

    # ══════════════════════════════════════════════════════════
    # 分组排序持久化
    # ══════════════════════════════════════════════════════════

    def _group_order_path(self) -> Path:
        """_group_order.json 文件路径。"""
        return self.prompts_dir / '_group_order.json'

    def _load_group_order(self) -> list[str]:
        """加载分组排序列表。

        Returns:
            list[str]: 分组名列表，按保存顺序。文件不存在/损坏 → 返回 []
        """
        path = self._group_order_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return [item for item in data if isinstance(item, str)]
        except Exception:
            pass
        return []

    def _save_group_order(self, order: list[str]) -> None:
        """覆写分组排序列表。原子写：临时文件 → os.replace。

        Args:
            order: 分组名列表（按所需显示顺序）
        """
        path = self._group_order_path()
        content = json.dumps(order, ensure_ascii=False, indent=2) + '\n'
        tmp_path = path.with_suffix('.tmp')
        try:
            tmp_path.write_text(content, encoding='utf-8')
            os.replace(str(tmp_path), str(path))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def reorder_group(self, group_name: str, target_index: int) -> None:
        """将分组移动到目标位置。

        Args:
            group_name: 待移动的分组名
            target_index: 目标索引（0-based，在分组列表中的位置）

        Raises:
            ValueError: 分组不存在
        """
        current_order = self._load_group_order()
        # 扫描磁盘确保分组存在
        if not (self.prompts_dir / group_name).is_dir():
            raise ValueError(f'分组不存在: {group_name}')

        # 确保所有磁盘分组都在排序中
        disk_groups = set(
            d.name for d in self.prompts_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        )
        for g in disk_groups:
            if g not in current_order:
                current_order.append(g)

        # 移除旧位置
        if group_name in current_order:
            current_order.remove(group_name)

        # 插入到目标位置（clamp 到有效范围）
        target_index = max(0, min(target_index, len(current_order)))
        current_order.insert(target_index, group_name)

        # 仅保留磁盘中实际存在的分组
        current_order = [g for g in current_order if g in disk_groups]

        self._save_group_order(current_order)

    def _remove_group_from_order(self, group_name: str) -> None:
        """从排序文件中移除分组（分组删除时调用）。"""
        order = self._load_group_order()
        if group_name in order:
            order.remove(group_name)
            self._save_group_order(order)

    # ══════════════════════════════════════════════════════════
    # DT-02b · 重命名分组
    # ══════════════════════════════════════════════════════════

    def rename_group(self, old_name: str, new_name: str) -> None:
        """重命名分组目录，同步更新收藏引用。

        Args:
            old_name: 当前分组名
            new_name: 新分组名（需已 sanitize）

        Raises:
            FileNotFoundError: old_name 目录不存在
            FileExistsError: new_name 目录已存在
            ValueError: 名称为空
            OSError: 目录重命名失败
        """
        if not old_name or not new_name:
            raise ValueError('分组名不能为空')

        old_dir = self.prompts_dir / old_name
        new_dir = self.prompts_dir / new_name

        if not old_dir.is_dir():
            raise FileNotFoundError(f'分组不存在: {old_name}')
        if new_dir.exists():
            raise FileExistsError(f'目标分组已存在: {new_name}')

        # ① 重命名目录
        old_dir.rename(new_dir)

        # ② 更新收藏引用：所有 old_name/xxx → new_name/xxx
        favs = self.get_favorites()
        prefix = old_name + '/'
        updated = False
        for i, entry in enumerate(favs):
            if entry.startswith(prefix):
                favs[i] = new_name + '/' + entry[len(prefix):]
                updated = True
        if updated:
            self.save_favorites(favs)

        # ③ 更新排序文件中的分组名
        order = self._load_group_order()
        if old_name in order:
            idx = order.index(old_name)
            order[idx] = new_name
            self._save_group_order(order)

    # ══════════════════════════════════════════════════════════
    # DT-02c · 删除分组
    # ══════════════════════════════════════════════════════════

    def delete_group(self, group_name: str) -> int:
        """删除分组目录及组内全部提示词，清理收藏引用。

        Args:
            group_name: 待删除的分组名

        Returns:
            int: 删除的提示词文件数量

        Raises:
            FileNotFoundError: 分组目录不存在
            ValueError: 名称为空
            OSError: 目录删除失败
        """
        if not group_name:
            raise ValueError('分组名不能为空')

        group_dir = self.prompts_dir / group_name
        if not group_dir.is_dir():
            raise FileNotFoundError(f'分组不存在: {group_name}')

        # ① 统计并删除组内所有 .md 文件
        deleted_count = 0
        for f in group_dir.glob('*.md'):
            if f.is_file():
                f.unlink()
                deleted_count += 1

        # ② 删除目录（此时应已空）
        import shutil
        shutil.rmtree(group_dir)

        # ③ 清理收藏引用：移除所有 old_name/xxx 条目
        favs = self.get_favorites()
        prefix = group_name + '/'
        new_favs = [e for e in favs if not e.startswith(prefix)]
        if len(new_favs) != len(favs):
            self.save_favorites(new_favs)

        # ④ 清理排序文件
        self._remove_group_from_order(group_name)

        return deleted_count

    # ══════════════════════════════════════════════════════════
    # DT-02d · 创建分组
    # ══════════════════════════════════════════════════════════

    def create_group(self, group_name: str) -> None:
        """创建空分组目录。

        Args:
            group_name: 新分组名

        Raises:
            ValueError: 名称为空或已存在
        """
        if not group_name or not group_name.strip():
            raise ValueError('分组名不能为空')
        group_name = group_name.strip()
        group_dir = self.prompts_dir / group_name
        if group_dir.exists():
            raise ValueError(f'分组已存在: {group_name}')
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        group_dir.mkdir()

    # ══════════════════════════════════════════════════════════
    # DT-03a · 文件名 sanitize
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _sanitize_filename(description: str) -> str:
        """将说明文字安全化为文件名。

        规则：
        - 去除 Windows/Linux 文件名非法字符：< > : " / \\ | ? *
        - 去除首尾空白
        - 若结果为空 → 返回 'untitled'
        - 追加 .md 后缀
        """
        cleaned = _ILLEGAL_CHARS.sub('', description).strip()
        if not cleaned:
            cleaned = 'untitled'
        return f'{cleaned}.md'

    # ══════════════════════════════════════════════════════════
    # DT-03b · 读取提示词
    # ══════════════════════════════════════════════════════════

    def load_prompt(self, group: str, filename: str) -> Optional[Prompt]:
        """读取单个提示词文件，解析 YAML frontmatter + Markdown 正文。

        Args:
            group: 分组名（子目录名）
            filename: 文件名（含 .md 后缀）

        Returns:
            Prompt 对象，文件不存在或解析失败 → None

        解析逻辑：
        1. 读取文件全文
        2. 若以 '---' 开头 → 提取两个 '---' 之间的 frontmatter
        3. 第二个 '---' 之后的内容 = content（正文）
        4. 若无 frontmatter（旧格式兼容）→ description=文件名去后缀，created_at=当前时间
        """
        path = self.prompts_dir / group / filename
        if not path.is_file():
            return None

        try:
            text = path.read_text(encoding='utf-8')
        except Exception:
            return None

        fm, body = self._parse_frontmatter(text)
        if fm:
            description = fm.get('description', Path(filename).stem)
            created_at = fm.get('created_at', datetime.now(timezone.utc).isoformat())
        else:
            # 无 frontmatter → 兼容旧格式
            description = Path(filename).stem
            created_at = datetime.now(timezone.utc).isoformat()

        return Prompt(
            description=description,
            content=body.strip(),
            created_at=created_at,
        )

    # ══════════════════════════════════════════════════════════
    # DT-03c · 保存提示词（原子写）
    # ══════════════════════════════════════════════════════════

    def save_prompt(self, group: str, old_filename: Optional[str],
                    prompt: Prompt) -> str:
        """保存提示词到文件。原子写：临时文件 → os.replace。

        Args:
            group: 目标分组名
            old_filename: 旧文件名（若为新建则传 None，若为编辑已有则传旧文件名）
            prompt: Prompt 对象

        Returns:
            新文件名（sanitize 后的完整文件名，含 .md 后缀）

        Raises:
            FileExistsError: 若新文件名与同组已有文件冲突（排除 old_filename 自身）
            OSError: 目录创建或写入失败
        """
        group_dir = self.prompts_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)

        new_filename = self._sanitize_filename(prompt.description)

        # 冲突检查：新文件名与同组已有文件冲突（排除自身）
        if old_filename is None or old_filename != new_filename:
            existing = {f.name for f in group_dir.glob('*.md') if f.is_file()}
            if new_filename in existing:
                raise FileExistsError(
                    f'提示词已存在: {group}/{new_filename}'
                )

        # 生成文件内容：YAML frontmatter + 空行 + 正文
        # frontmatter 中不含 group/category 字段
        content = (
            f'---\n'
            f'description: {prompt.description}\n'
            f'created_at: {prompt.created_at}\n'
            f'---\n'
            f'\n'
            f'{prompt.content}\n'
        )

        target_path = group_dir / new_filename
        tmp_path = group_dir / f'{new_filename}.tmp'

        try:
            tmp_path.write_text(content, encoding='utf-8')
            os.replace(str(tmp_path), str(target_path))
        except Exception:
            # 清理可能的残留临时文件
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

        # 若旧文件名不同 → 删除旧文件
        if old_filename is not None and old_filename != new_filename:
            old_path = group_dir / old_filename
            old_path.unlink(missing_ok=True)

        return new_filename

    # ══════════════════════════════════════════════════════════
    # DT-03d · 删除提示词
    # ══════════════════════════════════════════════════════════

    def delete_prompt(self, group: str, filename: str) -> bool:
        """删除提示词文件。

        Args:
            group: 分组名
            filename: 文件名（含 .md 后缀）

        Returns:
            True 若删除成功，False 若文件不存在

        注意：
        - 不自动删除空目录（目录管理留给用户）
        - 不在此方法中清理 _favorites.json（收藏同步由 IT-13b PromptService 负责）
        """
        path = self.prompts_dir / group / filename
        if not path.is_file():
            return False
        path.unlink()
        return True

    # ══════════════════════════════════════════════════════════
    # DT-03e · 列出分组下所有提示词
    # ══════════════════════════════════════════════════════════

    def list_prompts(self, group: str) -> list[dict]:
        """列出某分组下所有提示词的元信息（不含正文）。

        Args:
            group: 分组名

        Returns:
            list[dict]: 每项含 group, filename, description, created_at
            按 description 字母排序
        """
        group_dir = self.prompts_dir / group
        if not group_dir.exists():
            return []

        result = []
        for f in sorted(group_dir.glob('*.md')):
            if not f.is_file():
                continue
            text = f.read_text(encoding='utf-8')
            fm, _ = self._parse_frontmatter(text)
            result.append({
                'group': group,
                'filename': f.name,
                'description': fm.get('description', f.stem),
                'created_at': fm.get('created_at', ''),
            })

        result.sort(key=lambda x: x['description'])
        return result

    # ══════════════════════════════════════════════════════════
    # DT-03f · 读取全部提示词（供搜索用）
    # ══════════════════════════════════════════════════════════

    def load_all_prompts(self) -> list[Prompt]:
        """读取所有分组下的全部提示词（含正文）。

        Returns:
            list[Prompt]: 全部提示词列表
        """
        all_prompts = []
        for group in self.get_groups():
            group_dir = self.prompts_dir / group
            for f in sorted(group_dir.glob('*.md')):
                if not f.is_file():
                    continue
                prompt = self.load_prompt(group, f.name)
                if prompt is not None:
                    all_prompts.append(prompt)
        return all_prompts

    # ══════════════════════════════════════════════════════════
    # DT-04 · _favorites.json 管理
    # ══════════════════════════════════════════════════════════

    def _favorites_path(self) -> Path:
        """_favorites.json 文件路径。"""
        return self.prompts_dir / '_favorites.json'

    def get_favorites(self) -> list[str]:
        """读取收藏列表。

        Returns:
            list[str]: 收藏路径数组，如 ['开局/标准开局', '收尾/快速收尾']
            若 _favorites.json 不存在 → 返回 []
            若 _favorites.json 格式损坏 → 返回 []（不崩溃）
        """
        path = self._favorites_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def save_favorites(self, favorites: list[str]) -> None:
        """覆写收藏列表。原子写：临时文件 → os.replace。

        Args:
            favorites: 收藏路径数组
        """
        path = self._favorites_path()
        content = json.dumps(favorites, ensure_ascii=False, indent=2) + '\n'
        tmp_path = path.with_suffix('.tmp')
        try:
            tmp_path.write_text(content, encoding='utf-8')
            os.replace(str(tmp_path), str(path))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def add_favorite(self, group: str, filename: str) -> None:
        """添加收藏。路径格式 'group/filename'（去掉 .md 后缀）。
        若已存在 → 无操作（幂等）。
        """
        fav_path = f'{group}/{Path(filename).stem}'
        favs = self.get_favorites()
        if fav_path not in favs:
            favs.append(fav_path)
            self.save_favorites(favs)

    def remove_favorite(self, group: str, filename: str) -> None:
        """移除收藏。若不存在 → 无操作（幂等）。"""
        fav_path = f'{group}/{Path(filename).stem}'
        favs = self.get_favorites()
        if fav_path in favs:
            favs.remove(fav_path)
            self.save_favorites(favs)

    def update_favorite_path(self, old_group: str, old_filename: str,
                              new_group: str, new_filename: str) -> None:
        """更新收藏引用——提示词改名或移动分组时调用。
        若旧路径不在收藏中 → 无操作。
        """
        old_path = f'{old_group}/{Path(old_filename).stem}'
        new_path = f'{new_group}/{Path(new_filename).stem}'
        favs = self.get_favorites()
        if old_path in favs:
            idx = favs.index(old_path)
            favs[idx] = new_path
            self.save_favorites(favs)

    # ══════════════════════════════════════════════════════════
    # 内部工具
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _parse_frontmatter(text: str) -> tuple[dict, str]:
        """解析 YAML frontmatter（手工解析，仅2字段）。

        Args:
            text: 文件全文

        Returns:
            (frontmatter_dict, body_text)
            - frontmatter_dict: {} 若无有效 frontmatter
            - body_text: frontmatter 之后的正文，保留原始 Markdown
        """
        if not text.startswith('---'):
            return {}, text

        parts = text.split('---', 2)
        if len(parts) < 3:
            return {}, text

        fm_raw = parts[1]
        body = parts[2]

        fm = {}
        for line in fm_raw.strip().split('\n'):
            line = line.strip()
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                if key and value:
                    fm[key] = value

        return fm, body


# ══════════════════════════════════════════════════════════
# DT-01 · SceneStore — scenes.json 持久化（标签1 v4 新增）
# ══════════════════════════════════════════════════════════

class SceneStore:
    """场景持久化 — scenes.json 读写。

    存储路径：scenes_dir/scenes.json（与 prompts/ 平级）。
    用于标签1场景变量的持久化，不依赖 PyQt6。
    """

    def __init__(self, scenes_dir: str):
        """初始化，拼接 scenes.json 路径。

        Args:
            scenes_dir: scenes.json 所在目录（如 csf-clarity/）
        """
        self._scenes_dir = Path(scenes_dir)
        self._scenes_path = self._scenes_dir / 'scenes.json'

    def load(self) -> dict:
        """加载场景数据。

        Returns:
            dict: {"current": "场景名", "scenes": {...}}
            文件不存在 → 返回 {"current": "default", "scenes": {"default": {}}}
            JSON 损坏 → 返回初始默认值（不崩溃）
        """
        if not self._scenes_path.is_file():
            return {"current": "default", "scenes": {"default": {}}}
        try:
            data = json.loads(self._scenes_path.read_text(encoding='utf-8'))
            if (not isinstance(data, dict)
                    or 'current' not in data
                    or 'scenes' not in data):
                return {"current": "default", "scenes": {"default": {}}}
            return data
        except (json.JSONDecodeError, Exception):
            return {"current": "default", "scenes": {"default": {}}}

    def save(self, data: dict) -> None:
        """保存场景数据。原子写：临时文件 → os.replace。

        Args:
            data: 完整的场景数据 {"current": str, "scenes": dict}
        """
        content = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        tmp_path = self._scenes_path.with_suffix('.tmp')
        try:
            tmp_path.write_text(content, encoding='utf-8')
            os.replace(str(tmp_path), str(self._scenes_path))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
