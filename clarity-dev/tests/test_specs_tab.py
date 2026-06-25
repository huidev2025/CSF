"""
SpecsTab V3 验收测试 — IT-11a-V2 DT-01~17。

PyQt6 UI 测试，验证标签3 v3 核心行为：
- DT-01: 正文只读
- DT-02: 外部编辑器打开
- DT-03: 正文刷新
- DT-04: 无保存按钮
- DT-05: 保存新版本语义
- DT-06: 文件树刷新按钮
- DT-07: Header 行
- DT-08: 布局重组
- DT-09: 说明区编辑 UX
- DT-12: 版本视图状态机
- DT-13: 版本历史面板重排
- DT-17: 新建文件智能目录

需要 Qt 运行环境（QApplication）。
"""

import pytest
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.core.file_system_ops import FileSystemOps
from src.core.backup_engine import BackupEngine
from src.service.specs_service import SpecsService
from src.ui.specs_tab import SpecsTab


# ── 测试夹具 ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def qapp():
    """会话级 QApplication，所有 UI 测试共用。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def service(tmp_path):
    """创建指向临时目录的 SpecsService，含预置文件。"""
    lite = tmp_path / 'csf-lite'
    clarity = tmp_path / 'csf-clarity'
    backups = clarity / 'backups'
    for d in [lite / 'core', lite / 'protocols', lite / 'workspace',
              clarity, backups]:
        d.mkdir(parents=True, exist_ok=True)

    (lite / 'core' / '守则.md').write_text('# 守则\n\n内容A', encoding='utf-8')
    (lite / 'core' / '协作规范.md').write_text('# 协作规范\n\n内容B', encoding='utf-8')
    (lite / 'cos-context.md').write_text('# context\n\n内容C', encoding='utf-8')
    (lite / 'README.md').write_text('# README', encoding='utf-8')
    (lite / 'workspace' / '用户文件.md').write_text('# 用户内容', encoding='utf-8')

    fs = FileSystemOps(str(lite), str(clarity))
    backup = BackupEngine(fs, str(clarity / 'sections'), str(backups))
    return SpecsService(fs, backup, str(lite), str(clarity))


@pytest.fixture
def tab(qapp, service):
    """创建 SpecsTab 实例。"""
    t = SpecsTab(service)
    # 预置版本历史用于测试
    service.save_new_version(
        'workspace/用户文件.md', '# v1', '第一个版本说明')
    service.save_new_version(
        'workspace/用户文件.md', '# v2', '第二个版本说明')
    # 重新打开以确保版本历史刷新
    t._open_file('workspace/用户文件.md')
    return t


# ═══════════════════════════════════════════════════════════
# DT-01: 正文区只读
# ═══════════════════════════════════════════════════════════

class TestBodyReadOnly:
    def test_body_edit_is_readonly(self, tab):
        """DT-01: 正文 QTextEdit 为只读"""
        assert tab._body_edit.isReadOnly() is True

    def test_no_dirty_tracking(self, tab):
        """DT-01: 移除 _dirty 属性"""
        assert not hasattr(tab, '_dirty')


# ═══════════════════════════════════════════════════════════
# DT-02: 外部编辑器打开
# ═══════════════════════════════════════════════════════════

class TestExternalEdit:
    def test_button_exists(self, tab):
        """DT-02: [外部编辑器打开] 按钮存在"""
        assert tab._body_external_btn is not None
        assert '外部编辑器' in tab._body_external_btn.text()

    def test_view_source_path_set(self, tab):
        """DT-02: 当前版本 _view_source_path 指向 csf-lite 文件"""
        assert tab._view_source_path
        assert 'csf-lite' in tab._view_source_path.replace('\\', '/')


# ═══════════════════════════════════════════════════════════
# DT-03: 正文刷新
# ═══════════════════════════════════════════════════════════

class TestBodyRefresh:
    def test_button_exists(self, tab):
        """DT-03: [🔄刷新] 按钮存在"""
        assert tab._body_refresh_btn is not None
        assert '刷新' in tab._body_refresh_btn.text()


# ═══════════════════════════════════════════════════════════
# DT-04: 无保存按钮
# ═══════════════════════════════════════════════════════════

class TestNoSaveButton:
    def test_no_save_button(self, tab):
        """DT-04: 移除 [保存] 按钮"""
        assert not hasattr(tab, '_save_btn')

    def test_no_dirty_tracking(self, tab):
        """DT-04: 无 dirty 状态跟踪"""
        assert not hasattr(tab, '_dirty')
        assert not hasattr(tab, '_on_body_changed')


# ═══════════════════════════════════════════════════════════
# DT-05: 保存新版本语义修正
# ═══════════════════════════════════════════════════════════

class TestSaveNewVersion:
    def test_button_exists(self, tab):
        """DT-05: [保存新版本] 按钮存在"""
        assert tab._save_new_btn is not None
        assert '保存新版本' in tab._save_new_btn.text()

    def test_get_current_source_content_current_view(self, tab):
        """DT-05: 当前版本视图下 _get_current_source_content 读磁盘"""
        content = tab._get_current_source_content()
        assert content == '# v2'


# ═══════════════════════════════════════════════════════════
# DT-06: 文件树刷新按钮
# ═══════════════════════════════════════════════════════════

class TestTreeRefresh:
    def test_button_exists(self, tab):
        """DT-06: [🔄] 文件树刷新按钮存在"""
        assert tab._tree_refresh_btn is not None
        assert '🔄' in tab._tree_refresh_btn.text()


# ═══════════════════════════════════════════════════════════
# DT-07: Header 行
# ═══════════════════════════════════════════════════════════

class TestHeader:
    def test_current_view_header(self, tab):
        """DT-07: 当前版本 Header 含「当前版本」"""
        assert '当前版本' in tab._header_label.text()
        assert '历史版本' not in tab._header_label.text()

    def test_historical_view_header_yellow(self, tab):
        """DT-07: 历史版本 Header 黄色背景"""
        # 模拟切换到历史版本
        versions = tab._svc.get_version_history('workspace/用户文件.md')
        if versions:
            v = versions[0]
            content = tab._svc.restore_version(v.storage_path)
            tab._switch_to_historical_view(
                v.storage_path, v.version, v.description or '', content)
            assert '历史版本' in tab._header_label.text()
            assert 'background-color: #fffde7' in tab._header_label.styleSheet()


# ═══════════════════════════════════════════════════════════
# DT-08: 布局重组
# ═══════════════════════════════════════════════════════════

class TestLayout:
    def test_baseline_buttons_exist(self, tab):
        """DT-08: 工具栏按钮存在"""
        assert tab._baseline_all_btn is not None
        assert tab._baseline_mgr_btn is not None

    def test_no_old_reload_button(self, tab):
        """DT-08: 移除旧的 [↺重新加载] 按钮"""
        assert not hasattr(tab, '_reload_btn')


# ═══════════════════════════════════════════════════════════
# DT-09: 说明区编辑 UX
# ═══════════════════════════════════════════════════════════

class TestDescriptionEditing:
    def test_edit_button_exists(self, tab):
        """DT-09: [编辑说明] 按钮存在"""
        assert tab._desc_edit_btn is not None

    def test_save_cancel_hidden_initially(self, tab):
        """DT-09: [保存说明]/[取消] 初始隐藏"""
        assert not tab._desc_save_btn.isVisible()
        assert not tab._desc_cancel_btn.isVisible()

    def test_enter_edit_mode_shows_buttons(self, tab):
        """DT-09: 进入编辑模式 → 按钮切换"""
        tab._on_edit_description()
        assert tab._desc_edit_btn.isHidden()
        assert not tab._desc_save_btn.isHidden()
        assert not tab._desc_cancel_btn.isHidden()
        assert tab._desc_editing is True
        assert tab._desc_title_label.text() == '文件说明 *'

    def test_cancel_restores_original(self, tab):
        """DT-09: 取消 → 恢复原内容 + 退出编辑模式"""
        original = tab._desc_edit.toPlainText()
        tab._on_edit_description()
        tab._desc_edit.setPlainText('修改后的内容')
        tab._on_cancel_description()
        assert tab._desc_edit.toPlainText() == original
        assert tab._desc_editing is False
        assert tab._desc_title_label.text() == '文件说明'

    def test_save_description_current_view(self, tab):
        """DT-09: 保存说明（当前版本）→ file_meta.json"""
        tab._on_edit_description()
        tab._desc_edit.setPlainText('新说明内容')
        tab._on_save_description()
        assert tab._svc._file_meta.get('用户文件') == '新说明内容'
        assert tab._desc_editing is False


# ═══════════════════════════════════════════════════════════
# DT-12: 版本视图状态机
# ═══════════════════════════════════════════════════════════

class TestViewStateMachine:
    def test_default_view_is_current(self, tab):
        """DT-12: 打开文件默认加载当前版本"""
        assert tab._view_state == 'current'

    def test_switch_to_historical_changes_state(self, tab):
        """DT-12: 切换到历史版本 → view_state='historical'"""
        versions = tab._svc.get_version_history('workspace/用户文件.md')
        if versions:
            v = versions[0]
            content = tab._svc.restore_version(v.storage_path)
            tab._switch_to_historical_view(
                v.storage_path, v.version, v.description or '', content)
            assert tab._view_state == 'historical'
            assert '历史版本' in tab._header_label.text()

    def test_open_file_resets_to_current(self, tab):
        """DT-12: _open_file 重置为当前版本视图"""
        # 先切换到历史版本
        versions = tab._svc.get_version_history('workspace/用户文件.md')
        if versions:
            v = versions[0]
            content = tab._svc.restore_version(v.storage_path)
            tab._switch_to_historical_view(
                v.storage_path, v.version, v.description or '', content)
            assert tab._view_state == 'historical'

        # 重新打开文件 → 回到当前版本
        tab._open_file('workspace/用户文件.md')
        assert tab._view_state == 'current'


# ═══════════════════════════════════════════════════════════
# DT-13: 版本历史面板重排
# ═══════════════════════════════════════════════════════════

class TestVersionHistoryPanel:
    def test_panel_has_items(self, tab):
        """DT-13: 版本历史面板有条目（预置2个版本）"""
        count = tab._version_list.count()
        assert count >= 2, f'预期≥2条版本历史，实际{count}'

    def test_version_item_has_rich_text(self, tab):
        """DT-13: 版本历史条目使用富文本（QLabel item widget）"""
        item = tab._version_list.item(0)
        widget = tab._version_list.itemWidget(item)
        assert widget is not None

    def test_click_version_switches_view(self, tab):
        """DT-13: 单击版本 → 切换到历史视图"""
        item = tab._version_list.item(0)
        if item:
            storage_path = item.data(Qt.ItemDataRole.UserRole)
            if storage_path:
                tab._on_version_clicked(item)
                assert tab._view_state == 'historical'
                assert tab._view_source_path == storage_path


# ═══════════════════════════════════════════════════════════
# DT-17: 新建文件智能目录
# ═══════════════════════════════════════════════════════════

class TestNewFileSmartDir:
    def test_button_exists(self, tab):
        """DT-17: [＋新建文件] 按钮存在"""
        assert tab._new_file_btn is not None
        assert '新建文件' in tab._new_file_btn.text()


# ═══════════════════════════════════════════════════════════
# 代码质量检查
# ═══════════════════════════════════════════════════════════

class TestCodeQuality:
    def test_no_plain_text_edit_in_body(self, tab):
        """IT-11a: 正文区使用 QTextEdit（只读），非 QPlainTextEdit"""
        from PyQt6.QtWidgets import QTextEdit, QPlainTextEdit
        assert isinstance(tab._body_edit, QTextEdit)
        assert not isinstance(tab._body_edit, QPlainTextEdit)

    def test_no_save_button(self, tab):
        """IT-11a: 无 [保存] 按钮"""
        assert not hasattr(tab, '_save_btn')
        assert not hasattr(tab, '_on_save')
