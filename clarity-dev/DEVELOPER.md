# Clarity 开发者参考

> 面向：开发者（Dev）
> 本文件 = 你在 clarity-dev 中工作时的操作速查。非 CSF 规范（规范在 csf-lite/ 中），只覆盖本项目的工程惯例。

---

## 一、环境

```powershell
# 首次
cd clarity-dev
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 日常（不依赖 activate 脚本）
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

**依赖**：PyQt6 ≥6.5、markdown ≥3.4、pytest ≥7.0、pyinstaller ≥6.0、pyyaml ≥6.0

---

## 二、版本号

版本号在 `src/main.py` 的 `VERSION = "X.Y.Z"` 行。**不要手动改**——构建时 `bump_version.py` 自动 +0.0.1。

---

## 三、发布流程

```
build.bat                 ← 唯一入口，双击或终端运行
  ├─ [1/4] pytest 全量测试（不通过则中止）
  ├─ [2/4] bump_version.py（版本 +1 → 收割 RELEASE_NOTES.txt → 写入 RELEASE.md → 清空）
  ├─ [3/4] PyInstaller 打包 → dist/clarity.exe
  └─ [4/4] 复制 → csf-lite/clarity.exe
```

### RELEASE_NOTES.txt 约定

- **位置**：项目根目录（`../RELEASE_NOTES.txt`，即 clarity-dev 的上级）
- **写入**：每次代码改动后追加一行。格式自由，但必须含：`日期  类型  一句话说明`
- **类型**：修复 / 新增 / 优化 / 变更
- **示例**：
  ```
  2026-06-25  修复：标签2 段列表排序错乱（bootstrap_tab.py L42 比较逻辑修正）
  2026-06-25  新增：标签1 搜索框支持拼音模糊匹配
  ```
- **不要手动清空**——构建时 bump_version.py 自动收割后清空

### RELEASE.md

- **位置**：`clarity-dev/RELEASE.md`
- **性质**：永久发布历史，由 bump_version.py 自动追加。不要手动编辑

---

## 四、测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v     # 全量
.\.venv\Scripts\python.exe -m pytest tests/test_models.py -v  # 单文件
```

当前基线：314 测试，全量约 13 秒。

---

## 五、轻量变更 vs STB

| 你的改动… | 走什么流程 |
|---|---|
| 单文件、路径清晰、无架构影响 | **直接改** → devlog 记录 → RELEASE_NOTES.txt 加一行 |
| 跨文件 / 路径不清 / 涉架构 / 不确定 | **转参谋长**，走 STB |

详细规则见 `csf-lite/dev-context.md` §A「轻量变更」节。
