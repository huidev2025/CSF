# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
PromptService v3 — 提示词业务服务：CRUD无版本 + 复制新建 + 收藏 + 搜索 + 出厂预置。

纯业务逻辑层：接收 PromptStore v3 实例，所有持久化通过 store 完成。
不直接操作文件系统，不依赖 PyQt6。
[IT-13b]
"""

import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.core.models import Prompt
from src.data.prompt_store import PromptStore, SceneStore

# ── 出厂预置内容（§二.C）──────────────────────────────────

_FACTORY_PRESETS: list[dict] = [
    {"group": "开局", "description": "标准开局 — 标准CSF开局协议，AI读取context并执行加载链，产出7项brief",
     "content": "阅读 {path}cos-context.md，开局。按标准开局协议执行：读§A全文+加载链→建session log→产出7项brief"},
    {"group": "开局", "description": "聚焦式开局 — 聚焦特定关注点的开局，在正文中修改关注点后使用",
     "content": "阅读 {path}cos-context.md，开局。聚焦【{在此填写关注点}】…"},
    {"group": "收尾", "description": "标准收尾 — 标准CSF收尾协议，AI覆写§C/§D，更新进度和备忘",
     "content": "收尾。按标准收尾协议执行：补全笔记→覆写§C→覆写§D→备忘区更新→经验归位"},
    {"group": "收尾", "description": "快速收尾 — 精简收尾，适用于日常简短会话",
     "content": "收尾。快速覆写§C/§D，不执行完整收尾协议"},
    {"group": "立项", "description": "快速立项 — 触发AI读取立项协议，建立TP并分解IT",
     "content": "阅读 {path}protocols/立项协议.md，建立新TP。按立项动作序列7步执行"},
    {"group": "修复", "description": "Bug修复 — 触发AI读取BugFix协议，走标准修复流程",
     "content": "阅读 {path}protocols/BugFix-修复机制.md，走标准修复流程"},
    {"group": "复盘", "description": "会话复盘 — 触发AI回顾本次会话，沉淀经验教训",
     "content": "回顾本次会话，按反思场景②记录得失。按E8反馈通路沉淀经验"},
]


class PromptService:
    """提示词服务 v3 — CRUD + 复制新建 + 收藏 + 搜索 + 出厂预置。

    接收 PromptStore v3 实例，所有持久化通过 store 完成。
    不直接操作文件系统。
    """

    # ── DT-01a 构造函数 ────────────────────────────────────

    def __init__(self, store: PromptStore, scenes_dir: str = None):
        """接收 PromptStore v3 实例 + 可选 scenes_dir。

        Args:
            store: PromptStore 实例
            scenes_dir: scenes.json 所在目录。默认从 prompts_dir 父目录推导。
        """
        self._store = store
        if scenes_dir is None:
            scenes_dir = str(store.prompts_dir.parent)
        self._scene_store = SceneStore(scenes_dir)

    # ── DT-01b list_groups ─────────────────────────────────

    def list_groups(self) -> list[str]:
        """返回所有分组名。直接委托 PromptStore.get_groups()。

        Returns:
            list[str]: 分组名列表，按字母排序
        """
        return self._store.get_groups()

    # ── DT-01b2 rename_group ──────────────────────────────

    def rename_group(self, old_name: str, new_name: str) -> None:
        """重命名分组——sanitize 新名称后委托 store。

        Args:
            old_name: 当前分组名
            new_name: 新分组名

        Raises:
            ValueError: 名称为空 / 新名称 sanitize 后为空 / 新旧相同
            FileNotFoundError: 旧分组不存在
            FileExistsError: 新名称与已有分组冲突
        """
        if not old_name or not isinstance(old_name, str) or not old_name.strip():
            raise ValueError('当前分组名不能为空')
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            raise ValueError('新分组名不能为空')

        old_name = old_name.strip()
        new_name = new_name.strip()

        if old_name == new_name:
            raise ValueError('新旧分组名相同，无需修改')

        # sanitize：去掉非法文件名字符（同 _sanitize_filename 规则，但无 .md 后缀）
        import re
        _ILLEGAL = re.compile(r'[<>:"/\\|?*]')
        cleaned = _ILLEGAL.sub('', new_name).strip()
        if not cleaned:
            raise ValueError('新分组名 sanitize 后为空，请重新输入')

        # 检查新名称不与已有分组冲突（排除自身）
        existing = self._store.get_groups()
        if cleaned in existing and cleaned != old_name:
            raise FileExistsError(f'分组 "{cleaned}" 已存在')

        self._store.rename_group(old_name, cleaned)

    # ── DT-01b3 delete_group ──────────────────────────────

    def delete_group(self, group_name: str) -> int:
        """删除分组及组内全部提示词，清理收藏引用。

        Args:
            group_name: 待删除的分组名

        Returns:
            int: 删除的提示词文件数量

        Raises:
            ValueError: 名称为空
            FileNotFoundError: 分组不存在
        """
        if not group_name or not isinstance(group_name, str) or not group_name.strip():
            raise ValueError('分组名不能为空')
        return self._store.delete_group(group_name.strip())

    # ── DT-01b4 create_group ──────────────────────────────

    def create_group(self, group_name: str) -> None:
        """创建空分组。

        Args:
            group_name: 新分组名

        Raises:
            ValueError: 名称为空或已存在
        """
        if not group_name or not isinstance(group_name, str) or not group_name.strip():
            raise ValueError('分组名不能为空')
        self._store.create_group(group_name.strip())

    # ── DT-01b5 reorder_group ────────────────────────────

    def reorder_group(self, group_name: str, target_index: int) -> None:
        """将分组移动到目标位置（拖拽排序）。

        Args:
            group_name: 待移动的分组名
            target_index: 目标索引（0-based，在分组列表中的位置）

        Raises:
            ValueError: 分组不存在
        """
        if not group_name or not isinstance(group_name, str) or not group_name.strip():
            raise ValueError('分组名不能为空')
        self._store.reorder_group(group_name.strip(), target_index)

    # ── DT-01c list_by_group ───────────────────────────────

    def list_by_group(self, group: str) -> list[dict]:
        """列出某分组下所有提示词的元信息。

        Returns:
            list[dict]: 每项含 {group, filename, description, created_at}
        """
        return self._store.list_prompts(group)

    # ── DT-01d get ─────────────────────────────────────────

    def get(self, group: str, filename: str) -> Prompt:
        """获取提示词（无版本链）。

        store.load_prompt 返回 None 时 → 转为 FileNotFoundError。

        Raises:
            FileNotFoundError: 提示词不存在
        """
        prompt = self._store.load_prompt(group, filename)
        if prompt is None:
            raise FileNotFoundError(f'提示词不存在: {group}/{filename}')
        return prompt

    # ── DT-01e create ──────────────────────────────────────

    def create(self, group: str, description: str, content: str) -> Prompt:
        """创建新提示词。

        验证规则：
        ① group 非空字符串
        ② description 非空字符串
        ③ 同组内 sanitize 后的文件名不重复

        Returns:
            Prompt: 新创建的提示词

        Raises:
            ValueError: group 为空 / description 为空 / 同组重名
        """
        # 验证 group
        if not group or not isinstance(group, str) or not group.strip():
            raise ValueError('group 不能为空')

        # 验证 description
        if not description or not isinstance(description, str) or not description.strip():
            raise ValueError('description 不能为空')

        # 检查同组重名：sanitize 后文件名是否冲突
        new_filename = self._store._sanitize_filename(description)
        existing = self._store.list_prompts(group)
        for item in existing:
            if item['filename'] == new_filename:
                raise ValueError(
                    f'提示词 "{description}" 在分组 "{group}" 中已存在')

        # 构造 Prompt
        now = datetime.now(timezone.utc).isoformat()
        prompt = Prompt(description=description, content=content, created_at=now)

        # 保存并返回
        saved_filename = self._store.save_prompt(group, None, prompt)
        return self._store.load_prompt(group, saved_filename)

    # ── DT-01f update ──────────────────────────────────────

    def update(self, group: str, filename: str, content: str,
               new_group: str | None = None,
               new_description: str | None = None) -> Prompt:
        """更新提示词内容，可选改名/移动分组。

        验证规则：
        ① 提示词存在
        ② 若 new_description 非 None → 非空
        ③ 若 new_group 非 None → 非空

        Returns:
            Prompt: 更新后的提示词

        Raises:
            FileNotFoundError: 提示词不存在
            ValueError: 参数验证失败
            FileExistsError: 目标位置重名（由 store.save_prompt 抛出）
        """
        # 检查存在性
        prompt = self._store.load_prompt(group, filename)
        if prompt is None:
            raise FileNotFoundError(f'提示词不存在: {group}/{filename}')

        # 验证参数
        if new_description is not None:
            if not new_description or not isinstance(new_description, str) or not new_description.strip():
                raise ValueError('new_description 不能为空')
        if new_group is not None:
            if not new_group or not isinstance(new_group, str) or not new_group.strip():
                raise ValueError('new_group 不能为空')

        # 更新字段
        prompt.content = content
        if new_description is not None:
            prompt.description = new_description

        target_group = new_group if new_group is not None else group

        # 保存
        new_filename = self._store.save_prompt(target_group, filename, prompt)

        # 若改名或移动分组 → 同步收藏引用
        if new_group is not None or new_description is not None:
            old_fn_no_ext = filename.replace('.md', '')
            new_fn_no_ext = new_filename.replace('.md', '')
            self._store.update_favorite_path(group, old_fn_no_ext,
                                             target_group, new_fn_no_ext)

        return self._store.load_prompt(target_group, new_filename)

    # ── DT-01g delete ──────────────────────────────────────

    def delete(self, group: str, filename: str) -> None:
        """删除提示词。

        步骤：
        ① 清理收藏引用
        ② 调用 store.delete_prompt
        ③ 文件不存在不抛异常（容错）
        """
        # 清理收藏引用（去掉 .md 后缀）
        fn_no_ext = filename.replace('.md', '')
        self._store.remove_favorite(group, fn_no_ext)

        # 删除文件（不抛异常）
        self._store.delete_prompt(group, filename)

    # ── DT-02 duplicate 复制新建 ───────────────────────────

    def duplicate(self, group: str, filename: str, content: str) -> Prompt:
        """复制新建提示词——数字前缀自动生成。

        逻辑：
        ① 加载原提示词
        ② 提取「基础名」——去掉前导数字前缀
        ③ 扫描同组已有编号，取最大值+1
        ④ 生成新说明、新文件

        Args:
            group: 当前提示词所在分组
            filename: 当前提示词文件名（含 .md 后缀）
            content: 新提示词的正文内容

        Returns:
            Prompt: 新创建的提示词

        Raises:
            FileNotFoundError: 原提示词不存在
        """
        # 加载原提示词
        original = self._store.load_prompt(group, filename)
        if original is None:
            raise FileNotFoundError(f'提示词不存在: {group}/{filename}')

        # 提取基础名：去掉前导数字前缀
        # "标准开局 — ..."        → 基础名 = "标准开局 — ..."
        # "2 标准开局 — ..."      → 基础名 = "标准开局 — ..."
        # "10 标准开局 — ..."     → 基础名 = "标准开局 — ..."
        match = re.match(r'^(\d+)\s+(.+)$', original.description)
        if match:
            base_name = match.group(2)
        else:
            base_name = original.description

        # 在同组中扫描已有提示词，找最大编号
        existing_prompts = self._store.list_prompts(group)
        max_num = 1  # 默认从2开始（max_num+1）
        base_pattern = re.escape(base_name)
        for item in existing_prompts:
            m = re.match(r'^(\d+)\s+' + base_pattern + r'$', item['description'])
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num

        # 生成新编号（从 max_num+1 开始，递增直到不冲突）
        new_num = max_num + 1
        existing_descriptions = {item['description'] for item in existing_prompts}
        while True:
            new_description = f"{new_num} {base_name}"
            if new_description not in existing_descriptions:
                break
            new_num += 1

        # 构造新 Prompt
        now = datetime.now(timezone.utc).isoformat()
        new_prompt = Prompt(description=new_description, content=content,
                           created_at=now)

        # 保存
        new_filename = self._store.save_prompt(group, None, new_prompt)
        return self._store.load_prompt(group, new_filename)

    # ── DT-03a get_favorites ───────────────────────────────

    def get_favorites(self) -> list[dict]:
        """获取收藏列表（含 description 便于UI显示）。

        步骤：
        ① 调用 store.get_favorites() → ["开局/标准开局", "收尾/快速收尾"]
        ② 逐条解析路径，加载 description
        ③ 若某条收藏的提示词文件已被删除 → 跳过该条

        Returns:
            list[dict]: 每项含 {group, filename, description}
        """
        result = []
        for entry in self._store.get_favorites():
            # 解析路径：group/fn_no_ext
            parts = entry.split('/', 1)
            if len(parts) != 2:
                continue
            fav_group, fn_no_ext = parts
            fav_filename = fn_no_ext + '.md'

            # 加载提示词获取 description
            prompt = self._store.load_prompt(fav_group, fav_filename)
            if prompt is None:
                continue  # 文件已删除，跳过

            result.append({
                'group': fav_group,
                'filename': fav_filename,
                'description': prompt.description,
            })
        return result

    # ── DT-03b toggle_favorite ─────────────────────────────

    def toggle_favorite(self, group: str, filename: str) -> bool:
        """切换收藏状态——收藏→取消，未收藏→添加。

        Returns:
            bool: 切换后的收藏状态（True=已收藏，False=已取消）
        """
        fn_no_ext = filename.replace('.md', '')
        entry = f"{group}/{fn_no_ext}"
        current = self._store.get_favorites()

        if entry in current:
            self._store.remove_favorite(group, fn_no_ext)
            return False
        else:
            self._store.add_favorite(group, fn_no_ext)
            return True

    # ── DT-03c is_favorite ─────────────────────────────────

    def is_favorite(self, group: str, filename: str) -> bool:
        """查询某提示词是否已收藏。"""
        fn_no_ext = filename.replace('.md', '')
        return f"{group}/{fn_no_ext}" in self._store.get_favorites()

    # ── DT-04 search ───────────────────────────────────────

    def search(self, query: str) -> list[dict]:
        """搜索提示词——子串匹配说明文字 + 正文内容。

        匹配逻辑：
        ① query 为空或仅空白 → 返回空列表
        ② 大小写不敏感
        ③ 子串匹配（中文友好，不需要分词）

        Returns:
            list[dict]: 每项含 {group, filename, description, created_at}
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower()
        results = []

        for group in self._store.get_groups():
            # 先获取元信息（含 description）
            prompts_meta = self._store.list_prompts(group)
            for meta in prompts_meta:
                matched = False

                # description 匹配 → 直接加入（不加载正文）
                if query_lower in meta['description'].lower():
                    matched = True
                else:
                    # 加载正文检查
                    prompt = self._store.load_prompt(group, meta['filename'])
                    if prompt is not None and query_lower in prompt.content.lower():
                        matched = True

                if matched:
                    results.append({
                        'group': meta['group'],
                        'filename': meta['filename'],
                        'description': meta['description'],
                        'created_at': meta['created_at'],
                    })

        # 按 group + description 排序
        results.sort(key=lambda x: (x['group'], x['description']))
        return results

    # ── DT-03 · render — 场景变量渲染 ─────────────────────

    def render(self, content: str) -> str:
        """用当前场景变量渲染提示词正文。{var}→值，未定义变量保留原样。

        Args:
            content: 含 {var} 占位符的提示词正文

        Returns:
            渲染后的字符串。未定义变量保留 {var} 原样。
        """
        data = self._scene_store.load()
        current = data.get('current', 'default')
        scenes = data.get('scenes', {})
        vars_dict = scenes.get(current, {})

        if not vars_dict:
            return content

        result = content
        for var_name, var_value in vars_dict.items():
            placeholder = '{' + var_name + '}'
            result = result.replace(placeholder, str(var_value))
        return result

    # ── DT-04 · 场景管理方法 ×5 ───────────────────────────

    def get_scenes(self) -> dict:
        """返回完整 scenes 数据 {"current": str, "scenes": dict}。"""
        return self._scene_store.load()

    def get_current_scene_vars(self) -> dict:
        """返回当前场景的变量键值对。"""
        data = self._scene_store.load()
        current = data.get('current', 'default')
        return data.get('scenes', {}).get(current, {})

    def save_current_scene(self, scene_name: str) -> None:
        """切换 current 字段，持久化。"""
        data = self._scene_store.load()
        if scene_name in data.get('scenes', {}):
            data['current'] = scene_name
            self._scene_store.save(data)

    def save_scene(self, name: str, vars_dict: dict) -> None:
        """保存/更新场景变量，持久化。若 name 不在 scenes 中→新增。

        Args:
            name: 场景名
            vars_dict: 变量键值对
        """
        data = self._scene_store.load()
        if 'scenes' not in data:
            data['scenes'] = {}
        data['scenes'][name] = vars_dict
        self._scene_store.save(data)

    def delete_scene(self, name: str) -> None:
        """删除场景。若删除的是 current→自动切到第一个剩余场景。
        只剩一个场景时不允许删除。

        Args:
            name: 场景名

        Raises:
            ValueError: 只剩一个场景时
        """
        data = self._scene_store.load()
        scenes = data.get('scenes', {})
        if len(scenes) <= 1:
            raise ValueError('至少保留一个场景')
        if name not in scenes:
            return
        del scenes[name]
        if data['current'] == name:
            data['current'] = next(iter(scenes.keys()))
        self._scene_store.save(data)

    # ── DT-05 · send_to_chat — 场景变量渲染 ────────────────

    def send_to_chat(self, content: str, auto_enter: bool = True) -> str:
        """渲染提示词正文（{var} → 场景变量值）。

        UI 层负责剪贴板操作和发送。本方法仅做纯文本渲染。

        Args:
            content: 提示词正文（含 {var} 占位符）
            auto_enter: 保留参数，当前未使用

        Returns:
            str: 渲染后的文本
        """
        return self.render(content)

    # ── paste_to_prev_window — 隐藏→粘贴→恢复 ──

    def paste_to_prev_window(self, auto_enter: bool = True,
                             hwnd: int = 0) -> bool:
        """短暂隐藏 Clarity → 系统自动聚焦下层窗口 → Ctrl+V → 恢复。

        Args:
            auto_enter: 粘贴后是否自动回车
            hwnd: Clarity 窗口句柄。0=自动取 GetForegroundWindow()

        Returns:
            bool: True=粘贴成功，False=失败
        """
        if sys.platform != 'win32':
            return False

        import ctypes
        user32 = ctypes.windll.user32

        VK_CONTROL = 0x11
        VK_V = 0x56
        VK_RETURN = 0x0D
        KEYEVENTF_KEYUP = 0x0002

        try:
            if not hwnd:
                hwnd = user32.GetForegroundWindow()

            # 短暂隐藏 Clarity，让下层窗口获得焦点
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
            time.sleep(0.2)

            # Ctrl+V（发到当前焦点窗口）
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            if auto_enter:
                time.sleep(0.08)
                user32.keybd_event(VK_RETURN, 0, 0, 0)
                time.sleep(0.05)
                user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

            # 恢复 Clarity
            time.sleep(0.1)
            user32.ShowWindow(hwnd, 5)  # SW_SHOW
            time.sleep(0.05)
            user32.SetForegroundWindow(hwnd)

            return True

        except Exception:
            return False

    # ── DT-05 initialize_factory_presets ───────────────────

    def initialize_factory_presets(self) -> bool:
        """首次运行时初始化出厂预置提示词。

        判断逻辑：
        ① store.get_groups() 返回非空 → 已有内容，跳过
        ② 否则创建 5 分组 7 条提示词 + 空收藏列表

        Returns:
            bool: True=执行了初始化，False=已有内容跳过
        """
        groups = self._store.get_groups()
        if groups:
            return False

        now = datetime.now(timezone.utc).isoformat()
        for preset in _FACTORY_PRESETS:
            prompt = Prompt(description=preset['description'],
                           content=preset['content'],
                           created_at=now)
            self._store.save_prompt(preset['group'], None, prompt)

        self._store.save_favorites([])
        return True
