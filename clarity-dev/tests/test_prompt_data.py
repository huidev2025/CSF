"""
test_prompt_data.py — IT-13a 数据层验收测试。

覆盖 DT-01（Prompt v3 数据模型）、DT-02（分组扫描）、
DT-03（文件读写：sanitize/load/save/delete/list/load_all）、
DT-04（_favorites.json 管理）。

全部 36 条验收断言，pytest 自动化，tmp_path 隔离。
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime, timezone

from src.core.models import Prompt
from src.data.prompt_store import PromptStore


# ══════════════════════════════════════════════════════════════
# 测试夹具
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def store(tmp_path):
    """创建使用临时目录的 PromptStore 实例。"""
    d = tmp_path / 'prompts'
    return PromptStore(str(d))


@pytest.fixture
def populated_store(store):
    """创建一个含两个分组、各两条提示词的 store。"""
    now = datetime.now(timezone.utc).isoformat()
    # 分组1: 开局
    store.save_prompt('开局', None, Prompt(
        description='标准开局 — 标准CSF开局协议',
        content='阅读 cos-context，开局。',
        created_at=now,
    ))
    store.save_prompt('开局', None, Prompt(
        description='聚焦式开局',
        content='针对特定主题的聚焦式开局。',
        created_at=now,
    ))
    # 分组2: 收尾
    store.save_prompt('收尾', None, Prompt(
        description='标准收尾',
        content='执行收尾协议。',
        created_at=now,
    ))
    store.save_prompt('收尾', None, Prompt(
        description='快速收尾',
        content='快速收尾。',
        created_at=now,
    ))
    return store


# ══════════════════════════════════════════════════════════════
# DT-01 · Prompt v3 数据模型（🟢强档 · 4 断言）
# ══════════════════════════════════════════════════════════════

class TestDT01PromptV3Model:
    """验证 Prompt v3 数据模型结构正确。"""

    def test_prompt_has_only_three_fields(self):
        """✅ Prompt 数据类仅有 description、content、created_at 三个字段。"""
        from dataclasses import fields
        field_names = {f.name for f in fields(Prompt)}
        assert field_names == {'description', 'content', 'created_at'}

    def test_prompt_no_category_field(self):
        """✅ Prompt 无 category 字段。"""
        assert not hasattr(Prompt, 'category') or 'category' not in {
            f.name for f in Prompt.__dataclass_fields__.values()}

    def test_prompt_no_versions_field(self):
        """✅ Prompt 无 versions 字段。"""
        from dataclasses import fields
        field_names = {f.name for f in fields(Prompt)}
        assert 'versions' not in field_names

    def test_prompt_docstring_updated_to_v3(self):
        """✅ Prompt docstring 已更新为 v3 描述。"""
        doc = Prompt.__doc__ or ''
        assert 'v3' in doc.lower() or '极简' in doc


# ══════════════════════════════════════════════════════════════
# DT-02 · 分组扫描（🔵中档 · 4 断言）
# ══════════════════════════════════════════════════════════════

class TestDT02GetGroups:
    """验证 get_groups() 分组扫描正确。"""

    def test_get_groups_returns_sorted_subdirs(self, populated_store):
        """✅ get_groups() 返回字母排序的分组列表。"""
        groups = populated_store.get_groups()
        assert groups == ['开局', '收尾']

    def test_get_groups_nonexistent_dir_returns_empty(self, tmp_path):
        """✅ prompts/ 目录不存在 → 返回 []。"""
        s = PromptStore(str(tmp_path / 'nonexistent'))
        assert s.get_groups() == []

    def test_get_groups_empty_dir_returns_empty(self, store):
        """✅ prompts/ 存在但无子目录 → 返回 []。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        assert store.get_groups() == []

    def test_get_groups_excludes_hidden_dirs(self, store):
        """✅ 隐藏目录（以 . 开头）被排除。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        (store.prompts_dir / '.versions').mkdir()
        (store.prompts_dir / '开局').mkdir()
        groups = store.get_groups()
        assert '.versions' not in groups
        assert '开局' in groups


# ══════════════════════════════════════════════════════════════
# DT-03 · 提示词文件读写（🟢强档 · 19 断言）
# ══════════════════════════════════════════════════════════════

class TestDT03aSanitizeFilename:
    """验证文件名 sanitize。"""

    def test_sanitize_normal_description(self):
        """✅ _sanitize_filename('标准开局 — 协议') → '标准开局 — 协议.md'。"""
        result = PromptStore._sanitize_filename('标准开局 — 协议')
        assert result == '标准开局 — 协议.md'

    def test_sanitize_removes_illegal_chars(self):
        """✅ _sanitize_filename('a<b>:c') → 'abc.md'（非法字符去除）。"""
        result = PromptStore._sanitize_filename('a<b>:c')
        assert result == 'abc.md'

    def test_sanitize_empty_input_fallback(self):
        """✅ _sanitize_filename('   ') → 'untitled.md'（空输入回退）。"""
        result = PromptStore._sanitize_filename('   ')
        assert result == 'untitled.md'


class TestDT03bLoadPrompt:
    """验证 load_prompt() 读取正确。"""

    def test_load_prompt_parses_frontmatter(self, populated_store):
        """✅ load_prompt() 正确解析 YAML frontmatter。"""
        prompt = populated_store.load_prompt('开局', '标准开局 — 标准CSF开局协议.md')
        assert prompt is not None
        assert prompt.description == '标准开局 — 标准CSF开局协议'
        assert prompt.created_at  # 非空
        assert 'created_at' not in ('', None)

    def test_load_prompt_extracts_body(self, populated_store):
        """✅ load_prompt() 正确提取正文（frontmatter 之后的内容）。"""
        prompt = populated_store.load_prompt('开局', '标准开局 — 标准CSF开局协议.md')
        assert prompt is not None
        assert '阅读 cos-context' in prompt.content

    def test_load_prompt_no_frontmatter_fallback(self, store):
        """✅ load_prompt() 对无 frontmatter 文件做兼容处理。"""
        group_dir = store.prompts_dir / '旧格式'
        group_dir.mkdir(parents=True)
        (group_dir / '旧提示词.md').write_text('纯正文内容', encoding='utf-8')

        prompt = store.load_prompt('旧格式', '旧提示词.md')
        assert prompt is not None
        assert prompt.description == '旧提示词'  # 文件名去后缀
        assert '纯正文内容' in prompt.content

    def test_load_prompt_not_found_returns_none(self, store):
        """✅ load_prompt() 文件不存在 → 返回 None。"""
        prompt = store.load_prompt('开局', '不存在.md')
        assert prompt is None


class TestDT03cSavePrompt:
    """验证 save_prompt() 原子保存。"""

    def test_save_new_prompt_creates_file(self, store):
        """✅ save_prompt() 新建提示词 → 文件正确创建。"""
        now = datetime.now(timezone.utc).isoformat()
        filename = store.save_prompt('开局', None, Prompt(
            description='标准开局',
            content='阅读上下文，开局。',
            created_at=now,
        ))
        assert filename == '标准开局.md'
        path = store.prompts_dir / '开局' / '标准开局.md'
        assert path.is_file()

    def test_save_prompt_content_has_frontmatter_and_body(self, store):
        """✅ save_prompt() 文件内容含 frontmatter+正文。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('开局', None, Prompt(
            description='测试提示词',
            content='正文内容',
            created_at=now,
        ))
        path = store.prompts_dir / '开局' / '测试提示词.md'
        text = path.read_text(encoding='utf-8')
        assert text.startswith('---')
        assert 'description: 测试提示词' in text
        assert 'created_at:' in text
        assert '正文内容' in text

    def test_save_edit_existing_no_rename(self, store):
        """✅ save_prompt() 编辑已有提示词（不改名）→ 文件正确更新。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('开局', None, Prompt(
            description='测试',
            content='第一版',
            created_at=now,
        ))
        store.save_prompt('开局', '测试.md', Prompt(
            description='测试',
            content='第二版更新',
            created_at=now,
        ))
        text = (store.prompts_dir / '开局' / '测试.md').read_text(encoding='utf-8')
        assert '第二版更新' in text

    def test_save_rename_deletes_old_file(self, store):
        """✅ save_prompt() 改名保存 → 新文件创建，旧文件删除。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('开局', None, Prompt(
            description='旧名称',
            content='内容',
            created_at=now,
        ))
        new_filename = store.save_prompt('开局', '旧名称.md', Prompt(
            description='新名称',
            content='新内容',
            created_at=now,
        ))
        assert new_filename == '新名称.md'
        assert (store.prompts_dir / '开局' / '新名称.md').is_file()
        assert not (store.prompts_dir / '开局' / '旧名称.md').exists()

    def test_save_rename_conflict_raises_error(self, store):
        """✅ save_prompt() 改名保存时新文件名冲突 → raise FileExistsError。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('开局', None, Prompt(
            description='A提示词',
            content='AAA',
            created_at=now,
        ))
        store.save_prompt('开局', None, Prompt(
            description='B提示词',
            content='BBB',
            created_at=now,
        ))
        with pytest.raises(FileExistsError):
            store.save_prompt('开局', 'A提示词.md', Prompt(
                description='B提示词',  # 冲突！
                content='XXX',
                created_at=now,
            ))

    def test_save_creates_group_dir(self, store):
        """✅ save_prompt() 分组目录不存在 → 自动创建。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('新分组', None, Prompt(
            description='新提示词',
            content='内容',
            created_at=now,
        ))
        assert (store.prompts_dir / '新分组').is_dir()

    def test_save_no_group_field_in_frontmatter(self, store):
        """✅ save_prompt() frontmatter 中不含 group/category 字段。"""
        now = datetime.now(timezone.utc).isoformat()
        store.save_prompt('开局', None, Prompt(
            description='测试',
            content='正文',
            created_at=now,
        ))
        text = (store.prompts_dir / '开局' / '测试.md').read_text(encoding='utf-8')
        assert 'group:' not in text
        assert 'category:' not in text


class TestDT03dDeletePrompt:
    """验证 delete_prompt() 删除正确。"""

    def test_delete_success_returns_true(self, populated_store):
        """✅ delete_prompt() 删除文件成功 → 返回 True。"""
        result = populated_store.delete_prompt('开局', '标准开局 — 标准CSF开局协议.md')
        assert result is True

    def test_delete_not_found_returns_false(self, store):
        """✅ delete_prompt() 文件不存在 → 返回 False。"""
        result = store.delete_prompt('开局', '不存在.md')
        assert result is False

    def test_delete_empty_dir_not_removed(self, populated_store):
        """✅ delete_prompt() 删除后空目录不自动删除。"""
        # 先确保分组下只有一个文件
        populated_store.delete_prompt('收尾', '标准收尾.md')
        populated_store.delete_prompt('收尾', '快速收尾.md')
        assert (populated_store.prompts_dir / '收尾').is_dir()


class TestDT03eListPrompts:
    """验证 list_prompts() 列表正确。"""

    def test_list_prompts_returns_sorted_by_description(self, populated_store):
        """✅ list_prompts() 返回按 description 排序的列表。"""
        items = populated_store.list_prompts('开局')
        assert len(items) == 2
        assert items[0]['description'] < items[1]['description']

    def test_list_prompts_no_content_field(self, populated_store):
        """✅ list_prompts() 不含正文 content。"""
        items = populated_store.list_prompts('开局')
        assert len(items) > 0
        for item in items:
            assert 'content' not in item
            assert 'description' in item
            assert 'filename' in item
            assert 'group' in item
            assert 'created_at' in item

    def test_list_prompts_nonexistent_group_returns_empty(self, store):
        """✅ list_prompts() 不存在的分组 → 返回 []。"""
        assert store.list_prompts('不存在') == []


class TestDT03fLoadAllPrompts:
    """验证 load_all_prompts() 全量读取。"""

    def test_load_all_prompts_returns_all(self, populated_store):
        """✅ load_all_prompts() 返回全部提示词。"""
        all_p = populated_store.load_all_prompts()
        assert len(all_p) == 4

    def test_load_all_prompts_includes_content(self, populated_store):
        """✅ load_all_prompts() 含正文。"""
        all_p = populated_store.load_all_prompts()
        for p in all_p:
            assert isinstance(p, Prompt)
            assert p.content  # 非空


# ══════════════════════════════════════════════════════════════
# DT-04 · _favorites.json 管理（🔵中档 · 9 断言）
# ══════════════════════════════════════════════════════════════

class TestDT04Favorites:
    """验证 _favorites.json 收藏管理。"""

    def test_get_favorites_no_file_returns_empty(self, store):
        """✅ get_favorites() 文件不存在 → 返回 []。"""
        assert store.get_favorites() == []

    def test_get_favorites_corrupted_returns_empty(self, store):
        """✅ get_favorites() 格式损坏 → 返回 []。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        (store.prompts_dir / '_favorites.json').write_text('这不是JSON', encoding='utf-8')
        assert store.get_favorites() == []

    def test_add_favorite_saves_correctly(self, store):
        """✅ add_favorite() 添加新收藏 → _favorites.json 更新正确。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '标准开局.md')
        favs = store.get_favorites()
        assert '开局/标准开局' in favs

        # 验证文件内容
        data = json.loads(
            (store.prompts_dir / '_favorites.json').read_text(encoding='utf-8'))
        assert '开局/标准开局' in data

    def test_add_favorite_idempotent(self, store):
        """✅ add_favorite() 重复添加 → 幂等无重复。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '标准开局.md')
        store.add_favorite('开局', '标准开局.md')
        store.add_favorite('开局', '标准开局.md')
        favs = store.get_favorites()
        assert favs.count('开局/标准开局') == 1

    def test_remove_favorite_existing(self, store):
        """✅ remove_favorite() 移除存在的收藏 → 正确移除。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '标准开局.md')
        store.add_favorite('收尾', '快速收尾.md')
        store.remove_favorite('开局', '标准开局.md')
        favs = store.get_favorites()
        assert '开局/标准开局' not in favs
        assert '收尾/快速收尾' in favs

    def test_remove_favorite_nonexistent_noop(self, store):
        """✅ remove_favorite() 移除不存在的收藏 → 无操作。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '标准开局.md')
        store.remove_favorite('收尾', '不存在.md')
        assert store.get_favorites() == ['开局/标准开局']

    def test_update_favorite_path_existing(self, store):
        """✅ update_favorite_path() 旧路径存在 → 更新为新路径。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '旧名称.md')
        store.update_favorite_path('开局', '旧名称.md', '开局', '新名称.md')
        favs = store.get_favorites()
        assert '开局/旧名称' not in favs
        assert '开局/新名称' in favs

    def test_update_favorite_path_nonexistent_noop(self, store):
        """✅ update_favorite_path() 旧路径不存在 → 无操作。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.add_favorite('开局', '标准开局.md')
        before = store.get_favorites().copy()
        store.update_favorite_path('收尾', '不存在.md', '开局', '新.md')
        assert store.get_favorites() == before

    def test_save_favorites_atomic_write(self, store):
        """✅ save_favorites() 使用原子写（验证无 .tmp 残留）。"""
        store.prompts_dir.mkdir(parents=True, exist_ok=True)
        store.save_favorites(['开局/测试1', '收尾/测试2'])
        # 验证文件内容正确
        favs = store.get_favorites()
        assert len(favs) == 2
        # 验证无 .tmp 残留
        tmp_files = list(store.prompts_dir.glob('*.tmp'))
        assert len(tmp_files) == 0
