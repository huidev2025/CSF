"""
FileSystemOps 测试 — IT-03-V2 DT-01~06。

≥10条测试：读写/原子写入/目录树/staging/路径解析。
"""

import pytest
from pathlib import Path

from src.core.file_system_ops import FileSystemOps
from src.core.models import TreeNode


@pytest.fixture
def fs(tmp_path):
    """创建指向临时目录的 FileSystemOps 实例。"""
    lite = tmp_path / 'csf-lite'
    clarity = tmp_path / 'csf-clarity'
    lite.mkdir()
    clarity.mkdir()
    return FileSystemOps(str(lite), str(clarity))


# ── DT-02: read_file ──────────────────────────────────────

class TestReadFile:
    def test_read_existing(self, fs, tmp_path):
        """DT-02: 读已存在的文件"""
        f = tmp_path / 'csf-lite' / 'test.md'
        f.write_text('hello', encoding='utf-8')
        assert fs.read_file('test.md') == 'hello'

    def test_read_not_found(self, fs):
        """DT-02: 文件不存在 → FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            fs.read_file('nonexistent.md')


# ── DT-03: write_file ─────────────────────────────────────

class TestWriteFile:
    def test_write_and_read_roundtrip(self, fs):
        """DT-03: 写→读 roundtrip"""
        fs.write_file('roundtrip.md', 'hello world')
        assert fs.read_file('roundtrip.md') == 'hello world'

    def test_write_creates_parent_dirs(self, fs, tmp_path):
        """DT-03: 自动创建父目录"""
        fs.write_file('sub/deep/file.txt', 'content')
        assert (tmp_path / 'csf-lite' / 'sub' / 'deep' / 'file.txt').exists()

    def test_write_overwrites(self, fs):
        """DT-03: 覆盖写入"""
        fs.write_file('over.md', 'v1')
        fs.write_file('over.md', 'v2')
        assert fs.read_file('over.md') == 'v2'

    def test_write_utf8(self, fs):
        """DT-03: UTF-8 中文写入"""
        fs.write_file('中文.md', '你好世界')
        assert fs.read_file('中文.md') == '你好世界'

    def test_write_no_tmp_leftover(self, fs, tmp_path):
        """DT-03: 原子写入后无 .tmp 残留"""
        fs.write_file('atomic.md', 'data')
        leftovers = list((tmp_path / 'csf-lite').glob('*.tmp'))
        assert len(leftovers) == 0


# ── DT-04: ensure_dir ─────────────────────────────────────

class TestEnsureDir:
    def test_create_dir(self, fs, tmp_path):
        """DT-04: 创建目录"""
        fs.ensure_dir('newdir')
        assert (tmp_path / 'csf-lite' / 'newdir').is_dir()

    def test_ensure_existing_dir_no_error(self, fs, tmp_path):
        """DT-04: 确保已存在目录不报错"""
        (tmp_path / 'csf-lite' / 'existing').mkdir()
        fs.ensure_dir('existing')  # 不应抛异常


# ── DT-05: list_tree ──────────────────────────────────────

class TestListTree:
    @pytest.fixture
    def tree_dir(self, fs, tmp_path):
        """创建含文件和子目录的测试目录树。"""
        root = tmp_path / 'csf-lite' / 'testroot'
        root.mkdir()
        (root / 'readme.md').write_text('readme')
        (root / 'config.json').write_text('{}')
        sub = root / 'subdir'
        sub.mkdir()
        (sub / 'notes.md').write_text('notes')
        (sub / '.versions').mkdir()  # 应被排除
        (sub / '.versions' / 'x.v1.md').write_text('x')
        (sub / '.hidden').write_text('hidden')  # 应被排除
        return root

    def test_tree_structure(self, fs, tree_dir):
        """DT-05: 目录树结构正确"""
        tree = fs.list_tree(str(tree_dir))
        assert tree.is_dir is True
        assert len(tree.children) == 3  # readme.md, config.json, subdir（排除.git等）

        names = [c.name for c in tree.children]
        assert 'readme.md' in names
        assert 'subdir' in names

    def test_tree_file_node(self, fs, tree_dir):
        """DT-05: 文件节点 is_dir=False"""
        tree = fs.list_tree(str(tree_dir))
        for child in tree.children:
            if child.name == 'readme.md':
                assert child.is_dir is False
                assert child.children == []

    def test_tree_dir_node(self, fs, tree_dir):
        """DT-05: 目录节点含子节点"""
        tree = fs.list_tree(str(tree_dir))
        for child in tree.children:
            if child.name == 'subdir':
                assert child.is_dir is True
                # .versions 和 .hidden 被排除，只剩 notes.md
                sub_names = [c.name for c in child.children]
                assert '.versions' not in sub_names
                assert '.hidden' not in sub_names

    def test_tree_excludes_hidden(self, fs, tree_dir):
        """DT-05: 排除隐藏文件和 .versions/"""
        tree = fs.list_tree(str(tree_dir))
        all_names = set()
        def collect(n):
            all_names.add(n.name)
            for c in n.children:
                collect(c)
        collect(tree)
        assert '.hidden' not in all_names
        assert '.versions' not in all_names


# ── DT-06: Staging 操作 ───────────────────────────────────

class TestStaging:
    def test_write_and_read_staging(self, fs):
        """DT-06: write_staging → read_staging 一致"""
        content = '# staging\nstatus: pending\n'
        fs.write_staging(content)
        assert fs.read_staging() == content

    def test_delete_staging(self, fs):
        """DT-06: delete_staging → read_staging FileNotFoundError"""
        fs.write_staging('test')
        fs.delete_staging()
        with pytest.raises(FileNotFoundError):
            fs.read_staging()


# ── 路径解析 ──────────────────────────────────────────────

class TestPathResolution:
    def test_absolute_path(self, fs, tmp_path):
        """绝对路径直接使用"""
        abs_path = tmp_path / 'absolute.md'
        abs_path.write_text('abs')
        assert fs.read_file(str(abs_path)) == 'abs'

    def test_relative_path_resolves_to_csf_lite(self, fs, tmp_path):
        """相对路径拼接到 csf_lite_root"""
        (tmp_path / 'csf-lite' / 'rel.md').write_text('rel')
        assert fs.read_file('rel.md') == 'rel'
