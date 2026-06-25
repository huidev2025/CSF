"""
PromptService v3 验收测试 — IT-13b。

39条测试，覆盖全部5个DT。使用 mock PromptStore，不创建真实文件。
"""

import pytest
from unittest.mock import Mock, call

from src.service.prompt_service import PromptService
from src.core.models import Prompt


# ── 测试夹具 ──────────────────────────────────────────────

@pytest.fixture
def store():
    """创建 mock PromptStore。"""
    return Mock()


@pytest.fixture
def service(store):
    """创建 PromptService 实例。"""
    return PromptService(store)


def _make_prompt(description="测试提示词", content="正文内容",
                 created_at="2026-01-01T00:00:00+00:00"):
    return Prompt(description=description, content=content, created_at=created_at)


# ═══════════════════════════════════════════════════════════
# DT-01 CRUD（无版本）— 16条断言
# ═══════════════════════════════════════════════════════════

class TestListGroups:
    """DT-01b"""

    def test_delegates_to_store(self, service, store):
        """#1 list_groups() 返回 store.get_groups() 的结果"""
        store.get_groups.return_value = ["开局", "收尾"]
        result = service.list_groups()
        assert result == ["开局", "收尾"]
        store.get_groups.assert_called_once()


class TestListByGroup:
    """DT-01c"""

    def test_delegates_to_store(self, service, store):
        """#2 list_by_group("开局") 返回 store.list_prompts("开局") 的结果"""
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "a.md", "description": "A", "created_at": "t"}
        ]
        result = service.list_by_group("开局")
        assert result == store.list_prompts.return_value
        store.list_prompts.assert_called_once_with("开局")


class TestGet:
    """DT-01d"""

    def test_returns_prompt(self, service, store):
        """#3 get() 返回 Prompt 对象，字段完整"""
        prompt = _make_prompt()
        store.load_prompt.return_value = prompt
        result = service.get("开局", "标准开局.md")
        assert result is prompt
        assert result.description == "测试提示词"
        assert result.content == "正文内容"

    def test_not_found_raises(self, service, store):
        """#4 get 对不存在的提示词 → FileNotFoundError"""
        store.load_prompt.return_value = None
        with pytest.raises(FileNotFoundError, match="提示词不存在"):
            service.get("开局", "不存在.md")


class TestCreate:
    """DT-01e"""

    def test_create_success(self, service, store):
        """#5 create() 成功创建，调用 store.save_prompt(group, None, prompt)"""
        store._sanitize_filename.return_value = "新提示词.md"
        store.list_prompts.return_value = []
        store.save_prompt.return_value = "新提示词.md"
        prompt = _make_prompt()
        store.load_prompt.return_value = prompt

        result = service.create("开局", "新提示词", "正文")

        store.save_prompt.assert_called_once()
        call_args = store.save_prompt.call_args
        assert call_args[0][0] == "开局"  # group
        assert call_args[0][1] is None    # old_filename=None（新建）
        assert result is prompt

    def test_empty_group_raises(self, service, store):
        """#6 create group 为空字符串 → ValueError"""
        with pytest.raises(ValueError, match="group 不能为空"):
            service.create("", "描述", "正文")
        with pytest.raises(ValueError, match="group 不能为空"):
            service.create("   ", "描述", "正文")

    def test_empty_description_raises(self, service, store):
        """#7 create description 为空字符串 → ValueError"""
        with pytest.raises(ValueError, match="description 不能为空"):
            service.create("开局", "", "正文")
        with pytest.raises(ValueError, match="description 不能为空"):
            service.create("开局", "   ", "正文")

    def test_duplicate_name_raises(self, service, store):
        """#8 create 同组重名 → ValueError"""
        store._sanitize_filename.return_value = "重名.md"
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "重名.md", "description": "重名", "created_at": "t"}
        ]
        with pytest.raises(ValueError, match="已存在"):
            service.create("开局", "重名", "正文")


class TestUpdate:
    """DT-01f"""

    def test_update_content_only(self, service, store):
        """#9 update 仅改内容，new_group=new_description=None"""
        old_prompt = _make_prompt(description="旧名")
        updated_prompt = _make_prompt(description="旧名", content="新正文")
        store.load_prompt.side_effect = [old_prompt, updated_prompt]
        store.save_prompt.return_value = "旧名.md"

        result = service.update("开局", "旧名.md", "新正文")

        # 验证 save_prompt 调用参数
        call_args = store.save_prompt.call_args
        assert call_args[0][0] == "开局"           # target_group = group
        assert call_args[0][1] == "旧名.md"         # old_filename
        assert call_args[0][2].content == "新正文"   # prompt.content 已更新
        assert result is updated_prompt

    def test_update_rename(self, service, store):
        """#10 update 改名：new_description="新名称" → prompt.description 更新"""
        old_prompt = _make_prompt(description="旧名")
        new_prompt = _make_prompt(description="新名称")
        store.load_prompt.side_effect = [old_prompt, new_prompt]
        store.save_prompt.return_value = "新名称.md"

        service.update("开局", "旧名.md", "正文", new_description="新名称")

        # 验证 save_prompt 接收更新后的 prompt.description
        saved_prompt = store.save_prompt.call_args[0][2]
        assert saved_prompt.description == "新名称"

    def test_update_move_group(self, service, store):
        """#11 update 移动分组：new_group="收尾" → store.save_prompt("收尾", filename, prompt)"""
        old_prompt = _make_prompt()
        new_prompt = _make_prompt()
        store.load_prompt.side_effect = [old_prompt, new_prompt]
        store.save_prompt.return_value = "测试提示词.md"

        service.update("开局", "测试提示词.md", "正文", new_group="收尾")

        call_args = store.save_prompt.call_args
        assert call_args[0][0] == "收尾"  # target_group

    def test_update_not_found(self, service, store):
        """#12 update 提示词不存在 → FileNotFoundError"""
        store.load_prompt.return_value = None
        with pytest.raises(FileNotFoundError, match="提示词不存在"):
            service.update("开局", "不存在.md", "正文")

    def test_update_empty_new_description_raises(self, service, store):
        """#13 update new_description 为空 → ValueError"""
        store.load_prompt.return_value = _make_prompt()
        with pytest.raises(ValueError, match="new_description 不能为空"):
            service.update("开局", "a.md", "正文", new_description="")

    def test_update_syncs_favorite_on_rename(self, service, store):
        """#14 update 改名时调用 store.update_favorite_path 同步收藏"""
        store.load_prompt.side_effect = [
            _make_prompt(description="旧名"),
            _make_prompt(description="新名称"),
        ]
        store.save_prompt.return_value = "新名称.md"

        service.update("开局", "旧名.md", "正文", new_description="新名称")

        store.update_favorite_path.assert_called_once_with(
            "开局", "旧名", "开局", "新名称"
        )


class TestDelete:
    """DT-01g"""

    def test_delete_calls_remove_favorite_then_delete(self, service, store):
        """#15 delete 成功：先调 store.remove_favorite，再调 store.delete_prompt"""
        service.delete("开局", "待删.md")

        # 验证调用顺序
        assert store.remove_favorite.called
        assert store.delete_prompt.called
        # remove_favorite 应在 delete_prompt 之前
        remove_call_idx = store.method_calls.index(call.remove_favorite("开局", "待删"))
        delete_call_idx = store.method_calls.index(call.delete_prompt("开局", "待删.md"))
        assert remove_call_idx < delete_call_idx

    def test_delete_not_found_no_error(self, service, store):
        """#16 delete 文件不存在 → 不抛异常"""
        store.delete_prompt.return_value = False
        # 不应抛异常
        service.delete("开局", "不存在.md")


# ═══════════════════════════════════════════════════════════
# DT-02 复制新建 — 6条断言
# ═══════════════════════════════════════════════════════════

class TestDuplicate:
    """DT-02"""

    def test_duplicate_no_number_prefix(self, service, store):
        """#17 duplicate 原无编号 → 新 description="2 基础名" """
        store.load_prompt.side_effect = [
            _make_prompt(description="标准开局"),     # 第一次：加载原提示词
            _make_prompt(description="2 标准开局"),   # 第二次：加载新创建的
        ]
        store.list_prompts.return_value = []  # 无冲突
        store.save_prompt.return_value = "2 标准开局.md"

        result = service.duplicate("开局", "标准开局.md", "正文")

        saved = store.save_prompt.call_args[0][2]
        assert saved.description == "2 标准开局"
        assert result.description == "2 标准开局"

    def test_duplicate_with_number_prefix_increments(self, service, store):
        """#18 原 description="2 标准开局 — 描述" → 基础名="标准开局 — 描述"，新编号=3"""
        store.load_prompt.side_effect = [
            _make_prompt(description="2 标准开局 — 描述"),
            _make_prompt(description="3 标准开局 — 描述"),
        ]
        # 包含原提示词以建立 max_num=2
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "2 标准开局 — 描述.md", "description": "2 标准开局 — 描述", "created_at": "t"}
        ]
        store.save_prompt.return_value = "3 标准开局 — 描述.md"

        result = service.duplicate("开局", "2 标准开局 — 描述.md", "正文")

        saved = store.save_prompt.call_args[0][2]
        assert saved.description == "3 标准开局 — 描述"

    def test_duplicate_skips_existing_number(self, service, store):
        """#19 同组已有 "2 标准开局" → 跳过到 "3 标准开局" """
        store.load_prompt.side_effect = [
            _make_prompt(description="标准开局"),
            _make_prompt(description="3 标准开局"),
        ]
        # list_prompts 返回已有 "2 标准开局"
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "2 标准开局.md", "description": "2 标准开局", "created_at": "t"}
        ]
        store.save_prompt.return_value = "3 标准开局.md"

        result = service.duplicate("开局", "标准开局.md", "正文")

        saved = store.save_prompt.call_args[0][2]
        assert saved.description == "3 标准开局"

    def test_duplicate_large_number(self, service, store):
        """#20 原 description="10 标准开局" → 基础名="标准开局"，新编号=11"""
        store.load_prompt.side_effect = [
            _make_prompt(description="10 标准开局"),
            _make_prompt(description="11 标准开局"),
        ]
        # 包含原提示词以建立 max_num=10
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "10 标准开局.md", "description": "10 标准开局", "created_at": "t"}
        ]
        store.save_prompt.return_value = "11 标准开局.md"

        result = service.duplicate("开局", "10 标准开局.md", "正文")

        saved = store.save_prompt.call_args[0][2]
        assert saved.description == "11 标准开局"

    def test_duplicate_no_number_prefix_gets_2(self, service, store):
        """#21 原 description 无数字前缀 → 基础名保持，新编号=2"""
        store.load_prompt.side_effect = [
            _make_prompt(description="标准开局 — 描述"),
            _make_prompt(description="2 标准开局 — 描述"),
        ]
        store.list_prompts.return_value = []
        store.save_prompt.return_value = "2 标准开局 — 描述.md"

        result = service.duplicate("开局", "标准开局 — 描述.md", "正文")

        saved = store.save_prompt.call_args[0][2]
        assert saved.description == "2 标准开局 — 描述"

    def test_duplicate_original_not_found(self, service, store):
        """#22 duplicate 原提示词不存在 → FileNotFoundError"""
        store.load_prompt.return_value = None
        with pytest.raises(FileNotFoundError, match="提示词不存在"):
            service.duplicate("开局", "不存在.md", "正文")


# ═══════════════════════════════════════════════════════════
# DT-03 收藏管理 — 7条断言
# ═══════════════════════════════════════════════════════════

class TestGetFavorites:
    """DT-03a"""

    def test_returns_with_description(self, service, store):
        """#23 get_favorites() 返回含 group/filename/description 的结构"""
        store.get_favorites.return_value = ["开局/标准开局"]
        store.load_prompt.return_value = _make_prompt(description="标准开局 — 描述")

        result = service.get_favorites()

        assert len(result) == 1
        assert result[0] == {
            "group": "开局",
            "filename": "标准开局.md",
            "description": "标准开局 — 描述",
        }

    def test_skips_deleted_file(self, service, store):
        """#24 get_favorites() 某条收藏的文件已删除 → 跳过不崩溃"""
        store.get_favorites.return_value = ["开局/标准开局", "开局/已删除"]
        # 第一条存在，第二条返回None（已删除）
        store.load_prompt.side_effect = [
            _make_prompt(description="标准开局"),
            None,
        ]

        result = service.get_favorites()

        assert len(result) == 1
        assert result[0]["filename"] == "标准开局.md"


class TestToggleFavorite:
    """DT-03b"""

    def test_toggle_add(self, service, store):
        """#25 toggle_favorite 未收藏→已收藏，返回 True"""
        store.get_favorites.return_value = []

        result = service.toggle_favorite("开局", "标准开局.md")

        assert result is True
        store.add_favorite.assert_called_once_with("开局", "标准开局")

    def test_toggle_remove(self, service, store):
        """#26 toggle_favorite 已收藏→取消，返回 False"""
        store.get_favorites.return_value = ["开局/标准开局"]

        result = service.toggle_favorite("开局", "标准开局.md")

        assert result is False
        store.remove_favorite.assert_called_once_with("开局", "标准开局")

    def test_toggle_strips_md_suffix(self, service, store):
        """#27 toggle_favorite 调用时 filename 参数正确去掉 .md 后缀"""
        store.get_favorites.return_value = []

        service.toggle_favorite("开局", "标准开局.md")

        store.add_favorite.assert_called_once_with("开局", "标准开局")


class TestIsFavorite:
    """DT-03c"""

    def test_is_favorite_true(self, service, store):
        """#28 is_favorite → True"""
        store.get_favorites.return_value = ["开局/标准开局"]
        assert service.is_favorite("开局", "标准开局.md") is True

    def test_is_favorite_false(self, service, store):
        """#29 is_favorite → False"""
        store.get_favorites.return_value = []
        assert service.is_favorite("开局", "不存在.md") is False


# ═══════════════════════════════════════════════════════════
# DT-04 搜索过滤 — 5条断言
# ═══════════════════════════════════════════════════════════

class TestSearch:
    """DT-04"""

    def test_search_returns_matches(self, service, store):
        """#30 search("开局") 返回匹配的提示词列表"""
        store.get_groups.return_value = ["开局"]
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "a.md", "description": "标准开局", "created_at": "t1"},
            {"group": "开局", "filename": "b.md", "description": "不匹配", "created_at": "t2"},
        ]
        # 第二条 description 不匹配→加载正文
        store.load_prompt.return_value = _make_prompt(content="开局相关正文")

        result = service.search("开局")

        # 结果按 (group, description) 排序，"不匹配" < "标准开局" 在 Unicode 下
        assert len(result) == 2
        descriptions = {r["description"] for r in result}
        assert descriptions == {"标准开局", "不匹配"}

    def test_search_empty_query_returns_empty(self, service, store):
        """#31 search("") 返回空列表"""
        result = service.search("")
        assert result == []
        store.get_groups.assert_not_called()

    def test_search_whitespace_returns_empty(self, service, store):
        """#32 search("   ") 仅空白 → 返回空列表"""
        result = service.search("   ")
        assert result == []

    def test_search_no_match_returns_empty(self, service, store):
        """#33 搜索无匹配 → 返回空列表"""
        store.get_groups.return_value = ["开局"]
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "a.md", "description": "ABC", "created_at": "t"}
        ]
        store.load_prompt.return_value = _make_prompt(content="DEF")

        result = service.search("XYZ")
        assert result == []

    def test_search_description_match_skips_load(self, service, store):
        """#34 description 匹配时不额外调 load_prompt（性能）"""
        store.get_groups.return_value = ["开局"]
        store.list_prompts.return_value = [
            {"group": "开局", "filename": "a.md", "description": "开局协议", "created_at": "t"}
        ]

        service.search("开局")

        # description 匹配 → 不应调 load_prompt
        store.load_prompt.assert_not_called()


# ═══════════════════════════════════════════════════════════
# DT-05 出厂预置初始化 — 5条断言
# ═══════════════════════════════════════════════════════════

class TestInitializeFactoryPresets:
    """DT-05"""

    def test_initializes_when_empty(self, service, store):
        """#35 prompts/ 为空 → 执行初始化，返回 True"""
        store.get_groups.return_value = []
        store.save_prompt.return_value = "x.md"

        result = service.initialize_factory_presets()

        assert result is True
        assert store.save_prompt.call_count == 7

    def test_skips_when_not_empty(self, service, store):
        """#36 prompts/ 已有分组 → 跳过，返回 False"""
        store.get_groups.return_value = ["开局"]

        result = service.initialize_factory_presets()

        assert result is False
        store.save_prompt.assert_not_called()

    def test_initializes_empty_favorites(self, service, store):
        """#37 初始化后 store.save_favorites([]) 被调用"""
        store.get_groups.return_value = []
        store.save_prompt.return_value = "x.md"

        service.initialize_factory_presets()

        store.save_favorites.assert_called_once_with([])

    def test_creates_5_groups(self, service, store):
        """#38 初始化创建了 5 个分组：开局/收尾/立项/修复/复盘"""
        store.get_groups.return_value = []
        store.save_prompt.return_value = "x.md"

        service.initialize_factory_presets()

        # 提取所有 save_prompt 调用的 group 参数
        groups = {c[0][0] for c in store.save_prompt.call_args_list}
        assert groups == {"开局", "收尾", "立项", "修复", "复盘"}

    def test_creates_7_prompts(self, service, store):
        """#39 初始化创建了 7 条提示词"""
        store.get_groups.return_value = []
        store.save_prompt.return_value = "x.md"

        service.initialize_factory_presets()

        assert store.save_prompt.call_count == 7
