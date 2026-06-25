# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — Clarity V3 单文件 exe。

用法：
    pyinstaller clarity.spec
    或 build.bat（推荐：含测试→打包→部署全流程）

输出：
    dist/clarity.exe  — 单文件可执行程序

体积优化（每次构建自动执行）：
    1. 排除未使用的 Qt 模块：Qml/Quick/Sql/PrintSupport/Test
    2. 筛除 Qt 翻译文件（~10MB）+ QML 引擎（~14MB）
    3. 构建数据收集中排除 .exe/.dll（防旧构建产物污染）
    
    结果：185MB → 133MB（↓28%）。Qt6 ~140MB 是硬下限。
    
    已知限制：Qt6 DLL 全部启用 CFG（Control Flow Guard），UPX 无法压缩。
    单文件模式下 133MB 为当前最优值。
"""

import os
from pathlib import Path
from PyInstaller.building.datastruct import TOC

# 从 clarity-dev/ 运行 pyinstaller，CWD即项目根
_PROJECT_ROOT = Path.cwd()

# ── 体积优化：未使用的 Qt 模块 ──────────────────────────
_UNUSED_QT_MODULES = [
    'PyQt6.QtQml',
    'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets',
    'PyQt6.QtSql',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtTest',
]

# 收集 csf-lite/ 内核文件（排除 .versions/、.tmp、__pycache__）
def _collect_tree(root_dir: str, prefix: str) -> list[tuple[str, str]]:
    """递归收集目录下的文件，排除隐藏和临时文件。"""
    result = []
    base = Path(root_dir)
    if not base.exists():
        return result
    for entry in base.rglob('*'):
        if entry.is_dir():
            continue
        # 排除
        if '.versions' in entry.parts:
            continue
        if entry.suffix == '.tmp':
            continue
        if '__pycache__' in entry.parts:
            continue
        if entry.name.startswith('.'):
            continue
        # 排除二进制可执行文件（旧构建产物不应进入新构建）
        if entry.suffix in ('.exe', '.dll', '.pyd', '.so', '.dylib'):
            continue
        rel = str(entry.relative_to(base))
        result.append((str(entry), f'{prefix}/{rel}'))
    return result

csf_lite_datas = _collect_tree(str(_PROJECT_ROOT.parent / 'csf-lite'), 'csf-lite')
csf_clarity_datas = _collect_tree(str(_PROJECT_ROOT.parent / 'csf-clarity'), 'csf-clarity')
resources_datas = _collect_tree(str(_PROJECT_ROOT / 'resources'), 'resources')

a = Analysis(
    [str(_PROJECT_ROOT / 'src' / 'main.py')],
    pathex=[str(_PROJECT_ROOT / 'src')],
    binaries=[],
    datas=csf_lite_datas + csf_clarity_datas + resources_datas,
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_UNUSED_QT_MODULES,
    noarchive=False,
    optimize=0,
)

# ── 体积优化：筛除 Qt translations + QML ──────────────
# PyInstaller Qt hook 自动收集所有翻译文件和 QML 引擎，Clarity 不需要
a.datas = TOC([
    d for d in a.datas
    if not any(sep in d[0] for sep in ['/translations/', '\\translations\\', '/qml/', '\\qml\\'])
])

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='clarity',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                     # Qt6 DLL 全部 CFG 保护，UPX 无效
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_PROJECT_ROOT / 'resources' / 'clarity.ico') if (_PROJECT_ROOT / 'resources' / 'clarity.ico').exists() else None,
)
