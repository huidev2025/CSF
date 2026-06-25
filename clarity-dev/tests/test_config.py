"""
配置路径测试 — IT-01-V2 DT-12。

验证所有路径常量指向存在的目录（开发模式）。
"""

import sys
from pathlib import Path
import pytest

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class TestConfigPaths:
    """DT-12: config.py 路径常量测试"""

    def test_all_paths_are_path_objects(self):
        """验证所有路径常量是 Path 对象"""
        from src.config import (
            CSF_LITE_ROOT, CSF_CLARITY_DIR, STAGING_DIR,
            SECTIONS_DIR, TEMPLATES_DIR, PROMPTS_DIR, BACKUPS_DIR,
        )
        for name, p in [
            ('CSF_LITE_ROOT', CSF_LITE_ROOT),
            ('CSF_CLARITY_DIR', CSF_CLARITY_DIR),
            ('STAGING_DIR', STAGING_DIR),
            ('SECTIONS_DIR', SECTIONS_DIR),
            ('TEMPLATES_DIR', TEMPLATES_DIR),
            ('PROMPTS_DIR', PROMPTS_DIR),
            ('BACKUPS_DIR', BACKUPS_DIR),
        ]:
            assert isinstance(p, Path), f'{name} 应为 Path 对象，实际: {type(p)}'

    def test_csf_lite_root_exists(self):
        """验证 CSF_LITE_ROOT 指向存在的目录"""
        from src.config import CSF_LITE_ROOT
        assert CSF_LITE_ROOT.exists(), f'{CSF_LITE_ROOT} 不存在'

    def test_csf_clarity_dir_exists(self):
        """验证 CSF_CLARITY_DIR 指向存在的目录"""
        from src.config import CSF_CLARITY_DIR
        assert CSF_CLARITY_DIR.exists(), f'{CSF_CLARITY_DIR} 不存在'

    def test_staging_dir_exists(self):
        """验证 STAGING_DIR 指向存在的目录"""
        from src.config import STAGING_DIR
        assert STAGING_DIR.exists(), f'{STAGING_DIR} 不存在'

    def test_sections_dir_exists(self):
        """验证 SECTIONS_DIR 指向存在的目录"""
        from src.config import SECTIONS_DIR
        assert SECTIONS_DIR.exists(), f'{SECTIONS_DIR} 不存在'

    def test_templates_dir_exists(self):
        """验证 TEMPLATES_DIR 指向存在的目录"""
        from src.config import TEMPLATES_DIR
        assert TEMPLATES_DIR.exists(), f'{TEMPLATES_DIR} 不存在'

    def test_prompts_dir_exists(self):
        """验证 PROMPTS_DIR 指向存在的目录"""
        from src.config import PROMPTS_DIR
        assert PROMPTS_DIR.exists(), f'{PROMPTS_DIR} 不存在'

    def test_backups_dir_exists(self):
        """验证 BACKUPS_DIR 指向存在的目录"""
        from src.config import BACKUPS_DIR
        assert BACKUPS_DIR.exists(), f'{BACKUPS_DIR} 不存在'

    def test_no_db_path(self):
        """验证 config 模块中无 DB_PATH"""
        import src.config as cfg
        assert not hasattr(cfg, 'DB_PATH'), 'config 不应有 DB_PATH'

    def test_no_sqlite_import(self):
        """验证 config 模块中无 sqlite3 导入"""
        import src.config as cfg
        source = Path(cfg.__file__).read_text(encoding='utf-8')
        assert 'sqlite3' not in source, 'config.py 不应导入 sqlite3'
        assert 'index.db' not in source, 'config.py 不应引用 index.db'
