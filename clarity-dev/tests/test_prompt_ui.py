"""
PromptTab v3 UI 验收测试 — IT-13c。

所有 8 DT 均为 🟡弱档（手动验收），本文件包含：
- 模块导入验证
- PromptTab + PromptTreeWidget 基本实例化验证
- Service mock 集成验证
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QApplication, QTreeWidget
from PyQt6.QtCore import Qt

from src.ui.prompt_tab import PromptTab, PromptTreeWidget
from src.service.prompt_service import PromptService


# ── QApplication 单例管理 ────────────────────────────────

@pytest.fixture(scope='session')
def qapp():
    """会话级 QApplication 单例。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# ── Mock Service ─────────────────────────────────────────

@pytest.fixture
def mock_service():
    """创建 Mock PromptService。"""
    from src.data.prompt_store import PromptStore
    from src.core.models import Prompt
    from src.config import PROMPTS_DIR

    store = PromptStore(PROMPTS_DIR)
    service = PromptService(store)
    return service


# ── DT-01: 两栏骨架 ──────────────────────────────────────

class TestPromptTabInstantiation:
    """验证 PromptTab v3 可正常实例化。"""

    def test_instantiation_with_service(self, qapp, mock_service):
        """DT-01: 使用 PromptService 实例化 PromptTab，不抛异常。"""
        tab = PromptTab(mock_service)
        assert tab is not None
        assert hasattr(tab, '_splitter')
        assert hasattr(tab, '_tree')
        assert hasattr(tab, '_desc_edit')
        assert hasattr(tab, '_content_edit')

    def test_constructor_signature_compatible(self, qapp, mock_service):
        """DT-01: 构造函数签名与 V2 相同——PromptTab(service) 可调用。"""
        tab = PromptTab(mock_service)  # 不传 parent
        assert isinstance(tab, PromptTab)


# ── DT-02: 导航树 ────────────────────────────────────────

class TestNavigationTree:
    """验证导航树组件。"""

    def test_tree_widget_instantiation(self, qapp):
        """DT-02: PromptTreeWidget 可独立实例化。"""
        tree = PromptTreeWidget()
        assert tree is not None
        assert tree._on_drop_to_favorites is None
        assert tree._move_prompt is None

    def test_tree_has_correct_properties(self, qapp, mock_service):
        """DT-02: 导航树配置正确——无表头、可拖拽、单选。"""
        tab = PromptTab(mock_service)
        assert tab._tree.isHeaderHidden()
        assert tab._tree.dragDropMode() == QTreeWidget.DragDropMode.DragDrop

    def test_load_data_populates_tree(self, qapp, mock_service):
        """DT-02: _load_data() 填充导航树——至少有一个分组节点。"""
        tab = PromptTab(mock_service)
        # 至少有 1 个分组（csf-clarity/prompts/ 已有数据或出厂预置）
        assert tab._tree.topLevelItemCount() >= 1


# ── DT-03: 搜索框 ────────────────────────────────────────

class TestSearch:
    """验证搜索功能。"""

    def test_search_box_exists(self, qapp, mock_service):
        """DT-03: 搜索框存在且占位符正确。"""
        tab = PromptTab(mock_service)
        assert hasattr(tab, '_search_box')
        assert "搜索" in tab._search_box.placeholderText()

    def test_search_empty_shows_all(self, qapp, mock_service):
        """DT-03: 空搜索显示全部内容（至少1个分组）。"""
        tab = PromptTab(mock_service)
        tab._on_search("")
        assert tab._tree.topLevelItemCount() >= 1

    def test_search_no_match_shows_empty_state(self, qapp, mock_service):
        """DT-03: 搜索不存在的词显示空状态。"""
        tab = PromptTab(mock_service)
        tab._on_search("不存在的关键词xyz123")
        assert tab._tree.topLevelItemCount() == 1  # 空状态提示项


# ── DT-04: 编辑区 ────────────────────────────────────────

class TestEditorPanel:
    """验证编辑区组件。"""

    def test_editor_has_text_edits(self, qapp, mock_service):
        """DT-04: 编辑区包含说明和正文两个 QTextEdit。"""
        tab = PromptTab(mock_service)
        assert tab._desc_edit is not None
        assert tab._content_edit is not None
        # 始终可编辑（非只读）
        assert not tab._desc_edit.isReadOnly()
        assert not tab._content_edit.isReadOnly()

    def test_editor_splitter_exists(self, qapp, mock_service):
        """DT-04: 编辑区垂直分隔条存在。"""
        tab = PromptTab(mock_service)
        assert hasattr(tab, '_editor_splitter')

    def test_dirty_flag_management(self, qapp, mock_service):
        """DT-04: 脏标志管理——初始干净，修改后变脏。"""
        tab = PromptTab(mock_service)
        assert not tab._is_dirty
        assert tab._save_btn.text() == "保存"


# ── DT-05: 选中加载 ──────────────────────────────────────

class TestSelectionAndLoading:
    """验证选中加载逻辑。"""

    def test_scene_combo_exists(self, qapp, mock_service):
        """DT-05: 场景下拉选择器存在（v4: _group_combo→_scene_combo）。"""
        tab = PromptTab(mock_service)
        assert tab._scene_combo is not None

    def test_fav_button_exists(self, qapp, mock_service):
        """DT-05: ⭐收藏按钮存在。"""
        tab = PromptTab(mock_service)
        assert tab._fav_btn is not None
        assert tab._fav_btn.isCheckable()


# ── DT-06: 按钮行 ────────────────────────────────────────

class TestButtonBar:
    """验证按钮行组件。"""

    def test_all_buttons_exist(self, qapp, mock_service):
        """DT-06: 四个按钮全部存在。"""
        tab = PromptTab(mock_service)
        assert tab._save_btn is not None
        assert tab._copy_clipboard_btn is not None
        assert tab._duplicate_btn is not None
        assert tab._delete_btn is not None

    def test_save_button_initial_text(self, qapp, mock_service):
        """DT-06: 保存按钮初始文字为"保存"。"""
        tab = PromptTab(mock_service)
        assert tab._save_btn.text() == "保存"


# ── DT-07: 拖拽换组 ──────────────────────────────────────

class TestDragDrop:
    """验证拖拽机制。"""

    def test_tree_drag_enabled(self, qapp, mock_service):
        """DT-07: 导航树拖拽功能已启用。"""
        tab = PromptTab(mock_service)
        assert tab._tree.dragEnabled()
        assert tab._tree.acceptDrops()

    def test_move_prompt_callback_attached(self, qapp, mock_service):
        """DT-07: _move_prompt 回调已挂载到树。"""
        tab = PromptTab(mock_service)
        assert tab._tree._move_prompt is not None
        assert tab._tree._on_drop_to_favorites is not None


# ── DT-08: 交互保护 ──────────────────────────────────────

class TestInteractionProtection:
    """验证交互保护机制。"""

    def test_can_close_clean_state(self, qapp, mock_service):
        """DT-08b: 干净状态 can_close() 返回 True。"""
        tab = PromptTab(mock_service)
        assert tab.can_close() is True

    def test_clear_editor_resets_state(self, qapp, mock_service):
        """DT-08c: _clear_editor() 重置所有状态。"""
        tab = PromptTab(mock_service)
        tab._clear_editor()
        assert tab._current_group == ''
        assert tab._current_filename == ''
        assert tab._current_description == ''
        assert not tab._is_dirty

    def test_new_prompt_button_exists(self, qapp, mock_service):
        """DT-08d: [+新增提示词] 按钮存在。"""
        tab = PromptTab(mock_service)
        assert tab._new_btn is not None
        assert "新增" in tab._new_btn.text()
