# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
MainWindow V2 — Clarity 主窗口（QMainWindow + 置顶 + 托盘 + 三标签）。

DT-02: 窗口骨架 — 悬浮置顶 + QTabWidget + 位置恢复
DT-03: 窗口位置持久化 — QSettings 存储/恢复
DT-04: 系统托盘 — 关闭到托盘 + 右键菜单 + 双击恢复
DT-05: 标签切换数据同步 — currentChanged → refresh()
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QSystemTrayIcon, QMenu,
    QApplication, QStyle, QHBoxLayout, QPushButton,
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QEvent
from PyQt6.QtGui import QAction, QIcon
from pathlib import Path


class MainWindow(QMainWindow):
    """Clarity 主窗口 — 悬浮置顶 + 三标签 + 系统托盘。"""

    # ── DT-02: 窗口骨架 ────────────────────────────────────

    def __init__(self, tabs: list[tuple[str, QWidget]],
                 settings_scope: str = "Clarity",
                 version: str = "",
                 parent=None):
        """DT-02: 创建主窗口。

        Args:
            tabs: [(标签名, QWidget实例), ...]
            settings_scope: QSettings scope（测试用"ClarityTest"，正式用"Clarity"）
            version: 版本号字符串（如 "1.1.1"），显示在标题栏
        """
        super().__init__(parent)
        self._tabs = tabs
        self._settings = QSettings("CSF", settings_scope)
        self._really_quit = False

        # 窗口基本属性
        title = f"Clarity v{version} — CSF Lite" if version else "Clarity — CSF Lite"
        self.setWindowTitle(title)

        # DT-01: 恢复置顶状态（默认置顶）
        always_on_top = self._settings.value("alwaysOnTop", True, type=bool)
        if always_on_top:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

        # 默认大小
        self.resize(950, 680)
        self.setMinimumSize(600, 400)

        # 标签容器
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setStyleSheet(
            'QTabWidget::pane { padding: 0px; border: none; }'
            'QTabBar::tab {'
            '  padding: 4px 16px; font-size: 13px;'
            '  border: 1px solid #D0D0D0;'
            '  border-bottom: none;'
            '  background: #F0F0F0; color: #777;'
            '}'
            'QTabBar::tab:selected {'
            '  background: #2980B9; color: #FFF; font-weight: 600;'
            '  border-color: #2980B9;'
            '}'
            'QTabBar::tab:last {'
            '  background: #FEF9E7; color: #7D6608; font-weight: 600;'
            '  border-color: #F9E076;'
            '}'
            'QTabBar::tab:last:selected {'
            '  background: #2980B9; color: #FFF; font-weight: 600;'
            '  border-color: #2980B9;'
            '}'
        )
        for name, widget in tabs:
            self._tab_widget.addTab(widget, name)
        self.setCentralWidget(self._tab_widget)

        # DT-01/02: 标签栏右侧按钮区（钉住 + 恢复默认布局）
        self._setup_corner_buttons()

        # 标签切换信号
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # 恢复窗口位置
        self._restore_geometry()

        # 设置窗口图标
        self._set_app_icon()

        # 系统托盘
        self._setup_tray()

        # DT-06: 恢复 Splitter 状态
        self._restore_splitter_states()

    # ── 图标加载 ──────────────────────────────────────────

    @staticmethod
    def _load_icon() -> QIcon:
        """加载 Clarity 应用图标，找不到则返回默认图标。"""
        # 多个搜索路径：资源目录 / exe旁边 / 开发目录
        search_paths = [
            Path(__file__).resolve().parent.parent.parent / 'resources' / 'clarity.png',
            Path.cwd() / 'resources' / 'clarity.png',
        ]
        # PyInstaller 打包后资源在 sys._MEIPASS
        import sys
        if getattr(sys, 'frozen', False):
            meipass = Path(sys._MEIPASS)
            search_paths.insert(0, meipass / 'resources' / 'clarity.png')

        for p in search_paths:
            if p.exists():
                return QIcon(str(p))
        # 回退：内置默认图标
        return QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon)

    def _set_app_icon(self):
        """设置窗口图标。"""
        icon = self._load_icon()
        self.setWindowIcon(icon)
        QApplication.instance().setWindowIcon(icon)

    # ── DT-03: 窗口位置持久化 ──────────────────────────────

    def _restore_geometry(self):
        """DT-03: 从 QSettings 恢复窗口位置。"""
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            # 首次运行：居中显示
            screen = self.screen()
            if screen:
                center = screen.availableGeometry().center()
                frame = self.frameGeometry()
                frame.moveCenter(center)
                self.move(frame.topLeft())

    def changeEvent(self, event):
        """最小化时隐藏到托盘，而非任务栏。"""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                self.hide()
                return
        super().changeEvent(event)

    def closeEvent(self, event):
        """关闭窗口 → 保存状态并真正退出。"""
        self._save_splitter_states()
        self._settings.setValue("geometry", self.saveGeometry())
        if hasattr(self, '_tray_icon') and self._tray_icon:
            self._tray_icon.hide()
        event.accept()

    # ── DT-04: 系统托盘 ────────────────────────────────────

    def _setup_tray(self):
        """DT-04: 创建系统托盘图标和菜单。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return

        icon = self._load_icon()
        self._tray_icon = QSystemTrayIcon(icon, self)
        self._tray_icon.setToolTip("Clarity — CSF Lite")

        # 右键菜单
        menu = QMenu()
        show_action = QAction("显示 Clarity", self)
        show_action.triggered.connect(self._show_from_tray)
        menu.addAction(show_action)

        # DT-03: 置顶项（checkable，与钉住按钮双向同步）
        always_on_top = self._settings.value("alwaysOnTop", True, type=bool)
        self._tray_pin_action = QAction("置顶", self)
        self._tray_pin_action.setCheckable(True)
        self._tray_pin_action.setChecked(always_on_top)
        self._tray_pin_action.triggered.connect(self._on_toggle_pin)
        menu.addAction(self._tray_pin_action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_from_tray)
        menu.addAction(quit_action)

        self._tray_icon.setContextMenu(menu)

        # 双击托盘 → 显示窗口
        self._tray_icon.activated.connect(self._on_tray_activated)

        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        """托盘双击 → 显示窗口。"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self):
        """从托盘恢复窗口。"""
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self):
        """托盘退出 → 真正关闭。"""
        self._really_quit = True
        self.close()

    def showEvent(self, event):
        """窗口显示时确保托盘可见。"""
        super().showEvent(event)
        if hasattr(self, '_tray_icon') and self._tray_icon:
            self._tray_icon.show()

    # ── DT-05: 标签切换数据同步 ────────────────────────────

    def _on_tab_changed(self, index: int):
        """DT-05: 标签切换 → 调用当前标签的 refresh()。"""
        if 0 <= index < len(self._tabs):
            widget = self._tabs[index][1]
            if hasattr(widget, 'refresh') and callable(widget.refresh):
                try:
                    widget.refresh()
                except Exception:
                    pass  # 静默失败，不影响标签切换

    # ── DT-01: 钉住按钮 ────────────────────────────────────

    def _setup_corner_buttons(self):
        """DT-01/02: 标签栏右侧按钮区（钉住 + 恢复默认布局）。"""
        corner = QWidget()
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(4)

        # DT-01: 钉住按钮
        always_on_top = self._settings.value("alwaysOnTop", True, type=bool)
        self._pin_btn = QPushButton("📌 置顶" if always_on_top else "📍 置顶")
        self._pin_btn.setCheckable(True)
        self._pin_btn.setChecked(always_on_top)
        self._pin_btn.clicked.connect(self._on_toggle_pin)
        layout.addWidget(self._pin_btn)

        # DT-02: 恢复默认布局按钮
        self._reset_layout_btn = QPushButton("🔄 默认布局")
        self._reset_layout_btn.clicked.connect(self._on_reset_layout)
        layout.addWidget(self._reset_layout_btn)

        self._tab_widget.setCornerWidget(corner, Qt.Corner.TopRightCorner)

    def _on_toggle_pin(self, checked: bool):
        """DT-01/03: 切换窗口置顶状态。

        同时响应钉住按钮（QPushButton.clicked）和托盘置顶项（QAction.triggered）。
        """
        if checked:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

        self._settings.setValue("alwaysOnTop", checked)
        self._sync_pin_ui(checked)
        self.show()  # setWindowFlags 后必须 show() 才能生效

    def _sync_pin_ui(self, is_pinned: bool):
        """DT-01/03: 同步钉住按钮文字和托盘菜单勾选状态。"""
        if hasattr(self, '_pin_btn') and self._pin_btn:
            self._pin_btn.setText("📌 置顶" if is_pinned else "📍 置顶")
            self._pin_btn.setChecked(is_pinned)
        if hasattr(self, '_tray_pin_action') and self._tray_pin_action:
            self._tray_pin_action.setChecked(is_pinned)

    # ── DT-02: 恢复默认布局 ────────────────────────────────

    def _on_reset_layout(self):
        """DT-02: 恢复默认布局 — 窗口尺寸+位置+Splitter比例。"""
        # 1. 窗口尺寸恢复 950×680
        self.resize(950, 680)
        # 居中
        screen = self.screen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

        # 2. 清除 QSettings 中 Splitter 键
        self._settings.remove("splitter/prompt_tab")
        self._settings.remove("splitter/specs_tab")

        # 3. 重置所有 Splitter 为默认比例
        for _, tab in self._tabs:
            if hasattr(tab, 'reset_splitter_to_default') and callable(
                    tab.reset_splitter_to_default):
                tab.reset_splitter_to_default()

    # ── DT-06: Splitter 持久化 ─────────────────────────────

    def _save_splitter_states(self):
        """DT-06: 保存所有 Tab 的 Splitter 状态到 QSettings。"""
        for _, tab in self._tabs:
            if hasattr(tab, 'save_splitter_state') and callable(
                    tab.save_splitter_state):
                tab.save_splitter_state(self._settings)

    def _restore_splitter_states(self):
        """DT-06: 从 QSettings 恢复所有 Tab 的 Splitter 状态。"""
        for _, tab in self._tabs:
            if hasattr(tab, 'restore_splitter_state') and callable(
                    tab.restore_splitter_state):
                tab.restore_splitter_state(self._settings)
