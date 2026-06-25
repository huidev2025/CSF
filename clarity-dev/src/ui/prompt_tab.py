# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
PromptTab v4 — 标签1：提示词标签页（PyQt6 QSplitter 两栏布局）。

[IT-13c] v3 基线完全重写 → [tag1-v4] v4 增量：场景变量+发送通道+布局优化。

v4 新增（DT-09~14）：
- 右侧垂直 QSplitter（树 / 场景面板）
- 场景面板（场景选择+变量表+增删场景/变量）
- 双击发送到 Chat
- 右键菜单（发送/发送并回车/复制新建/删除）
- 删除分组下拉框 + ⭐移至按钮行
- 树样式优化（缩进/交替行色/行高）
"""

from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QEvent
from PyQt6.QtGui import QFont, QAction
import traceback

from src.service.prompt_service import PromptService


# ── DT-07: 自定义 QTreeWidget 拦截拖放 ─────────────────────

class PromptTreeWidget(QTreeWidget):
    """自定义 QTreeWidget，拦截拖放实现文件移动 / 分组重排。

    拖放行为：
    - 拖分组 → 重排分组顺序（持久化到 _group_order.json）
    - 拖提示词到其他分组 → 移动文件
    - 拖提示词到收藏区 → 切换收藏状态

    放手判定宽松化：使用 dropIndicatorPosition() 代替 itemAt() 的 OnItem 判定，
    光标在行上半部 → 落入上方，在下半部 → 落入下方。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on_drop_to_favorites = None  # 外部回调：toggle_favorite
        self._move_prompt = None           # 外部回调：move_prompt
        self._on_reorder_group = None      # 外部回调：reorder_group
        self._drag_item = None             # 拖拽起点 item（mousePressEvent 记录）

    def mousePressEvent(self, event):
        """记录拖拽起点 item，确保 dropEvent 拿到正确的源。"""
        item = self.itemAt(event.position().toPoint())
        if item is not None:
            self._drag_item = item
        super().mousePressEvent(event)

    def dragMoveEvent(self, event):
        """接受拖拽移动（DragDrop 模式下必须显式接受）。"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """拦截拖放 → 分组重排 / 提示词移动 / 收藏切换。"""
        target_item = self.itemAt(event.position().toPoint())
        drop_pos = self.dropIndicatorPosition()

        # ── 获取拖拽源：优先用 mousePressEvent 记录的 _drag_item ──
        dragged = self._drag_item
        if dragged is None:
            dragged = self.currentItem()
        if dragged is None:
            event.ignore()
            self._drag_item = None
            return
        drag_data = dragged.data(0, Qt.ItemDataRole.UserRole)
        self._drag_item = None  # 一次性消费

        # ═══════════════════════════════════════════════════════
        # CASE 1: 拖拽分组项 → 重排分组顺序
        # ═══════════════════════════════════════════════════════
        if isinstance(drag_data, str) and drag_data != "__favorites__":
            dragged_group = drag_data
            all_groups = self._get_group_names_in_order()
            current_list_index = self._get_group_index(dragged_group)

            # 计算目标索引（在分组列表中的位置，不含收藏）
            if target_item is not None:
                target_data = target_item.data(0, Qt.ItemDataRole.UserRole)

                if isinstance(target_data, str) and target_data != "__favorites__":
                    target_group = target_data
                    target_list_index = all_groups.index(target_group) if target_group in all_groups else len(all_groups)
                elif isinstance(target_data, tuple):
                    # 拖到提示词上 → 取其所属分组
                    target_group = target_data[0]
                    target_list_index = all_groups.index(target_group) if target_group in all_groups else len(all_groups)
                elif target_data == "__favorites__":
                    # 拖到收藏区 → 放到最前面
                    target_list_index = 0
                else:
                    event.ignore()
                    return

                # 根据 dropIndicatorPosition：上部落上方，下/中部落下方
                if drop_pos == QTreeWidget.DropIndicatorPosition.AboveItem:
                    new_index = target_list_index
                else:
                    # BelowItem / OnItem → 落到目标下方
                    new_index = target_list_index + 1
            elif drop_pos == QTreeWidget.DropIndicatorPosition.OnViewport:
                # 拖到空白区 → 放到末尾
                new_index = len(all_groups)
            else:
                event.ignore()
                return

            # 补偿修正：reorder_group 先 remove 再 insert，
            # 若拖拽项在原列表目标位置之前，remove 会让目标索引 -1
            if current_list_index is not None and current_list_index < new_index:
                new_index -= 1

            # 无位移 → 忽略
            if current_list_index == new_index:
                event.ignore()
                return

            if self._on_reorder_group:
                self._on_reorder_group(dragged_group, new_index)

            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return

        # ═══════════════════════════════════════════════════════
        # CASE 2: 拖拽提示词项 → 复制/收藏
        # ═══════════════════════════════════════════════════════
        if target_item is None:
            event.ignore()
            return

        target_data = target_item.data(0, Qt.ItemDataRole.UserRole)

        # 确定目标分组
        if isinstance(target_data, str) and target_data != "__favorites__":
            target_group = target_data  # 拖到分组节点上
        elif isinstance(target_data, tuple):
            target_group = target_data[0]  # 拖到提示词节点上→取其分组
        elif target_data == "__favorites__":
            # 拖到收藏区→切换收藏状态
            if self._on_drop_to_favorites:
                if isinstance(drag_data, tuple):
                    self._on_drop_to_favorites(drag_data[0], drag_data[1])
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return
        else:
            event.ignore()
            return

        if not isinstance(drag_data, tuple):
            event.ignore()
            return

        src_group, src_filename = drag_data

        # 同组拖拽 → 忽略
        if src_group == target_group:
            event.ignore()
            return

        # 执行文件复制
        if self._move_prompt:
            self._move_prompt(src_group, src_filename, target_group)

        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def _get_group_names_in_order(self) -> list[str]:
        """获取当前树中顶层分组的名称列表（按树中顺序，排除收藏）。"""
        groups = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, str) and data != "__favorites__":
                groups.append(data)
        return groups

    def _get_group_index(self, group_name: str) -> int | None:
        """获取分组在分组列表中的索引（0-based，不含收藏）。"""
        groups = self._get_group_names_in_order()
        try:
            return groups.index(group_name)
        except ValueError:
            return None


# ── DT-01~08: PromptTab v3 ──────────────────────────────────

class PromptTab(QWidget):
    """提示词标签页 v3 — QSplitter 左编辑右导航。

    构造函数签名与 V2 相同（接收 PromptService），确保 main.py 集成零改动。
    """

    def __init__(self, service: PromptService, parent=None):
        super().__init__(parent)
        self._service = service
        self._current_group: str = ''
        self._current_filename: str = ''       # 当前选中提示词的文件名（含 .md）
        self._current_description: str = ''    # 当前选中提示词的说明
        self._is_dirty: bool = False
        self._auto_saving: bool = False    # 防递归自动保存
        self._original_description: str = ''
        self._original_content: str = ''
        self._empty_item: QTreeWidgetItem | None = None

        self._build_ui()
        self._load_data()

    # ── DT-01: 两栏骨架 ────────────────────────────────────

    def _build_ui(self):
        """构建 QSplitter 水平两栏布局。默认比例 1:1，拖拽后 QSettings 持久化。"""
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 左侧：编辑区
        left = self._build_editor_panel()
        self._splitter.addWidget(left)

        # 右侧：导航区
        right = self._build_nav_panel()
        self._splitter.addWidget(right)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)

        # 拖拽防抖持久化（300ms）
        self._splitter_save_timer = QTimer(self)
        self._splitter_save_timer.setSingleShot(True)
        self._splitter_save_timer.setInterval(300)
        self._splitter_save_timer.timeout.connect(self._save_splitter_state)
        self._splitter.splitterMoved.connect(
            lambda: self._splitter_save_timer.start())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._splitter)

        # 状态栏（定高，不参与窗口缩放）
        self._status_label = QLabel("")
        self._status_label.setFixedHeight(26)
        self._status_label.setStyleSheet(
            "color: #666; padding: 3px 8px; font-size: 11px;"
            "background: #f0f0f0; border-top: 1px solid #ddd;")
        main_layout.addWidget(self._status_label)

        self._restore_splitter_state()

    def _save_splitter_state(self):
        """持久化 QSplitter 比例到 QSettings。"""
        settings = QSettings("CSF", "Clarity")
        settings.setValue("prompt_splitter", self._splitter.saveState())

    def _restore_splitter_state(self):
        """从 QSettings 恢复 QSplitter 比例。"""
        settings = QSettings("CSF", "Clarity")
        state = settings.value("prompt_splitter")
        if state:
            self._splitter.restoreState(state)

    # ── DT-02: 导航树（v4: 树样式+双击+右键）─────────────

    def _build_nav_panel(self) -> QWidget:
        """构建右侧导航区：搜索框 + 树 + [+新增] + 场景面板。

        v4 结构（垂直 QSplitter）：
        ├── 上方：搜索框 + PromptTreeWidget + [+新增提示词]
        └── 下方：场景面板
        """
        panel = QWidget()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # ── 垂直 QSplitter：树区 / 场景面板 ──
        nav_splitter = QSplitter(Qt.Orientation.Vertical)

        # ── 上方：搜索框 + 树 + 新增按钮 ──
        tree_wrapper = QWidget()
        layout = QVBoxLayout(tree_wrapper)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框（DT-03）
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍 搜索提示词…")
        self._search_box.textChanged.connect(self._on_search)
        layout.addWidget(self._search_box)

        # 导航树（DT-02 + DT-07 拖拽 + DT-12 样式 + DT-13 双击 + DT-14 右键）
        self._tree = PromptTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
        self._tree.setDefaultDropAction(Qt.DropAction.CopyAction)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        # DT-12: 树样式优化
        self._tree.setIndentation(12)
        self._tree.setAlternatingRowColors(True)
        self._tree.setStyleSheet("QTreeWidget::item { padding: 3px 0px; }")
        # DT-13: 双击发送
        self._tree.itemDoubleClicked.connect(self._on_tree_double_clicked)
        # DT-14: 右键菜单
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(
            self._on_tree_context_menu)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree._on_drop_to_favorites = self._on_drop_to_favorites
        self._tree._move_prompt = self._move_prompt
        self._tree._on_reorder_group = self._on_reorder_group
        layout.addWidget(self._tree, stretch=1)

        # [+新增提示词]
        self._new_btn = QPushButton("+ 新增提示词")
        self._new_btn.clicked.connect(self._on_new_prompt)
        layout.addWidget(self._new_btn)

        nav_splitter.addWidget(tree_wrapper)

        # ── 下方：场景面板（DT-10）──
        self._scene_panel = self._build_scene_panel()
        nav_splitter.addWidget(self._scene_panel)

        # 默认比例 树:场景 ≈ 2:1
        nav_splitter.setStretchFactor(0, 2)
        nav_splitter.setStretchFactor(1, 1)

        # 拖拽持久化（300ms 防抖）
        self._nav_splitter_save_timer = QTimer(self)
        self._nav_splitter_save_timer.setSingleShot(True)
        self._nav_splitter_save_timer.setInterval(300)
        self._nav_splitter_save_timer.timeout.connect(
            self._save_nav_splitter_state)
        nav_splitter.splitterMoved.connect(
            lambda: self._nav_splitter_save_timer.start())

        outer_layout.addWidget(nav_splitter)

        self._restore_nav_splitter_state()

        return panel

    def _save_nav_splitter_state(self):
        """持久化导航区垂直分隔条比例。"""
        settings = QSettings("CSF", "Clarity")
        # 通过 parent 找 splitter
        nav_splitter = self._scene_panel.parent()
        if isinstance(nav_splitter, QSplitter):
            settings.setValue("prompt_nav_splitter", nav_splitter.saveState())

    def _restore_nav_splitter_state(self):
        """恢复导航区垂直分隔条比例。"""
        settings = QSettings("CSF", "Clarity")
        state = settings.value("prompt_nav_splitter")
        if state:
            nav_splitter = self._scene_panel.parent()
            if isinstance(nav_splitter, QSplitter):
                nav_splitter.restoreState(state)

    def _rebuild_tree(self, groups: list[str],
                      favorites: list[dict],
                      search_results: list[dict] | None = None):
        """完全重建导航树。

        Args:
            groups: 分组名列表
            favorites: 收藏列表（每项 {group, filename, description}）
            search_results: 搜索过滤结果。None=不过滤，显示全部。
        """
        self._tree.clear()
        self._empty_item = None  # clear() 删除了旧的空状态 item

        # 若有搜索结果 → 构建快速查找集合
        result_keys: set | None = None
        if search_results is not None:
            result_keys = {(r['group'], r['filename']) for r in search_results}

        # ① 收藏虚拟分组（有收藏时置顶）
        if favorites:
            fav_parent = QTreeWidgetItem(self._tree, ["⭐ 收藏"])
            fav_parent.setData(0, Qt.ItemDataRole.UserRole, "__favorites__")
            fav_font = fav_parent.font(0)
            fav_font.setBold(True)
            fav_parent.setFont(0, fav_font)
            fav_parent.setExpanded(True)

            for fav in favorites:
                grp = fav['group']
                fn = fav['filename']
                desc = fav['description']
                if result_keys is not None and (grp, fn) not in result_keys:
                    continue
                child = QTreeWidgetItem(fav_parent, [desc])
                child.setData(0, Qt.ItemDataRole.UserRole, (grp, fn))

            if fav_parent.childCount() == 0:
                self._tree.takeTopLevelItem(
                    self._tree.indexOfTopLevelItem(fav_parent))

        # ② 各分组
        for grp in groups:
            prompts = self._service.list_by_group(grp)

            if result_keys is not None:
                prompts = [
                    p for p in prompts
                    if (p['group'], p['filename']) in result_keys
                ]
                if not prompts:
                    continue

            parent_item = QTreeWidgetItem(self._tree, [grp])
            parent_item.setData(0, Qt.ItemDataRole.UserRole, grp)
            parent_item.setFlags(parent_item.flags() | Qt.ItemFlag.ItemIsDropEnabled)

            for p in prompts:
                child = QTreeWidgetItem(parent_item, [p['description']])
                child.setData(0, Qt.ItemDataRole.UserRole, (grp, p['filename']))

            parent_item.setExpanded(True)

    # ── DT-03: 搜索框 ──────────────────────────────────────

    def _on_search(self, text: str):
        """搜索框 textChanged 信号处理——实时过滤导航树。"""
        text = text.strip()
        if not text:
            self._load_data()
        else:
            results = self._service.search(text)
            groups = self._service.list_groups()
            favorites = self._service.get_favorites()
            self._rebuild_tree(groups, favorites, search_results=results)

        self._check_empty_state(text)

    def _load_data(self):
        """加载全部数据并重建导航树（无搜索过滤）。v4: 同时加载场景面板。"""
        groups = self._service.list_groups()
        favorites = self._service.get_favorites()

        if not groups:
            if self._service.initialize_factory_presets():
                groups = self._service.list_groups()

        self._rebuild_tree(groups, favorites)

        # v4: 加载场景面板数据
        self._load_scene_panel()

        self._check_empty_state('')

    def _check_empty_state(self, filter_text: str):
        """检查并更新空状态显示。"""
        if self._tree.topLevelItemCount() == 0:
            if filter_text:
                self._show_empty_state("无匹配结果")
            else:
                self._show_empty_state("暂无提示词，[+新增] 或恢复出厂预置")
        else:
            self._hide_empty_state()

    def _show_empty_state(self, message: str):
        """在导航区显示空状态提示。"""
        if self._empty_item is None:
            self._empty_item = QTreeWidgetItem(self._tree, [message])
            self._empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
        else:
            self._empty_item.setText(0, message)

    def _hide_empty_state(self):
        """隐藏空状态提示。"""
        if self._empty_item is not None:
            idx = self._tree.indexOfTopLevelItem(self._empty_item)
            if idx >= 0:
                self._tree.takeTopLevelItem(idx)
            self._empty_item = None

    # ── DT-04: 编辑区（v4: 删除分组下拉+⭐移位，顶部行已移除）──

    def _build_editor_panel(self) -> QWidget:
        """构建左侧编辑区。

        v4 布局（从上到下）：
        ├── 说明区（QTextEdit 多行）
        ├── ── 垂直分隔条 QSplitter ──
        ├── 正文区（QTextEdit 多行）
        └── 按钮行 [⭐收藏] [保存*] [复制到剪贴板] [复制新建] [删除]
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── 垂直分隔条：说明区 / 正文区 ──
        self._editor_splitter = QSplitter(Qt.Orientation.Vertical)
        self._editor_splitter.setChildrenCollapsible(False)

        # 说明区包装
        desc_wrapper = QWidget()
        desc_layout = QVBoxLayout(desc_wrapper)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_label = QLabel("说明：")
        desc_label.setStyleSheet("font-weight: bold;")
        desc_layout.addWidget(desc_label)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText(
            "提示词说明 — 导航区直接显示此段文字。用最前面几个字标识区别，后面展开解释")
        self._desc_edit.setMinimumHeight(60)
        self._desc_edit.setAcceptRichText(False)
        self._desc_edit.textChanged.connect(self._on_editor_changed)
        desc_layout.addWidget(self._desc_edit)

        self._editor_splitter.addWidget(desc_wrapper)

        # 正文区包装
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_label = QLabel("正文：")
        content_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(content_label)

        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("提示词正文…")
        self._content_edit.setMinimumHeight(120)
        self._content_edit.setAcceptRichText(False)
        self._content_edit.textChanged.connect(self._on_editor_changed)
        content_layout.addWidget(self._content_edit)

        # 失焦自动保存
        self._desc_edit.installEventFilter(self)
        self._content_edit.installEventFilter(self)

        self._editor_splitter.addWidget(content_wrapper)

        # 默认比例 说明:正文 = 1:2
        self._editor_splitter.setStretchFactor(0, 1)
        self._editor_splitter.setStretchFactor(1, 2)

        # 编辑区分隔条拖拽持久化（300ms 防抖）
        self._editor_splitter_save_timer = QTimer(self)
        self._editor_splitter_save_timer.setSingleShot(True)
        self._editor_splitter_save_timer.setInterval(300)
        self._editor_splitter_save_timer.timeout.connect(
            self._save_editor_splitter_state)
        self._editor_splitter.splitterMoved.connect(
            lambda: self._editor_splitter_save_timer.start())

        layout.addWidget(self._editor_splitter, stretch=1)

        # ── 按钮行（DT-06）──
        btn_layout = self._build_button_bar()
        layout.addLayout(btn_layout)

        self._restore_editor_splitter_state()

        return panel

    def _save_editor_splitter_state(self):
        """持久化编辑区垂直分隔条比例。"""
        settings = QSettings("CSF", "Clarity")
        settings.setValue("prompt_editor_splitter",
                          self._editor_splitter.saveState())

    def _restore_editor_splitter_state(self):
        """恢复编辑区垂直分隔条比例。"""
        settings = QSettings("CSF", "Clarity")
        state = settings.value("prompt_editor_splitter")
        if state:
            self._editor_splitter.restoreState(state)

    # ── 脏状态管理（DT-04）─────────────────────────────────

    def _on_editor_changed(self):
        """编辑区内容变更 → 更新脏状态 + [保存*]文字。"""
        if self._auto_saving:
            return
        current_desc = self._desc_edit.toPlainText()
        current_content = self._content_edit.toPlainText()
        is_dirty = (current_desc != self._original_description or
                    current_content != self._original_content)

        if is_dirty != self._is_dirty:
            self._is_dirty = is_dirty
            self._update_save_button()

    def eventFilter(self, obj, event):
        """事件过滤器：文本框失焦 → 自动保存。"""
        if event.type() == QEvent.Type.FocusOut:
            if obj in (self._desc_edit, self._content_edit):
                if self._is_dirty and self._current_filename:
                    self._auto_save()
        return super().eventFilter(obj, event)

    def _auto_save(self):
        """静默自动保存（无弹窗）。"""
        if not self._current_filename or self._auto_saving:
            return
        desc = self._desc_edit.toPlainText().strip()
        if not desc:
            return  # 说明为空时不保存
        content = self._content_edit.toPlainText()
        if desc == self._original_description and content == self._original_content:
            return  # 无实际变化

        self._auto_saving = True
        try:
            new_description = desc if desc != self._original_description else None
            prompt = self._service.update(
                self._current_group, self._current_filename, content,
                new_group=None, new_description=new_description)
            self._current_description = prompt.description
            self._original_description = prompt.description
            self._original_content = prompt.content
            self._is_dirty = False
            self._update_save_button()
            self._load_data()
            self._update_current_filename_from_tree()
            self._select_in_tree(self._current_group, self._current_description)
        except (FileNotFoundError, ValueError):
            pass  # 自动保存失败静默忽略
        finally:
            self._auto_saving = False

    def _update_save_button(self):
        """更新保存按钮文字：脏→[保存*]，干净→[保存]。"""
        if self._is_dirty:
            self._save_btn.setText("保存*")
        else:
            self._save_btn.setText("保存")

    # ── DT-05: 选中加载 + 分组下拉 ─────────────────────────

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """导航树节点点击 → 加载提示词到编辑区。"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return

        # 分组节点 / 收藏虚拟分组节点 → 不加载
        if isinstance(data, str):
            return

        # 提示词节点
        if isinstance(data, tuple) and len(data) == 2:
            group, filename = data

            if self._is_dirty and self._current_filename:
                self._auto_save()

            self._load_prompt_to_editor(group, filename)

    def _load_prompt_to_editor(self, group: str, filename: str):
        """加载提示词到编辑区。"""
        try:
            prompt = self._service.get(group, filename)
        except FileNotFoundError:
            return

        # 阻断信号避免触发 _on_editor_changed
        self._desc_edit.blockSignals(True)
        self._content_edit.blockSignals(True)

        self._desc_edit.setPlainText(prompt.description)
        self._content_edit.setPlainText(prompt.content)

        self._desc_edit.blockSignals(False)
        self._content_edit.blockSignals(False)

        self._current_group = group
        self._current_filename = filename
        self._current_description = prompt.description
        self._original_description = prompt.description
        self._original_content = prompt.content
        self._is_dirty = False
        self._update_save_button()

        self._update_fav_button()

    # ── DT-06: 按钮行（v4: ⭐移至最前）────────────────────

    def _build_button_bar(self) -> QHBoxLayout:
        """构建编辑区底部按钮行：[⭐收藏] [保存*] [复制到剪贴板] [复制新建] [删除]。"""
        layout = QHBoxLayout()

        self._fav_btn = QPushButton("☆")
        self._fav_btn.setToolTip("收藏 / 取消收藏")
        self._fav_btn.setFixedWidth(36)
        self._fav_btn.setCheckable(True)
        self._fav_btn.clicked.connect(self._on_toggle_favorite)
        layout.addWidget(self._fav_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        layout.addWidget(self._save_btn)

        self._copy_clipboard_btn = QPushButton("复制到剪贴板")
        self._copy_clipboard_btn.clicked.connect(self._on_copy_clipboard)
        layout.addWidget(self._copy_clipboard_btn)

        self._duplicate_btn = QPushButton("复制新建")
        self._duplicate_btn.clicked.connect(self._on_duplicate)
        layout.addWidget(self._duplicate_btn)

        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._on_delete_prompt)
        layout.addWidget(self._delete_btn)

        layout.addStretch()
        return layout

    # ── 保存 ───────────────────────────────────────────────

    def _on_save(self):
        """保存当前提示词。v4: 不再支持通过下拉框更改分组。"""
        if not self._current_filename:
            return

        desc = self._desc_edit.toPlainText().strip()
        content = self._content_edit.toPlainText()

        if not desc:
            QMessageBox.warning(self, "保存失败", "说明不能为空")
            return

        new_description = desc if desc != self._original_description else None

        try:
            prompt = self._service.update(
                self._current_group, self._current_filename, content,
                new_group=None, new_description=new_description)
        except (FileNotFoundError, ValueError) as e:
            QMessageBox.warning(self, "保存失败", str(e))
            return

        self._current_description = prompt.description
        self._original_description = prompt.description
        self._original_content = prompt.content
        self._is_dirty = False
        self._update_save_button()

        self._load_data()
        self._update_current_filename_from_tree()
        self._select_in_tree(self._current_group, self._current_description)

    # ── 复制到剪贴板（v4: 先 render 再复制）──────────────

    def _on_copy_clipboard(self):
        """复制正文内容到系统剪贴板（含未保存修改）。v4: 先渲染场景变量。"""
        content = self._content_edit.toPlainText()
        rendered = self._service.render(content)
        QApplication.clipboard().setText(rendered)

    # ── 复制新建 ───────────────────────────────────────────

    def _on_duplicate(self):
        """复制新建——弹窗预填说明和分组，用户可改后创建。"""
        if not self._current_filename:
            return

        content = self._content_edit.toPlainText()
        try:
            new_prompt = self._service.duplicate(
                self._current_group, self._current_filename, content)
        except (FileNotFoundError, ValueError) as e:
            QMessageBox.warning(self, "复制失败", str(e))
            return

        # 弹出预填对话框：说明
        desc, ok = QInputDialog.getText(
            self, "复制新建", "提示词说明：",
            text=new_prompt.description)
        if not ok or not desc.strip():
            self._cleanup_duplicate_file(new_prompt.description)
            return

        # 弹出预填对话框：分组
        groups = self._service.list_groups() or ["开局"]
        default_idx = (groups.index(self._current_group)
                       if self._current_group in groups else 0)
        group, ok2 = QInputDialog.getItem(
            self, "选择分组", "分组：", groups,
            current=default_idx, editable=True)
        if not ok2:
            self._cleanup_duplicate_file(new_prompt.description)
            return

        desc_changed = (desc.strip() != new_prompt.description)
        group_changed = (group != self._current_group)

        if desc_changed or group_changed:
            self._cleanup_duplicate_file(new_prompt.description)
            try:
                final_prompt = self._service.create(
                    group, desc.strip(), content)
            except ValueError as e:
                QMessageBox.warning(self, "创建失败", str(e))
                return
        else:
            final_prompt = new_prompt
            group = self._current_group

        self._load_data()
        for p in self._service.list_by_group(group):
            if p['description'] == final_prompt.description:
                self._select_in_tree(group, final_prompt.description)
                self._load_prompt_to_editor(group, p['filename'])
                return

        self._select_in_tree(group, final_prompt.description)

    def _cleanup_duplicate_file(self, description: str):
        """清理 duplicate 自动创建的文件。"""
        try:
            fn = description + '.md'
            self._service.delete(self._current_group, fn)
        except (FileNotFoundError, AttributeError):
            pass

    # ── 删除 ───────────────────────────────────────────────

    def _on_delete_prompt(self):
        """删除当前提示词。"""
        if not self._current_filename:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除「{self._current_description}」？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.delete(self._current_group, self._current_filename)
        except FileNotFoundError:
            pass

        self._load_data()
        self._auto_select_next()

    # ── ⭐ 收藏切换 ────────────────────────────────────────

    def _on_toggle_favorite(self):
        """切换当前提示词的收藏状态。"""
        if not self._current_filename:
            return

        self._service.toggle_favorite(
            self._current_group, self._current_filename)
        self._update_fav_button()
        self._load_data()
        self._select_in_tree(self._current_group, self._current_description)

    def _update_fav_button(self):
        """更新⭐按钮状态——实心/空心。"""
        if not self._current_filename:
            self._fav_btn.setChecked(False)
            self._fav_btn.setText("☆")
            return

        is_fav = self._service.is_favorite(
            self._current_group, self._current_filename)
        self._fav_btn.setChecked(is_fav)
        self._fav_btn.setText("⭐" if is_fav else "☆")

    # ── DT-07: 拖拽换组 ────────────────────────────────────

    def _move_prompt(self, src_group: str, src_filename: str,
                     target_group: str):
        """复制提示词到目标分组（保留源文件）。

        流程：碰撞检查 → 用户确认 → 写入目标组 → 重建树。
        save_prompt 在 old_filename == new_filename 时跳过碰撞检查，
        因此需要提前校验目标组内是否已有同名文件。
        """
        try:
            prompt = self._service.get(src_group, src_filename)
        except FileNotFoundError:
            return

        # 碰撞检查：目标组是否已存在同名文件
        target_prompts = self._service.list_by_group(target_group)
        target_filenames = {p['filename'] for p in target_prompts}
        if src_filename in target_filenames:
            reply = QMessageBox.question(
                self, "同名提示词",
                f'目标分组 "{target_group}" 中已存在同名提示词\n'
                f'「{prompt.description}」。\n\n是否替换？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            self._service.update(src_group, src_filename, prompt.content,
                                 new_group=target_group)
        except (FileNotFoundError, ValueError, FileExistsError) as e:
            QMessageBox.warning(self, "复制失败", str(e))
            return

        self._load_data()
        self._select_in_tree(target_group, prompt.description)

        if src_filename == self._current_filename:
            self._load_prompt_to_editor(target_group, src_filename)

    def _on_drop_to_favorites(self, group: str, filename: str):
        """拖到收藏区 → 切换收藏状态。"""
        self._service.toggle_favorite(group, filename)
        self._load_data()

    def _on_reorder_group(self, group_name: str, target_index: int):
        """拖拽分组重排 → 持久化新顺序并重建树。

        target_index 是分组列表中的目标索引（0-based，不含收藏）。
        """
        try:
            self._service.reorder_group(group_name, target_index)
        except ValueError as e:
            QMessageBox.warning(self, "排序失败", str(e))
            return
        self._load_data()

    # ── DT-08: 交互保护 ────────────────────────────────────

    # 8a: 切换未保存弹窗
    def _prompt_save_before_switch(self, new_group: str, new_filename: str):
        """切换提示词前检测脏状态 → 三选项弹窗。"""
        reply = QMessageBox.question(
            self, "未保存的修改",
            f"「{self._current_description}」有未保存的修改。\n是否保存后再切换？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)

        if reply == QMessageBox.StandardButton.Save:
            self._on_save()
            self._load_prompt_to_editor(new_group, new_filename)
        elif reply == QMessageBox.StandardButton.Discard:
            self._load_prompt_to_editor(new_group, new_filename)
        # Cancel → 不做任何操作

    # 8b: 窗口/标签关闭保护
    def can_close(self) -> bool:
        """检查是否可以安全关闭（无未保存修改）。

        Returns:
            bool: True=可关闭，False=用户取消
        """
        if not self._is_dirty:
            return True

        reply = QMessageBox.question(
            self, "未保存的修改",
            f"「{self._current_description}」有未保存的修改。\n是否保存后关闭？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)

        if reply == QMessageBox.StandardButton.Save:
            self._on_save()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

    # 8c: 删除后自动加载下一条
    def _auto_select_next(self):
        """删除后自动选择下一条提示词。

        优先级：第一个分组的第一个可见提示词节点 → 无则清空编辑区。
        """
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            if parent.childCount() > 0:
                pdata = parent.data(0, Qt.ItemDataRole.UserRole)
                if pdata == "__favorites__":
                    continue
                child = parent.child(0)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(data, tuple):
                    self._tree.setCurrentItem(child)
                    self._load_prompt_to_editor(data[0], data[1])
                    return

        self._clear_editor()
        self._show_empty_state("暂无提示词，[+新增] 或恢复出厂预置")

    def _clear_editor(self):
        """清空编辑区。"""
        self._desc_edit.clear()
        self._content_edit.clear()
        self._current_group = ''
        self._current_filename = ''
        self._current_description = ''
        self._original_description = ''
        self._original_content = ''
        self._is_dirty = False
        self._update_save_button()

    # 8d: 新增提示词
    def _on_new_prompt(self):
        """新增提示词——弹出对话框选择分组+输入说明。"""
        default_group = self._current_group
        if not default_group:
            groups = self._service.list_groups()
            default_group = groups[0] if groups else "开局"

        description, ok = QInputDialog.getText(
            self, "新增提示词", "提示词说明：",
            text="")
        if not ok or not description.strip():
            return

        groups = self._service.list_groups() or ["开局"]
        default_idx = (groups.index(default_group)
                       if default_group in groups else 0)
        group, ok2 = QInputDialog.getItem(
            self, "选择分组", "分组：",
            groups, current=default_idx, editable=True)
        if not ok2:
            return

        try:
            self._service.create(group, description.strip(), "")
        except ValueError as e:
            QMessageBox.warning(self, "创建失败", str(e))
            return

        self._load_data()
        for p in self._service.list_by_group(group):
            if p['description'] == description.strip():
                self._select_in_tree(group, description.strip())
                self._load_prompt_to_editor(group, p['filename'])
                return
        self._select_in_tree(group, description.strip())

    # ── 辅助方法 ───────────────────────────────────────────

    def _select_in_tree(self, group: str, description: str):
        """在导航树中定位并选中指定提示词节点。"""
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(data, tuple) and len(data) == 2:
                    c_group, c_filename = data
                    if c_group == group and child.text(0) == description:
                        self._tree.setCurrentItem(child)
                        return

    def _update_current_filename_from_tree(self):
        """从导航树中找到当前选中提示词的 filename（保存后 filename 可能改变）。"""
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(data, tuple) and len(data) == 2:
                    if (data[0] == self._current_group and
                            child.text(0) == self._current_description):
                        self._current_filename = data[1]
                        self._tree.setCurrentItem(child)
                        return
        else:
            self._splitter.setSizes([700, 300])

    def _do_debounced_save(self):
        """DT-04: 防抖回调 — 300ms 无拖拽后保存 Splitter 状态。"""
        if hasattr(self, '_splitter_settings') and self._splitter_settings is not None:
            self.save_splitter_state(self._splitter_settings)

    # ══════════════════════════════════════════════════════════
    # v4 新增：场景面板 + 双击发送 + 右键菜单
    # ══════════════════════════════════════════════════════════

    # ── DT-10: 场景面板 UI ─────────────────────────────────

    def _build_scene_panel(self) -> QWidget:
        """构建场景面板。

        结构：
        ├── 第一行：场景：[下拉] [新增] [删除]
        ├── QTableWidget：变量 | 值
        └── [+ 添加变量]
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── 第一行：场景选择器 + 按钮 ──
        top_row = QHBoxLayout()

        scene_label = QLabel("场景：")
        top_row.addWidget(scene_label)

        self._scene_combo = QComboBox()
        self._scene_combo.setEditable(True)
        self._scene_combo.setToolTip("选择或输入场景名")
        self._scene_combo.currentTextChanged.connect(self._on_scene_changed)
        top_row.addWidget(self._scene_combo, stretch=1)

        self._add_scene_btn = QPushButton("新增")
        self._add_scene_btn.clicked.connect(self._on_add_scene)
        top_row.addWidget(self._add_scene_btn)

        self._delete_scene_btn = QPushButton("删除")
        self._delete_scene_btn.clicked.connect(self._on_delete_scene)
        top_row.addWidget(self._delete_scene_btn)

        layout.addLayout(top_row)

        # ── 变量表 ──
        self._scene_table = QTableWidget(0, 2)
        self._scene_table.setHorizontalHeaderLabels(["变量", "值"])
        self._scene_table.horizontalHeader().setStretchLastSection(True)
        self._scene_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive)
        self._scene_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked |
            QAbstractItemView.EditTrigger.AnyKeyPressed)
        self._scene_table.cellChanged.connect(self._on_scene_vars_changed)
        self._scene_table.setToolTip("双击或再次单击编辑，焦点离开自动保存")
        layout.addWidget(self._scene_table, stretch=1)

        # ── 编辑提示 ──
        hint_label = QLabel("💡 双击或再次单击编辑，焦点离开自动保存")
        hint_label.setStyleSheet("color: #999; font-size: 10px; padding: 1px 4px;")
        layout.addWidget(hint_label)

        # ── 添加变量按钮 ──
        self._add_var_btn = QPushButton("+ 添加变量")
        self._add_var_btn.clicked.connect(self._on_add_variable)
        layout.addWidget(self._add_var_btn)

        return panel

    # ── DT-11: 场景面板数据绑定 ────────────────────────────

    def _load_scene_panel(self):
        """从 service 加载场景数据到面板。"""
        # 阻断信号避免触发 cellChanged
        self._scene_combo.blockSignals(True)

        data = self._service.get_scenes()
        current = data.get('current', 'default')
        scenes = data.get('scenes', {})

        # 刷新下拉框
        self._scene_combo.clear()
        scene_names = list(scenes.keys())
        self._scene_combo.addItems(scene_names)
        if current in scene_names:
            self._scene_combo.setCurrentText(current)

        self._scene_combo.blockSignals(False)

        # 刷新变量表
        self._refresh_scene_table(current, scenes)

        # 更新删除按钮状态
        self._delete_scene_btn.setEnabled(len(scenes) > 1)

    def _refresh_scene_table(self, scene_name: str, scenes: dict):
        """刷新变量表为指定场景的变量。"""
        self._scene_table.blockSignals(True)
        self._scene_table.setRowCount(0)

        vars_dict = scenes.get(scene_name, {})
        for var_name, var_value in vars_dict.items():
            row = self._scene_table.rowCount()
            self._scene_table.insertRow(row)
            name_item = QTableWidgetItem(var_name)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._scene_table.setItem(row, 0, name_item)
            value_item = QTableWidgetItem(str(var_value))
            value_item.setFlags(value_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._scene_table.setItem(row, 1, value_item)

        self._scene_table.blockSignals(False)

    def _on_scene_changed(self, name: str):
        """场景下拉切换 → 保存当前场景名 + 刷新变量表。"""
        if not name:
            return
        self._service.save_current_scene(name)
        data = self._service.get_scenes()
        self._refresh_scene_table(name, data.get('scenes', {}))
        self._delete_scene_btn.setEnabled(
            len(data.get('scenes', {})) > 1)

    def _on_scene_vars_changed(self, row: int, col: int):
        """变量表单元格编辑完成 → 收集全表 → 保存。"""
        current_scene = self._scene_combo.currentText()
        if not current_scene:
            return

        vars_dict = {}
        for r in range(self._scene_table.rowCount()):
            name_item = self._scene_table.item(r, 0)
            value_item = self._scene_table.item(r, 1)
            if name_item and name_item.text().strip():
                var_name = name_item.text().strip()
                var_value = value_item.text() if value_item else ''
                vars_dict[var_name] = var_value

        self._service.save_scene(current_scene, vars_dict)

    def _on_add_scene(self):
        """新增场景——弹窗输入场景名。"""
        name, ok = QInputDialog.getText(
            self, "新增场景", "场景名称：", text="")
        if not ok or not name.strip():
            return

        name = name.strip()
        data = self._service.get_scenes()
        if name in data.get('scenes', {}):
            QMessageBox.warning(self, "场景已存在", f"场景「{name}」已存在")
            return

        self._service.save_scene(name, {})
        self._service.save_current_scene(name)
        self._load_scene_panel()

    def _on_delete_scene(self):
        """删除当前场景——确认弹窗。"""
        name = self._scene_combo.currentText()
        if not name:
            return

        reply = QMessageBox.question(
            self, "确认删除", f"确定删除场景「{name}」？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.delete_scene(name)
        except ValueError as e:
            QMessageBox.warning(self, "无法删除", str(e))
            return

        self._load_scene_panel()

    def _on_add_variable(self):
        """在变量表末尾插入空行。"""
        self._scene_table.blockSignals(True)
        row = self._scene_table.rowCount()
        self._scene_table.insertRow(row)
        self._scene_table.setItem(row, 0, QTableWidgetItem("新变量"))
        self._scene_table.setItem(row, 1, QTableWidgetItem(""))
        self._scene_table.blockSignals(False)

    # ── DT-13: 双击列表条目 → 复制到剪贴板 ─────────────────

    def _on_tree_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击导航树节点：
        - 分组节点 → 展开/折叠
        - 提示词节点 → 渲染 → 复制到剪贴板
        不改变编辑区选中状态。
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return

        # 分组节点（含收藏虚拟分组）→ 展开/折叠
        if isinstance(data, str):
            item.setExpanded(not item.isExpanded())
            return

        # 提示词节点 → 渲染 + 复制到剪贴板 + [置顶时自动粘贴]
        if isinstance(data, tuple) and len(data) == 2:
            group, filename = data
            try:
                prompt = self._service.get(group, filename)
                rendered = self._service.send_to_chat(prompt.content)
                QApplication.clipboard().setText(rendered)
                desc = prompt.description or filename

                # 置顶时自动切窗粘贴
                if self.window() and self.window().windowFlags() & Qt.WindowType.WindowStaysOnTopHint:
                    sent = self._service.paste_to_prev_window(auto_enter=True)
                    if sent:
                        self._status_label.setText(f'已发送: {desc}')
                    else:
                        self._status_label.setText(f'已复制到剪贴板: {desc}')
                else:
                    self._status_label.setText(f'已复制到剪贴板: {desc}')
            except Exception as e:
                tb = traceback.format_exc()
                self._status_label.setText(f'发送失败: {e}')
                print(tb)

    # ── DT-14: 右键菜单 ────────────────────────────────────

    def _on_tree_context_menu(self, pos):
        """右键菜单：
        - 提示词节点 → 4项：发送/发送并回车/分隔线/复制新建/删除
        - 分组节点 → 新增提示词到此分组 / 修改分组名称
        - 收藏虚拟分组 → 无菜单
        - 空白区域 → 无菜单
        """
        item = self._tree.itemAt(pos)
        if item is None:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return

        # 收藏虚拟分组 → 无菜单
        if data == "__favorites__":
            return

        menu = QMenu(self)

        # 分组节点 → 4项
        if isinstance(data, str):
            new_group_action = menu.addAction("新建分组")
            new_group_action.triggered.connect(
                lambda checked=False: self._on_new_group())

            menu.addSeparator()

            action = menu.addAction("新增提示词到此分组")
            action.triggered.connect(
                lambda checked=False: self._on_new_prompt_in_group(data))

            rename_action = menu.addAction("修改分组名称")
            rename_action.triggered.connect(
                lambda checked=False: self._on_rename_group(data))

            del_action = menu.addAction("删除分组")
            del_action.triggered.connect(
                lambda checked=False: self._on_delete_group(data))

            menu.exec(self._tree.viewport().mapToGlobal(pos))
            return

        # 提示词节点 → 4项菜单
        if isinstance(data, tuple) and len(data) == 2:
            group, filename = data

            # 项1：发送到聊天窗口
            send_action = menu.addAction("发送到聊天窗口")
            send_action.triggered.connect(
                lambda checked=False, g=group, f=filename: self._send_by_menu(g, f, False))

            # 项2：发送并回车
            send_enter_action = menu.addAction("发送并回车")
            send_enter_action.triggered.connect(
                lambda checked=False, g=group, f=filename: self._send_by_menu(g, f, True))

            menu.addSeparator()

            # 项3：复制新建
            dup_action = menu.addAction("复制新建")
            dup_action.triggered.connect(
                lambda checked=False, g=group, f=filename: self._duplicate_by_menu(g, f))

            # 项4：删除
            del_action = menu.addAction("删除")
            del_action.triggered.connect(
                lambda checked=False, g=group, f=filename: self._delete_by_menu(g, f))

            menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _send_by_menu(self, group: str, filename: str, auto_enter: bool):
        """右键菜单 → 复制到剪贴板 + [置顶时自动粘贴]."""
        import time
        try:
            prompt = self._service.get(group, filename)
            rendered = self._service.send_to_chat(prompt.content,
                                                   auto_enter=auto_enter)
            QApplication.clipboard().setText(rendered)
            desc = prompt.description or filename

            if self.window() and self.window().windowFlags() & Qt.WindowType.WindowStaysOnTopHint:
                # 菜单已关闭，GetForegroundWindow() 能正确返回 Clarity 句柄
                # 不能用 int(self.window().winId())——PyQt6 返回的句柄未必是 Win32 顶层窗口句柄
                time.sleep(0.15)  # 等菜单完全关闭
                sent = self._service.paste_to_prev_window(
                    auto_enter=auto_enter)
                if sent:
                    self._status_label.setText(f'已发送: {desc}')
                else:
                    self._status_label.setText(f'已复制到剪贴板: {desc}')
            else:
                self._status_label.setText(f'已复制到剪贴板: {desc}')
        except Exception as e:
            import traceback as _tb
            tb = _tb.format_exc()
            self._status_label.setText(f'发送失败: {e}')
            # 写完整 traceback 到文件，方便诊断
            try:
                from pathlib import Path as _Path
                from datetime import datetime as _dt
                log_path = _Path(__file__).resolve().parent.parent.parent / 'logs' / 'send_error.log'
                log_path.write_text(f'[右键发送异常] {_dt.now().isoformat()}\n{tb}\n', encoding='utf-8')
            except Exception:
                pass
            print(f'[右键发送异常]\n{tb}')

    def _duplicate_by_menu(self, group: str, filename: str):
        """右键菜单 → 复制新建。加载到编辑区后调用 _on_duplicate。"""
        # 先处理脏状态
        if self._is_dirty and self._current_filename:
            reply = QMessageBox.question(
                self, "未保存的修改",
                f"「{self._current_description}」有未保存的修改。\n是否保存后再继续？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if reply == QMessageBox.StandardButton.Save:
                self._on_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
            # Discard → 继续
        self._load_prompt_to_editor(group, filename)
        self._on_duplicate()

    def _delete_by_menu(self, group: str, filename: str):
        """右键菜单 → 删除。确认弹窗后删除。
        
        规则：
        - 删除当前加载的提示词 → 确认→删除→_auto_select_next（同按钮删除）
        - 删除其他提示词 → 仅重建树。若编辑区脏→先触发保存询问
        """
        is_current = (group == self._current_group
                      and filename == self._current_filename)

        # 删除非当前提示词，但编辑区有未保存修改 → 先触发保存询问
        if not is_current and self._is_dirty and self._current_filename:
            reply = QMessageBox.question(
                self, "未保存的修改",
                f"「{self._current_description}」有未保存的修改。\n是否保存后再继续？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if reply == QMessageBox.StandardButton.Save:
                self._on_save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
            # Discard → 继续

        prompt = None
        try:
            prompt = self._service.get(group, filename)
        except FileNotFoundError:
            return

        desc = prompt.description if prompt else filename
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除「{desc}」？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.delete(group, filename)
        except FileNotFoundError:
            pass

        self._load_data()
        if is_current:
            self._auto_select_next()

    def _on_new_prompt_in_group(self, group: str):
        """右键分组 → 新增提示词，默认分组为该分组。"""
        description, ok = QInputDialog.getText(
            self, "新增提示词", f"添加到「{group}」的提示词说明：",
            text="")
        if not ok or not description.strip():
            return

        try:
            self._service.create(group, description.strip(), "")
        except ValueError as e:
            QMessageBox.warning(self, "创建失败", str(e))
            return

        self._load_data()
        self._select_in_tree(group, description.strip())
        self._load_prompt_to_editor(group, description.strip())

    def _on_new_group(self):
        """右键分组 → 新建分组。弹窗输入分组名，创建空分组目录。"""
        name, ok = QInputDialog.getText(
            self, "新建分组", "分组名称：", text="")
        if not ok or not name.strip():
            return

        name = name.strip()
        try:
            self._service.create_group(name)
        except ValueError as e:
            QMessageBox.warning(self, "创建失败", str(e))
            return

        self._load_data()

    def _on_rename_group(self, old_name: str):
        """右键分组 → 修改分组名称。"""
        new_name, ok = QInputDialog.getText(
            self, "修改分组名称",
            f"将「{old_name}」重命名为：",
            text=old_name)
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name == old_name:
            return

        try:
            self._service.rename_group(old_name, new_name)
        except (ValueError, FileNotFoundError, FileExistsError) as e:
            QMessageBox.warning(self, "重命名失败", str(e))
            return

        self._load_data()

    def _on_delete_group(self, group_name: str):
        """右键分组 → 删除分组及组内全部提示词。"""
        # 统计组内提示词数量
        prompts = self._service.list_by_group(group_name)
        count = len(prompts)

        msg = f"确定删除分组「{group_name}」？"
        if count > 0:
            msg += f"\n\n组内 {count} 条提示词将被一并删除。"
        msg += "\n此操作不可撤销。"

        reply = QMessageBox.question(
            self, "确认删除分组", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.delete_group(group_name)
        except (ValueError, FileNotFoundError) as e:
            QMessageBox.warning(self, "删除失败", str(e))
            return

        # 若删除的是当前编辑区的分组 → 清空编辑区
        if group_name == self._current_group:
            self._clear_editor()

        self._load_data()
