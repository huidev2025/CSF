# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
Clarity V2 全局配置 — 路径常量与运行环境。

所有路径常量集中定义于此，其他模块通过 import 引用，
不自行硬编码路径。

路径规则：
  - 开发模式：clarity-dev/src/ 运行，CSF_LITE_ROOT=../csf-lite
  - 发布模式：clarity.exe 在 csf-lite/ 下，CSF_LITE_ROOT=exe所在目录
  - csf-clarity/ 始终是 csf-lite/ 的兄弟目录，即 exe 父目录下的 csf-clarity/
"""

import sys
from pathlib import Path


def _get_app_dir() -> Path:
    """获取应用所在目录。

    打包为exe时 = exe所在目录（即csf-lite/）
    开发模式时 = clarity-app/ （项目根）
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys.executable).resolve().parent
    else:
        # 开发模式：config.py 在 clarity-dev/src/，项目根是上两级
        return Path(__file__).resolve().parent.parent


_APP_DIR = _get_app_dir()

# ── CSF Lite 内核文件根目录 ─────────────────────────────────
# 发布模式：exe 即在此目录中
# 开发模式：项目根下的 csf-lite/
if getattr(sys, 'frozen', False):
    CSF_LITE_ROOT = _APP_DIR
else:
    CSF_LITE_ROOT = _APP_DIR.parent / "csf-lite"

# ── Clarity 私有数据目录 ─────────────────────────────────────
# csf-clarity/ 与 csf-lite/ 同级（L-030a：AI不可访问）
if getattr(sys, 'frozen', False):
    CSF_CLARITY_DIR = _APP_DIR.parent / "csf-clarity"
else:
    CSF_CLARITY_DIR = _APP_DIR.parent / "csf-clarity"

# ── staging 中转目录 ────────────────────────────────────────
STAGING_DIR = CSF_LITE_ROOT / "staging"

# ── V2 新增路径 ─────────────────────────────────────────────
SECTIONS_DIR = CSF_CLARITY_DIR / "sections"
TEMPLATES_DIR = CSF_CLARITY_DIR / "templates"
PROMPTS_DIR = CSF_CLARITY_DIR / "prompts"
BACKUPS_DIR = CSF_CLARITY_DIR / "backups"
