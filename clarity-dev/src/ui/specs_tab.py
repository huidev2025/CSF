# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
SpecsTab V3 — 标签3：CSF规则标签页（PyQt6）。

v3 重写（IT-11a-V2）：从「内置编辑器+保存」切换到「只读查看器+外部编辑器+统一版本模型」。
- DT-01: 正文区只读化
- DT-02: [外部编辑器打开] 按钮
- DT-03: [🔄刷新] 正文按钮
- DT-04: 移除 [保存] 按钮及 dirty 追踪
- DT-05: [保存新版本] 语义修正 + description 支持
- DT-06: [🔄] 文件树刷新按钮
- DT-07: Header 行（当前版本 / 历史版本 + 黄色背景）
- DT-08: 布局重组
- DT-09: 说明区编辑 UX（编辑/保存/取消 + * 标记 + 切换文件提醒）
- DT-12: 版本视图状态机（current | historical）
- DT-13: 版本历史面板重排（说明粗体首行 + 版本号灰色小字）
- DT-17: 新建文件智能目录
"""

import os
import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QTextEdit, QLabel, QPushButton, QLineEdit,
    QInputDialog, QMessageBox, QMenu,
    QProgressDialog, QDialog, QDialogButtonBox, QCheckBox,
    QGroupBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QAction

from src.service.specs_service import SpecsService, COS_CONTEXT_WARNING
from src.core.models import TreeNode


# ── 颜色常量 ──────────────────────────────────────────────

_FACTORY_COLOR = QColor(0, 0, 0)
_USER_COLOR = QColor(0, 90, 180)
_ORANGE_COLOR = QColor(200, 120, 0)
_GRAY_BG = 'background-color: #f5f5f5;'
_YELLOW_BG = 'background-color: #fffde7;'
_STATUS_GREEN = 'color: green;'


class SpecsTab(QWidget):
    """CSF规则标签页 v3 — 只读查看器 + 统一版本模型。"""

    def __init__(self, specs_service: SpecsService, parent=None):
        super().__init__(parent)
        self._svc = specs_service
        self._current_path: str = ''
        # DT-12: 版本视图状态机
        self._view_state: str = 'current'      # 'current' | 'historical'
        self._view_source_path: str = ''        # 当前显示版本的源文件绝对路径
        # DT-09: 说明编辑状态
        self._desc_editing: bool = False
        self._desc_original: str = ''

        # DT-02: 搜索防抖定时器
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._on_search_debounced)

        self._build_ui()
        self._load_file_tree()
        self._load_unapplied_rules()

    # ══════════════════════════════════════════════════════════
    # DT-08: 骨架布局
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        """DT-08: 构建 v3 布局。"""
        main = QVBoxLayout(self)
        main.setContentsMargins(4, 2, 4, 4)
        main.setSpacing(2)

        # ── 顶部工具栏（DT-08: 基线按钮占位）──
        toolbar = QHBoxLayout()
        self._baseline_all_btn = QPushButton('备份全部CSF基线')
        self._baseline_all_btn.clicked.connect(self._on_baseline)
        self._baseline_mgr_btn = QPushButton('基线管理')
        self._baseline_mgr_btn.clicked.connect(self._on_baseline_manager)
        toolbar.addWidget(self._baseline_all_btn)
        toolbar.addWidget(self._baseline_mgr_btn)
        toolbar.addStretch()
        main.addLayout(toolbar)

        # ── Header 行（DT-07）──
        self._header_label = QLabel('')
        self._header_label.setVisible(False)  # 初始为空，隐藏以减少间距
        self._header_label.setStyleSheet(
            'font-size: 12px; padding: 2px 6px; border-radius: 3px;')
        main.addWidget(self._header_label)

        # ── 两栏 QSplitter ──
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(
            'QSplitter::handle { background-color: #D0D0D0; }'
        )

        left = self._build_tree_panel()
        self._splitter.addWidget(left)

        right = self._build_viewer_panel()
        self._splitter.addWidget(right)

        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 7)

        # Splitter 持久化（IT-10-V2）
        self._splitter_save_timer = QTimer(self)
        self._splitter_save_timer.setSingleShot(True)
        self._splitter_save_timer.setInterval(300)
        self._splitter_save_timer.timeout.connect(self._do_debounced_save)
        self._splitter.splitterMoved.connect(
            lambda: self._splitter_save_timer.start())

        main.addWidget(self._splitter, stretch=1)

        # ── 状态栏 ──
        self._status_label = QLabel('')
        main.addWidget(self._status_label)

    # ══════════════════════════════════════════════════════════
    # 左侧：文件树面板
    # ══════════════════════════════════════════════════════════

    def _build_tree_panel(self) -> QWidget:
        """构建文件树面板 + 搜索框（DT-02）+ 左侧 QSplitter（DT-04）。"""
        panel = QWidget()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── DT-04: 左侧 QSplitter（文件树 ↔ 未应用规则）──
        self._left_splitter = QSplitter(Qt.Orientation.Vertical)
        self._left_splitter.setHandleWidth(4)
        self._left_splitter.setStyleSheet(
            'QSplitter::handle { background-color: #D0D0D0; }'
        )

        # 上半：文件树容器
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(2)

        # DT-02: 文件树标题行 + 搜索框 + ✕清除 + [🔄]刷新
        tree_header = QHBoxLayout()
        tree_header.addWidget(QLabel('文件树：'))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('搜索...')
        self._search_box.textChanged.connect(self._on_search_text_changed)
        tree_header.addWidget(self._search_box, stretch=1)
        self._search_clear_btn = QPushButton('✕')
        self._search_clear_btn.setFixedWidth(28)
        self._search_clear_btn.setVisible(False)
        self._search_clear_btn.clicked.connect(self._on_search_clear)
        tree_header.addWidget(self._search_clear_btn)
        self._tree_refresh_btn = QPushButton('🔄')
        self._tree_refresh_btn.setToolTip('刷新文件树')
        self._tree_refresh_btn.setFixedWidth(36)
        self._tree_refresh_btn.clicked.connect(self._on_tree_refresh)
        tree_header.addWidget(self._tree_refresh_btn)
        tree_layout.addLayout(tree_header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        tree_layout.addWidget(self._tree, stretch=1)

        # 新建文件按钮（DT-17）
        self._new_file_btn = QPushButton('＋新建文件')
        self._new_file_btn.clicked.connect(self._on_new_file)
        tree_layout.addWidget(self._new_file_btn)

        self._left_splitter.addWidget(tree_container)

        # 下半：未应用规则容器
        unapplied_container = QWidget()
        unapplied_layout = QVBoxLayout(unapplied_container)
        unapplied_layout.setContentsMargins(0, 0, 0, 0)
        unapplied_layout.setSpacing(2)

        unapplied_label = QLabel('── 未应用规则 ──')
        unapplied_label.setStyleSheet(
            'color: gray; font-size: 11px; padding: 4px 0 2px 0;')
        unapplied_layout.addWidget(unapplied_label)

        self._unapplied_list = QListWidget()
        self._unapplied_list.itemClicked.connect(self._on_unapplied_clicked)
        unapplied_layout.addWidget(self._unapplied_list, stretch=1)

        self._left_splitter.addWidget(unapplied_container)
        self._left_splitter.setStretchFactor(0, 7)
        self._left_splitter.setStretchFactor(1, 3)
        self._left_splitter.splitterMoved.connect(
            lambda: self._splitter_save_timer.start())

        outer_layout.addWidget(self._left_splitter)
        return panel

    # ══════════════════════════════════════════════════════════
    # 右侧：查看器面板
    # ══════════════════════════════════════════════════════════

    def _build_viewer_panel(self) -> QWidget:
        """构建查看器面板：DT-05 嵌套QSplitter（说明↔正文↔版本）。"""
        panel = QWidget()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(4, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── DT-05: 右侧外层 QSplitter（说明 ↔ 正文+版本）──
        self._right_outer_splitter = QSplitter(Qt.Orientation.Vertical)
        self._right_outer_splitter.setHandleWidth(4)
        self._right_outer_splitter.setStyleSheet(
            'QSplitter::handle { background-color: #D0D0D0; }'
        )

        # 说明区容器
        desc_container = QWidget()
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(0, 0, 0, 4)
        desc_layout.setSpacing(4)

        desc_header = QHBoxLayout()
        self._desc_title_label = QLabel('文件说明')
        desc_header.addWidget(self._desc_title_label)
        desc_header.addStretch()
        self._desc_edit_btn = QPushButton('编辑说明')
        self._desc_edit_btn.clicked.connect(self._on_edit_description)
        self._desc_save_btn = QPushButton('保存说明')
        self._desc_save_btn.clicked.connect(self._on_save_description)
        self._desc_save_btn.setVisible(False)
        self._desc_cancel_btn = QPushButton('取消')
        self._desc_cancel_btn.clicked.connect(self._on_cancel_description)
        self._desc_cancel_btn.setVisible(False)
        desc_header.addWidget(self._desc_edit_btn)
        desc_header.addWidget(self._desc_save_btn)
        desc_header.addWidget(self._desc_cancel_btn)
        desc_layout.addLayout(desc_header)

        self._desc_edit = QTextEdit()
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setMinimumHeight(48)
        self._desc_edit.setStyleSheet(_GRAY_BG)
        self._desc_edit.setPlaceholderText('（无说明）')
        desc_layout.addWidget(self._desc_edit, stretch=1)

        self._right_outer_splitter.addWidget(desc_container)

        # ── DT-05: 右侧内层 QSplitter（正文 ↔ 版本信息）──
        self._right_inner_splitter = QSplitter(Qt.Orientation.Vertical)
        self._right_inner_splitter.setHandleWidth(4)
        self._right_inner_splitter.setStyleSheet(
            'QSplitter::handle { background-color: #D0D0D0; }'
        )

        # 正文区容器
        body_container = QWidget()
        body_layout = QVBoxLayout(body_container)
        body_layout.setContentsMargins(0, 0, 0, 4)
        body_layout.setSpacing(4)

        body_header = QHBoxLayout()
        body_header.addStretch()
        self._body_external_btn = QPushButton('外部编辑器打开')
        self._body_external_btn.setToolTip('用系统默认编辑器打开当前文件')
        self._body_external_btn.clicked.connect(self._on_external_edit)
        self._body_refresh_btn = QPushButton('🔄 刷新')
        self._body_refresh_btn.setToolTip('从数据来源重新读取正文和说明')
        self._body_refresh_btn.clicked.connect(self._on_body_refresh)
        body_header.addWidget(self._body_external_btn)
        body_header.addWidget(self._body_refresh_btn)
        body_layout.addLayout(body_header)

        self._body_edit = QTextEdit()
        self._body_edit.setReadOnly(True)
        body_layout.addWidget(self._body_edit, stretch=1)

        # 底部按钮栏
        btn_layout = QHBoxLayout()
        self._save_new_btn = QPushButton('保存新版本')
        self._save_new_btn.clicked.connect(self._on_save_new)
        btn_layout.addWidget(self._save_new_btn)

        self._delete_btn = QPushButton('删除')
        self._delete_btn.setToolTip('删除当前版本或历史版本')
        self._delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self._delete_btn)

        self._apply_btn = QPushButton('应用为当前版本')
        self._apply_btn.setToolTip('将此历史版本设为当前版本')
        self._apply_btn.clicked.connect(self._on_apply_version)
        self._apply_btn.setVisible(False)
        btn_layout.addWidget(self._apply_btn)

        btn_layout.addStretch()
        body_layout.addLayout(btn_layout)

        self._right_inner_splitter.addWidget(body_container)

        # 版本信息容器
        version_container = QWidget()
        version_layout = QVBoxLayout(version_container)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(2)
        version_layout.addWidget(QLabel('版本信息：'))
        self._version_list = QListWidget()
        self._version_list.itemClicked.connect(self._on_version_clicked)
        version_layout.addWidget(self._version_list, stretch=1)
        version_layout.addStretch()  # 吸收多余高度，防止标题被拉伸

        self._right_inner_splitter.addWidget(version_container)

        self._right_inner_splitter.setStretchFactor(0, 1)  # 正文区获得全部额外高度
        self._right_inner_splitter.setStretchFactor(1, 0)  # 版本区不参与拉伸（有maxHeight=180）
        self._right_inner_splitter.splitterMoved.connect(
            lambda: self._splitter_save_timer.start())

        self._right_outer_splitter.addWidget(self._right_inner_splitter)
        self._right_outer_splitter.setStretchFactor(0, 0)  # 说明区不参与拉伸（有maxHeight=150）
        self._right_outer_splitter.setStretchFactor(1, 1)  # 正文+版本区获得全部额外高度
        self._right_outer_splitter.splitterMoved.connect(
            lambda: self._splitter_save_timer.start())

        outer_layout.addWidget(self._right_outer_splitter)
        return panel

    # ══════════════════════════════════════════════════════════
    # DT-06: 文件树加载与刷新
    # ══════════════════════════════════════════════════════════

    def _load_file_tree(self):
        """加载/刷新文件树。"""
        self._tree.clear()
        tree = self._svc.get_file_tree()
        self._populate_tree(None, tree)

    def _populate_tree(self, parent: QTreeWidgetItem | None,
                       node: TreeNode):
        """递归填充文件树。"""
        if parent is None:
            item = QTreeWidgetItem(self._tree, [node.name])
        else:
            item = QTreeWidgetItem(parent, [node.name])

        item.setData(0, Qt.ItemDataRole.UserRole, node.path)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, node.is_dir)

        if node.is_dir:
            item.setForeground(0, _FACTORY_COLOR)
            for child in node.children:
                self._populate_tree(item, child)
            if parent is None:
                item.setExpanded(True)  # 仅展开根节点一层
        else:
            if node.path == 'cos-context.md':
                item.setForeground(0, _ORANGE_COLOR)
                item.setToolTip(0, COS_CONTEXT_WARNING)
            elif node.is_factory:
                item.setForeground(0, _FACTORY_COLOR)
            else:
                item.setForeground(0, _USER_COLOR)

    def _on_tree_refresh(self):
        """DT-06: [🔄] 文件树刷新——重新扫描目录 + DT-16 同步刷新未应用规则。
        搜索框非空时清空搜索框并恢复完整树（DT-02）。"""
        if self._search_box.text():
            self._search_box.clear()
        self._load_file_tree()
        self._load_unapplied_rules()
        self._status_label.setText('文件树已刷新')

    # ══════════════════════════════════════════════════════════
    # IT-03e DT-02/03: 搜索框 + 文件树过滤
    # ══════════════════════════════════════════════════════════

    def _on_search_text_changed(self):
        """DT-02: 搜索框文本变化 → 启停防抖定时器 + 更新 UI 控件可见性。"""
        has_text = bool(self._search_box.text().strip())
        self._search_clear_btn.setVisible(has_text)
        self._tree_refresh_btn.setVisible(not has_text)
        self._search_timer.start()

    def _on_search_debounced(self):
        """DT-02/03: 300ms 防抖后触发搜索。"""
        query = self._search_box.text().strip()
        if not query:
            # 空查询 → 恢复完整树
            self._load_file_tree()
            self._status_label.setText('')
            return

        try:
            matched = self._svc.search_files(query)
        except Exception as e:
            self._status_label.setText(f'搜索出错: {e}')
            return

        self._apply_tree_filter(matched)
        self._status_label.setText(
            f'搜索「{query}」— {len(matched)} 个匹配')

    def _on_search_clear(self):
        """DT-02: 点击 ✕ 清空搜索框 → 恢复完整树。"""
        self._search_box.clear()

    def _apply_tree_filter(self, matched_paths: list[str]):
        """DT-03: 根据匹配路径过滤文件树。

        matched_paths 为空 → 恢复完整树。
        matched_paths 非空 → 仅显示匹配文件及其祖先目录（目录展开）。
        """
        if not matched_paths:
            self._load_file_tree()
            return

        matched_set = set(matched_paths)

        def _filter_item(item: QTreeWidgetItem) -> bool:
            """递归过滤：返回 True 表示该节点（或其子孙）应保留。"""
            path = item.data(0, Qt.ItemDataRole.UserRole)
            is_dir = item.data(0, Qt.ItemDataRole.UserRole + 1)

            if is_dir:
                any_child_visible = False
                for i in range(item.childCount()):
                    child = item.child(i)
                    if _filter_item(child):
                        any_child_visible = True
                item.setHidden(not any_child_visible)
                if any_child_visible:
                    item.setExpanded(True)
                return any_child_visible
            else:
                visible = path in matched_set
                item.setHidden(not visible)
                return visible

        for i in range(self._tree.topLevelItemCount()):
            _filter_item(self._tree.topLevelItem(i))

    # ══════════════════════════════════════════════════════════
    # 文件树交互
    # ══════════════════════════════════════════════════════════

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """点击文件树节点 → 打开（当前版本）。目录不响应。"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return

        is_dir = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if is_dir:
            return

        # DT-09: 切换文件前检查未保存说明（仅内容确实改变时才提醒）
        if self._desc_editing and self._current_path:
            current_text = self._desc_edit.toPlainText()
            if current_text != self._desc_original:
                reply = QMessageBox.question(
                    self, '说明已修改',
                    '文件说明已修改，是否保存？',
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    self._on_save_description()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
                else:
                    self._desc_edit.setPlainText(self._desc_original)
                    self._exit_desc_edit_mode()
            else:
                self._exit_desc_edit_mode()

        self._open_file(path)

    # ══════════════════════════════════════════════════════════
    # DT-12: 版本视图状态机 + 文件打开
    # ══════════════════════════════════════════════════════════

    def _open_file(self, rel_path: str):
        """DT-12: 打开文件—默认加载当前版本（current view）。"""
        try:
            info = self._svc.open_file(rel_path)
        except FileNotFoundError:
            return
        except Exception as e:
            QMessageBox.warning(self, '打开文件失败',
                                f'无法打开「{rel_path}」：\n{type(e).__name__}: {e}')
            return

        self._current_path = rel_path
        abs_path = str(self._svc.csf_lite_root / rel_path)

        # 切换到当前版本视图
        self._view_state = 'current'
        self._view_source_path = abs_path

        self._body_edit.setPlainText(info['content'])
        self._desc_edit.setPlainText(info['description'] or '')
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setStyleSheet(_GRAY_BG)
        self._exit_desc_edit_mode()
        self._update_header()
        self._update_viewer_buttons()

        # 加载版本历史
        try:
            self._load_version_history(rel_path)
        except Exception:
            pass

        self._status_label.setText(f'已打开: {rel_path}')

        # DT-16: 刷新未应用规则面板
        self._load_unapplied_rules()

    def _switch_to_historical_view(self, storage_path: str, version_num: int,
                                    description: str, content: str):
        """DT-12: 切换到历史版本视图（只读）。"""
        self._view_state = 'historical'
        self._view_source_path = storage_path

        self._body_edit.setPlainText(content)
        self._desc_edit.setPlainText(description or '')
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setStyleSheet(_GRAY_BG)
        self._exit_desc_edit_mode()
        self._update_header()
        self._update_viewer_buttons()
        self._status_label.setText(
            f'正在查看: {self._current_path} · v{version_num}（历史版本）')

    # ══════════════════════════════════════════════════════════
    # DT-07: Header 行
    # ══════════════════════════════════════════════════════════

    def _update_header(self):
        """DT-07: 更新 Header 行显示。空文本时隐藏以减少间距。"""
        if not self._current_path:
            self._header_label.setText('')
            self._header_label.setStyleSheet('')
            self._header_label.setVisible(False)
            return

        self._header_label.setVisible(True)
        if self._view_state == 'current':
            text = f'当前打开：{self._current_path}  ·  当前版本'
            self._header_label.setText(text)
            self._header_label.setStyleSheet(
                'font-size: 12px; padding: 2px 6px; border-radius: 3px;')
        else:
            m = re.search(r'v(\d+)\.md$', self._view_source_path)
            v_num = m.group(1) if m else '?'
            text = f'当前打开：{self._current_path}  ·  v{v_num}（历史版本）'
            self._header_label.setText(text)
            self._header_label.setStyleSheet(
                f'font-size: 12px; padding: 2px 6px; border-radius: 3px;'
                f' {_YELLOW_BG}')

    def _update_viewer_buttons(self):
        """DT-12: 根据视图状态和文件类型更新按钮可见性。

        - [应用为当前版本]：仅历史视图显示
        - [删除]：当前视图+出厂文件时隐藏；历史视图始终显示
        - [保存新版本]：始终可见（从来源读内容保存）
        """
        if self._view_state == 'historical':
            self._apply_btn.setVisible(True)
            self._delete_btn.setVisible(True)
            self._delete_btn.setText('删除（此备份）')
        else:
            self._apply_btn.setVisible(False)
            self._delete_btn.setText('删除')
            # 出厂文件当前版本 → 隐藏 [删除]
            if self._current_path and self._svc._is_factory(self._current_path):
                self._delete_btn.setVisible(False)
            else:
                self._delete_btn.setVisible(True)

    # ══════════════════════════════════════════════════════════
    # DT-10: 删除
    # ══════════════════════════════════════════════════════════

    def _on_delete(self):
        """DT-10: 删除按钮——根据视图状态分发到删除当前版本或历史版本。"""
        if not self._current_path:
            return

        if self._view_state == 'current':
            self._do_delete_current()
        else:
            self._do_delete_backup()

    def _do_delete_current(self):
        """DT-10: 删除当前版本——删源文件+file_meta，自动导航。"""
        rel_path = self._current_path
        is_factory = self._svc._is_factory(rel_path)

        if is_factory:
            QMessageBox.warning(self, '不可删除',
                                f'「{rel_path}」是出厂文件，其当前版本不可删除。')
            return

        # 确认
        reply = QMessageBox.question(
            self, '确认删除',
            f'即将删除「{rel_path}」的当前版本。\n'
            f'备份版本不受影响。是否继续？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self._svc.delete_current_version(rel_path)
        except Exception as e:
            QMessageBox.warning(self, '删除失败', str(e))
            return

        # 刷新文件树
        self._load_file_tree()
        self._load_unapplied_rules()

        if result['fallback_type'] == 'backup':
            # 自动打开最新备份
            try:
                content = self._svc.restore_version(
                    result['fallback_path'])
                self._switch_to_historical_view(
                    result['fallback_path'],
                    result['fallback_version'],
                    result['fallback_description'],
                    content)
            except Exception:
                self._current_path = ''
                self._body_edit.clear()
                self._desc_edit.clear()
                self._header_label.setText('该文件已被删除')
                self._header_label.setStyleSheet('')
                self._header_label.setVisible(True)
        elif result['fallback_type'] == 'none':
            # 无备份 → 清空面板
            self._current_path = ''
            self._body_edit.clear()
            self._desc_edit.clear()
            self._header_label.setText('该文件已被删除')
            self._header_label.setStyleSheet('')
            self._header_label.setVisible(True)
            self._version_list.clear()

        self._status_label.setText(f'已删除: {rel_path}')

    def _do_delete_backup(self):
        """DT-10: 删除历史版本——删备份文件，自动切回当前版本。"""
        storage_path = self._view_source_path
        rel_path = self._current_path

        reply = QMessageBox.question(
            self, '确认删除',
            f'即将删除此备份版本。是否继续？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._svc.delete_backup_version(storage_path, rel_path)
        except Exception as e:
            QMessageBox.warning(self, '删除失败', str(e))
            return

        # 自动切回当前版本
        try:
            self._open_file(rel_path)
        except Exception:
            self._current_path = ''
            self._body_edit.clear()
            self._desc_edit.clear()
            self._header_label.setText('')
            self._header_label.setVisible(False)

        self._status_label.setText(f'已删除备份版本')

    # ══════════════════════════════════════════════════════════
    # DT-11: 应用为当前版本
    # ══════════════════════════════════════════════════════════

    def _on_apply_version(self):
        """DT-11: 应用为当前版本——三选项确认框。"""
        if not self._current_path or self._view_state != 'historical':
            return

        storage_path = self._view_source_path
        rel_path = self._current_path

        # 提取版本号
        m = re.search(r'v(\d+)\.md$', storage_path)
        v_num = m.group(1) if m else '?'

        # 自定义三选项对话框
        msg = QMessageBox(self)
        msg.setWindowTitle('应用为当前版本')
        msg.setText(f'即将用 v{v_num} 替换当前版本。\n是否先备份当前版本？')
        msg.setIcon(QMessageBox.Icon.Question)

        backup_btn = msg.addButton('先备份再应用',
                                    QMessageBox.ButtonRole.AcceptRole)
        direct_btn = msg.addButton('直接应用',
                                    QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg.addButton('取消',
                                    QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(backup_btn)

        msg.exec()

        clicked = msg.clickedButton()

        if clicked == cancel_btn:
            return

        backup_first = (clicked == backup_btn)

        # v4: 移除 backup_note，apply_version 直接使用当前 file_meta 的 description
        try:
            result = self._svc.apply_version(
                storage_path, rel_path,
                backup_first=backup_first)
        except Exception as e:
            QMessageBox.warning(self, '应用失败', str(e))
            return

        # 切回当前版本视图
        self._open_file(rel_path)
        self._load_unapplied_rules()
        self._status_label.setText(
            f'已应用 v{v_num} 为当前版本: {rel_path}')

    # ══════════════════════════════════════════════════════════
    # DT-02: 外部编辑器打开
    # ══════════════════════════════════════════════════════════

    def _on_external_edit(self):
        """DT-02: 用系统默认编辑器打开当前显示版本的源文件。"""
        if not self._view_source_path:
            return
        try:
            os.startfile(self._view_source_path)
            self._status_label.setText('已在外部编辑器中打开')
        except Exception as e:
            QMessageBox.warning(self, '打开失败',
                                f'无法打开外部编辑器：\n{e}')

    # ══════════════════════════════════════════════════════════
    # DT-03: 正文刷新
    # ══════════════════════════════════════════════════════════

    def _on_body_refresh(self):
        """DT-03: 从当前显示版本的数据来源重新读取正文和说明。"""
        if not self._view_source_path or not self._current_path:
            return

        try:
            if self._view_state == 'current':
                info = self._svc.open_file(self._current_path)
                self._body_edit.setPlainText(info['content'])
                self._desc_edit.setPlainText(info['description'] or '')
            else:
                # 历史版本：从备份文件读取
                content = self._svc.restore_version(self._view_source_path)
                self._body_edit.setPlainText(content)
                # 重新读取 description
                versions = self._svc.get_version_history(self._current_path)
                for v in versions:
                    if v.storage_path == self._view_source_path:
                        self._desc_edit.setPlainText(v.description or '')
                        break

            self._status_label.setText('已刷新')
        except Exception as e:
            QMessageBox.warning(self, '刷新失败', str(e))

    # ══════════════════════════════════════════════════════════
    # DT-05: 保存新版本（语义修正）
    # ══════════════════════════════════════════════════════════

    def _get_current_source_content(self) -> str:
        """DT-05: 从当前显示版本的数据来源读取内容。"""
        if self._view_state == 'current':
            info = self._svc.open_file(self._current_path)
            return info['content']
        else:
            return self._svc.restore_version(self._view_source_path)

    def _on_save_new(self):
        """DT-05: 保存新版本——版本说明可选，留空取正文摘要。"""
        if not self._current_path:
            return

        desc, ok = QInputDialog.getText(
            self, '保存新版本',
            '版本说明（可选）：',
            text='')
        if not ok:
            return

        try:
            content = self._get_current_source_content()
        except Exception as e:
            QMessageBox.warning(self, '读取失败',
                                f'无法读取当前内容：\n{e}')
            return

        vm = self._svc.save_new_version(
            self._current_path, content, desc.strip())

        self._status_label.setText(f'已保存新版本 v{vm.version}')
        self._load_version_history(self._current_path)
        self._load_unapplied_rules()

    # ══════════════════════════════════════════════════════════
    # DT-09: 说明区编辑 UX
    # ══════════════════════════════════════════════════════════

    def _on_edit_description(self):
        """DT-09: 进入说明编辑模式。"""
        if not self._current_path:
            return
        self._desc_original = self._desc_edit.toPlainText()
        self._desc_edit.setReadOnly(False)
        self._desc_edit.setStyleSheet('')
        self._desc_title_label.setText('文件说明 *')
        self._desc_edit_btn.setVisible(False)
        self._desc_save_btn.setVisible(True)
        self._desc_cancel_btn.setVisible(True)
        self._desc_editing = True

    def _on_save_description(self):
        """DT-09: 保存说明——按版本类型写入不同存储。"""
        if not self._current_path:
            return

        desc = self._desc_edit.toPlainText()

        if self._view_state == 'current':
            self._svc.update_file_description(self._current_path, desc)
        else:
            try:
                self._svc.backup.update_backup_description(
                    self._view_source_path, desc)
            except Exception as e:
                QMessageBox.warning(self, '保存失败',
                                    f'无法更新历史版本说明：\n{e}')
                return

        self._exit_desc_edit_mode()
        self._status_label.setText('说明已保存')

    def _on_cancel_description(self):
        """DT-09: 取消说明编辑，恢复原内容。"""
        self._desc_edit.setPlainText(self._desc_original)
        self._exit_desc_edit_mode()

    def _exit_desc_edit_mode(self):
        """DT-09: 退出说明编辑模式。"""
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setStyleSheet(_GRAY_BG)
        self._desc_title_label.setText('文件说明')
        self._desc_edit_btn.setVisible(True)
        self._desc_save_btn.setVisible(False)
        self._desc_cancel_btn.setVisible(False)
        self._desc_editing = False

    # ══════════════════════════════════════════════════════════
    # DT-13: 版本历史面板（重排）
    # ══════════════════════════════════════════════════════════

    def _load_version_history(self, rel_path: str):
        """DT-13: 加载版本历史——说明粗体首行 + 版本号灰色小字。"""
        self._version_list.clear()
        try:
            versions = self._svc.get_version_history(rel_path)
        except Exception:
            return

        for v in versions:
            desc = v.description or ''
            desc_lines = desc.strip().split('\n')
            desc_first = desc_lines[0] if desc_lines else ''

            baseline_str = ' · '.join(v.baselines) if v.baselines else ''

            parts = []
            if desc_first:
                parts.append(f'<b>{desc_first}</b>')
            meta_parts = [f'v{v.version}']
            if baseline_str:
                meta_parts.append(baseline_str)
            if v.created_at:
                meta_parts.append(v.created_at[:10])
            meta_text = ' · '.join(meta_parts)
            parts.append(
                f'<span style="color:gray; font-size:11px;">{meta_text}</span>')

            if len(desc_lines) > 1:
                parts.append(
                    f'<br><span style="font-size:11px;">{desc_lines[1]}</span>')

            html = '<br>'.join(parts)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, v.storage_path)
            item.setData(Qt.ItemDataRole.UserRole + 1, v.version)
            item.setData(Qt.ItemDataRole.UserRole + 2, v.description or '')
            label = QLabel(html)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setWordWrap(True)
            self._version_list.addItem(item)
            self._version_list.setItemWidget(item, label)

        if not versions:
            self._version_list.addItem(QListWidgetItem('暂无历史版本'))

    def _on_version_clicked(self, item: QListWidgetItem):
        """DT-13: 单击版本 → 加载到只读查看器，切换到历史视图。"""
        storage_path = item.data(Qt.ItemDataRole.UserRole)
        if not storage_path:
            return

        version_num = item.data(Qt.ItemDataRole.UserRole + 1) or 0
        description = item.data(Qt.ItemDataRole.UserRole + 2) or ''

        try:
            content = self._svc.restore_version(storage_path)
        except Exception as e:
            QMessageBox.warning(self, '加载失败',
                                f'无法加载版本内容：\n{e}')
            return

        self._switch_to_historical_view(
            storage_path, version_num, description, content)

    # ══════════════════════════════════════════════════════════
    # DT-17: 新建文件（智能目录）
    # ══════════════════════════════════════════════════════════

    def _on_new_file(self):
        """DT-17: 新建文件——仅输入文件名，自动选目录。"""
        parent_dir = ''
        selected = self._tree.currentItem()
        if selected:
            path = selected.data(0, Qt.ItemDataRole.UserRole)
            is_dir = selected.data(0, Qt.ItemDataRole.UserRole + 1)
            if path:
                if is_dir:
                    parent_dir = path + '/'
                else:
                    parent_dir = str(Path(path).parent).replace('\\', '/')
                    if parent_dir and not parent_dir.endswith('/'):
                        parent_dir += '/'
                    if parent_dir in ('', '.'):
                        parent_dir = ''

        hint = (f'（将创建在 {parent_dir or "csf-lite/ 根目录"}）'
                if parent_dir else '（将创建在 csf-lite/ 根目录）')
        filename, ok = QInputDialog.getText(
            self, '新建文件',
            f'文件名（仅文件名，非路径）：\n{hint}',
            text='')
        if not ok or not filename.strip():
            return
        filename = filename.strip()

        try:
            full_path = self._svc.new_file(filename, content='',
                                           parent_dir=parent_dir)
        except Exception as e:
            QMessageBox.warning(self, '新建失败', str(e))
            return

        self._load_file_tree()
        self._open_file(full_path)
        self._status_label.setText(f'已创建: {full_path}')

    # ══════════════════════════════════════════════════════════
    # DT-14: 全局基线备份重做
    # ══════════════════════════════════════════════════════════

    def _on_baseline(self):
        """DT-14: 备份全部CSF基线——一个名称框，QProgressDialog进度条。"""
        name, ok = QInputDialog.getText(
            self, '备份全部CSF基线',
            '基线名称：',
            text='')
        if not ok or not name.strip():
            return
        name = name.strip()

        # 先统计文件数
        tree = self._svc.get_file_tree()
        all_files: list[str] = []

        def _collect(node: TreeNode):
            if not node.is_dir:
                all_files.append(node.path)
            for child in node.children:
                _collect(child)

        _collect(tree)
        total = len(all_files)

        # QProgressDialog
        progress = QProgressDialog(
            '正在备份全部CSF基线...', '取消', 0, total, self)
        progress.setWindowTitle('备份全部CSF基线')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        completed = 0

        def _progress_cb(current, total_count, filename):
            nonlocal completed
            completed = current
            progress.setValue(current)
            progress.setLabelText(f'正在备份：{filename} ({current}/{total_count})')
            return not progress.wasCanceled()

        try:
            result = self._svc.global_backup_all(name, _progress_cb)
        except Exception as e:
            progress.close()
            QMessageBox.warning(self, '备份失败', str(e))
            return

        progress.setValue(total)
        progress.close()

        QMessageBox.information(
            self, '全局基线已创建',
            f'基线「{result["name"]}」已创建，包含 {result["file_count"]} 个文件。\n'
            f'创建时间：{result["created_at"]}')
        self._status_label.setText(f'基线「{name}」已创建')

    # ══════════════════════════════════════════════════════════
    # DT-15: 基线管理面板
    # ══════════════════════════════════════════════════════════

    def _on_baseline_manager(self):
        """DT-15: 打开基线管理面板 QDialog。"""
        dialog = BaselineManagerDialog(self._svc, self)
        dialog.exec()
        self._load_unapplied_rules()

    # ══════════════════════════════════════════════════════════
    # DT-16: 未应用规则面板
    # ══════════════════════════════════════════════════════════

    def _load_unapplied_rules(self):
        """DT-16: 加载未应用规则——扫描所有文件的非当前版本备份。"""
        self._unapplied_list.clear()
        try:
            rules = self._svc.get_unapplied_rules()
        except Exception:
            return

        for r in rules:
            line = f'{r["file_name"]}  v{r["version"]}'
            if r.get('description_first_line'):
                line += f'  ({r["description_first_line"]})'

            item_ = QListWidgetItem(line)
            item_.setData(Qt.ItemDataRole.UserRole, r['storage_path'])
            item_.setData(Qt.ItemDataRole.UserRole + 1, r['version'])
            item_.setData(Qt.ItemDataRole.UserRole + 2,
                          r.get('description_first_line', ''))
            item_.setData(Qt.ItemDataRole.UserRole + 3, r['file_name'])
            self._unapplied_list.addItem(item_)

    def _on_unapplied_clicked(self, item: QListWidgetItem):
        """DT-16: 单击未应用规则 → 在右侧查看器加载该历史版本。"""
        storage_path = item.data(Qt.ItemDataRole.UserRole)
        if not storage_path:
            return

        version_num = item.data(Qt.ItemDataRole.UserRole + 1) or 0
        description = item.data(Qt.ItemDataRole.UserRole + 2) or ''
        file_name = item.data(Qt.ItemDataRole.UserRole + 3) or ''

        try:
            content = self._svc.restore_version(storage_path)
        except Exception as e:
            QMessageBox.warning(self, '加载失败',
                                f'无法加载版本内容：\n{e}')
            return

        # 设置当前路径为文件名，切换到历史视图
        self._current_path = file_name
        self._switch_to_historical_view(
            storage_path, version_num, description, content)

    # ══════════════════════════════════════════════════════════
    # 右键菜单
    # ══════════════════════════════════════════════════════════

    def _on_context_menu(self, pos: QPoint):
        """文件树右键菜单（DT-10: 含删除功能）。"""
        item = self._tree.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        is_dir = item.data(0, Qt.ItemDataRole.UserRole + 1)
        is_factory = self._svc._is_factory(path)

        menu = QMenu(self)

        if not is_dir:
            open_action = QAction('打开', self)
            open_action.triggered.connect(lambda: self._open_file(path))
            menu.addAction(open_action)

            # 外部编辑器打开
            ext_action = QAction('外部编辑器打开', self)
            ext_action.triggered.connect(
                lambda p=path: os.startfile(str(self._svc.csf_lite_root / p)))
            menu.addAction(ext_action)

            menu.addSeparator()

            # 删除（出厂文件不可删当前版本）
            if not is_factory:
                del_action = QAction('删除', self)
                del_action.triggered.connect(
                    lambda p=path: self._on_context_delete(p))
                menu.addAction(del_action)

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _on_context_delete(self, rel_path: str):
        """右键删除确认——确认后删除当前版本。"""
        reply = QMessageBox.question(
            self, '确认删除',
            f'即将删除「{rel_path}」的当前版本。\n'
            f'备份版本不受影响。是否继续？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self._svc.delete_current_version(rel_path)
        except Exception as e:
            QMessageBox.warning(self, '删除失败', str(e))
            return

        self._load_file_tree()
        self._load_unapplied_rules()

        if result['fallback_type'] == 'backup':
            try:
                content = self._svc.restore_version(result['fallback_path'])
                self._current_path = rel_path
                self._switch_to_historical_view(
                    result['fallback_path'],
                    result['fallback_version'],
                    result['fallback_description'],
                    content)
            except Exception:
                self._current_path = ''
                self._body_edit.clear()
                self._desc_edit.clear()
                self._header_label.setText('该文件已被删除')
                self._header_label.setStyleSheet('')
                self._header_label.setVisible(True)
        elif result['fallback_type'] == 'none':
            self._current_path = ''
            self._body_edit.clear()
            self._desc_edit.clear()
            self._header_label.setText('该文件已被删除')
            self._header_label.setStyleSheet('')
            self._header_label.setVisible(True)
            self._version_list.clear()

        self._status_label.setText(f'已删除: {rel_path}')

    # ══════════════════════════════════════════════════════════
    # DT-06: 多 Splitter 持久化
    # ══════════════════════════════════════════════════════════

    def save_splitter_state(self, settings) -> None:
        """DT-06: 保存 4 个 QSplitter 状态到 QSettings。"""
        settings.setValue("splitter/specs_tab/main",
                          self._splitter.saveState())
        settings.setValue("splitter/specs_tab/left",
                          self._left_splitter.saveState())
        settings.setValue("splitter/specs_tab/right_outer",
                          self._right_outer_splitter.saveState())
        settings.setValue("splitter/specs_tab/right_inner",
                          self._right_inner_splitter.saveState())

    def restore_splitter_state(self, settings) -> None:
        """DT-06: 从 QSettings 恢复 QSplitter 状态。
        优先读 splitter/specs_tab/main，fallback 读旧 key splitter/specs_tab（兼容旧版升级）。
        """
        self._splitter_settings = settings

        # 主 splitter：优先新 key，fallback 旧 key
        state = settings.value("splitter/specs_tab/main")
        if state is None:
            state = settings.value("splitter/specs_tab")
        if state is not None:
            self._splitter.restoreState(state)

        # 左侧 splitter
        state = settings.value("splitter/specs_tab/left")
        if state is not None:
            self._left_splitter.restoreState(state)

        # 右侧外层 splitter
        state = settings.value("splitter/specs_tab/right_outer")
        if state is not None:
            self._right_outer_splitter.restoreState(state)

        # 右侧内层 splitter
        state = settings.value("splitter/specs_tab/right_inner")
        if state is not None:
            self._right_inner_splitter.restoreState(state)

    def reset_splitter_to_default(self):
        """DT-06: 重置所有 QSplitter 为默认比例。
        main=30:70 / left=70:30 / right_outer=10:90 / right_inner=75:25
        """
        # 主 splitter
        w = self._splitter.width()
        main_sizes = [int(w * 0.3), int(w * 0.7)] if w > 0 else [300, 700]
        self._splitter.setSizes(main_sizes)

        # 左侧 splitter
        h = self._left_splitter.height()
        left_sizes = [int(h * 0.7), int(h * 0.3)] if h > 0 else [350, 150]
        self._left_splitter.setSizes(left_sizes)

        # 右侧外层 splitter
        h = self._right_outer_splitter.height()
        outer_sizes = [int(h * 0.1), int(h * 0.9)] if h > 0 else [80, 720]
        self._right_outer_splitter.setSizes(outer_sizes)

        # 右侧内层 splitter
        h = self._right_inner_splitter.height()
        inner_sizes = [int(h * 0.75), int(h * 0.25)] if h > 0 else [450, 150]
        self._right_inner_splitter.setSizes(inner_sizes)

    def _do_debounced_save(self):
        """防抖回调 — 300ms 无拖拽后保存 Splitter 状态。"""
        if hasattr(self, '_splitter_settings') and self._splitter_settings is not None:
            self.save_splitter_state(self._splitter_settings)


class BaselineManagerDialog(QDialog):
    """IT-11b DT-15: 基线管理面板 — QDialog。"""

    def __init__(self, svc: SpecsService, parent=None):
        super().__init__(parent)
        self._svc = svc
        self.setWindowTitle('基线管理')
        self.setMinimumSize(700, 500)
        self._build_ui()
        self._load_baselines()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── 上半：基线列表 + 文件预览 ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：基线列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel('基线列表：'))
        self._baseline_list = QListWidget()
        self._baseline_list.itemClicked.connect(self._on_baseline_selected)
        left_layout.addWidget(self._baseline_list)

        # 删除基线按钮
        del_btn = QPushButton('删除选中基线')
        del_btn.clicked.connect(self._on_delete_baseline)
        left_layout.addWidget(del_btn)

        splitter.addWidget(left)

        # 右侧：文件清单预览
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel('包含文件：'))
        self._file_preview = QListWidget()
        right_layout.addWidget(self._file_preview)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, stretch=1)

        # ── 下半：操作按钮 ──
        btn_layout = QHBoxLayout()

        self._restore_btn = QPushButton('批量应用')
        self._restore_btn.setToolTip('将基线中所有文件恢复到当前')
        self._restore_btn.clicked.connect(self._on_restore)
        btn_layout.addWidget(self._restore_btn)

        self._export_btn = QPushButton('导出基线')
        self._export_btn.setToolTip('按原目录结构导出基线所有文件')
        self._export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self._export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_baselines(self):
        """加载基线列表。"""
        self._baseline_list.clear()
        try:
            baselines = self._svc.baseline_list()
        except Exception:
            return

        self._baselines_data = baselines
        for b in baselines:
            label = b['name']
            if b.get('is_factory'):
                label += '  [出厂]'
            label += f'  —  {b["file_count"]} 文件'
            if b.get('created_at'):
                label += f'  ({b["created_at"][:10]})'

            item_ = QListWidgetItem(label)
            item_.setData(Qt.ItemDataRole.UserRole, b['name'])
            self._baseline_list.addItem(item_)

    def _on_baseline_selected(self, item: QListWidgetItem):
        """选中基线 → 右侧预览文件清单。"""
        name = item.data(Qt.ItemDataRole.UserRole)
        if not name:
            return

        self._file_preview.clear()
        try:
            files = self._svc.baseline_get_files(name)
        except Exception:
            return

        for f in files:
            desc_first = ''
            if f.get('description'):
                desc_lines = f['description'].strip().split('\n')
                desc_first = desc_lines[0] if desc_lines else ''

            line = f['target_id']
            if f.get('version'):
                line += f'  v{f["version"]}'
            if desc_first:
                line += f'  —  {desc_first}'
            self._file_preview.addItem(QListWidgetItem(line))

    def _on_delete_baseline(self):
        """删除选中基线。"""
        current = self._baseline_list.currentItem()
        if not current:
            return
        name = current.data(Qt.ItemDataRole.UserRole)

        # 检查是否出厂基线
        for b in self._baselines_data:
            if b['name'] == name and b.get('is_factory'):
                QMessageBox.warning(self, '不可删除',
                                    '「v1-出厂基线」不可删除。')
                return

        reply = QMessageBox.question(
            self, '确认删除',
            f'即将删除基线「{name}」。备份文件不受影响。是否继续？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._svc.baseline_delete(name)
        except Exception as e:
            QMessageBox.warning(self, '删除失败', str(e))
            return

        self._load_baselines()
        self._file_preview.clear()

    def _on_restore(self):
        """DT-15: 批量应用基线——确认框+先备份复选框+进度条。"""
        current = self._baseline_list.currentItem()
        if not current:
            QMessageBox.information(self, '提示', '请先选择一个基线。')
            return
        name = current.data(Qt.ItemDataRole.UserRole)

        # 获取文件数
        try:
            files = self._svc.baseline_get_files(name)
        except Exception:
            return
        total = len(files)

        # 确认框
        msg = QMessageBox(self)
        msg.setWindowTitle('批量应用基线')
        msg.setText(f'即将用基线「{name}」覆盖所有 {total} 个当前文件。\n建议先备份。')
        msg.setIcon(QMessageBox.Icon.Question)

        # 复选框
        cb = QCheckBox('先备份当前全部文件再应用')
        cb.setChecked(True)
        msg.setCheckBox(cb)

        ok_btn = msg.addButton('确认应用', QMessageBox.ButtonRole.AcceptRole)
        msg.addButton('取消', QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() != ok_btn:
            return

        backup_first = cb.isChecked()

        # QProgressDialog
        progress = QProgressDialog(
            '正在应用基线...', '取消', 0, total, self)
        progress.setWindowTitle('批量应用基线')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def _progress_cb(current, total_count, filename):
            progress.setValue(current)
            progress.setLabelText(f'正在恢复：{filename} ({current}/{total_count})')
            return not progress.wasCanceled()

        try:
            result = self._svc.baseline_restore(
                name, backup_first=backup_first,
                progress_callback=_progress_cb)
        except Exception as e:
            progress.close()
            QMessageBox.warning(self, '批量应用失败', str(e))
            return

        progress.setValue(total)
        progress.close()

        QMessageBox.information(
            self, '批量应用完成',
            f'基线「{name}」已应用。\n恢复 {result["restored_count"]}/{result["total_count"]} 个文件。')

    def _on_export(self):
        """DT-15: 导出基线——文件对话框+进度条+manifest。"""
        current = self._baseline_list.currentItem()
        if not current:
            QMessageBox.information(self, '提示', '请先选择一个基线。')
            return
        name = current.data(Qt.ItemDataRole.UserRole)

        export_dir = QFileDialog.getExistingDirectory(
            self, '选择导出目录')
        if not export_dir:
            return

        try:
            files = self._svc.baseline_get_files(name)
        except Exception:
            return
        total = len(files)

        progress = QProgressDialog(
            '正在导出基线...', '取消', 0, total, self)
        progress.setWindowTitle('导出基线')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def _progress_cb(current, total_count, filename):
            progress.setValue(current)
            progress.setLabelText(f'正在导出：{filename} ({current}/{total_count})')
            return not progress.wasCanceled()

        try:
            manifest_path = self._svc.baseline_export(
                name, export_dir, _progress_cb)
        except Exception as e:
            progress.close()
            QMessageBox.warning(self, '导出失败', str(e))
            return

        progress.setValue(total)
        progress.close()

        QMessageBox.information(
            self, '导出完成',
            f'基线「{name}」已导出到：\n{export_dir}\n'
            f'清单文件：_baseline_manifest.json')
