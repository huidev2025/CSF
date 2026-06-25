"""
BackupEngine 测试 — IT-03-V2 DT-07~14。

≥15条测试：段版本/文件备份/版本扫描/恢复/基线。
所有测试用临时目录，不污染真实 csf-clarity/ / csf-lite/。
"""

import os
import pytest
from pathlib import Path

from src.core.file_system_ops import FileSystemOps
from src.core.backup_engine import BackupEngine
from src.core.models import VersionMeta


@pytest.fixture
def engine(tmp_path):
    """创建指向临时目录的 BackupEngine 实例。"""
    lite = tmp_path / 'csf-lite'
    clarity = tmp_path / 'csf-clarity'
    sections = clarity / 'sections'
    backups = clarity / 'backups'
    lite.mkdir()
    clarity.mkdir()
    sections.mkdir()
    backups.mkdir()
    (sections / '.versions').mkdir()

    fs = FileSystemOps(str(lite), str(clarity))
    engine = BackupEngine(fs, str(sections), str(backups))
    return engine


def _read_raw(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')


# ── DT-08: save_section_version ───────────────────────────

class TestSectionVersion:
    def test_first_save_v1(self, engine):
        """DT-08: 首次保存 → version=1"""
        vm = engine.save_section_version(
            '项目背景', '# 背景\n内容', '初始版本')
        assert vm.version == 1
        assert vm.target_type == 'section'
        assert vm.target_id == '项目背景'
        assert vm.description == '初始版本'
        assert '.v1.md' in vm.storage_path

    def test_sequential_saves_increment(self, engine):
        """DT-08: 连续保存3次 → v1, v2, v3"""
        v1 = engine.save_section_version('任务窗口', '# B', 'v1')
        v2 = engine.save_section_version('任务窗口', '# B2', 'v2')
        v3 = engine.save_section_version('任务窗口', '# B3', 'v3')
        assert v1.version == 1
        assert v2.version == 2
        assert v3.version == 3

    def test_version_file_content_has_frontmatter(self, engine):
        """DT-08: 版本文件含正确的 YAML frontmatter"""
        vm = engine.save_section_version('背景', '# 内容', '测试备注')
        text = _read_raw(vm.storage_path)
        assert text.startswith('---')
        assert 'section_id: 背景' in text
        assert 'version: 1' in text
        assert 'description: 测试备注' in text
        assert 'baselines:' in text
        assert '# 内容' in text

    def test_versions_dir_auto_created(self, engine):
        """DT-08: .versions 目录自动创建"""
        vm = engine.save_section_version('新段', '# X', 'n')
        assert '.versions' in vm.storage_path


# ── DT-09: save_file_backup ───────────────────────────────

class TestFileBackup:
    def test_first_backup_v001(self, engine):
        """DT-09: 首次文件备份 → v001"""
        vm = engine.save_file_backup(
            'core/守则.md', '# 守则\n内容', '初始备份')
        assert vm.version == 1
        assert vm.target_type == 'file'
        assert vm.target_id == 'core/守则.md'
        assert 'v001.md' in vm.storage_path

    def test_sequential_backups_increment(self, engine):
        """DT-09: 连续备份3次 → v001, v002, v003"""
        v1 = engine.save_file_backup('x.md', 'a', '1')
        v2 = engine.save_file_backup('x.md', 'b', '2')
        v3 = engine.save_file_backup('x.md', 'c', '3')
        assert v1.version == 1
        assert v2.version == 2
        assert v3.version == 3
        assert 'v001.md' in v1.storage_path
        assert 'v002.md' in v2.storage_path
        assert 'v003.md' in v3.storage_path

    def test_path_traversal_rejected(self, engine):
        """DT-09: 含 '..' 的路径被拒绝"""
        with pytest.raises(ValueError):
            engine.save_file_backup('../secret.md', 'x', 'note')

    def test_file_backup_content(self, engine):
        """DT-09: 备份内容含 YAML frontmatter"""
        vm = engine.save_file_backup('docs/readme.md', '# README', '备份')
        text = _read_raw(vm.storage_path)
        assert 'file_path: docs/readme.md' in text
        assert 'version: 1' in text
        assert '# README' in text


# ── DT-10: scan_version_history ───────────────────────────

class TestScanHistory:
    def test_scan_returns_descending(self, engine):
        """DT-10: 扫描返回降序排列"""
        engine.save_section_version('扫描测试', 'v1', '1')
        engine.save_section_version('扫描测试', 'v2', '2')
        engine.save_section_version('扫描测试', 'v3', '3')

        history = engine.scan_version_history(
            os.path.join(engine.sections_dir, '.versions'))
        assert len(history) >= 3
        versions = [v.version for v in history if v.target_id == '扫描测试']
        assert versions == sorted(versions, reverse=True)

    def test_scan_empty_dir(self, engine):
        """DT-10: 空目录扫描返回空列表"""
        history = engine.scan_version_history(
            os.path.join(engine.sections_dir, '.versions'))
        assert history == []

    def test_scan_file_backup_dir(self, engine):
        """DT-10: 扫描文件备份目录"""
        engine.save_file_backup('core/rule.md', '# R', 'n')
        history = engine.scan_version_history(
            os.path.join(engine.backups_dir, 'files', 'core', 'rule.md'))
        assert len(history) == 1
        assert history[0].target_type == 'file'


# ── DT-11: restore_version ────────────────────────────────

class TestRestore:
    def test_restore_returns_content(self, engine):
        """DT-11: restore 返回原始内容"""
        vm = engine.save_section_version('恢复段', '# 原始\n正文', '备注')
        content = engine.restore_version(vm.storage_path)
        assert '# 原始' in content
        assert '正文' in content

    def test_restore_no_frontmatter(self, engine):
        """DT-11: restore 不包含 YAML frontmatter"""
        vm = engine.save_file_backup('clean.md', '纯内容', 'n')
        content = engine.restore_version(vm.storage_path)
        assert not content.startswith('---')


# ── DT-12: create_baseline ────────────────────────────────

class TestBaselineCreate:
    def test_create_baseline_file(self, engine):
        """DT-12: 基线清单文件已创建"""
        result = engine.create_baseline('v1-test')
        assert result['name'] == 'v1-test'
        assert result['version_count'] == 0

        path = os.path.join(engine.backups_dir, 'baselines', 'v1-test.md')
        text = _read_raw(path)
        assert 'v1-test' in text
        assert 'v1-test' in text

    def test_baseline_yaml_format(self, engine):
        """DT-12: 基线文件 YAML frontmatter 格式正确"""
        engine.create_baseline('fmt-test')
        path = os.path.join(engine.backups_dir, 'baselines', 'fmt-test.md')
        text = _read_raw(path)
        assert text.startswith('---')
        assert 'name: fmt-test' in text


# ── DT-13: add_to_baseline ────────────────────────────────

class TestAddToBaseline:
    def test_add_version_to_baseline(self, engine):
        """DT-13: 添加版本到基线"""
        vm = engine.save_section_version('基线段', '# C', '版本1')
        engine.create_baseline('mybl')
        engine.add_to_baseline('mybl', vm)

        # 验证基线文件含引用行
        path = os.path.join(engine.backups_dir, 'baselines', 'mybl.md')
        text = _read_raw(path)
        assert vm.target_id in text

    def test_baselines_field_updated(self, engine):
        """DT-13: version_meta.baselines 字段已更新"""
        vm = engine.save_section_version('段X', '# X', 'v1')
        engine.create_baseline('基线Y')
        engine.add_to_baseline('基线Y', vm)
        assert '基线Y' in vm.baselines


# ── DT-14: restore_baseline ───────────────────────────────

class TestRestoreBaseline:
    def test_restore_baseline_writes_back(self, engine, tmp_path):
        """DT-14: restore_baseline 将内容写回原文件"""
        # 先创建并备份一个文件
        orig_path = tmp_path / 'csf-lite' / 'testfile.md'
        orig_path.parent.mkdir(parents=True, exist_ok=True)
        orig_path.write_text('原始内容', encoding='utf-8')

        vm = engine.save_file_backup('testfile.md', '原始内容', '备份')
        engine.create_baseline('恢复测试')
        engine.add_to_baseline('恢复测试', vm)

        # 修改原文件
        engine.fs.write_file('testfile.md', '被修改的内容')

        # 恢复基线
        restored = engine.restore_baseline('恢复测试')
        assert 'testfile.md' in restored
        assert restored['testfile.md'] == '原始内容'

        # 验证原文件已恢复
        assert engine.fs.read_file('testfile.md') == '原始内容'


# ── 代码质量 ──────────────────────────────────────────────

class TestCodeQuality:
    def test_no_sqlite_in_backup_engine(self):
        """DT: 代码中无 sqlite3 引用"""
        import inspect
        from src.core import backup_engine as be
        source = inspect.getsource(be)
        assert 'sqlite3' not in source
        assert '.db' not in source.split('\n')[0]  # 简单的检查

    def test_no_sqlite_in_file_system_ops(self):
        """DT: 代码中无 sqlite3 引用"""
        import inspect
        from src.core import file_system_ops as fso
        source = inspect.getsource(fso)
        assert 'sqlite3' not in source
