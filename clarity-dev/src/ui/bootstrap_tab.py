# Copyright (c) 2025 zhanghui <dapangangang@gmail.com>
# SPDX-License-Identifier: MIT
# https://github.com/huidev2025/CSF

"""
BootstrapTab — 标签4「自举」：用户自助打包CSF环境。

功能：
- 个人宣传资料/联系方式（静态文字）
- 「打包CSF环境」按钮 → 清理+导出zip
"""
import json
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QProgressDialog,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.config import CSF_LITE_ROOT, CSF_CLARITY_DIR


# ── §B+ 清洁模板（cos-context.md）────────────────────────

_COS_CLEAN_TAIL = """\
<!-- @SECTION:B -->
## §B 任务窗口

<!--
  本段由参谋长维护。结构：全景图 + 三元组指针 + 通用资源。
  三元组文件（目的/方法/资源/进度/备忘）在 triplets/ 目录下独立维护。
-->

### 全景图

<!-- @MODE:阶段 -->
```
GP: <!-- 项目名 — 一句话描述 -->

├─ S1 <!-- 第一阶段 -->
│   └─ ⬜ 待立项
│
├─ 🐛 修复 💤
└─ 🧭 探索 💤
```

### 三元组指针

> 活跃三元组：[triplets/<!-- 文件名 -->.md](triplets/<!-- 文件名 -->.md)
>
> 开局回合 1 由参谋长基于 §D 方向 + [三元组索引](triplets/_index.md) 提议本次会话使用的三元组，Owner 确认后可调整。
> 三元组文件包含：目的 + 方法 + 资源 + 进度表 + 会话索引 + 活跃防御 + 备忘。

### 通用资源（每次会话必读）

1. cos-context.md（本文件）
2. `triplets/` — 当前活跃三元组文件（开局回合 2 精读）

<!-- @/SECTION:B -->
---

<!-- @SECTION:C -->
## §C 上次会话

（无）

<!-- @/SECTION:C -->
---

<!-- @SECTION:D -->
## §D 下次会话

（无）

<!-- @/SECTION:D -->
---

<!-- @SECTION:INBOX -->
## §收件箱

> 本段 = 开发者→参谋长的异步消息。
>
<!-- 哨兵格式：每条用 <!-- @MSG:N -->...<!-- @/MSG:N --> 包围 -->
<!-- @/SECTION:INBOX -->
"""


_DEV_CLEAN_TAIL = """\

<!-- @SECTION:B -->
## §B 任务窗口

<!--
  本段由参谋长维护。结构：进度表 + 通用资源 + 防御 + 备忘。
  开发者不改 §B（备忘区除外）。开发者做完任务 → 标 🟡 → 参谋长验收后标 ✅。
-->

### 定位

- **产品**：<!-- 填入产品名称和一句话描述 -->
- **当前阶段**：<!-- 填入当前阶段 -->

### 进度表（即时全景 · 唯一权威）

> 参谋长维护设计列 + 开发者维护开发列。

| TP/IT | 设计 | 开发 | 阻塞 | 备注 |
|---|---|---|---|---|
| — | — | — | — | — |

### 通用资源（每次会话必读）

1. context-开发者.md（本文件）
2. 当前IT的任务书

### 活跃防御

1. **凭印象 = 红线**
2. **不沉默**：发现问题立即报

### 备忘（跨会话持久 / 只能显式关闭）

<!--
- [ ] 条目描述。来源：session-NNN
-->

<!-- @/SECTION:B -->
---

<!-- @SECTION:C -->
## §C 上次会话

（无）

<!-- @/SECTION:C -->
---

<!-- @SECTION:D -->
## §D 下次会话

（无）

<!-- @/SECTION:D -->
---

<!-- @SECTION:INBOX -->
## §收件箱（参谋长→开发者）

> 本段 = 参谋长发给开发者的异步消息。
>
<!-- 哨兵格式：每条用 <!-- @MSG:N -->...<!-- @/MSG:N --> 包围 -->
<!-- @/SECTION:INBOX -->
"""


# ── 清洁函数 ────────────────────────────────────────────

def clean_context_file(content: str, clean_tail: str,
                      marker: str = r'<!--\s*@SECTION:B\s*-->') -> str:
    """截断 marker 之后的内容，替换为干净模板。

    Args:
        content: 原始文件内容
        clean_tail: 干净的 §B-§收件箱模板（含 @SECTION 哨兵）
        marker: 截断标记（正则，默认为 @SECTION:B 哨兵）

    Returns:
        清理后的文件内容
    """
    lines = content.split('\n')
    cut_idx = None

    for i, line in enumerate(lines):
        if re.match(marker, line):
            cut_idx = i
            break

    if cut_idx is None:
        return content

    before = '\n'.join(lines[:cut_idx]).rstrip('\n')
    return before + '\n' + clean_tail


def reset_json_file(path: Path, default: dict) -> None:
    """将 JSON 文件重置为默认值。"""
    path.write_text(json.dumps(default, indent=2, ensure_ascii=False),
                    encoding='utf-8')


# ── 打包配置加载 ────────────────────────────────────────

# 协议文件路径（相对于 CSF_LITE_ROOT）
_PACK_PROTOCOL_PATH = Path('protocols') / 'CSF打包协议.md'

# 内置默认配置（当协议文件不可用时使用）
_BUILTIN_CONFIG = {
    'version': '1.0',
    'package': {
        'name_template': 'CSF-{timestamp}.zip',
        'root_files': {},
        'copy_files': {
            '安装与配置.pdf': '../安装与配置.pdf',
            'LICENSE-Clarity.txt': '../clarity-dev/LICENSE',
        },
    },
    'csf_lite': {
        'exclude_dirs': ['staging'],
        'empty_dirs': ['sessions', 'staging', 'workspace'],
        'clean_triplets': True,
        'triplets_keep': ['_TEMPLATE.md'],
        'triplets_index_template': '',
        'clean_files': {
            'cos-context.md': {
                'method': 'cut_at_marker',
                'marker': r'<!--\s*@SECTION:B\s*-->',
                'replacement': _COS_CLEAN_TAIL,
            },
            'dev-context.md': {
                'method': 'cut_at_marker',
                'marker': r'<!--\s*@SECTION:B\s*-->',
                'replacement': _DEV_CLEAN_TAIL,
            },
        },
    },
    'csf_clarity': {
        'copy_dirs': ['prompts'],
        'empty_dirs': ['sections', 'templates', 'backups'],
        'reset_json': {
            'file_meta.json': {},
            'section_meta.json': {},
            'scenes.json': {'current': 'default', 'scenes': {'default': {}}},
            'draft.json': {},
        },
    },
}


def _load_pack_config() -> dict:
    """从协议文件加载打包配置。

    读取 csf-lite/protocols/CSF打包协议.md，提取 YAML 配置块。
    若文件不存在或 YAML 解析失败，返回内置默认配置。
    """
    protocol_path = Path(CSF_LITE_ROOT) / _PACK_PROTOCOL_PATH

    if not protocol_path.exists():
        return dict(_BUILTIN_CONFIG)

    try:
        text = protocol_path.read_text(encoding='utf-8')
    except Exception:
        return dict(_BUILTIN_CONFIG)

    # 提取 YAML 代码块（```yaml ... ```）
    # 闭合的 ``` 必须在行首（顶格），避免匹配 YAML 内容中缩进的 ``` 
    yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', text, re.DOTALL)
    if not yaml_match:
        return dict(_BUILTIN_CONFIG)

    yaml_text = yaml_match.group(1)

    if yaml is not None:
        try:
            config = yaml.safe_load(yaml_text)
            if isinstance(config, dict):
                return config
        except Exception:
            pass

    return dict(_BUILTIN_CONFIG)


def _deep_get(d: dict, *keys, default=None):
    """深层获取 dict 嵌套值。"""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


# ── 打包函数 ────────────────────────────────────────────

def _package_csf(output_zip_path: str,
                 progress: QProgressDialog | None = None) -> list[str]:
    """执行打包流程，返回遇到的问题列表（空 = 成功）。

    在临时目录中组装，不修改磁盘原文件。
    打包规则从 csf-lite/protocols/CSF打包协议.md 读取。
    """
    issues: list[str] = []
    tmp_dir = Path(tempfile.mkdtemp(prefix='csf_pack_'))
    config = _load_pack_config()

    def _step(msg: str):
        if progress:
            progress.setLabelText(msg)

    try:
        lite_cfg = config.get('csf_lite', {})
        clarity_cfg = config.get('csf_clarity', {})

        # ── 0. 路径诊断 ──────────────────────────────
        lite_src = Path(CSF_LITE_ROOT)
        clarity_src = Path(CSF_CLARITY_DIR)
        if not lite_src.exists():
            issues.append(f"csf-lite/ 不存在：{lite_src}")
        if not clarity_src.exists():
            issues.append(f"csf-clarity/ 不存在：{clarity_src}")

        # ── 1. 复制 csf-lite/ ──────────────────────────
        _step("复制 csf-lite/ …")
        lite_dst = tmp_dir / 'csf-lite'
        exclude = set(lite_cfg.get('exclude_dirs', []))
        _copytree_filtered(lite_src, lite_dst, exclude_names=exclude)

        # ── 2. 创建 csf-clarity/ ───────────────────────
        _step("准备 csf-clarity/ …")
        clarity_dst = tmp_dir / 'csf-clarity'
        clarity_dst.mkdir(parents=True, exist_ok=True)

        # 复制指定目录
        for sub in clarity_cfg.get('copy_dirs', []):
            src_sub = clarity_src / sub
            dst_sub = clarity_dst / sub
            if src_sub.exists():
                shutil.copytree(str(src_sub), str(dst_sub))
            else:
                issues.append(f"csf-clarity/{sub}/ 不存在，创建空目录")
                dst_sub.mkdir(parents=True, exist_ok=True)

        # ── 3. 清空指定目录 ────────────────────────────
        _step("清洁目录…")
        # csf-lite 侧
        for sub in lite_cfg.get('empty_dirs', []):
            target = lite_dst / sub
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
            target.mkdir(parents=True, exist_ok=True)
        # csf-clarity 侧
        for sub in clarity_cfg.get('empty_dirs', []):
            target = clarity_dst / sub
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
            target.mkdir(parents=True, exist_ok=True)

        # ── 4. 清洁三元组 ──────────────────────────────
        if lite_cfg.get('clean_triplets', True):
            _step("清洁 triplets/ …")
            _clean_triplets_dir(lite_dst / 'triplets', lite_cfg)

        # ── 5. 清洁 context 文件 ───────────────────────
        clean_files_cfg = lite_cfg.get('clean_files', {})
        for filename, file_cfg in clean_files_cfg.items():
            _step(f"清洁 {filename} …")
            file_path = lite_dst / filename
            if file_path.exists() and file_cfg.get('method') == 'cut_at_marker':
                original = file_path.read_text(encoding='utf-8')
                marker = file_cfg.get('marker', r'<!--\s*@SECTION:B\s*-->')
                replacement = file_cfg.get('replacement', '')
                cleaned = clean_context_file(original, replacement, marker=marker)
                file_path.write_text(cleaned, encoding='utf-8')

        # ── 6. 重置 JSON 文件 ──────────────────────────
        _step("重置配置…")
        for json_file, default_val in clarity_cfg.get('reset_json', {}).items():
            reset_json_file(clarity_dst / json_file, default_val)

        # ── 7. 生成根目录文件 ──────────────────────────
        root_files = _deep_get(config, 'package', 'root_files', default={})
        if root_files:
            _step("生成根目录文件…")
            for filename, content in root_files.items():
                root_path = tmp_dir / filename
                root_path.write_text(content, encoding='utf-8')

        # ── 7b. 拷贝外部文件到 zip 根目录 ─────────────
        copy_files = _deep_get(config, 'package', 'copy_files', default={})
        if copy_files:
            _step("拷贝附加文件…")
            for filename, src_rel in copy_files.items():
                src_path = (lite_src / src_rel).resolve()
                dst_path = tmp_dir / filename
                if src_path.exists():
                    shutil.copy2(str(src_path), str(dst_path))
                else:
                    issues.append(f"附加文件不存在：{src_rel}")
        # ── 8. 创建 zip ────────────────────────────────
        _step("打包 zip …")
        _make_zip(output_zip_path, tmp_dir)

    except Exception as e:
        issues.append(f"打包异常：{e}")
    finally:
        _step("清理临时文件…")
        shutil.rmtree(str(tmp_dir), ignore_errors=True)

    return issues


def _clean_triplets_dir(triplets_dir: Path, lite_cfg: dict) -> None:
    """清洁 triplets/ 目录：仅保留指定文件，重置 _index.md。"""
    if not triplets_dir.exists():
        triplets_dir.mkdir(parents=True, exist_ok=True)

    keep_files = set(lite_cfg.get('triplets_keep', ['_TEMPLATE.md']))
    keep_files.add('_index.md')  # 索引文件始终保留（但内容重置）

    # 删除不在保留列表中的文件
    for item in os.listdir(str(triplets_dir)):
        if item not in keep_files:
            item_path = triplets_dir / item
            if item_path.is_dir():
                shutil.rmtree(str(item_path), ignore_errors=True)
            else:
                item_path.unlink(missing_ok=True)

    # 重置 _index.md
    index_template = lite_cfg.get('triplets_index_template', '')
    index_path = triplets_dir / '_index.md'
    if index_template:
        index_path.write_text(index_template, encoding='utf-8')
    else:
        # 最小空索引
        index_path.write_text(
            '# 三元组索引\n\n> 版本: v1.0\n'
            '> 本文件列出所有活跃三元组。\n\n'
            '---\n\n'
            '## 活跃三元组\n\n'
            '（暂无。首次会话时由参谋长建立第一个三元组文件。）\n\n'
            '---\n\n'
            '## 使用规则\n\n'
            '- 每次会话使用**一个**三元组。\n'
            '- 新建三元组：参考 `_TEMPLATE.md` 模板。\n',
            encoding='utf-8',
        )


def _copytree_filtered(src: Path, dst: Path, exclude_names: set[str]):
    """复制目录树，排除指定名称的子目录/文件。"""
    dst.mkdir(parents=True, exist_ok=True)

    for item in os.listdir(str(src)):
        if item in exclude_names:
            continue
        s = src / item
        d = dst / item
        if s.is_dir():
            shutil.copytree(str(s), str(d))
        else:
            shutil.copy2(str(s), str(d))


def _make_zip(output_path: str, root_dir: Path) -> None:
    """创建 zip 文件，包含所有文件和空目录。

    使用 os.walk 遍历，确保空目录也被显式加入 zip。
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(str(root_dir)):
            rel_dir = Path(dirpath).relative_to(root_dir)
            # 添加目录条目（即使是空的）
            if rel_dir != Path('.'):
                arcname = str(rel_dir).replace('\\', '/') + '/'
                info = zipfile.ZipInfo(arcname)
                info.external_attr = 0o40755 << 16  # drwxr-xr-x
                zf.writestr(info, '')
            # 添加文件
            for fname in filenames:
                full = Path(dirpath) / fname
                arcname = str(full.relative_to(root_dir)).replace('\\', '/')
                zf.write(str(full), arcname)


# ── 标签4 UI ────────────────────────────────────────────

class BootstrapTab(QWidget):
    """标签4「自举」— 用户自助打包 CSF 环境。"""

    # 默认社区与授权信息（使用者可按需修改此处）
    # {image_path} 在 _build_ui 中替换为知识星球图片的绝对路径
    DEFAULT_BIO = """\
<div style="font-size:13px; line-height:1.9; color:#333;">
<p style="font-size:14px;"><b>💡 使用方法：说清楚自己要什么</b></p>
<p style="text-align:left;"><img src="{image_path}" width="260"></p>
<p style="font-size:15px;"><b>🪐 知识星球 —— 你的 CSF 大本营</b></p>
<p>
加入知识星球，你可以：<br>
✅ 获得使用答疑 —— 遇到问题随时提问<br>
✅ 看到真实案例 —— 别人怎么用 CSF 做项目<br>
✅ 第一时间获取版本更新<br>
✅ 与其他用户交流经验、互相启发<br>
✅ 直接影响 CSF 的发展方向
</p>
<p>
📬 <b>联系与关注</b><br>
🌐 GitHub：<a href="https://github.com/huidev2025/CSF">github.com/huidev2025/CSF</a><br>
📧 邮箱：<a href="mailto:dapangangang@gmail.com">dapangangang@gmail.com</a>
</p>
<hr style="border:none;border-top:1px solid #E0E0E0;margin:12px 0;">
<p style="font-size:14px;"><b>📜 使用授权</b></p>
<p>
• <b>个人、学术、非营利使用</b>：自由传播、翻译、改编，请保留署名（dapangangang）与原始链接。<br>
• <b>商业使用</b>：请提前联系作者。<br>
• <b>创业者</b>：免费。<br>
• <b>不确定是否算商用</b>：发个 Issue 或邮件问一下就好。
</p>
</div>
"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ── UI 构建 ────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("起码，我们还有分享的自由。")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 分割线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(line)

        # 社区 & 授权展示区
        bio_label = QLabel("📋 社区 & 授权")
        bio_label.setStyleSheet("font-weight:600; font-size:13px; color:#555;")
        layout.addWidget(bio_label)

        # 构造知识星球图片路径
        image_path = (Path(CSF_LITE_ROOT).parent / 'csf-lite-doc' / 'csf发行.jpg').as_posix()

        self._bio_text = QTextEdit()
        self._bio_text.setReadOnly(True)
        self._bio_text.setHtml(self.DEFAULT_BIO.format(image_path=image_path))
        self._bio_text.setStyleSheet("""
            QTextEdit {
                background: #FAFBFC;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        # stretch=1 → bio_text 占据 bio_label 与底部按钮之间的全部剩余空间
        layout.addWidget(self._bio_text, stretch=1)

        # 说明文字（自然高度，始终贴底）
        desc = QLabel(
            "点击下方按钮，将当前 CSF 环境打包为一个干净的 zip 文件。<br>"
            "打包内容：csf-lite 内核 + 你的提示词集合（csf-clarity/prompts）。<br>"
            "<b>上下文文件会被自动清理</b>（清空任务窗口、会话记录、收件箱），"
            "个人段库和备份<b>不会</b>被打包。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#666; font-size:12px; line-height:1.6;")
        layout.addWidget(desc)

        # 打包按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._pack_btn = QPushButton("📦 打包CSF环境")
        self._pack_btn.setMinimumHeight(44)
        self._pack_btn.setMinimumWidth(200)
        self._pack_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: 600;
                padding: 8px 28px;
                background: #2980B9;
                color: #FFF;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #2471A3;
            }
            QPushButton:pressed {
                background: #1F618D;
            }
        """)
        self._pack_btn.clicked.connect(self._on_pack)
        btn_row.addWidget(self._pack_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ── 打包流程 ────────────────────────────────────────

    def _on_pack(self):
        """用户点击「打包CSF环境」按钮。"""
        # 生成默认文件名
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        default_name = f"CSF-{ts}.zip"

        # 弹出保存对话框
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存打包文件",
            default_name,
            "ZIP 文件 (*.zip);;所有文件 (*)"
        )
        if not save_path:
            return  # 用户取消

        # 进度对话框
        progress = QProgressDialog("正在打包 CSF 环境…", None, 0, 0, self)
        progress.setWindowTitle("打包中")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()

        # 执行打包
        issues = _package_csf(save_path, progress)

        # 关闭进度
        progress.close()

        # 结果
        if issues:
            QMessageBox.warning(
                self, "打包完成（有警告）",
                "打包过程中遇到以下问题：\n\n" +
                "\n".join(f"• {i}" for i in issues) +
                f"\n\n文件已保存到：\n{save_path}"
            )
        else:
            size_mb = Path(save_path).stat().st_size / (1024 * 1024)
            QMessageBox.information(
                self, "打包完成 ✅",
                f"CSF 环境已成功打包！\n\n"
                f"📁 位置：{save_path}\n"
                f"📏 大小：{size_mb:.1f} MB\n\n"
                f"你可以将此 zip 文件发给他人，解压后即可使用。"
            )
