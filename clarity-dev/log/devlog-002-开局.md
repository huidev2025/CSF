# devlog-002 — 开局

> 日期：2026-06-25
> 会话：全局会话 #002
> 状态：进行中

---

## 加载链声明

- [加载链] 开发者-instructions.md — 读至末尾 ✅
- [加载链] 守则.md — 读至 §附：守则的边界 末尾 ✅
- [加载链] 协作规范.md — 读至 §5.2 末尾 ✅

---

## 开局 brief

已汇报，Owner 分配任务：处理其他细节 bug。

---

## Bug 修复：标签1 新增提示词后编辑区不刷新

### 现象
点击"新增提示词"，输入说明和选择分组后，导航树中出现新提示词，但右侧编辑区仍显示之前选中的旧提示词内容。

### 原因
`_on_new_prompt()` 中调用 `_load_prompt_to_editor(group, description.strip())` 传入了 description（如"我的提示词"），但该方法签名是 `(group: str, filename: str)`，需要含 `.md` 后缀的文件名。`_service.get()` 找不到文件 → `FileNotFoundError` → 静默返回，编辑区内容不更新。

### 修正
`prompt_tab.py:998-1001` — 参照 `_on_duplicate` 的正确模式：`_load_data()` 后遍历 `list_by_group(group)` 匹配 description 获取正确 filename，再传入 `_load_prompt_to_editor`。

```python
# 修正前
self._load_data()
self._select_in_tree(group, description.strip())
self._load_prompt_to_editor(group, description.strip())

# 修正后
self._load_data()
for p in self._service.list_by_group(group):
    if p['description'] == description.strip():
        self._load_prompt_to_editor(group, p['filename'])
        return
self._select_in_tree(group, description.strip())
```

### 验证
- 测试：314 passed ✅
- 耗时：~5min
- 归因：自己疏忽（参数类型不匹配，description vs filename）

---

## Bug 修复：复制新建后导航树未选中新提示词

### 现象
"复制新建"后，左侧编辑区内容切换为新提示词，但右侧导航树仍高亮旧节点。

### 原因
`_on_duplicate()` 的 success 分支调用 `_load_prompt_to_editor()` 后直接 `return`，跳过了末尾的 `_select_in_tree()`。

### 修正
`prompt_tab.py:768` — 在 success 分支中 `_load_prompt_to_editor` 之前插入 `_select_in_tree(group, final_prompt.description)`。

### 验证
- 测试：314 passed ✅
- 耗时：~2min
- 归因：逻辑遗漏（成功路径缺少树选中调用）

---

## 发版 v1.1.29

- build.bat 执行：测试 314 passed → 版本 1.1.28→1.1.29 → PyInstaller 打包 → 复制到 csf-lite/
- dist/clarity.exe: 35,685,803 bytes
- csf-lite/clarity.exe: 已同步
- RELEASE_NOTES.txt: 已收割清空

---

## Bug 修复：新增提示词后导航树未选中新条目

### 现象
上一轮修复后编辑区已正确刷新，但右侧导航树仍高亮旧节点。

### 原因
`_on_new_prompt()` 的 success 分支同 `_on_duplicate` 之前的 bug——调了 `_load_prompt_to_editor()` 直接 `return`，跳过了 `_select_in_tree()`。

### 修正
`prompt_tab.py:1004` — success 分支中 `_load_prompt_to_editor` 之前补 `_select_in_tree()`。

### 验证
- 测试：314 passed ✅
- 耗时：~1min
- 归因：逻辑遗漏（第一轮修 _on_new_prompt 时未同步补 _select_in_tree）

---

## 优化：标签1 失焦/切换条目自动保存

### 需求
不再弹窗提醒"未保存的修改"，改为：
1. 说明/正文文本框失焦 → 自动保存
2. 导航树点击其他条目 → 自动保存后切换

### 改动
`prompt_tab.py`:
- 导入 `QEvent`
- 新增 `_auto_saving` 标志防递归
- `_desc_edit` / `_content_edit` 安装 `eventFilter` → `FocusOut` 触发 `_auto_save()`
- `_on_tree_item_clicked`：`_prompt_save_before_switch` 弹窗 → `_auto_save()` 静默保存
- 新增 `_auto_save()` 方法：与 `_on_save()` 逻辑相同但不弹窗，失败静默忽略
- `_on_editor_changed`：自动保存期间跳过脏状态更新

### 验证
- 测试：314 passed ✅
- 耗时：~10min
- 归因：UX 优化

---

## 新增：标签2 管理模板增加重命名

### 需求
[管理模板] 对话框中只有删除按钮，没有重命名入口。

### 改动
- `context_service.py`：新增 `rename_template(old_name, new_name)` — 读旧→写新→删旧，含同名检查和存在检查
- `context_tab.py`：
  - `_on_manage_templates` 每行增加 [重命名] 按钮
  - 新增 `_do_rename_template()` — 弹出输入框预填原名 → 调用 service → 刷新对话框

### 验证
- 测试：314 passed ✅
- 耗时：~10min
- 归因：功能缺失

---

## 发版 v1.1.30

- build.bat 执行：测试 314 passed → 版本 1.1.29→1.1.30 → PyInstaller 打包 → 复制到 csf-lite/
- dist/clarity.exe + csf-lite/clarity.exe: 35,688,582 bytes
- RELEASE_NOTES.txt: 已收割清空
