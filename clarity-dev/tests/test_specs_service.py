"""
SpecsService 测试 — IT-08-V2 DT-01~11。

≥18条测试：文件树/打开/保存/版本/删除/新建/说明/基线。
使用真实 FileSystemOps + BackupEngine 指向临时目录。
"""

import json
import pytest
from pathlib import Path

from src.core.file_system_ops import FileSystemOps
from src.core.backup_engine import BackupEngine
from src.service.specs_service import SpecsService, COS_CONTEXT_WARNING


# ── 测试夹具 ──────────────────────────────────────────────

@pytest.fixture
def service(tmp_path):
    """创建指向临时目录的 SpecsService 实例，含预置出厂文件。"""
    lite = tmp_path / 'csf-lite'
    clarity = tmp_path / 'csf-clarity'
    backups = clarity / 'backups'
    for d in [lite / 'core', lite / 'protocols', lite / 'workspace',
              clarity, backups]:
        d.mkdir(parents=True, exist_ok=True)

    # 创建预置出厂文件
    (lite / 'core' / '守则.md').write_text('# 守则\n\n内容A', encoding='utf-8')
    (lite / 'core' / '协作规范.md').write_text('# 协作规范\n\n内容B', encoding='utf-8')
    (lite / 'cos-context.md').write_text('# context\n\n内容C', encoding='utf-8')
    (lite / 'README.md').write_text('# README', encoding='utf-8')
    (lite / 'workspace' / '用户文件.md').write_text('# 用户内容', encoding='utf-8')

    fs = FileSystemOps(str(lite), str(clarity))
    backup = BackupEngine(fs, str(clarity / 'sections'), str(backups))

    return SpecsService(fs, backup, str(lite), str(clarity))


def _write_factory_file(lite: Path, rel_path: str, content: str):
    """辅助：在 csf-lite/ 下写入文件。"""
    p = lite / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


# ═══════════════════════════════════════════════════════════
# DT-01: __init__
# ═══════════════════════════════════════════════════════════

class TestInit:
    def test_init_loads_empty_file_meta(self, tmp_path):
        """DT-01: file_meta.json 不存在 → 空 dict"""
        lite = tmp_path / 'csf-lite2'
        clarity = tmp_path / 'csf-clarity2'
        lite.mkdir()
        clarity.mkdir()
        (clarity / 'backups').mkdir()
        fs = FileSystemOps(str(lite), str(clarity))
        backup = BackupEngine(fs, str(clarity / 'sections'),
                              str(clarity / 'backups'))
        svc = SpecsService(fs, backup, str(lite), str(clarity))
        assert svc._file_meta == {}

    def test_init_loads_file_meta(self, tmp_path):
        """DT-01: file_meta.json 存在 → 正确加载"""
        lite = tmp_path / 'csf-lite3'
        clarity = tmp_path / 'csf-clarity3'
        lite.mkdir()
        clarity.mkdir()
        (clarity / 'backups').mkdir()
        (clarity / 'file_meta.json').write_text(
            '{"core/守则.md": "最高纲领"}', encoding='utf-8')
        fs = FileSystemOps(str(lite), str(clarity))
        backup = BackupEngine(fs, str(clarity / 'sections'),
                              str(clarity / 'backups'))
        svc = SpecsService(fs, backup, str(lite), str(clarity))
        assert svc._file_meta == {'core/守则.md': '最高纲领'}


# ═══════════════════════════════════════════════════════════
# DT-02: get_file_tree
# ═══════════════════════════════════════════════════════════

class TestGetFileTree:
    def test_tree_has_core_dir(self, service):
        """DT-02: 文件树包含 core/ 目录"""
        tree = service.get_file_tree()
        children_names = [c.name for c in tree.children]
        assert 'core' in children_names

    def test_factory_file_marked(self, service):
        """DT-02: 出厂文件 is_factory=True"""
        tree = service.get_file_tree()

        def find_node(node, name):
            if node.name == name and not node.is_dir:
                return node
            for c in node.children:
                found = find_node(c, name)
                if found:
                    return found
            return None

        node = find_node(tree, '守则.md')
        assert node is not None
        assert node.is_factory is True

    def test_user_file_not_factory(self, service):
        """DT-02: 用户文件 is_factory=False"""
        tree = service.get_file_tree()

        def find_node(node, name):
            if node.name == name and not node.is_dir:
                return node
            for c in node.children:
                found = find_node(c, name)
                if found:
                    return found
            return None

        node = find_node(tree, '用户文件.md')
        assert node is not None
        assert node.is_factory is False

    def test_cos_context_has_warning(self, service):
        """DT-02: cos-context.md description 含特殊警告"""
        tree = service.get_file_tree()

        def find_node(node, name):
            if node.name == name and not node.is_dir:
                return node
            for c in node.children:
                found = find_node(c, name)
                if found:
                    return found
            return None

        node = find_node(tree, 'cos-context.md')
        assert node is not None
        assert node.description == COS_CONTEXT_WARNING


# ═══════════════════════════════════════════════════════════
# DT-03: open_file
# ═══════════════════════════════════════════════════════════

class TestOpenFile:
    def test_returns_correct_fields(self, service):
        """DT-03: open_file 返回 content/description/is_factory/path"""
        result = service.open_file('core/守则.md')
        assert result['content'] == '# 守则\n\n内容A'
        assert result['is_factory'] is True
        assert result['path'] == 'core/守则.md'

    def test_not_found_raises(self, service):
        """DT-03: 文件不存在 → FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            service.open_file('core/不存在.md')


# ═══════════════════════════════════════════════════════════
# DT-04: save_file
# ═══════════════════════════════════════════════════════════

class TestSaveFile:
    def test_roundtrip(self, service):
        """DT-04: save → open 验证内容一致"""
        service.save_file('workspace/用户文件.md', '新内容')
        result = service.open_file('workspace/用户文件.md')
        assert result['content'] == '新内容'


# ═══════════════════════════════════════════════════════════
# DT-05: save_new_version
# ═══════════════════════════════════════════════════════════

class TestSaveNewVersion:
    def test_creates_version(self, service):
        """DT-05: save_new_version 返回 VersionMeta"""
        vm = service.save_new_version(
            'workspace/用户文件.md', 'v2内容', '第二次修改')
        assert vm.version >= 1
        assert vm.target_type == 'file'

    def test_empty_description_uses_fallback(self, service):
        """DT-05: description 为空 → 自动取正文摘要（v4: 不再抛异常）"""
        vm = service.save_new_version('workspace/用户文件.md', '内容', '')
        assert vm.version >= 1
        vm2 = service.save_new_version('workspace/用户文件.md', '内容', '  ')
        assert vm2.version >= 2

    def test_content_updated(self, service):
        """DT-05: save_new_version 后文件内容已更新"""
        service.save_new_version('workspace/用户文件.md', 'v2内容', '改版')
        result = service.open_file('workspace/用户文件.md')
        assert result['content'] == 'v2内容'


# ═══════════════════════════════════════════════════════════
# DT-06: new_file
# ═══════════════════════════════════════════════════════════

class TestNewFile:
    def test_creates_file_and_meta(self, service):
        """DT-06: new_file 创建文件 + file_meta 注册（v4: 键为规则名）"""
        service.new_file('workspace/test.md', 'hello')
        result = service.open_file('workspace/test.md')
        assert result['content'] == 'hello'
        # file_meta 已注册空说明（v4: 键为规则名）
        assert 'test' in service._file_meta

    def test_default_empty_content(self, service):
        """DT-06: 默认空内容"""
        service.new_file('workspace/empty.md')
        result = service.open_file('workspace/empty.md')
        assert result['content'] == ''


# ═══════════════════════════════════════════════════════════
# DT-07: delete_file
# ═══════════════════════════════════════════════════════════

class TestDeleteFile:
    def test_deletes_user_file(self, service):
        """DT-07: 删除用户文件成功"""
        service.new_file('workspace/to_delete.md', 'bye')
        service.delete_file('workspace/to_delete.md')
        with pytest.raises(FileNotFoundError):
            service.open_file('workspace/to_delete.md')

    def test_factory_file_raises(self, service):
        """DT-07: 出厂文件不可删除 → ValueError"""
        with pytest.raises(ValueError, match='出厂文件不可删除'):
            service.delete_file('core/守则.md')

    def test_not_found_raises(self, service):
        """DT-07: 文件不存在 → FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            service.delete_file('workspace/不存在.md')

    def test_cleans_file_meta(self, service):
        """DT-07: 删除后 file_meta 清理（v4: 键为规则名）"""
        service.new_file('workspace/clean_me.md', 'x')
        assert 'clean_me' in service._file_meta
        service.delete_file('workspace/clean_me.md')
        assert 'clean_me' not in service._file_meta


# ═══════════════════════════════════════════════════════════
# DT-08: get_version_history
# ═══════════════════════════════════════════════════════════

class TestGetVersionHistory:
    def test_empty_for_new_file(self, service):
        """DT-08: 新文件无版本历史"""
        history = service.get_version_history('workspace/用户文件.md')
        assert history == []

    def test_returns_versions_after_save(self, service):
        """DT-08: save_new_version 后版本历史非空"""
        service.save_new_version('workspace/用户文件.md', 'v1', '首次')
        service.save_new_version('workspace/用户文件.md', 'v2', '第二次')
        history = service.get_version_history('workspace/用户文件.md')
        assert len(history) >= 2


# ═══════════════════════════════════════════════════════════
# DT-09: restore_version
# ═══════════════════════════════════════════════════════════

class TestRestoreVersion:
    def test_restores_content(self, service):
        """DT-09: restore_version 返回版本内容（纯正文，无frontmatter）"""
        vm = service.save_new_version(
            'workspace/用户文件.md', '原始内容', '第一个版本')
        restored = service.restore_version(vm.storage_path)
        assert restored == '原始内容'


# ═══════════════════════════════════════════════════════════
# DT-10: create_global_baseline
# ═══════════════════════════════════════════════════════════

class TestCreateGlobalBaseline:
    def test_returns_dict(self, service):
        """DT-10: create_global_baseline 返回 dict（v4: 移除 note 参数）"""
        result = service.create_global_baseline('v1-测试')
        assert result['name'] == 'v1-测试'
        assert 'created_at' in result


# ═══════════════════════════════════════════════════════════
# DT-11: update_file_description
# ═══════════════════════════════════════════════════════════

class TestUpdateFileDescription:
    def test_updates_and_persists(self, service):
        """DT-11: update_file_description 更新内存 + 持久化（v4: 键为规则名）"""
        service.update_file_description('core/守则.md', 'CSF最高纲领')
        # 内存中已更新
        assert service._file_meta['守则'] == 'CSF最高纲领'
        # 重新加载验证持久化
        meta_path = service.csf_clarity_dir / 'file_meta.json'
        saved = json.loads(meta_path.read_text('utf-8'))
        assert saved['守则'] == 'CSF最高纲领'

    def test_new_description(self, service):
        """DT-11: 为新文件添加说明（v4: 键为规则名）"""
        service.update_file_description('workspace/用户文件.md', '我的笔记')
        assert service._file_meta['用户文件'] == '我的笔记'


# ═══════════════════════════════════════════════════════════
# DT-20: save_new_version 支持 description + new_file 智能目录
# ═══════════════════════════════════════════════════════════

class TestSaveNewVersionDescription:
    def test_description_written_to_backup_yaml(self, service):
        """DT-20: save_new_version 将 description 写入备份 YAML（v4: note已移除）"""
        vm = service.save_new_version(
            'workspace/用户文件.md', 'v2内容', '这是第二版，补充了细节')
        assert vm.description == '这是第二版，补充了细节'
        # 验证 YAML 中确实写入了 description
        import yaml
        backup_text = Path(vm.storage_path).read_text(encoding='utf-8')
        fm, _ = service.backup._parse_frontmatter(backup_text)
        assert fm.get('description') == '这是第二版，补充了细节'

    def test_description_empty_default(self, service):
        """DT-20: description 默认空字符串"""
        vm = service.save_new_version(
            'workspace/用户文件.md', 'v3内容', '无说明版本')
        assert vm.description == '无说明版本'

    def test_description_syncs_file_meta(self, service):
        """DT-20: 保存后 description 同步更新 file_meta（v4: 键为规则名）"""
        service.save_new_version(
            'workspace/用户文件.md', 'v4内容', '新说明')
        assert service._file_meta.get('用户文件') == '新说明'


class TestNewFileSmartDir:
    def test_new_file_in_subdir(self, service):
        """DT-20: new_file 支持 parent_dir 创建在子目录"""
        rel_path = service.new_file(
            '子文件.md', content='子目录内容', parent_dir='workspace/')
        assert rel_path == 'workspace/子文件.md'
        result = service.open_file('workspace/子文件.md')
        assert result['content'] == '子目录内容'
        assert '子文件' in service._file_meta

    def test_new_file_in_root_when_no_parent(self, service):
        """DT-20: parent_dir 为空时创建在根目录"""
        rel_path = service.new_file('根文件.md', parent_dir='')
        assert rel_path == '根文件.md'
        result = service.open_file('根文件.md')
        assert result['content'] == ''

    def test_new_file_returns_correct_path(self, service):
        """DT-20: new_file 返回完整相对路径"""
        rel_path = service.new_file(
            'nested.md', parent_dir='workspace/')
        assert 'nested.md' in rel_path
        assert rel_path.startswith('workspace/')


class TestOpenFileReturnsIsFactory:
    def test_is_factory_true_for_factory_file(self, service):
        """DT-20: open_file 对出厂文件返回 is_factory=True"""
        result = service.open_file('core/守则.md')
        assert result['is_factory'] is True

    def test_is_factory_false_for_user_file(self, service):
        """DT-20: open_file 对用户文件返回 is_factory=False"""
        result = service.open_file('workspace/用户文件.md')
        assert result['is_factory'] is False


# ═══════════════════════════════════════════════════════════
# 代码质量检查
# ═══════════════════════════════════════════════════════════

class TestCodeQuality:
    def test_no_sqlite_in_specs_service(self):
        """IT-08: SpecsService 不含 sqlite3"""
        import inspect
        from src.service import specs_service as mod
        source = inspect.getsource(mod)
        assert 'sqlite3' not in source
        assert 'import sqlite' not in source
        assert '.db' not in source


# ═══════════════════════════════════════════════════════════
# IT-03e DT-01: search_files 全文搜索
# ═══════════════════════════════════════════════════════════

class TestSearchFiles:
    def test_search_matches_content(self, service):
        """DT-01: 搜索"守则"返回含 core/守则.md 的列表"""
        results = service.search_files('守则')
        assert 'core/守则.md' in results

    def test_search_nonexistent_returns_empty(self, service):
        """DT-01: 搜索不存在的字符串返回空列表"""
        results = service.search_files('xyznonexist')
        assert results == []

    def test_search_empty_query_returns_empty(self, service):
        """DT-01: 空 query 返回空列表"""
        results = service.search_files('')
        assert results == []

    def test_search_whitespace_query_returns_empty(self, service):
        """DT-01: 纯空白 query 返回空列表"""
        results = service.search_files('   ')
        assert results == []

    def test_search_case_insensitive(self, service):
        """DT-01: 搜索不区分大小写"""
        results_lower = service.search_files('readme')
        results_upper = service.search_files('README')
        assert results_lower == results_upper
        assert len(results_lower) > 0

    def test_search_multiple_matches(self, service):
        """DT-01: 搜索"内容"匹配多个文件"""
        results = service.search_files('内容')
        # 内容A/B/C/用户内容 都含"内容"
        assert len(results) >= 3
        assert 'core/守则.md' in results
        assert 'workspace/用户文件.md' in results

    def test_search_results_sorted(self, service):
        """DT-01: 搜索结果按路径排序"""
        results = service.search_files('内容')
        assert results == sorted(results)
