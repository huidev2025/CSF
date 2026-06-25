# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
Clarity V2 程序入口 — 完整启动流程（IT-09-V2）。

DT-01: QApplication + 依赖组装 + 三标签创建 + MainWindow
DT-06: ensure_directories() 首次运行初始化
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


# ── DT-06: 首次运行目录初始化 ─────────────────────────────

def ensure_directories():
    """DT-06: 确保 csf-clarity/ 完整目录树存在（幂等）。"""
    from src.config import CSF_CLARITY_DIR, CSF_LITE_ROOT

    clarity = Path(CSF_CLARITY_DIR)
    lite = Path(CSF_LITE_ROOT)

    # csf-clarity/ 子目录
    dirs_to_create = [
        clarity / 'sections' / '.versions',
        clarity / 'backups' / 'files',
        clarity / 'backups' / 'baselines',
        clarity / 'templates',
        clarity / 'prompts',
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

    # file_meta.json（不存在时创建空对象）
    meta_path = clarity / 'file_meta.json'
    if not meta_path.exists():
        meta_path.write_text('{}', encoding='utf-8')

    # csf-lite/staging/
    staging = lite / 'staging'
    staging.mkdir(parents=True, exist_ok=True)

    # v4 (IT-03d): 首次运行自动创建 v1-出厂基线
    baseline_path = clarity / 'backups' / 'baselines' / 'v1-出厂基线.md'
    if not baseline_path.exists():
        _create_factory_baseline(str(lite), str(clarity))


def _create_factory_baseline(csf_lite_root: str, csf_clarity_dir: str):
    """DT-08/IT-03d: 首次运行时遍历出厂文件，创建 v1-出厂基线。"""
    from src.core.file_system_ops import FileSystemOps
    from src.core.backup_engine import BackupEngine
    from src.config import SECTIONS_DIR, BACKUPS_DIR

    fs = FileSystemOps(csf_lite_root, csf_clarity_dir)
    backup = BackupEngine(fs, str(SECTIONS_DIR), str(BACKUPS_DIR))

    # 收集所有出厂文件
    tree = fs.list_tree(csf_lite_root)
    factory_files: list[str] = []

    def _collect(node):
        from src.core.models import TreeNode
        if not node.is_dir:
            # 判断是否出厂文件
            from src.service.specs_service import FACTORY_ROOTS
            for root in FACTORY_ROOTS:
                if node.path == root or (
                    root.endswith('/') and node.path.startswith(root)
                ):
                    factory_files.append(node.path)
                    break
        for child in node.children:
            _collect(child)

    _collect(tree)

    if not factory_files:
        return

    # 创建基线
    backup.create_baseline('v1-出厂基线')

    for rel_path in factory_files:
        try:
            content = fs.read_file(rel_path)
            vm = backup.save_file_backup(rel_path, content, 'v1-出厂基线')
            backup.add_to_baseline('v1-出厂基线', vm)
        except Exception:
            continue


# ── DT-01: 主入口 ─────────────────────────────────────────

VERSION = "1.1.37"


def main() -> None:
    """DT-01: 完整启动流程。"""
    from src.config import (
        CSF_LITE_ROOT, CSF_CLARITY_DIR, SECTIONS_DIR,
        TEMPLATES_DIR, PROMPTS_DIR, BACKUPS_DIR, STAGING_DIR,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Clarity")
    app.setApplicationVersion(VERSION)

    # ── 单实例检测（QLocalServer）──────────────────────
    SERVER_NAME = "ClaritySingleInstance"
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(500):
        # 已有实例运行 → 通知它闪到最前 → 静默退出
        socket.write(b"activate")
        socket.waitForBytesWritten(500)
        socket.close()
        sys.exit(0)

    _instance_server = QLocalServer()
    _instance_server.listen(SERVER_NAME)

    # DT-06: 首次运行目录检查
    ensure_directories()

    # ── Core 层 ──────────────────────────────────────────
    from src.core.sentinel_parser import SentinelParser
    from src.core.file_system_ops import FileSystemOps
    from src.core.backup_engine import BackupEngine

    sentinel = SentinelParser()
    fs = FileSystemOps(str(CSF_LITE_ROOT), str(CSF_CLARITY_DIR))
    backup = BackupEngine(fs, str(SECTIONS_DIR), str(BACKUPS_DIR))

    # ── Data 层 ──────────────────────────────────────────
    from src.data.prompt_store import PromptStore

    prompt_store = PromptStore(str(PROMPTS_DIR))

    # ── Service 层 ───────────────────────────────────────
    from src.service.prompt_service import PromptService
    from src.service.specs_service import SpecsService

    prompt_service = PromptService(prompt_store)
    specs_service = SpecsService(
        fs, backup, str(CSF_LITE_ROOT), str(CSF_CLARITY_DIR))

    # ── UI 层（容错：逐Tab导入，失败→占位Label）──────────

    def _make_placeholder(name: str) -> QLabel:
        label = QLabel(f"[{name}] — 模块加载中…")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    # 标签1: 提示词
    try:
        from src.ui.prompt_tab import PromptTab
        prompt_tab = PromptTab(prompt_service)
    except ImportError:
        prompt_tab = _make_placeholder("提示词")

    # 标签2: 会话上下文（v3）
    try:
        from src.service.context_service import ContextService
        from src.ui.context_tab import ContextTab

        context_service = ContextService(
            cos_context_path=str(CSF_LITE_ROOT / "cos-context.md"),
            draft_path=str(CSF_CLARITY_DIR / "draft.json"),
            section_meta_path=str(CSF_CLARITY_DIR / "section_meta.json"),
            staging_path=str(STAGING_DIR / "pending.md"),
            sections_dir=str(SECTIONS_DIR),
            templates_dir=str(TEMPLATES_DIR),
        )

        # 首次运行：模版为空 → 自动导入 cos-context.md 作为基线模版
        if not context_service.load_templates():
            cos_path = CSF_LITE_ROOT / "cos-context.md"
            if cos_path.exists():
                try:
                    context_service.import_context(str(cos_path))
                except Exception:
                    pass  # 静默失败，不阻塞启动

        context_tab = ContextTab(context_service)
    except ImportError:
        context_tab = _make_placeholder("会话上下文 — v3 重建中")

    # 标签3: CSF规则
    try:
        from src.ui.specs_tab import SpecsTab
        specs_tab = SpecsTab(specs_service)
    except ImportError:
        specs_tab = _make_placeholder("CSF规则")

    # 标签4: 自举
    try:
        from src.ui.bootstrap_tab import BootstrapTab
        bootstrap_tab = BootstrapTab()
    except ImportError:
        bootstrap_tab = _make_placeholder("自举")

    # ── MainWindow ───────────────────────────────────────
    from src.ui.main_window import MainWindow

    tabs = [
        ("提示词", prompt_tab),
        ("上下文", context_tab),
        ("CSF规则", specs_tab),
        ("凡人皆知己所欲", bootstrap_tab),
    ]

    window = MainWindow(tabs, version=VERSION)

    # 单实例：收到第二个实例的激活请求 → 闪到最前
    def _on_activate_request():
        client = _instance_server.nextPendingConnection()
        if client:
            client.close()
        window.show()
        window.raise_()
        window.activateWindow()
        QApplication.alert(window, 0)

    _instance_server.newConnection.connect(_on_activate_request)

    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
