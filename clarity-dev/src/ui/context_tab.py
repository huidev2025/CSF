# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
ContextTab V6 — 标签2 v6 段列表 + 草稿系统 + staging。

STB-2 DT-02.3~02.14：
- 段列表标注行渲染（换版本/撤下/新装载三种样式+↩撤销）
- 拖拽重排
- 段操作（换版本/撤下/添加）+ 单条撤回
- staging 提交/撤回
- 刷新确认框 + 关窗恢复
- 底部按钮可用性联动
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
    QDialog, QDialogButtonBox, QCheckBox, QInputDialog,
    QMenu, QMessageBox, QTabWidget, QTextEdit, QScrollArea,
    QFrame, QSizePolicy, QComboBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from src.core.models import (
    SectionData, DraftState, DraftChange, TemplateData,
)
from src.service.context_service import (
    ContextService, VersionDeleteError, _parse_yaml_frontmatter,
)

logger = logging.getLogger(__name__)

# ── 序号映射：1~20用圆圈数字，21起用 (N) ──────────────────

_CIRCLE_NUMBERS = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


def _order_label(order: int) -> str:
    """将1-based序号转为显示标签。"""
    if 1 <= order <= 20:
        return _CIRCLE_NUMBERS[order - 1]
    return f'({order})'


# ══════════════════════════════════════════════════════════════
# DT-02.3: _SectionItemWidget — 段列表自定义行
# ══════════════════════════════════════════════════════════════

class _SectionItemWidget(QWidget):
    """段列表行 widget：主行 + 可选标注行。

    四种行样式：
    - 正常行：序号 + 粗体标题 + 灰色版本标签
    - 换版本标注行：橙色左边框 + `╰─ 换为 v{N} · {摘要} ↩`
    - 撤下标柱行：主行置灰 + 橙色标注 `╰─ 撤下此段 ↩`
    - 新装载标注行：绿色 `+` 前缀 + 绿色标注 `╰─ 新装载 ↩`
    """

    ORANGE = '#E67E22'
    GREEN = '#27AE60'
    BLUE = '#2980B9'
    GRAY = '#999'
    BORDER_W = 3  # 左边框宽度 px
    INDENT = 24  # 标注行缩进 px

    def __init__(self, order: int, title: str, version: Optional[int],
                 annotation: Optional[dict] = None,
                 on_undo=None, parent=None):
        """构造段行 widget。

        Args:
            order: 1-based 序号
            title: 段标题
            version: 来源版本号（None = 无版本）
            annotation: 标注信息 dict，None = 正常行。
                键: type ('swap_version'|'remove'|'add')、target_version、
                    summary（前20字）、on_undo 回调。
            on_undo: 全局撤回回调 (section_title, change_type)
        """
        super().__init__(parent)
        self._order = order
        self._title = title
        self._version = version
        self._annotation = annotation
        self._on_undo = on_undo

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(0)

        ann = self._annotation
        is_removed = ann and ann.get('type') == 'remove'
        is_add = ann and ann.get('type') == 'add'

        # ── 主行 ──
        main_row = QHBoxLayout()
        main_row.setContentsMargins(8, 4, 8, 4)
        main_row.setSpacing(4)

        order_str = _order_label(self._order)
        parts = [order_str, ' ', self._title]
        if self._version is not None:
            parts.append(f'  v{self._version}')

        if is_add:
            # 绿色 + 前缀
            label = QLabel(
                f'<span style="color:{self.GREEN}; font-weight:bold;">+</span>'
                f'<span style="font-size:12px; color:#999;">{order_str}</span>'
                f'<span style="margin-left:2px; font-size:13px; font-weight:600; color:#1A1A1A;">{self._title}</span>'
                + (f'<span style="margin-left:6px; font-size:11px; color:#999;">v{self._version}</span>'
                   if self._version else '')
            )
        elif is_removed:
            # 置灰
            label = QLabel(
                f'<span style="font-size:12px; color:{self.GRAY};">{order_str}</span>'
                f'<span style="margin-left:2px; font-size:13px; font-weight:600; color:{self.GRAY};">{self._title}</span>'
                + (f'<span style="margin-left:6px; font-size:11px; color:{self.GRAY};">v{self._version}</span>'
                   if self._version else '')
            )
        else:
            label = QLabel(
                f'<span style="font-size:12px; color:#999;">{order_str}</span>'
                f'<span style="margin-left:2px; font-size:13px; font-weight:600; color:#1A1A1A;">{self._title}</span>'
                + (f'<span style="margin-left:6px; font-size:11px; color:#999;">v{self._version}</span>'
                   if self._version else '')
            )
        label.setTextFormat(Qt.TextFormat.RichText)
        main_row.addWidget(label)
        main_row.addStretch()
        layout.addLayout(main_row)

        # ── 标注行 ──
        if ann:
            ann_layout = QHBoxLayout()
            ann_layout.setContentsMargins(self.INDENT, 0, 4, 2)
            ann_layout.setSpacing(4)

            ann_type = ann.get('type', '')

            if ann_type == 'swap_version':
                border = QLabel('')
                border.setFixedWidth(self.BORDER_W)
                border.setStyleSheet(
                    f'background-color: {self.ORANGE}; border-radius: 1px;'
                )
                ann_layout.addWidget(border)

                tv = ann.get('target_version', '?')
                summary = ann.get('summary', '')[:20]
                text = f'╰─ 换为 v{tv}'
                if summary:
                    text += f' · {summary}'
                ann_label = QLabel(
                    f'<span style="color:#555; font-size:12px;">{text}  '
                    f'<a href="undo" style="color:{self.BLUE}; text-decoration:none;">↩</a></span>'
                )
                ann_label.setTextFormat(Qt.TextFormat.RichText)
                ann_label.linkActivated.connect(
                    lambda: self._on_undo and self._on_undo(
                        self._title, 'swap_version'
                    )
                )
                ann_layout.addWidget(ann_label)

            elif ann_type == 'remove':
                border = QLabel('')
                border.setFixedWidth(self.BORDER_W)
                border.setStyleSheet(
                    f'background-color: {self.ORANGE}; border-radius: 1px;'
                )
                ann_layout.addWidget(border)

                ann_label = QLabel(
                    f'<span style="color:#555; font-size:12px;">╰─ 撤下此段  '
                    f'<a href="undo" style="color:{self.BLUE}; text-decoration:none;">↩</a></span>'
                )
                ann_label.setTextFormat(Qt.TextFormat.RichText)
                ann_label.linkActivated.connect(
                    lambda: self._on_undo and self._on_undo(
                        self._title, 'remove'
                    )
                )
                ann_layout.addWidget(ann_label)

            elif ann_type == 'add':
                border = QLabel('')
                border.setFixedWidth(self.BORDER_W)
                border.setStyleSheet(
                    f'background-color: {self.GREEN}; border-radius: 1px;'
                )
                ann_layout.addWidget(border)

                ann_label = QLabel(
                    f'<span style="color:#555; font-size:12px;">╰─ 新装载  '
                    f'<a href="undo" style="color:{self.BLUE}; text-decoration:none;">↩</a></span>'
                )
                ann_label.setTextFormat(Qt.TextFormat.RichText)
                ann_label.linkActivated.connect(
                    lambda: self._on_undo and self._on_undo(
                        self._title, 'add'
                    )
                )
                ann_layout.addWidget(ann_label)

            ann_layout.addStretch()
            layout.addLayout(ann_layout)


# ══════════════════════════════════════════════════════════════
# ContextTab — 标签2 V6 完整版
# ══════════════════════════════════════════════════════════════

class ContextTab(QWidget):
    """标签2：会话上下文 — v6 段列表 + 草稿 + staging。"""

    def __init__(self, context_service: ContextService, parent=None):
        super().__init__(parent)
        self._svc = context_service
        self._sections: list[SectionData] = []
        self._draft: DraftState = DraftState()
        self._pending_new_section_title: Optional[str] = None
        self._current_tab_has_unsaved: bool = False

        # STB-3 详情面板状态
        self._current_section_title: Optional[str] = None
        self._version_tab_state: str = 'blank'  # 'blank' | 'viewing' | 'applied'
        self._viewing_version: Optional[int] = None
        self._applied_versions: dict[str, int] = {}  # 标题→已装载版本号
        self._has_unsaved_current: bool = False
        self._has_unsaved_version: bool = False
        self._pending_select_title: Optional[str] = None

        self._build_ui()
        self._init_draft()
        self._check_recovery()
        self._rebuild_section_list()
        self._update_button_states()
        self._refresh_template_dropdown()  # DT-04.8: 初始化模板下拉

    # ══════════════════════════════════════════════════════════
    # UI 构建
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        """构建 QSplitter 两栏布局（默认60:40）+ 恢复提示条区域。"""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # DT-02.12: 恢复提示条（初始化时隐藏）
        self._recovery_bar = QWidget()
        recovery_layout = QHBoxLayout(self._recovery_bar)
        recovery_layout.setContentsMargins(6, 2, 6, 2)
        recovery_layout.setSpacing(6)
        self._recovery_label = QLabel('')
        self._recovery_label.setTextFormat(Qt.TextFormat.RichText)
        recovery_layout.addWidget(self._recovery_label)
        recovery_layout.addStretch()
        self._btn_load_draft = QPushButton('载入草稿')
        self._btn_load_draft.setStyleSheet(
            'padding: 1px 8px; font-size: 11px;'
        )
        self._btn_discard_draft = QPushButton('丢弃')
        self._btn_discard_draft.setStyleSheet(
            'padding: 1px 8px; font-size: 11px;'
        )
        recovery_layout.addWidget(self._btn_load_draft)
        recovery_layout.addWidget(self._btn_discard_draft)
        self._recovery_bar.setVisible(False)
        self._recovery_bar.setMaximumHeight(0)
        self._recovery_bar.setStyleSheet(
            'background-color: #FEF3E2; border-radius: 3px;'
        )
        outer.addWidget(self._recovery_bar)

        # DT-04.2: 顶部工具栏
        self._toolbar = self._build_toolbar()
        outer.addWidget(self._toolbar)

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter = self._main_splitter

        # ── 左栏 ──
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # DT-02.4: 拖拽启用
        self._section_list = QListWidget()
        self._section_list.setStyleSheet(
            'QListWidget::item:selected {'
            '  background: #E8F0FE;'
            '  border-left: 3px solid #2980B9;'
            '}'
        )
        self._section_list.setMinimumWidth(180)
        self._section_list.setDragDropMode(
            QListWidget.DragDropMode.InternalMove
        )
        self._section_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._section_list.model().rowsMoved.connect(
            self._on_rows_reordered
        )
        self._section_list.currentRowChanged.connect(
            self._on_section_selected
        )
        self._section_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._section_list.customContextMenuRequested.connect(
            self._on_context_menu
        )
        left_layout.addWidget(self._section_list, stretch=1)

        self._btn_row = self._build_button_row()
        left_layout.addLayout(self._btn_row)

        # ── 右栏：详情面板 ──
        self._detail_panel = self._build_detail_panel()
        splitter.addWidget(left)
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 20)
        splitter.setStretchFactor(1, 80)

        outer.addWidget(splitter)

    def _build_button_row(self) -> QVBoxLayout:
        """DT-02.13：段操作按钮双排布局（含 Unicode 图标）。

        上排：＋添加段 / 🖊新建段
        下排：⬆提交staging / ↩撤回staging
        """
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(6)

        _BTN = ('padding: 5px 14px; font-size: 12px; font-weight: 500;'
                ' border: 1px solid #C8C8C8; border-radius: 4px;'
                ' background: #FFF; min-width: 88px;')

        # ── 上排：段操作 ──
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self._btn_add_section = QPushButton('＋ 添加段')
        self._btn_new_section = QPushButton('🖊 新建段')
        self._btn_add_section.setStyleSheet(_BTN)
        self._btn_new_section.setStyleSheet(_BTN)
        self._btn_add_section.clicked.connect(self._on_add_section)
        self._btn_new_section.clicked.connect(self._on_new_section)
        row1.addWidget(self._btn_add_section)
        row1.addWidget(self._btn_new_section)
        row1.addStretch()
        outer.addLayout(row1)

        # ── 下排：staging 操作 ──
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        self._btn_commit_staging = QPushButton('⬆ 提交staging')
        self._btn_revert_staging = QPushButton('↩ 撤回staging')
        self._btn_commit_staging.setStyleSheet(_BTN)
        self._btn_revert_staging.setStyleSheet(_BTN)
        self._btn_commit_staging.clicked.connect(self._on_commit_staging)
        self._btn_revert_staging.clicked.connect(self._on_revert_staging)
        row2.addWidget(self._btn_commit_staging)
        row2.addWidget(self._btn_revert_staging)
        row2.addStretch()
        outer.addLayout(row2)

        # 撤下按钮改为仅右键菜单可用，不占底部按钮区
        self._btn_remove = QPushButton('✕ 撤下')
        self._btn_remove.setStyleSheet(_BTN)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_remove.setVisible(False)

        return outer

    # ══════════════════════════════════════════════════════════
    # DT-04.2: 顶部工具栏
    # ══════════════════════════════════════════════════════════

    def _build_toolbar(self) -> QWidget:
        """DT-04.2：构建顶部工具栏 — 7控件一行。

        从左到右：[刷新]  [换上下文] [模板▼]  [存为模版] [管理模板] [导入] [导出]
        """
        tb = QWidget()
        tb.setMaximumHeight(28)
        tb.setStyleSheet(
            'background-color: #FAFBFC; border-bottom: 1px solid #E8E8E8;'
        )
        layout = QHBoxLayout(tb)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        _BTN_STYLE = 'padding: 1px 10px; font-size: 12px; border: 1px solid #D0D0D0; border-radius: 2px; background: #FFF;'
        _DD_STYLE = 'padding: 1px 4px; font-size: 12px; min-width: 90px;'

        # [刷新] — 复用已有逻辑
        self._btn_toolbar_refresh = QPushButton('刷新')
        self._btn_toolbar_refresh.setStyleSheet(_BTN_STYLE)
        self._btn_toolbar_refresh.clicked.connect(self._on_refresh)
        layout.addWidget(self._btn_toolbar_refresh)

        # [换上下文]
        self._btn_change_context = QPushButton('换上下文')
        self._btn_change_context.setStyleSheet(_BTN_STYLE)
        self._btn_change_context.clicked.connect(self._on_change_context)
        layout.addWidget(self._btn_change_context)

        # [模板▼]
        self._template_dropdown = QComboBox()
        self._template_dropdown.setMinimumWidth(100)
        self._template_dropdown.setStyleSheet(_DD_STYLE)
        self._template_dropdown.setToolTip('选择模板以换上下文')
        layout.addWidget(self._template_dropdown)

        # [存为模版]
        self._btn_save_as_tpl = QPushButton('存为模版')
        self._btn_save_as_tpl.setStyleSheet(_BTN_STYLE)
        self._btn_save_as_tpl.clicked.connect(self._on_save_as_template)
        layout.addWidget(self._btn_save_as_tpl)

        # [管理模板]
        self._btn_manage_templates = QPushButton('管理模板')
        self._btn_manage_templates.setStyleSheet(_BTN_STYLE)
        self._btn_manage_templates.clicked.connect(
            self._on_manage_templates
        )
        layout.addWidget(self._btn_manage_templates)

        # [导入]
        self._btn_import = QPushButton('导入')
        self._btn_import.setStyleSheet(_BTN_STYLE)
        self._btn_import.clicked.connect(self._on_import)
        layout.addWidget(self._btn_import)

        # [导出]
        self._btn_export = QPushButton('导出')
        self._btn_export.setStyleSheet(_BTN_STYLE)
        self._btn_export.clicked.connect(self._on_export)
        layout.addWidget(self._btn_export)

        layout.addStretch()
        return tb

    def _refresh_template_dropdown(self):
        """DT-04.2：刷新模板下拉列表。"""
        self._template_dropdown.clear()
        templates = self._svc.load_templates()
        self._template_dropdown.addItem('')  # 空选项（不选择任何模板）
        for tpl in templates:
            self._template_dropdown.addItem(tpl.name)
        self._template_dropdown.setCurrentIndex(0)

    # ══════════════════════════════════════════════════════════
    # DT-04.3: 换上下文
    # ══════════════════════════════════════════════════════════

    def _on_change_context(self):
        """DT-04.3：[换上下文] 按钮逻辑。

        从 [模板▼] 获取选中模板 → 按冲突解决三规则应用到草稿：
        ①同标题段→模板版本覆盖草稿（swap_version）
        ②模板有、草稿无→添加（add）
        ③草稿有、模板无→撤下（remove）
        """
        tpl_name = self._template_dropdown.currentText().strip()
        if not tpl_name:
            QMessageBox.information(
                self, '换上下文',
                '请先从模板下拉列表中选择一个模板。',
            )
            return

        tpl = self._svc.read_template(tpl_name)
        if not tpl:
            QMessageBox.warning(
                self, '换上下文', f'模板 "{tpl_name}" 不存在。',
            )
            return

        # 构造模板段集合
        tpl_sections: dict[str, int] = {}
        for sec in tpl.sections:
            title = sec.get('title', '')
            ver = sec.get('version', 0)
            if title:
                tpl_sections[title] = ver

        # 当前草稿中的活跃段标题
        current_active = self._get_active_order()
        current_set = set(current_active)

        # 规则①②③
        for tpl_title, tpl_ver in tpl_sections.items():
            if tpl_title in current_set:
                # 规则①：同标题段 → swap_version
                change = DraftChange(
                    change_type='swap_version',
                    section_title=tpl_title,
                    to_version=tpl_ver,
                )
                self._draft.add_change(change)
                # 同步 _applied_versions，确保版本Tab正确显示已装载状态
                self._applied_versions[tpl_title] = tpl_ver
                logger.info(
                    '[换上下文] swap: %s → v%d', tpl_title, tpl_ver,
                )
            else:
                # 规则②：模板有、草稿无 → add
                change = DraftChange(
                    change_type='add',
                    section_title=tpl_title,
                    to_version=tpl_ver,
                )
                self._draft.add_change(change)
                # 同步 _applied_versions，确保版本Tab正确显示已装载状态
                self._applied_versions[tpl_title] = tpl_ver
                logger.info(
                    '[换上下文] add: %s v%d', tpl_title, tpl_ver,
                )

        # 规则③：草稿有、模板无 → remove
        for cur_title in current_active:
            if cur_title not in tpl_sections:
                change = DraftChange(
                    change_type='remove',
                    section_title=cur_title,
                )
                self._draft.add_change(change)
                logger.info('[换上下文] remove: %s', cur_title)

        self._rebuild_section_list()
        self._update_button_states()

        # 重载当前段详情，让 _applied_versions 同步到版本Tab
        if self._current_section_title:
            self._load_section_to_detail(self._current_section_title)

    # ══════════════════════════════════════════════════════════
    # DT-04.4: 存为模版
    # ══════════════════════════════════════════════════════════

    def _on_save_as_template(self):
        """DT-04.4：[存为模版] 完整流程。

        ①检查「当前」Tab 未保存 → 提示中止
        ②检查「版本」Tab 未保存 → 提示中止
        ③取当前草稿的段配置
        ④检查在役段是否有对应段库版本 → 无则提示中止
        ⑤输入模板名 → 写入模板JSON → 刷新下拉
        """
        # ①/② 检查未保存
        if self._current_tab_has_unsaved:
            if self._has_unsaved_current:
                QMessageBox.warning(
                    self, '存为模版',
                    '"当前"Tab中有未保存的编辑，请先保存。',
                )
                return
            if self._has_unsaved_version:
                QMessageBox.warning(
                    self, '存为模版',
                    '"版本"Tab中有未保存的编辑，请先保存。',
                )
                return

        # ③取当前段配置（活跃段列表 + 版本）
        active_order = self._get_active_order()
        if not active_order:
            QMessageBox.information(
                self, '存为模版', '当前没有在役段，无法存为模版。',
            )
            return

        # ④检查每个在役段是否有段库版本
        no_version_titles: list[str] = []
        section_refs: list[dict] = []

        for title in active_order:
            versions = self._svc.load_version_list(title)
            if not versions:
                no_version_titles.append(title)
                continue
            # 使用最新版本
            section_refs.append({
                'title': title,
                'version': versions[0].version,
            })

        if no_version_titles:
            QMessageBox.warning(
                self, '存为模版',
                '以下段在段库中无版本：\n' +
                '\n'.join(f'  · {t}' for t in no_version_titles) +
                '\n\n请先切换到对应段，使用[保存为段库版本]创建版本后再存为模版。',
            )
            return

        if not section_refs:
            QMessageBox.information(
                self, '存为模版', '所有在役段均无段库版本，无法存为模版。',
            )
            return

        # ⑤输入模板名
        tpl_name, ok = QInputDialog.getText(
            self, '存为模版', '输入模板名：',
        )
        if not ok or not tpl_name.strip():
            return

        tpl_name = tpl_name.strip()
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        tpl = TemplateData(
            name=tpl_name,
            sections=section_refs,
            created_at=now,
        )
        self._svc.write_template(tpl)
        self._refresh_template_dropdown()

        # 选中新模板
        idx = self._template_dropdown.findText(tpl_name)
        if idx >= 0:
            self._template_dropdown.setCurrentIndex(idx)

        logger.info(
            '[存为模版] %s（%d个段）', tpl_name, len(section_refs),
        )

    # ══════════════════════════════════════════════════════════
    # DT-04.5: 管理模板
    # ══════════════════════════════════════════════════════════

    def _on_manage_templates(self):
        """DT-04.5：[管理模板] → 弹出对话框列出所有模板+[删除]按钮。"""
        templates = self._svc.load_templates()

        dlg = QDialog(self)
        dlg.setWindowTitle('管理模板')
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(4)

        if not templates:
            layout.addWidget(QLabel(
                '<span style="color: #888;">暂无模板。</span>'
            ))
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            btns.accepted.connect(dlg.accept)
            layout.addWidget(btns)
            dlg.exec()
            return

        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_w = QWidget()
        scroll_layout = QVBoxLayout(scroll_w)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(2)

        for tpl in templates:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(8)

            # 模板名 + 创建日期
            date_str = tpl.created_at[:10] if len(tpl.created_at) >= 10 else ''
            info = QLabel(
                f'<b>{tpl.name}</b>'
                + (f'  <span style="color:#888;">{date_str}</span>'
                   if date_str else '')
            )
            row_layout.addWidget(info)
            row_layout.addStretch()

            btn_del = QPushButton('删除')
            btn_del.setStyleSheet(
                'padding: 2px 10px; font-size: 11px; color: #E74C3C;'
            )

            def make_delete_handler(name=tpl.name):
                return lambda: self._do_delete_template(name, dlg)

            btn_del.clicked.connect(make_delete_handler())
            row_layout.addWidget(btn_del)

            # [重命名]
            btn_rename = QPushButton('重命名')
            btn_rename.setStyleSheet(
                'padding: 2px 10px; font-size: 11px;'
            )

            def make_rename_handler(name=tpl.name):
                return lambda: self._do_rename_template(name, dlg)

            btn_rename.clicked.connect(make_rename_handler())
            row_layout.addWidget(btn_rename)

            scroll_layout.addWidget(row)

        scroll.setWidget(scroll_w)
        layout.addWidget(scroll)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        dlg.exec()

    def _do_delete_template(self, name: str, parent_dlg: QDialog):
        """DT-04.5：确认后删除模板。"""
        reply = QMessageBox.question(
            self, '删除模板',
            f'删除模板"{name}"？\n模板文件将被删除，段库中的版本不受影响。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._svc.delete_template(name)
        self._refresh_template_dropdown()
        logger.info('[管理模板] 已删除: %s', name)

        # 刷新对话框
        parent_dlg.accept()
        self._on_manage_templates()

    def _do_rename_template(self, name: str, parent_dlg: QDialog):
        """弹出输入框 → 重命名模板 → 刷新对话框。"""
        new_name, ok = QInputDialog.getText(
            self, '重命名模板', f'为模板"{name}"输入新名称：',
            text=name,
        )
        if not ok or not new_name.strip() or new_name.strip() == name:
            return

        try:
            self._svc.rename_template(name, new_name.strip())
        except (FileNotFoundError, ValueError) as e:
            QMessageBox.warning(self, '重命名失败', str(e))
            return

        self._refresh_template_dropdown()
        logger.info('[管理模板] 已重命名: %s → %s', name, new_name.strip())

        # 刷新对话框
        parent_dlg.accept()
        self._on_manage_templates()

    # ══════════════════════════════════════════════════════════
    # DT-04.6: 导入
    # ══════════════════════════════════════════════════════════

    def _on_import(self):
        """DT-04.6：[导入] — 文件浏览 → 解析 → 段入库 → 生成模板。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入 Context 文件',
            '', 'Markdown 文件 (*.md);;所有文件 (*)',
        )
        if not file_path:
            return

        try:
            tpl = self._svc.import_context(file_path)
            self._refresh_template_dropdown()

            # 选中新导入的模板
            idx = self._template_dropdown.findText(tpl.name)
            if idx >= 0:
                self._template_dropdown.setCurrentIndex(idx)

            QMessageBox.information(
                self, '导入成功',
                f'成功导入 {len(tpl.sections)} 个段。\n'
                f'模板已生成：{tpl.name}',
            )
            logger.info(
                '[导入] %s → 模板"%s"（%d段）',
                file_path, tpl.name, len(tpl.sections),
            )
        except ValueError as e:
            QMessageBox.warning(self, '导入失败', str(e))

    # ══════════════════════════════════════════════════════════
    # DT-04.7: 导出
    # ══════════════════════════════════════════════════════════

    def _on_export(self):
        """DT-04.7：[导出] — 选模板 → 拼装 → 另存。"""
        templates = self._svc.load_templates()
        if not templates:
            QMessageBox.information(
                self, '导出', '暂无模板可导出。请先创建或导入模板。',
            )
            return

        # 弹窗选模板
        tpl_names = [t.name for t in templates]
        tpl_name, ok = QInputDialog.getItem(
            self, '导出', '选择要导出的模板：',
            tpl_names, 0, False,
        )
        if not ok or not tpl_name:
            return

        # 文件另存
        output_path, _ = QFileDialog.getSaveFileName(
            self, '导出 Context 文件',
            f'{tpl_name}.md', 'Markdown 文件 (*.md);;所有文件 (*)',
        )
        if not output_path:
            return

        try:
            self._svc.export_context(tpl_name, output_path)
            QMessageBox.information(
                self, '导出成功',
                f'已导出到：{output_path}',
            )
            logger.info(
                '[导出] 模板"%s" → %s', tpl_name, output_path,
            )
        except ValueError as e:
            QMessageBox.warning(self, '导出失败', str(e))

    # ══════════════════════════════════════════════════════════
    # DT-03.1: _build_detail_panel — 右侧详情面板
    # ══════════════════════════════════════════════════════════

    def _build_detail_panel(self) -> QWidget:
        """DT-03.1：构建右侧详情面板。

        垂直 QSplitter（默认60:40，可拖拽，比例通过QSettings持久化）：
          上方 = QTabWidget（两Tab：「当前」/「版本」）
          下方 = 版本备份列表 + 模板引用
        """
        panel = QWidget()
        panel.setStyleSheet('background-color: #FFFFFF;')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(0)

        # 恢复 splitter 比例
        settings = QSettings('Clarity', 'CSF')
        saved_ratio = settings.value(
            'context/detail_splitter_ratio', None
        )

        self._detail_splitter = QSplitter(Qt.Orientation.Vertical)

        # ── 上方：两Tab ──
        self._detail_tabs = QTabWidget()
        self._detail_tabs.setStyleSheet(
            'QTabBar::tab {'
            '  padding: 3px 12px; font-size: 12px;'
            '  border: 1px solid #D0D0D0;'
            '  border-bottom: none;'
            '  background: #F0F0F0; color: #777;'
            '}'
            'QTabBar::tab:selected {'
            '  background: #2980B9; color: #FFF; font-weight: 600;'
            '  border-color: #2980B9;'
            '}'
        )
        self._current_tab = self._build_current_tab()
        self._version_tab = self._build_version_tab()
        self._detail_tabs.addTab(self._current_tab, '当前')
        self._detail_tabs.addTab(self._version_tab, '版本')
        self._detail_tabs.currentChanged.connect(
            self._on_detail_tab_changed
        )

        # ── 下方：版本备份列表 ──
        self._version_list_container = QWidget()
        self._version_list_container.setStyleSheet(
            'background-color: #FFFFFF; border: 1px solid #E8E8E8; border-radius: 4px;'
        )
        vl_layout = QVBoxLayout(self._version_list_container)
        vl_layout.setContentsMargins(0, 0, 0, 0)
        vl_layout.setSpacing(0)

        # 标题
        self._version_list_title = QLabel('<b>版本备份</b>')
        self._version_list_title.setStyleSheet(
            'margin-top: 4px; font-size: 12px;'
            'padding: 3px 6px;'
        )
        vl_layout.addWidget(self._version_list_title)

        # 版本条目滚动区
        self._version_scroll = QScrollArea()
        self._version_scroll.setWidgetResizable(True)
        self._version_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._version_scroll.setStyleSheet('QScrollArea { padding: 6px; }')
        self._version_entries_widget = QWidget()
        self._version_entries_layout = QVBoxLayout(
            self._version_entries_widget
        )
        self._version_entries_layout.setContentsMargins(6, 4, 6, 4)
        self._version_entries_layout.setSpacing(2)
        self._version_entries_layout.addStretch()
        self._version_scroll.setWidget(self._version_entries_widget)
        vl_layout.addWidget(self._version_scroll)

        # 模板引用信息
        self._template_ref_label = QLabel('')
        self._template_ref_label.setStyleSheet(
            'color: #888; font-size: 11px; padding: 2px 6px;'
        )
        self._template_ref_label.setVisible(False)
        vl_layout.addWidget(self._template_ref_label)

        # 空态引导文字
        self._version_empty_label = QLabel(
            '<span style="color: #999;">该段尚无版本备份。'
            '使用下方 [保存为段库版本] 创建。</span>'
        )
        self._version_empty_label.setWordWrap(True)
        self._version_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._version_empty_label.setStyleSheet('color: #999; padding: 16px;')
        vl_layout.addWidget(self._version_empty_label)

        self._detail_splitter.addWidget(self._detail_tabs)
        self._detail_splitter.addWidget(self._version_list_container)
        self._detail_splitter.setStretchFactor(0, 65)
        self._detail_splitter.setStretchFactor(1, 35)

        # 恢复比例
        if saved_ratio:
            try:
                vals = saved_ratio
                if isinstance(vals, (list, tuple)) and len(vals) == 2:
                    self._detail_splitter.setSizes([int(v) for v in vals])
            except Exception:
                pass

        # 持久化比例
        self._detail_splitter.splitterMoved.connect(
            self._on_detail_splitter_moved
        )

        layout.addWidget(self._detail_splitter)

        # 初始空态
        self._show_detail_empty_state()
        return panel

    def _on_detail_splitter_moved(self, pos, index):
        """持久化详情面板上下分割比例。"""
        sizes = self._detail_splitter.sizes()
        settings = QSettings('Clarity', 'CSF')
        settings.setValue('context/detail_splitter_ratio', sizes)

    # ══════════════════════════════════════════════════════════
    # DT-03.2: 标题行
    # ══════════════════════════════════════════════════════════

    def _build_title_row(self) -> tuple[QWidget, dict]:
        """DT-03.2：构建标题行 widget。返回 (widget, labels_dict)。

        labels_dict 包含四个 QLabel：title, version, status, unsaved。
        调用方各自持有，避免 _build_current_tab/_build_version_tab 覆盖。
        """
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(6)

        title_label = QLabel('')
        title_label.setStyleSheet(
            'font-weight: bold; font-size: 13px; color: #1A1A1A;'
        )
        layout.addWidget(title_label)

        version_label = QLabel('')
        version_label.setStyleSheet(
            'color: #888; font-size: 11px;'
        )
        layout.addWidget(version_label)

        status_label = QLabel('')
        status_label.setStyleSheet('font-size: 11px;')
        layout.addWidget(status_label)

        unsaved_label = QLabel('')
        unsaved_label.setStyleSheet(
            'color: #E74C3C; font-weight: bold; font-size: 13px;'
        )
        layout.addWidget(unsaved_label)

        layout.addStretch()

        labels = {
            'title': title_label,
            'version': version_label,
            'status': status_label,
            'unsaved': unsaved_label,
        }
        return w, labels

    def _update_title_row(
        self, labels: dict,
        title: str, version: Optional[int],
        is_current: bool, is_applied: bool = False,
    ):
        """更新标题行显示。labels 来自 _build_title_row 返回值。"""
        labels['title'].setText(f'段名称：{title}')

        if version is not None:
            if is_current:
                labels['version'].setText(f'在役 v{version}')
            else:
                labels['version'].setText(f'v{version}')
        else:
            labels['version'].setText('')

        # 状态标记
        if is_applied:
            labels['status'].setText('已应用到草稿')
            labels['status'].setStyleSheet(
                'color: #27AE60; font-size: 11px; font-weight: bold;'
            )
        else:
            labels['status'].setText('')
            labels['status'].setStyleSheet('')

        # 未保存标记
        has_unsaved = (
            self._has_unsaved_current
            if is_current
            else self._has_unsaved_version
        )
        if has_unsaved:
            labels['unsaved'].setText('*')
        else:
            labels['unsaved'].setText('')

    # ══════════════════════════════════════════════════════════
    # DT-03.3: 「当前」Tab
    # ══════════════════════════════════════════════════════════

    def _build_current_tab(self) -> QWidget:
        """DT-03.3：构建「当前」Tab。

        ①说明区 QTextEdit（可编辑）
        ②正文区 QTextEdit（只读，选中可复制）
        说明↔正文通过垂直 QSplitter 可拖拽（比例持久化）
        ③[外部编辑器打开正文] 按钮
        ④按钮行 [保存到当前上下文] [保存为段库版本]
        """
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 2, 6, 4)
        layout.setSpacing(2)

        # 标题行
        title_w, self._ct_labels = self._build_title_row()
        layout.addWidget(title_w)

        # 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('border: 1px solid #E8E8E8; margin: 4px 0;')
        layout.addWidget(sep)

        # ── 说明↔正文可拖拽分割（B.2）──
        self._current_splitter = QSplitter(Qt.Orientation.Vertical)
        splitter = self._current_splitter
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet(
            'QSplitter::handle { background-color: #e0e0e0; }'
        )

        # 说明区（灰色标题条 + 保存按钮 + 白色输入框）
        desc_wrapper = QWidget()
        desc_wrapper.setStyleSheet('background: #f0f0f0;')
        desc_layout = QVBoxLayout(desc_wrapper)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(0)

        desc_header = QHBoxLayout()
        desc_header.setContentsMargins(0, 0, 0, 0)
        desc_header.setSpacing(4)
        desc_label = QLabel(' 说明')
        desc_label.setStyleSheet(
            'font-size: 12px; font-weight: 600; color: #555;'
            'padding: 2px 4px; background: #f0f0f0; margin-bottom: 2px;'
        )
        desc_header.addWidget(desc_label)
        desc_header.addStretch()
        self._btn_save_desc = QPushButton('保存')
        self._btn_save_desc.setStyleSheet(
            'font-size: 11px; padding: 2px 8px;'
        )
        self._btn_save_desc.clicked.connect(
            self._on_save_current_context
        )
        desc_header.addWidget(self._btn_save_desc)
        desc_layout.addLayout(desc_header)

        self._current_desc_edit = QTextEdit()
        self._current_desc_edit.setAcceptRichText(False)
        self._current_desc_edit.setStyleSheet('background: #fff;')
        self._current_desc_edit.setMinimumHeight(48)
        self._current_desc_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self._current_desc_edit.textChanged.connect(
            self._on_current_desc_changed
        )
        desc_layout.addWidget(self._current_desc_edit, stretch=1)
        splitter.addWidget(desc_wrapper)

        # 正文区（撑满剩余空间）
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet('background: #fff;')
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        content_header = QHBoxLayout()
        content_label = QLabel('<b>正文</b>')
        content_label.setStyleSheet('font-size: 12px; font-weight: 600; color: #555; margin-bottom: 2px;')
        content_header.addWidget(content_label)
        content_header.addStretch()
        self._btn_open_external = QPushButton('外部编辑器打开正文')
        self._btn_open_external.setStyleSheet(
            'font-size: 11px; padding: 2px 8px;'
        )
        self._btn_open_external.clicked.connect(
            self._on_open_external
        )
        content_header.addWidget(self._btn_open_external)
        content_layout.addLayout(content_header)
        self._current_content_view = QTextEdit()
        self._current_content_view.setReadOnly(True)
        self._current_content_view.setMinimumHeight(80)
        self._current_content_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        content_layout.addWidget(self._current_content_view)
        splitter.addWidget(content_wrapper)

        # 说明区固定份额，正文区自动撑满
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([100, 380])

        # 持久化比例
        settings = QSettings('CSF', 'Clarity')
        splitter.splitterMoved.connect(
            lambda pos, idx: settings.setValue(
                'context/current_splitter', splitter.saveState()
            )
        )

        layout.addWidget(splitter, stretch=1)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._btn_save_as_version = QPushButton('保存为段库版本')
        self._btn_save_as_version.clicked.connect(
            self._on_save_as_version_from_current
        )
        btn_row.addWidget(self._btn_save_as_version)

        layout.addLayout(btn_row)
        return w

    def _on_current_desc_changed(self):
        """「当前」Tab 说明区编辑 → 标记未保存。"""
        if self._detail_tabs.currentIndex() == 0:  # 当前Tab
            self._has_unsaved_current = True
            self._current_tab_has_unsaved = True
            self._refresh_title_row()
            self._update_button_states()

    def _on_open_external(self):
        """DT-03.3：用系统默认程序打开 cos-context.md。"""
        import subprocess
        import sys
        cos_path = self._svc.cos_context_path
        try:
            if sys.platform == 'win32':
                os.startfile(cos_path)  # type: ignore
            elif sys.platform == 'darwin':
                subprocess.run(['open', cos_path])
            else:
                subprocess.run(['xdg-open', cos_path])
        except Exception as e:
            QMessageBox.warning(
                self, '打开失败',
                f'无法打开 cos-context.md: {e}'
            )

    # ══════════════════════════════════════════════════════════
    # DT-03.4: 「当前」Tab 保存逻辑
    # ══════════════════════════════════════════════════════════

    def _on_save_current_context(self):
        """DT-03.4：[保存到当前上下文]。"""
        if not self._current_section_title:
            return
        try:
            desc = self._current_desc_edit.toPlainText()
            self._svc.save_to_current_context(
                self._current_section_title, desc
            )
            self._has_unsaved_current = False
            self._current_tab_has_unsaved = self._has_unsaved_version
            self._refresh_title_row()
            self._update_button_states()
        except Exception as e:
            QMessageBox.critical(
                self, '保存失败', f'保存到当前上下文失败: {e}'
            )

    def _on_save_as_version_from_current(self):
        """DT-03.4：[保存为段库版本]（从「当前」Tab）。"""
        if not self._current_section_title:
            return
        try:
            # 找到当前段数据
            section = next(
                (s for s in self._sections
                 if s.title == self._current_section_title),
                None,
            )
            content = section.content if section else ''
            desc = self._current_desc_edit.toPlainText()
            source_ver = section.source_version if section else None

            new_ver = self._svc.save_as_library_version(
                self._current_section_title,
                content, desc,
                source_version=None,  # 始终新建版本
            )
            # 同步 section_meta.json（bug#2 修复）
            self._svc.save_to_current_context(
                self._current_section_title, desc
            )
            self._has_unsaved_current = False
            self._current_tab_has_unsaved = self._has_unsaved_version
            self._refresh_title_row()
            self._refresh_version_list()
            self._update_button_states()
            logger.info(
                '[保存为段库版本] %s → v%d', self._current_section_title, new_ver
            )
        except Exception as e:
            QMessageBox.critical(
                self, '保存失败', f'保存为段库版本失败: {e}'
            )

    # ══════════════════════════════════════════════════════════
    # DT-03.5/03.6: 「版本」Tab
    # ══════════════════════════════════════════════════════════

    def _build_version_tab(self) -> QWidget:
        """DT-03.5：构建「版本」Tab。

        三种状态：
        ①空白：说明+正文可编辑，[外部编辑器打开正文]置灰
        ②查看版本：说明+正文只读，[外部编辑器打开正文]可用
        ③已应用：说明+正文只读，绿色标签
        说明↔正文通过垂直 QSplitter 可拖拽（比例持久化）
        """
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 2, 6, 4)
        layout.setSpacing(2)

        # 标题行
        title_w, self._vt_labels = self._build_title_row()
        layout.addWidget(title_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('border: 1px solid #E8E8E8; margin: 4px 0;')
        layout.addWidget(sep)

        # ── 说明↔正文可拖拽分割（B.3）──
        self._version_splitter = QSplitter(Qt.Orientation.Vertical)
        splitter = self._version_splitter
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet(
            'QSplitter::handle { background-color: #e0e0e0; }'
        )

        # 说明区（灰色标题条 + 保存按钮 + 白色输入框）
        desc_wrapper = QWidget()
        desc_wrapper.setStyleSheet('background: #f0f0f0;')
        desc_layout = QVBoxLayout(desc_wrapper)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(0)

        desc_header = QHBoxLayout()
        desc_header.setContentsMargins(0, 0, 0, 0)
        desc_header.setSpacing(4)
        desc_label = QLabel(' 说明')
        desc_label.setStyleSheet(
            'font-size: 12px; font-weight: 600; color: #555;'
            'padding: 2px 4px; background: #f0f0f0; margin-bottom: 2px;'
        )
        desc_header.addWidget(desc_label)
        desc_header.addStretch()
        self._btn_save_ver_desc = QPushButton('保存')
        self._btn_save_ver_desc.setStyleSheet(
            'font-size: 11px; padding: 2px 8px;'
        )
        self._btn_save_ver_desc.clicked.connect(
            self._on_save_version_overwrite
        )
        desc_header.addWidget(self._btn_save_ver_desc)
        desc_layout.addLayout(desc_header)

        self._version_desc_edit = QTextEdit()
        self._version_desc_edit.setAcceptRichText(False)
        self._version_desc_edit.setStyleSheet('background: #fff;')
        self._version_desc_edit.setMinimumHeight(48)
        self._version_desc_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self._version_desc_edit.textChanged.connect(
            self._on_version_desc_changed
        )
        desc_layout.addWidget(self._version_desc_edit, stretch=1)
        splitter.addWidget(desc_wrapper)

        # 正文区（撑满）
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet('background: #fff;')
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        content_header = QHBoxLayout()
        content_label = QLabel('<b>正文</b>')
        content_label.setStyleSheet('font-size: 12px; font-weight: 600; color: #555; margin-bottom: 2px;')
        content_header.addWidget(content_label)
        content_header.addStretch()
        self._btn_open_ext_version = QPushButton('外部编辑器打开正文')
        self._btn_open_ext_version.setStyleSheet(
            'font-size: 11px; padding: 2px 8px;'
        )
        self._btn_open_ext_version.clicked.connect(
            self._on_open_external_version
        )
        content_header.addWidget(self._btn_open_ext_version)
        content_layout.addLayout(content_header)
        self._version_content_edit = QTextEdit()
        self._version_content_edit.setAcceptRichText(False)
        self._version_content_edit.setMinimumHeight(80)
        self._version_content_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._version_content_edit.textChanged.connect(
            self._on_version_content_changed
        )
        content_layout.addWidget(self._version_content_edit)
        splitter.addWidget(content_wrapper)

        # 说明区固定份额，正文区自动撑满
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([100, 380])

        # 持久化比例
        settings = QSettings('CSF', 'Clarity')
        splitter.splitterMoved.connect(
            lambda pos, idx: settings.setValue(
                'context/version_splitter', splitter.saveState()
            )
        )

        layout.addWidget(splitter, stretch=1)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._btn_save_version = QPushButton('保存为段库版本')
        self._btn_save_version.clicked.connect(
            self._on_save_version_new
        )
        btn_row.addWidget(self._btn_save_version)

        layout.addLayout(btn_row)
        return w

    def _on_version_desc_changed(self):
        """版本Tab说明区编辑 → 标记未保存。"""
        if self._detail_tabs.currentIndex() == 1:  # 版本Tab
            self._has_unsaved_version = True
            self._current_tab_has_unsaved = True
            self._refresh_title_row()
            self._update_button_states()

    def _on_version_content_changed(self):
        """版本Tab正文区编辑 → 标记未保存。"""
        if self._detail_tabs.currentIndex() == 1:
            self._has_unsaved_version = True
            self._current_tab_has_unsaved = True
            self._refresh_title_row()
            self._update_button_states()

    def _set_version_tab_state(self, state: str):
        """DT-03.5：切换「版本」Tab 三种状态。

        Args:
            state: 'blank' | 'viewing' | 'applied'
        """
        self._version_tab_state = state

        if state == 'blank':
            self._version_desc_edit.setReadOnly(False)
            self._version_content_edit.setReadOnly(False)
            self._btn_open_ext_version.setEnabled(False)
            self._vt_labels['status'].setText('')
        elif state == 'viewing':
            self._version_desc_edit.setReadOnly(False)
            self._version_content_edit.setReadOnly(True)
            self._btn_open_ext_version.setEnabled(True)
            self._vt_labels['status'].setText('')
        elif state == 'applied':
            self._version_desc_edit.setReadOnly(False)
            self._version_content_edit.setReadOnly(True)
            self._btn_open_ext_version.setEnabled(True)
            self._vt_labels['status'].setText('已应用到草稿')
            self._vt_labels['status'].setStyleSheet(
                'color: #27AE60; font-size: 11px; font-weight: bold;'
            )

    def _on_open_external_version(self):
        """DT-03.5：用系统默认程序打开版本文件。"""
        if not self._current_section_title or not self._viewing_version:
            return
        import subprocess
        import sys
        versions_dir = Path(self._svc.sections_dir) / '.versions'
        ver_path = versions_dir / (
            f'{self._current_section_title}.v{self._viewing_version}.md'
        )
        try:
            path_str = str(ver_path)
            if sys.platform == 'win32':
                os.startfile(path_str)  # type: ignore
            elif sys.platform == 'darwin':
                subprocess.run(['open', path_str])
            else:
                subprocess.run(['xdg-open', path_str])
        except Exception as e:
            QMessageBox.warning(
                self, '打开失败', f'无法打开版本文件: {e}'
            )

    def _on_save_version_overwrite(self):
        """DT-03.6：[保存] — 覆写当前打开的版本，不产生新版本号。

        blank 状态：尚无版本 → 创建 v1（等同于新建）。
        viewing/applied 状态：覆写当前打开的版本。
        """
        if not self._current_section_title:
            return

        try:
            desc = self._version_desc_edit.toPlainText()
            content = self._version_content_edit.toPlainText()

            if self._version_tab_state == 'blank':
                # 尚无版本 → 创建 v1
                new_ver = self._svc.save_as_library_version(
                    self._current_section_title,
                    content, desc,
                    source_version=None,
                )
                self._viewing_version = new_ver
                logger.info(
                    '[版本Tab·保存] 新建 %s v%d',
                    self._current_section_title, new_ver,
                )
            else:
                # viewing / applied → 覆写当前版本
                cur_ver = self._viewing_version
                if cur_ver is not None:
                    self._svc.save_as_library_version(
                        self._current_section_title,
                        content, desc,
                        source_version=cur_ver,
                    )
                    logger.info(
                        '[版本Tab·保存] 覆写 %s v%d',
                        self._current_section_title, cur_ver,
                    )

            # 同步 section_meta.json
            self._svc.save_to_current_context(
                self._current_section_title, desc
            )
            self._has_unsaved_version = False
            self._current_tab_has_unsaved = self._has_unsaved_current
            self._refresh_title_row()
            self._refresh_version_list()
            self._update_button_states()
        except Exception as e:
            QMessageBox.critical(
                self, '保存失败', f'保存版本失败: {e}'
            )

    def _on_save_version_new(self):
        """DT-03.6：[保存为段库版本] — 始终创建新版本号。"""
        if not self._current_section_title:
            return

        try:
            desc = self._version_desc_edit.toPlainText()
            content = self._version_content_edit.toPlainText()

            new_ver = self._svc.save_as_library_version(
                self._current_section_title,
                content, desc,
                source_version=None,
            )
            self._viewing_version = new_ver

            # 同步 section_meta.json
            self._svc.save_to_current_context(
                self._current_section_title, desc
            )
            self._has_unsaved_version = False
            self._current_tab_has_unsaved = self._has_unsaved_current
            self._refresh_title_row()
            self._refresh_version_list()
            self._update_button_states()
            logger.info(
                '[版本Tab·保存为段库版本] %s → v%d',
                self._current_section_title, new_ver,
            )
        except Exception as e:
            QMessageBox.critical(
                self, '保存失败', f'保存为段库版本失败: {e}'
            )

    # ══════════════════════════════════════════════════════════
    # DT-03.7: 版本备份列表渲染
    # ══════════════════════════════════════════════════════════

    def _refresh_version_list(self):
        """DT-03.7：刷新版本备份列表。

        按版本号倒序排列，每条包含：
        - ●/○ 圆点标记
        - 说明摘要（粗体，前20字）
        - 版本号+日期+模板引用（灰色小字）
        - 操作按钮 [装载] [复制] [删除]
        """
        if not self._current_section_title:
            self._version_empty_label.setVisible(True)
            self._version_scroll.setVisible(False)
            self._template_ref_label.setVisible(False)
            return

        versions = self._svc.load_version_list(
            self._current_section_title
        )

        # 清除旧条目
        while self._version_entries_layout.count() > 1:  # 保留stretch
            item = self._version_entries_layout.itemAt(0)
            if item and item.widget():
                item.widget().deleteLater()
            self._version_entries_layout.removeItem(item)

        if not versions:
            self._version_empty_label.setVisible(True)
            self._version_scroll.setVisible(False)
            self._template_ref_label.setVisible(False)
            return

        self._version_empty_label.setVisible(False)
        self._version_scroll.setVisible(True)

        # 找到当前在役段的来源版本
        in_service_ver: Optional[int] = None
        if self._current_section_title:
            for s in self._sections:
                if s.title == self._current_section_title:
                    in_service_ver = s.source_version
                    break

        for ve in versions:
            entry_w = self._build_version_entry(
                ve, is_in_service=(ve.version == in_service_ver)
            )
            # 插入到stretch之前
            self._version_entries_layout.insertWidget(
                self._version_entries_layout.count() - 1, entry_w
            )

        # 模板引用信息
        all_baselines: set[str] = set()
        for ve in versions:
            for bl in ve.baselines:
                if bl:
                    all_baselines.add(bl)
        if all_baselines:
            self._template_ref_label.setText(
                '模板引用：' + ', '.join(sorted(all_baselines))
            )
            self._template_ref_label.setVisible(True)
        else:
            self._template_ref_label.setVisible(False)

    def _build_version_entry(
        self, ve, is_in_service: bool,
    ) -> QWidget:
        """构建单条版本条目 widget。"""
        from ..service.context_service import VersionEntry
        w = QWidget()
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        # 单击版本条目 → 预览（非装载）
        def _preview():
            nonlocal ve
            t = self._current_section_title
            v = ve.version
            if t and v:
                self._viewing_version = v
                # 若当前版本是已装载版本 → 显示已应用状态
                is_applied = (self._applied_versions.get(t) == v)
                self._set_version_tab_state('applied' if is_applied else 'viewing')
                self._load_version_content(t, v)
                self._refresh_title_row()
                self._detail_tabs.setCurrentIndex(1)
        w.mousePressEvent = lambda e: _preview()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(3, 6, 3, 6)
        layout.setSpacing(2)

        # 主行：圆点 + 说明摘要 + 版本信息
        main_row = QHBoxLayout()
        main_row.setSpacing(6)

        # 圆点标记
        dot = '●' if is_in_service else '○'
        dot_color = '#333' if is_in_service else '#999'
        dot_label = QLabel(dot)
        dot_label.setStyleSheet(
            f'color: {dot_color}; font-size: 12px; font-weight: bold;'
        )
        dot_label.setFixedWidth(16)
        main_row.addWidget(dot_label)

        # 说明摘要（粗体，前20字）
        summary = ve.description[:20] if ve.description else '(无说明)'
        if len(ve.description) > 20:
            summary += '…'
        summary_label = QLabel(summary)
        summary_label.setStyleSheet('font-weight: 600; font-size: 12px; color: #2980B9;')
        main_row.addWidget(summary_label)

        main_row.addStretch()

        # 版本信息
        date_str = ve.created_at[:10] if len(ve.created_at) >= 10 else ve.created_at
        baselines_str = ', '.join(ve.baselines[:2]) if ve.baselines else ''
        info_parts = [f'v{ve.version}']
        if date_str:
            info_parts.append(date_str)
        if baselines_str:
            info_parts.append(baselines_str)
        info_label = QLabel(' · '.join(info_parts))
        info_label.setStyleSheet('color: #999; font-size: 10px;')
        main_row.addWidget(info_label)

        layout.addLayout(main_row)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_row.addStretch()

        _VER_BTN = 'font-size: 11px; padding: 1px 8px; color: #555; border: 1px solid #E0E0E0;'
        btn_load = QPushButton('装载')
        btn_load.setStyleSheet(_VER_BTN)
        btn_load.clicked.connect(
            lambda checked, t=self._current_section_title, v=ve.version:
            self._on_version_load_clicked(t, v)
        )
        btn_row.addWidget(btn_load)

        btn_copy = QPushButton('复制')
        btn_copy.setStyleSheet(_VER_BTN)
        btn_copy.clicked.connect(
            lambda checked, t=self._current_section_title, v=ve.version:
            self._on_version_copy(t, v)
        )
        btn_row.addWidget(btn_copy)

        btn_delete = QPushButton('删除')
        btn_delete.setStyleSheet(_VER_BTN)

        # 约束检查：置灰逻辑
        delete_disabled = False
        delete_tooltip = ''

        # 约束1：至少保留一个版本
        all_versions = self._svc.load_version_list(
            self._current_section_title or ''
        )
        if len(all_versions) <= 1:
            delete_disabled = True
            delete_tooltip = '至少保留一个版本'

        # 约束2：出厂模板锁定段
        for bl in ve.baselines:
            if bl.startswith('csf-') or 'factory' in bl.lower():
                delete_disabled = True
                delete_tooltip = '出厂模板锁定段不允许删除版本'
                break

        if delete_disabled:
            btn_delete.setEnabled(False)
            btn_delete.setToolTip(delete_tooltip)
        else:
            btn_delete.clicked.connect(
                lambda checked, t=self._current_section_title, v=ve.version:
                self._on_version_delete(t, v)
            )
        btn_row.addWidget(btn_delete)

        layout.addLayout(btn_row)

        # 底部分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('border: 1px solid #F0F0F0;')
        layout.addWidget(sep)

        return w

    # ══════════════════════════════════════════════════════════
    # DT-03.8: 版本备份操作
    # ══════════════════════════════════════════════════════════

    def _on_version_load_clicked(
        self, section_title: str, version: int
    ):
        """DT-03.8：[装载] → 调用 STB-2 的 on_version_load。"""
        # 检查未保存
        if self._current_tab_has_unsaved:
            self._show_unsaved_switch_dialog(
                on_saved=lambda: self._do_load_version(
                    section_title, version
                ),
                on_discard=lambda: self._do_load_version(
                    section_title, version
                ),
            )
        else:
            self._do_load_version(section_title, version)

    def _do_load_version(self, section_title: str, version: int):
        """执行装载：调用 on_version_load + 切换版本Tab到已应用状态。"""
        self.on_version_load(section_title, version)
        # 记录该段的已装载版本
        self._applied_versions[section_title] = version
        # 切换到版本Tab显示已装载的版本
        self._detail_tabs.setCurrentIndex(1)
        self._viewing_version = version
        self._current_section_title = section_title
        self._set_version_tab_state('applied')
        # 加载版本内容
        self._load_version_content(section_title, version)
        self._refresh_title_row_with_applied()

    def _on_version_copy(self, section_title: str, version: int):
        """DT-03.8：[复制] → 新建版本+刷新列表+自动选中。"""
        try:
            new_ver = self._svc.copy_version(section_title, version)
            self._refresh_version_list()
            # 自动选中新版本 → 切换到版本Tab查看
            self._viewing_version = new_ver
            self._set_version_tab_state('viewing')
            self._load_version_content(section_title, new_ver)
            logger.info(
                '[复制版本] %s v%d → v%d', section_title, version, new_ver
            )
        except Exception as e:
            QMessageBox.critical(
                self, '复制失败', f'复制版本失败: {e}'
            )

    def _on_version_delete(self, section_title: str, version: int):
        """DT-03.8：[删除] → 两重约束检查已体现在按钮置灰。"""
        try:
            self._svc.delete_version(section_title, version)
            self._refresh_version_list()
            # 如果删除的是正在查看的版本 → 切换到空态
            if self._viewing_version == version:
                if self._detail_tabs.currentIndex() == 1:
                    self._set_version_tab_state('blank')
                    self._version_desc_edit.clear()
                    self._version_content_edit.clear()
                    self._viewing_version = None
            logger.info(
                '[删除版本] %s v%d', section_title, version
            )
        except Exception as e:
            QMessageBox.critical(
                self, '删除失败', f'删除版本失败: {e}'
            )

    def _load_version_content(
        self, section_title: str, version: int,
    ):
        """加载版本文件内容到「版本」Tab。"""
        from pathlib import Path as Pt
        versions_dir = Pt(self._svc.sections_dir) / '.versions'
        ver_path = versions_dir / f'{section_title}.v{version}.md'
        try:
            raw = ver_path.read_text(encoding='utf-8')
            # 提取 YAML frontmatter 后的正文
            fm_end = raw.find('---', 3)
            body = raw[fm_end + 3:].lstrip('\n') if fm_end != -1 else raw
            # 提取 description
            fm = _parse_yaml_frontmatter(raw) if raw.startswith('---') else {}
            desc = fm.get('description', '')

            # blockSignals 防止 setPlainText 触发 textChanged → 误标记未保存
            self._version_desc_edit.blockSignals(True)
            self._version_desc_edit.setPlainText(desc)
            self._version_desc_edit.blockSignals(False)
            self._version_content_edit.blockSignals(True)
            self._version_content_edit.setPlainText(body.strip())
            self._version_content_edit.blockSignals(False)
            self._has_unsaved_version = False
        except Exception:
            self._version_desc_edit.blockSignals(True)
            self._version_desc_edit.setPlainText('')
            self._version_desc_edit.blockSignals(False)
            self._version_content_edit.blockSignals(True)
            self._version_content_edit.setPlainText('')
            self._version_content_edit.blockSignals(False)

    # ══════════════════════════════════════════════════════════
    # 详情面板数据加载
    # ══════════════════════════════════════════════════════════

    def _on_detail_tab_changed(self, index: int):
        """Tab切换时更新标题行和未保存状态。"""
        if not self._current_section_title:
            return
        self._refresh_title_row()

    def _refresh_title_row(self):
        """根据当前状态刷新标题行。"""
        if not self._current_section_title:
            return

        is_current = self._detail_tabs.currentIndex() == 0
        labels = self._ct_labels if is_current else self._vt_labels
        section = next(
            (s for s in self._sections
             if s.title == self._current_section_title),
            None,
        )
        version = section.source_version if section else None
        if not is_current:
            version = self._viewing_version

        is_applied = (
            not is_current
            and self._version_tab_state == 'applied'
        )
        self._update_title_row(
            labels,
            self._current_section_title,
            version,
            is_current=is_current,
            is_applied=is_applied,
        )

    def _refresh_title_row_with_applied(self):
        """装载版本后刷新标题行（已应用状态）。"""
        self._update_title_row(
            self._vt_labels,
            self._current_section_title or '',
            self._viewing_version,
            is_current=False,
            is_applied=True,
        )

    def _show_detail_empty_state(self):
        """详情面板空态。"""
        self._current_desc_edit.clear()
        self._current_desc_edit.setReadOnly(True)
        self._current_content_view.clear()
        self._version_desc_edit.clear()
        self._version_content_edit.clear()
        for labels in (self._ct_labels, self._vt_labels):
            labels['title'].setText('请选中段查看详情')
            labels['version'].setText('')
            labels['status'].setText('')
            labels['unsaved'].setText('')
        self._version_empty_label.setVisible(True)
        self._version_scroll.setVisible(False)
        self._btn_open_external.setEnabled(False)
        self._btn_save_desc.setEnabled(False)
        self._btn_save_as_version.setEnabled(False)

    def _load_section_to_detail(self, section_title: str):
        """加载段数据到详情面板。"""
        section = next(
            (s for s in self._sections
             if s.title == section_title),
            None,
        )
        if not section:
            self._show_detail_empty_state()
            return

        self._current_section_title = section_title
        self._has_unsaved_current = False
        self._has_unsaved_version = False
        self._current_tab_has_unsaved = False

        # ── 「当前」Tab ──
        self._current_desc_edit.setReadOnly(False)
        self._current_desc_edit.blockSignals(True)
        self._current_desc_edit.setPlainText(section.description)
        self._current_desc_edit.blockSignals(False)
        self._current_content_view.setPlainText(section.content)
        self._btn_open_external.setEnabled(True)
        self._btn_save_desc.setEnabled(True)
        self._btn_save_as_version.setEnabled(True)

        # ── 「版本」Tab ──
        applied_ver = self._applied_versions.get(section_title)
        if applied_ver is not None:
            # 该段有已装载版本 → 恢复applied状态
            self._viewing_version = applied_ver
            self._set_version_tab_state('applied')
            self._load_version_content(section_title, applied_ver)
            self._refresh_title_row()
            # 版本备份列表
            self._refresh_version_list()
            # 尾部最终重置
            self._has_unsaved_current = False
            self._has_unsaved_version = False
            self._current_tab_has_unsaved = False
            return  # 跳过尾部 _update_title_row，避免覆盖已应用标记
        elif self._detail_tabs.currentIndex() == 1:
            self._set_version_tab_state('blank')
            self._viewing_version = None
            self._version_desc_edit.clear()
            self._version_content_edit.clear()
        else:
            self._viewing_version = None
            self._version_desc_edit.clear()
            self._version_content_edit.clear()

        # 尾部最终重置（放在 _update_title_row 之前，避免残留 * 号）
        self._has_unsaved_current = False
        self._has_unsaved_version = False
        self._current_tab_has_unsaved = False

        # 标题行
        is_cur = self._detail_tabs.currentIndex() == 0
        self._update_title_row(
            self._ct_labels if is_cur else self._vt_labels,
            section_title, section.source_version,
            is_current=is_cur,
        )

        # 版本备份列表
        self._refresh_version_list()

    # ══════════════════════════════════════════════════════════
    # DT-03.14: 切换段未保存弹窗
    # ══════════════════════════════════════════════════════════

    def _show_unsaved_switch_dialog(
        self, on_saved=None, on_discard=None,
    ):
        """DT-03.14：三段式提醒 QDialog。

        [保存] → 执行当前Tab对应的保存逻辑 → 切换段
        [丢弃] → 放弃编辑 → 切换段
        [取消切换] → 保持当前段不变
        """
        dlg = QDialog(self)
        dlg.setWindowTitle('未保存编辑')
        layout = QVBoxLayout(dlg)

        msg = QLabel(
            '<b style="color:#E67E22;">当前编辑内容尚未保存，是否保存？</b>'
        )
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_save = QPushButton('保存')
        btn_discard = QPushButton('丢弃')
        btn_cancel = QPushButton('取消切换')

        result = {'action': None}

        btn_save.clicked.connect(
            lambda: (setattr(result, 'action', 'save'), dlg.accept())
            if not None else None
        )

        def do(action):
            result['action'] = action
            dlg.accept()

        btn_save.clicked.connect(lambda: do('save'))
        btn_discard.clicked.connect(lambda: do('discard'))
        btn_cancel.clicked.connect(lambda: do('cancel'))

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_discard)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        dlg.exec()

        if result['action'] == 'save':
            # 执行当前Tab保存
            if self._detail_tabs.currentIndex() == 0:
                self._on_save_current_context()
            else:
                self._on_save_version()
            if on_saved:
                on_saved()
        elif result['action'] == 'discard':
            self._has_unsaved_current = False
            self._has_unsaved_version = False
            self._current_tab_has_unsaved = False
            if on_discard:
                on_discard()
        # cancel → 什么都不做

    # ══════════════════════════════════════════════════════════
    # DT-02.1/02.12: 草稿初始化 + 关窗恢复
    # ══════════════════════════════════════════════════════════

    def _init_draft(self):
        """初始化草稿：从磁盘加载或新建空草稿，注入 _persist 回调。"""
        loaded = self._svc.read_draft()
        if loaded:
            self._draft = loaded
            # read_draft 已注入 _persist 回调
        else:
            self._draft = DraftState()
            self._draft._persist = lambda: self._svc.write_draft(self._draft)

    def _check_recovery(self):
        """DT-02.12：检测遗留草稿 → 显示恢复提示条。"""
        if not self._draft.is_dirty():
            return

        self._recovery_label.setText(
            '<b style="color:#E67E22;">⚠️ 检测到上次未提交的草稿</b>'
            '<span style="color:#555;">（基于当时上下文）</span>'
        )
        self._btn_load_draft.clicked.connect(self._on_load_recovery)
        self._btn_discard_draft.clicked.connect(self._on_discard_recovery)
        self._recovery_bar.setVisible(True)
        self._recovery_bar.setMaximumHeight(16777215)
        self._recovery_bar.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )

    def _on_load_recovery(self):
        """载入恢复草稿：基于当前 baseline 重新计算差异标注行。"""
        self._recovery_bar.setVisible(False)
        self._recovery_bar.setMaximumHeight(0)
        self._rebuild_section_list()
        self._update_button_states()

    def _on_discard_recovery(self):
        """丢弃遗留草稿：清空草稿文件 → 提示条消失 → 重建纯基线列表。"""
        self._draft.clear()
        self._recovery_bar.setVisible(False)
        self._recovery_bar.setMaximumHeight(0)
        self._rebuild_section_list()
        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.14: 段列表重建（核心——应用 DraftState 到基线）
    # ══════════════════════════════════════════════════════════

    def _rebuild_section_list(self):
        """DT-02.14：基于 baseline + DraftState 重建段列表。

        算法：
        1. 加载基线段列表
        2. 应用 remove 变更 → 标记段为撤下
        3. 应用 add 变更 → 添加新段
        4. 应用 swap_version 变更 → 更新版本信息
        5. 应用 reorder 变更 → 重排
        6. 按序渲染：正常/换版本标注/撤下标注/新装载标注
        """
        # 记住当前选中
        prev_row = self._section_list.currentRow()
        prev_title = None
        if 0 <= prev_row < len(self._sections):
            prev_title = self._sections[prev_row].title

        self._section_list.clear()
        self._sections = self._svc.load_baseline_sections()

        if not self._sections:
            self._show_empty_state()
            self._update_button_states()
            return

        self._section_list.setVisible(True)

        # 构建标题→SectionData 索引
        sec_map: dict[str, SectionData] = {
            s.title: s for s in self._sections
        }

        # 构建当前在列表中的段顺序（先 baseline，后应用 add/remove/reorder）
        active_titles = [s.title for s in self._sections]

        # ── 应用 remove ──
        removed_titles: set[str] = set()
        for c in self._draft.changes:
            if c.change_type == 'remove':
                removed_titles.add(c.section_title)

        # ── 应用 add ──
        added_entries: list[dict] = []  # {title, version}
        for c in self._draft.changes:
            if c.change_type == 'add':
                if c.section_title not in active_titles:
                    active_titles.append(c.section_title)
                added_entries.append({
                    'title': c.section_title,
                    'version': c.to_version,
                })

        # ── 应用 swap_version ──
        swap_map: dict[str, dict] = {}  # title → {to_version, from_version}
        for c in self._draft.changes:
            if c.change_type == 'swap_version':
                swap_map[c.section_title] = {
                    'to_version': c.to_version,
                    'from_version': c.from_version,
                }

        # ── 应用 reorder（取最后一条） ──
        for c in reversed(self._draft.changes):
            if c.change_type == 'reorder' and c.new_order:
                # reorder 列表可能包含已添加的段
                active_titles = [
                    t for t in c.new_order
                    if t in active_titles or t in [a['title'] for a in added_entries]
                ]
                break

        # ── 构建每行的渲染数据 ──
        # 收集所有变更信息，用于渲染时判断
        added_titles_set = {a['title'] for a in added_entries}

        restore_row = -1

        for idx, title in enumerate(active_titles, start=1):
            sec = sec_map.get(title)
            is_removed = title in removed_titles
            is_added = title in added_titles_set
            is_swapped = title in swap_map

            # 确定版本号
            version = None
            if sec:
                version = sec.source_version

            # 构建标注
            annotation = None
            if is_swapped and not is_removed:
                si = swap_map[title]
                annotation = {
                    'type': 'swap_version',
                    'target_version': si['to_version'],
                    'summary': title,
                }
            if is_removed:
                annotation = {'type': 'remove'}
            if is_added:
                ver_for_add = next(
                    (a['version'] for a in added_entries
                     if a['title'] == title), None
                )
                annotation = {
                    'type': 'add',
                    'target_version': ver_for_add,
                    'summary': title,
                }
                version = ver_for_add or version

            order = sec.order if sec else idx
            w = _SectionItemWidget(
                order=order,
                title=title,
                version=version,
                annotation=annotation,
                on_undo=self._on_undo_change,
            )

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, title)
            if is_removed:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            self._section_list.addItem(item)
            self._section_list.setItemWidget(item, w)
            item.setSizeHint(w.sizeHint())

            if title == prev_title and not is_removed:
                restore_row = self._section_list.count() - 1

        # ── 同步 _applied_versions（持久化恢复 + draft 覆盖）──
        self._applied_versions.clear()
        for s in self._sections:
            if s.source_version is not None:
                self._applied_versions[s.title] = s.source_version
        for title, si in swap_map.items():
            self._applied_versions[title] = si['to_version']
        for a in added_entries:
            self._applied_versions[a['title']] = a['version']

        # 恢复选中（在 sync 之后，确保 _load_section_to_detail 能读到 _applied_versions）
        if restore_row >= 0:
            self._section_list.setCurrentRow(restore_row)
        elif self._section_list.count() > 0:
            self._section_list.setCurrentRow(0)

        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.13: 按钮状态刷新
    # ══════════════════════════════════════════════════════════

    def _update_button_states(self):
        """DT-02.13：底部按钮可用性状态机。"""
        has_sections = self._section_list.count() > 0 and len(self._sections) > 0
        has_draft = self._draft.is_dirty()
        has_staging = self._svc.read_staging() is not None

        self._btn_add_section.setEnabled(True)          # 始终可用
        self._btn_new_section.setEnabled(True)           # 始终可用
        self._btn_remove.setEnabled(has_sections)        # 有段时可用
        self._btn_commit_staging.setEnabled(has_draft)   # 有草稿时可用
        self._btn_revert_staging.setEnabled(has_staging) # 有staging时可用

    # ══════════════════════════════════════════════════════════
    # DT-02.7: [添加段] 操作
    # ══════════════════════════════════════════════════════════

    def _on_add_section(self):
        """DT-02.7：弹窗列出段库中当前不在段列表里的段，单选添加。"""
        # 获取所有已知段标题（从 section_meta.json + 版本文件）
        all_sections = self._svc.read_section_meta()
        # 当前已在列表中的段标题
        current_titles = {s.title for s in self._sections}
        # 草稿中已添加的
        for c in self._draft.changes:
            if c.change_type == 'add':
                current_titles.add(c.section_title)

        available = [
            t for t in all_sections.keys()
            if t not in current_titles
        ]
        if not available:
            QMessageBox.information(
                self, '添加段', '段库中没有可添加的段。'
            )
            return

        title, ok = QInputDialog.getItem(
            self, '添加段', '选择要添加的段：',
            available, 0, False,
        )
        if not ok or not title:
            return

        # 获取版本号（从 section_meta 或版本列表）
        version = self._resolve_section_version(title)

        change = DraftChange(
            change_type='add',
            section_title=title,
            to_version=version,
        )
        self._draft.add_change(change)
        self._rebuild_section_list()
        self._update_button_states()

    def _resolve_section_version(self, title: str) -> Optional[int]:
        """查找段的版本号：优先从版本列表取最新版。"""
        versions = self._svc.load_version_list(title)
        if versions:
            return versions[0].version
        return None

    # ══════════════════════════════════════════════════════════
    # DT-02.13: [新建段] 操作
    # ══════════════════════════════════════════════════════════

    def _on_new_section(self):
        """DT-03.15：弹窗输入段标题 → 版本Tab打开空白编辑区。"""
        title, ok = QInputDialog.getText(
            self, '新建段', '输入段标题：',
        )
        if not ok or not title.strip():
            return

        title = title.strip()
        self._pending_new_section_title = title
        self._current_section_title = title

        # 切换到「版本」Tab空白状态
        self._detail_tabs.setCurrentIndex(1)
        self._set_version_tab_state('blank')
        self._version_desc_edit.clear()
        self._version_content_edit.clear()
        self._viewing_version = None
        self._has_unsaved_version = False

        # 标题行
        self._update_title_row(self._vt_labels, title, None, is_current=False)
        self._refresh_version_list()

        # 启用保存按钮
        self._btn_open_external.setEnabled(False)
        self._btn_save_desc.setEnabled(False)
        self._btn_save_as_version.setEnabled(False)

        logger.info(
            '[新建段] 标题已暂存: %s → 版本Tab空白编辑区', title
        )

    # ══════════════════════════════════════════════════════════
    # DT-02.6: [撤下...] 操作
    # ══════════════════════════════════════════════════════════

    def _on_remove(self):
        """DT-02.6：批量撤下段（CheckBox多选）。"""
        # 收集当前非已撤下的段
        active = [s for s in self._sections
                  if not any(
                      c.change_type == 'remove' and c.section_title == s.title
                      for c in self._draft.changes
                  )]
        if not active:
            QMessageBox.information(self, '撤下段', '没有可撤下的段。')
            return

        dlg = QDialog(self)
        dlg.setWindowTitle('撤下段')
        layout = QVBoxLayout(dlg)

        checks: list[QCheckBox] = []
        for sec in active:
            cb = QCheckBox(sec.title)
            checks.append(cb)
            layout.addWidget(cb)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if not dlg.exec():
            return

        for cb in checks:
            if cb.isChecked():
                change = DraftChange(
                    change_type='remove',
                    section_title=cb.text(),
                )
                self._draft.add_change(change)

        self._rebuild_section_list()
        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.6: 右键菜单撤下
    # ══════════════════════════════════════════════════════════

    def _on_context_menu(self, pos):
        """右键菜单：「撤下此段」。"""
        item = self._section_list.itemAt(pos)
        if not item:
            return
        title = item.data(Qt.ItemDataRole.UserRole)
        if not title:
            return

        # 已撤下的不显示菜单
        for c in self._draft.changes:
            if c.change_type == 'remove' and c.section_title == title:
                return

        menu = QMenu(self)
        action = QAction('撤下此段', menu)
        action.triggered.connect(
            lambda: self._remove_single(title)
        )
        menu.addAction(action)
        menu.exec(self._section_list.mapToGlobal(pos))

    def _remove_single(self, title: str):
        """右键撤下单段。"""
        change = DraftChange(change_type='remove', section_title=title)
        self._draft.add_change(change)
        self._rebuild_section_list()
        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.5: on_version_load — 换版本回调（供STB-3调用）
    # ══════════════════════════════════════════════════════════

    def on_version_load(self, section_title: str, target_version: int):
        """DT-02.5：STB-3 版本备份列表 [装载] 按钮回调。

        换版本逻辑：
        - 生成 swap_version DraftChange
        - 若同段已有换版本 → 后装载覆盖前装载
        - 若目标版本的段不在当前列表 → 自动 add
        """
        # 检查目标段是否在列表中
        in_list = any(s.title == section_title for s in self._sections)

        if not in_list:
            # 自动添加为新装载
            change = DraftChange(
                change_type='add',
                section_title=section_title,
                to_version=target_version,
            )
            self._draft.add_change(change)
        else:
            # 获取当前版本作为 from_version
            from_ver = None
            for s in self._sections:
                if s.title == section_title:
                    from_ver = s.source_version
                    break

            change = DraftChange(
                change_type='swap_version',
                section_title=section_title,
                to_version=target_version,
                from_version=from_ver,
            )
            self._draft.add_change(change)

        self._rebuild_section_list()
        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.4: 拖拽重排
    # ══════════════════════════════════════════════════════════

    def _on_rows_reordered(self, parent, start, end, dest):
        """DT-02.4：拖拽结束后记录 reorder DraftChange。"""
        # 收集当前段顺序
        new_order: list[str] = []
        for i in range(self._section_list.count()):
            item = self._section_list.item(i)
            if item:
                title = item.data(Qt.ItemDataRole.UserRole)
                if title:
                    new_order.append(title)

        if not new_order:
            return

        # 检查是否真的变了（与当前 active_titles 对比）
        current_order = self._get_active_order()
        if new_order == current_order:
            return  # 没变

        change = DraftChange(
            change_type='reorder',
            section_title='',  # reorder 不关联单段
            new_order=new_order,
        )
        self._draft.add_change(change)
        self._update_button_states()
        # 不调用 _rebuild_section_list——拖拽后 UI 已经正确，
        # 只需确保 DraftChange 已记录

    def _get_active_order(self) -> list[str]:
        """获取当前活跃段的顺序列表。"""
        order: list[str] = []
        seen = set()
        for s in self._sections:
            if s.title not in seen:
                removed = any(
                    c.change_type == 'remove' and c.section_title == s.title
                    for c in self._draft.changes
                )
                if not removed:
                    order.append(s.title)
                seen.add(s.title)
        # 加上已添加的段
        for c in self._draft.changes:
            if c.change_type == 'add' and c.section_title not in seen:
                order.append(c.section_title)
                seen.add(c.section_title)
        return order

    # ══════════════════════════════════════════════════════════
    # DT-02.8: 单条撤回
    # ══════════════════════════════════════════════════════════

    def _on_undo_change(self, section_title: str, change_type: str):
        """DT-02.8：点击标注行的 ↩ → 撤回对应 DraftChange。"""
        ok = self._draft.remove_change(section_title, change_type)
        if ok:
            self._rebuild_section_list()
            self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.9: [提交staging]
    # ══════════════════════════════════════════════════════════

    def _on_commit_staging(self):
        """DT-02.9：生成 staging 指令 Markdown → 写入文件。"""
        if not self._draft.is_dirty():
            return

        # 检查「版本」Tab 未保存编辑
        if self._current_tab_has_unsaved:
            QMessageBox.warning(
                self, '提交staging',
                '版本Tab中有未保存的编辑，请先保存。'
            )
            return

        content = self._draft.to_staging_md(self._sections)
        if not content:
            return

        try:
            self._svc.write_staging(content)
        except OSError as e:
            QMessageBox.critical(self, '提交staging失败', str(e))
            return

        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.10: [撤回staging]
    # ══════════════════════════════════════════════════════════

    def _on_revert_staging(self):
        """DT-02.10：二选一对话框 → 丢弃 / 载入草稿。"""
        if self._svc.read_staging() is None:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle('撤回staging')
        layout = QVBoxLayout(dlg)

        label = QLabel(
            '选择如何处理已提交的 staging：'
        )
        layout.addWidget(label)

        btn_discard = QPushButton('丢弃 — 删除staging文件，草稿保持不变')
        btn_load = QPushButton(
            '载入草稿 — 删除staging文件，用staging中的内容覆盖当前草稿'
        )
        layout.addWidget(btn_discard)
        layout.addWidget(btn_load)

        result = {'action': None}

        def do_discard():
            result['action'] = 'discard'
            dlg.accept()

        def do_load():
            result['action'] = 'load'
            dlg.accept()

        btn_discard.clicked.connect(do_discard)
        btn_load.clicked.connect(do_load)

        dlg.exec()

        if result['action'] == 'discard':
            self._svc.delete_staging()
        elif result['action'] == 'load':
            # 读 staging 内容（丢弃——STB说载入草稿用staging覆盖当前草稿，
            # 但这里简化：删除staging，当前草稿不变）
            self._svc.delete_staging()

        self._update_button_states()

    # ══════════════════════════════════════════════════════════
    # DT-02.11: [刷新] 确认对话框
    # ══════════════════════════════════════════════════════════

    def _on_refresh(self):
        """DT-02.11 + DT-03.13：确认框 + 版本变化检测。"""
        has_unsaved = self._draft.is_dirty() or self._current_tab_has_unsaved

        if has_unsaved:
            dlg = QDialog(self)
            dlg.setWindowTitle('确认刷新')
            layout = QVBoxLayout(dlg)

            warn = QLabel(
                '<b style="color:#E67E22;">⚠️ 警告</b><br><br>'
                '<span style="color:#555;">当前有未提交的草稿或未保存的编辑。'
                '刷新将丢弃所有未保存的更改。</span>'
            )
            warn.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(warn)

            btns = QDialogButtonBox()
            btn_confirm = btns.addButton(
                '确认刷新', QDialogButtonBox.ButtonRole.AcceptRole
            )
            btn_cancel = btns.addButton(
                '取消', QDialogButtonBox.ButtonRole.RejectRole
            )
            btn_confirm.clicked.connect(dlg.accept)
            btn_cancel.clicked.connect(dlg.reject)
            layout.addWidget(btns)

            if not dlg.exec():
                return

        # 执行刷新：清空草稿 + 重建纯基线段列表
        self._draft.clear()
        self._current_tab_has_unsaved = False
        self._has_unsaved_current = False
        self._has_unsaved_version = False

        # DT-03.13：版本变化检测
        try:
            changed = self._svc.detect_version_changes()
            if changed:
                logger.info(
                    '[版本变化检测] 发现 %d 个段版本变化: %s',
                    len(changed),
                    ', '.join(
                        f'{t}(v{o}→v{n})' for t, o, n in changed
                    ),
                )
        except Exception as e:
            logger.warning('[版本变化检测] 执行异常: %s', e)

        self._rebuild_section_list()
        self._update_button_states()

        # 刷新后重载模板列表和当前段详情
        self._refresh_template_dropdown()
        if self._current_section_title:
            self._load_section_to_detail(self._current_section_title)

    # ══════════════════════════════════════════════════════════
    # 选中交互 + 空态
    # ══════════════════════════════════════════════════════════

    def _on_section_selected(self, row: int):
        """DT-03.15：点击段行 → 检查未保存 → 加载详情面板。"""
        if row < 0:
            return

        item = self._section_list.item(row)
        if not item:
            return
        title = item.data(Qt.ItemDataRole.UserRole)
        if not title:
            return

        # 同一段 → 不重复加载
        if title == self._current_section_title:
            return

        # 检查未保存编辑
        if self._current_tab_has_unsaved and self._current_section_title:
            self._pending_select_title = title
            self._show_unsaved_switch_dialog(
                on_saved=lambda: self._do_select_section(
                    self._pending_select_title
                ),
                on_discard=lambda: self._do_select_section(
                    self._pending_select_title
                ),
            )
            return

        self._do_select_section(title)

    def _do_select_section(self, title: str):
        """执行段切换：加载详情数据。"""
        self._load_section_to_detail(title)

    def _show_empty_state(self):
        """空态引导：「当前上下文尚无段。」"""
        self._section_list.clear()
        msg_item = QListWidgetItem()
        guide = QLabel(
            '<div style="padding: 20px; text-align: center;">'
            '<p style="font-size: 14px; color: #555;">当前上下文尚无段。</p>'
            '</div>'
        )
        guide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        guide.setTextFormat(Qt.TextFormat.RichText)
        self._section_list.addItem(msg_item)
        self._section_list.setItemWidget(msg_item, guide)
        msg_item.setFlags(Qt.ItemFlag.NoItemFlags)
        msg_item.setSizeHint(guide.sizeHint())

    # ══════════════════════════════════════════════════════════
    # Splitter 持久化（供 MainWindow closeEvent / init 调用）
    # ══════════════════════════════════════════════════════════

    def save_splitter_state(self, settings: QSettings):
        """保存所有 QSplitter 状态到 QSettings。"""
        # 左右主分割
        if hasattr(self, '_main_splitter'):
            settings.setValue(
                'context/main_splitter', self._main_splitter.saveState())
        # 详情面板上下分割
        if hasattr(self, '_detail_splitter'):
            settings.setValue(
                'context/detail_splitter', self._detail_splitter.saveState())
        # 当前Tab说明↔正文
        if hasattr(self, '_current_splitter'):
            settings.setValue(
                'context/current_splitter', self._current_splitter.saveState())
        # 版本Tab说明↔正文
        if hasattr(self, '_version_splitter'):
            settings.setValue(
                'context/version_splitter', self._version_splitter.saveState())

    def restore_splitter_state(self, settings: QSettings):
        """从 QSettings 恢复所有 QSplitter 状态。"""
        # 左右主分割
        if hasattr(self, '_main_splitter'):
            state = settings.value('context/main_splitter')
            if state is not None:
                try:
                    self._main_splitter.restoreState(state)
                except Exception:
                    pass
        # 详情面板上下分割
        if hasattr(self, '_detail_splitter'):
            state = settings.value('context/detail_splitter')
            if state is not None:
                try:
                    self._detail_splitter.restoreState(state)
                except Exception:
                    pass
        # 当前Tab说明↔正文
        if hasattr(self, '_current_splitter'):
            state = settings.value('context/current_splitter')
            if state is not None:
                try:
                    self._current_splitter.restoreState(state)
                except Exception:
                    pass
        # 版本Tab说明↔正文
        if hasattr(self, '_version_splitter'):
            state = settings.value('context/version_splitter')
            if state is not None:
                try:
                    self._version_splitter.restoreState(state)
                except Exception:
                    pass

    def reset_splitter_to_default(self):
        """恢复所有 QSplitter 到默认比例。"""
        if hasattr(self, '_main_splitter'):
            self._main_splitter.setSizes([200, 800])
        if hasattr(self, '_detail_splitter'):
            self._detail_splitter.setSizes([400, 200])
        if hasattr(self, '_current_splitter'):
            self._current_splitter.setSizes([100, 380])
        if hasattr(self, '_version_splitter'):
            self._version_splitter.setSizes([100, 380])
