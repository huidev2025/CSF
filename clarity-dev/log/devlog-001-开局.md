# devlog-001 — 开局

> 会话: devlog-001
> 日期: 2026-06-25
> 类型: 开局（首次独立 Dev 会话）
> 全局会话号: 001

---

## 加载链声明

- [加载链] core/开发者-instructions.md — 读至末尾（身份内核） ✅
- [加载链] core/守则.md — 读至末尾（§附：守则的边界） ✅
- [加载链] core/协作规范.md — 读至 §3 末尾 ✅

---

## 环境确认

- Python: 3.13.14 ✅
- venv: `.venv` 就绪 ✅
- 测试: **314 passed in 8.68s** ✅
- 结论: 环境正常，可以开始工作。

---

## bug#1 修复：save_to_current_context 不再写入 @DESC 到 cos-context.md

**问题**：`save_to_current_context()` 向 cos-context.md 注入 `<!-- @DESC -->...<!-- @/DESC -->` 注释块，浪费 AI 上下文 token。描述已在 section_meta.json 中权威存储。

**修改**：
- `context_service.py` `save_to_current_context()`：移除 cos-context.md 定位/替换/写入逻辑（原 L622-694），仅保留 section_meta.json 同步
- `cos-context.md`：删除 §A 中遗留的 @DESC 空块（测试残留 "sfg sdfgsfg dsf"）

**验证**：314 passed in 7.50s ✅

**耗时**：~5min

**归因**：代码设计 — @DESC 哨兵对 AI 上下文无价值，属于 Clarity 内部存储泄漏到外部文件

---
## bug#2 修复 + 版本Tab按钮拆分

**问题**：
1. 「当前」Tab [保存为段库版本] 不更新 section_meta.json（bug#2）
2. 「版本」Tab 两个按钮 ([保存] / [保存到段库版本]) 调用同一 handler，语义混淆

**修改**（`context_tab.py`）：
- `_on_save_as_version_from_current()`：+1行 `save_to_current_context()` sync（bug#2 修复）
- 拆分 `_on_save_version` → `_on_save_version_overwrite` + `_on_save_version_new`
  - ③ [保存] → 覆写当前版本（blank时创建v1）
  - ④ [保存为段库版本] → 始终新建版本
  - 两个 handler 均补 section_meta.json 同步
- 按钮④文案从"保存到段库版本"改为"保存为段库版本"（与当前Tab一致）

**验证**：314 passed in 7.45s ✅

**耗时**：~10min

**归因**：代码遗漏 — save_as_library_version 设计时未考虑 section_meta.json 同步

---
## bug#3 修复：模板装载后版本Tab不显示已装载状态

**问题**：通过模板装载的段库版本，版本Tab标题不显示"已装载"标记和版本号，导致[保存]误创建新版本而非覆写已有版本。

**根因**：`_applied_versions` 只在手动点击[装载]按钮时写入（`_do_load_version`），模板装载路径（`_on_change_context` → swap_version/add DraftChange）绕过了它。

**修改**（`context_tab.py` `_on_change_context()`）：
- 规则① swap_version 后 + `self._applied_versions[tpl_title] = tpl_ver`
- 规则② add 后 + `self._applied_versions[tpl_title] = tpl_ver`

**验证**：314 passed in 7.57s ✅

**耗时**：~5min

**归因**：代码遗漏 — 模板装载未同步 `_applied_versions` 字典

---
## 新增 protocol：Staging-处理协议

**内容**：参谋长处理 Clarity 标签2 staging 指令的标准操作流程。

涵盖：
- §1 触发条件：开局检测 `csf-lite/staging/pending.md`
- §2 pending.md 格式：`@STAGING:N` + `@STG:CONTENT`
- §3 四种操作：换版本 / 撤下 / 添加段 / 重排，各含 @SOURCE 写入规范
- §4 收尾清理 + §5 异常处理 + §6 完整示例

**文件**：`csf-lite/protocols/Staging-处理协议.md`
**索引**：`csf-lite/protocols/_index.md` 已追加

---

## _applied_versions 同步顺序修正（v1.1.28）

**问题**：`_rebuild_section_list` 中 `_applied_versions` 同步在 `setCurrentRow` 之后，导致 `_load_section_to_detail` 时字典为空。

**修改**（`context_tab.py` `_rebuild_section_list`）：sync 块移到恢复选中之前。

**验证**：314 passed ✅

---

## Staging-处理协议 回退

按 Owner 要求清空 `Staging-处理协议.md`，退回 `_index.md` 条目。协议需 Owner 主导业务定义后重新起草。

---

## 修改自证清单

```
本会话 diff 统计：
  context_service.py  -80/+6  (save_to_current_context 精简)
  context_tab.py      +60/-30 (_on_save_version 拆分 / _on_change_context 修复 / _rebuild_section_list 同步)
  cos-context.md       -3      (@DESC 残留删除)
  build.bat            ~5      (venv 路径 + 测试数修正)
  dev-context.md       ~15     (§B/§C/§D/状态栏 收尾更新)

逐改追溯：
  context_service.py:save_to_current_context  ← bug#1「@DESC 哨兵浪费 AI 上下文」
  context_tab.py:_on_save_as_version_from_current +1行  ← bug#2「section_meta.json 未同步」
  context_tab.py:_on_save_version → 拆分  ← bug#2「版本Tab 双按钮语义混淆」
  context_tab.py:_on_change_context +4行  ← bug#3「模板装载 _applied_versions 缺失 + _load_section_to_detail 缺失」
  context_tab.py:_rebuild_section_list 同步顺序  ← devlog-001「重启后 _applied_versions 未恢复」
  cos-context.md:@DESC 删除  ← bug#1 配套清理
  build.bat:venv 路径 + 测试数  ← devlog-001「构建环境修正」

✅ 范围外动：0 处
🟡 范围内但非计划：1 处
   - protocols/Staging-处理协议.md 起草后清空（Owner 要求）
   - 建议：待 Owner 主导业务定义后重新起草
```

---

## 会话总结

- **总耗时**：~2h
- **发版**：v1.1.23 → v1.1.28（5 次构建）
- **测试**：每次修改后 314 passed
- **卡点**：Staging 协议需要 Owner 业务定义后才能继续
- **下一步**：待 Owner 分配新任务