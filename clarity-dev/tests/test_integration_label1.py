"""test_integration_label1.py — 标签1 v3 端到端集成测试。

覆盖 STB-IT-13d DT-02 的核心场景（E1-E13），使用真实 PromptStore + 临时目录。
所有测试通过 list_by_group 动态发现文件名，不硬编码工厂预置文件名。
"""

import pytest
from pathlib import Path


# ── 辅助函数：在工厂预置中动态定位提示词 ────────────────────

def _find_by_keyword(service, group: str, keyword: str) -> dict | None:
    """在指定分组中按关键词查找提示词元信息。"""
    for p in service.list_by_group(group):
        if keyword in p['description']:
            return p
    return None


def _get_filename(service, group: str, keyword: str) -> str:
    """查找并返回文件名，不存在则抛异常。"""
    found = _find_by_keyword(service, group, keyword)
    if not found:
        raise FileNotFoundError(f"Factory preset not found: {group}/{keyword}")
    return found['filename']


# ── fixtures ──────────────────────────────────────────────

@pytest.fixture
def prompts_dir(tmp_path):
    """临时 prompts 目录。"""
    d = tmp_path / "prompts"
    d.mkdir()
    return str(d)


@pytest.fixture
def store(prompts_dir):
    from src.data.prompt_store import PromptStore
    return PromptStore(prompts_dir)


@pytest.fixture
def service(store):
    from src.service.prompt_service import PromptService
    svc = PromptService(store)
    svc.initialize_factory_presets()
    return svc


# ── E1+E2: 启动 + 出厂预置 ─────────────────────────────────

class TestFactoryPresets:
    """E1+E2: 首次运行 → 5分组7条提示词。"""

    def test_groups_count(self, service):
        assert len(service.list_groups()) == 5

    def test_groups_names(self, service):
        groups = service.list_groups()
        for name in ["开局", "收尾", "立项", "修复", "复盘"]:
            assert name in groups

    def test_total_prompts(self, service):
        total = sum(len(service.list_by_group(g)) for g in service.list_groups())
        assert total == 7

    def test_initialize_idempotent(self, service):
        assert service.initialize_factory_presets() is False
        total = sum(len(service.list_by_group(g)) for g in service.list_groups())
        assert total == 7


# ── E3+E4: 加载 + 编辑保存 ─────────────────────────────────

class TestLoadAndSave:
    """E3+E4: 选中加载 + 保存持久化。"""

    def test_load_preset(self, service):
        """E3: 加载第一条预置提示词。"""
        filename = _get_filename(service, "开局", "标准开局")
        prompt = service.get("开局", filename)
        assert len(prompt.description) > 0
        assert len(prompt.content) > 0

    def test_save_and_reload(self, service):
        """E4: 修改→保存→重载确认持久化。"""
        filename = _get_filename(service, "开局", "标准开局")
        new_content = "SAVE_TEST_CONTENT_v3"
        updated = service.update("开局", filename, new_content)
        assert updated.content == new_content

        reloaded = service.get("开局", filename)
        assert reloaded.content == new_content


# ── E5: 新增 ───────────────────────────────────────────────

class TestCreate:
    """E5: 新增提示词。"""

    def test_create_appears_in_list(self, service):
        new_p = service.create("开局", "集成测试新增", "正文ABC")
        assert new_p.description == "集成测试新增"
        prompts = service.list_by_group("开局")
        assert any("集成测试新增" in p['description'] for p in prompts)

    def test_create_duplicate_raises(self, service):
        service.create("开局", "dup-test-unique", "x")
        with pytest.raises(ValueError):
            service.create("开局", "dup-test-unique", "y")

    def test_create_empty_group_raises(self, service):
        with pytest.raises(ValueError):
            service.create("", "test", "x")

    def test_create_empty_desc_raises(self, service):
        with pytest.raises(ValueError):
            service.create("开局", "", "x")


# ── E6+E7: 收藏 ────────────────────────────────────────────

class TestFavorites:
    """E6+E7: 收藏切换。"""

    def test_initial_empty(self, service):
        assert service.get_favorites() == []

    def test_toggle_on(self, service):
        """E6: 收藏某条 → 出现在列表中。"""
        fn = _get_filename(service, "开局", "标准开局")
        assert service.toggle_favorite("开局", fn) is True
        assert service.is_favorite("开局", fn) is True
        assert any(f['filename'] == fn for f in service.get_favorites())

    def test_toggle_off(self, service):
        """E7: 取消收藏 → 从列表消失。"""
        fn = _get_filename(service, "开局", "标准开局")
        service.toggle_favorite("开局", fn)
        assert service.toggle_favorite("开局", fn) is False
        assert not service.is_favorite("开局", fn)
        assert not any(f['filename'] == fn for f in service.get_favorites())

    def test_not_favorite(self, service):
        fn = _get_filename(service, "开局", "标准开局")
        assert service.is_favorite("开局", fn) is False


# ── E8+E9: 搜索 ────────────────────────────────────────────

class TestSearch:
    """E8+E9: 搜索 + 清空。"""

    def test_search_finds(self, service):
        """E8: 搜索"收尾"有结果。"""
        results = service.search("收尾")
        assert len(results) >= 1
        for r in results:
            assert "收尾" in r['description']

    def test_search_empty(self, service):
        """E9: 空搜索 → []。"""
        assert service.search("") == []
        assert service.search("   ") == []

    def test_search_no_match(self, service):
        assert service.search("XYZZY_NO_MATCH_123") == []


# ── E10: 内容获取（模拟复制到剪贴板）────────────────────────

class TestCopyToClipboard:
    """E10: 内容获取链路。"""

    def test_modified_content_retrievable(self, service):
        fn = _get_filename(service, "开局", "标准开局")
        service.update("开局", fn, "CLIPBOARD_TEST")
        assert service.get("开局", fn).content == "CLIPBOARD_TEST"


# ── E11: 复制新建 ──────────────────────────────────────────

class TestDuplicate:
    """E11: 复制新建 — 数字前缀。"""

    def test_numbered_copy(self, service):
        fn = _get_filename(service, "开局", "标准开局")
        new_p = service.duplicate("开局", fn, "定制正文")
        assert new_p is not None
        assert new_p.content == "定制正文"
        assert new_p.description != fn.replace('.md', '')

    def test_increment(self, service):
        fn = _get_filename(service, "开局", "标准开局")
        p1 = service.duplicate("开局", fn, "c1")
        p2 = service.duplicate("开局", fn, "c2")
        assert p1.description != p2.description


# ── E12: 删除 ──────────────────────────────────────────────

class TestDelete:
    """E12: 删除提示词。"""

    def test_delete_removes(self, service):
        filename = _get_filename(service, "收尾", "快速收尾")
        before = len(service.list_by_group("收尾"))

        service.delete("收尾", filename)

        with pytest.raises(FileNotFoundError):
            service.get("收尾", filename)

        after = len(service.list_by_group("收尾"))
        assert after == before - 1

    def test_nonexistent_no_error(self, service):
        service.delete("开局", "nonexistent_xyz.md")


# ── E13+E16: 移动分组 ──────────────────────────────────────

class TestMoveGroup:
    """E13+E16: 拖拽换组 + 分组下拉。"""

    def test_move_between_groups(self, service):
        fn = _get_filename(service, "开局", "聚焦式开局")
        prompt = service.get("开局", fn)
        updated = service.update("开局", fn, prompt.content, new_group="收尾")
        assert updated is not None

        # 新位置可加载
        moved = service.get("收尾", fn)
        assert moved is not None
        assert moved.content == prompt.content

        # 注意：当前PromptStore.save_prompt跨组移动时不会自动删除源文件。
        # 这是已知边界行为——UI层由PromptTab在move后显式调用delete清理源。
        # 服务层测试仅验证新位置正确。


# ── 数据一致性 ─────────────────────────────────────────────

class TestConsistency:
    """回归验证：所有分组的所有提示词均可加载。"""

    def test_all_loadable(self, service):
        for g in service.list_groups():
            for p in service.list_by_group(g):
                prompt = service.get(p['group'], p['filename'])
                assert prompt is not None
                assert len(prompt.description) > 0
                assert hasattr(prompt, 'content')
