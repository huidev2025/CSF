"""
bump_version.py — 打包前自动递增小版本号 + 维护 RELEASE.md。

用法：
    python bump_version.py                    # 自动递增
    python bump_version.py --dry-run          # 仅显示将要变成的版本号
    python bump_version.py --current          # 显示当前版本号

RELEASE_NOTES.txt 规则：
    - 若文件存在且非空 → 其内容作为本次 release notes
    - 若不存在或为空 → release notes 写 "例行发布"
    - 写入 RELEASE.md 后自动清空 RELEASE_NOTES.txt
"""
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_PY = SCRIPT_DIR / "src" / "main.py"
RELEASE_MD = SCRIPT_DIR / "RELEASE.md"
NOTES_TXT = SCRIPT_DIR.parent / "RELEASE_NOTES.txt"


def get_current_version() -> str:
    """从 main.py 提取当前版本号。"""
    text = MAIN_PY.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('VERSION = "'):
            return stripped.split('"')[1]
    raise SystemExit("ERROR: 在 main.py 中找不到 VERSION = \"...\" 行")


def bump_patch(version: str) -> str:
    """递增小版本号：1.1.21 → 1.1.22。"""
    parts = version.split(".")
    if len(parts) != 3:
        raise SystemExit(f"ERROR: 版本号格式错误: {version}")
    parts[2] = str(int(parts[2]) + 1)
    return ".".join(parts)


def update_main_py(old_ver: str, new_ver: str) -> None:
    """将 main.py 中的 VERSION 行替换为新版本号。"""
    text = MAIN_PY.read_text(encoding="utf-8")
    new_text = text.replace(f'VERSION = "{old_ver}"', f'VERSION = "{new_ver}"')
    if new_text == text:
        raise SystemExit(f"ERROR: 替换版本号失败: {old_ver} → {new_ver}")
    MAIN_PY.write_text(new_text, encoding="utf-8")
    print(f"  main.py: {old_ver} → {new_ver}")


def get_release_notes() -> str:
    """读取 RELEASE_NOTES.txt。不存在或为空 → 默认描述。"""
    if NOTES_TXT.exists():
        content = NOTES_TXT.read_text(encoding="utf-8").strip()
        if content:
            return content
    return "例行发布"


def append_release(version: str, notes: str) -> None:
    """在 RELEASE.md 顶部追加新版本条目。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"## v{version} — {now}\n\n"
        f"{notes}\n\n"
    )
    if RELEASE_MD.exists():
        existing = RELEASE_MD.read_text(encoding="utf-8")
        # 找到第一个 ## 标题前插入
        first_heading = existing.find("## v")
        if first_heading >= 0:
            new_content = existing[:first_heading] + entry + existing[first_heading:]
        else:
            new_content = entry + existing
    else:
        new_content = f"# Clarity 发布记录\n\n{entry}"
    RELEASE_MD.write_text(new_content, encoding="utf-8")
    print(f"  RELEASE.md: v{version}")


def clear_release_notes() -> None:
    """清空 RELEASE_NOTES.txt。"""
    NOTES_TXT.write_text("", encoding="utf-8")


def main():
    if "--current" in sys.argv:
        print(get_current_version())
        return

    old_ver = get_current_version()
    new_ver = bump_patch(old_ver)

    if "--dry-run" in sys.argv:
        print(f"  {old_ver} → {new_ver}")
        notes = get_release_notes()
        print(f"  notes: {notes[:80]}{'...' if len(notes) > 80 else ''}")
        return

    print(f"版本号: {old_ver} → {new_ver}")
    notes = get_release_notes()
    update_main_py(old_ver, new_ver)
    append_release(new_ver, notes)
    clear_release_notes()
    print(f"新版本: v{new_ver}")


if __name__ == "__main__":
    main()
