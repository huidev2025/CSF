# Clarity 发布记录

## v1.1.37 — 2026-06-26 05:24

例行发布

## v1.1.36 — 2026-06-26 05:08

例行发布

## v1.1.35 — 2026-06-26 04:59

例行发布

## v1.1.34 — 2026-06-26 04:54

例行发布

## v1.1.33 — 2026-06-26 04:49

例行发布

## v1.1.32 — 2026-06-26 04:39

例行发布

## v1.1.31 — 2026-06-26 03:13

例行发布

## v1.1.30 — 2026-06-25 19:24

2026-06-25  修复：标签1 新增提示词后导航树未选中新条目（prompt_tab.py _on_new_prompt 补 _select_in_tree）
2026-06-25  优化：标签1 失焦/切换条目自动保存，不再弹窗提醒（prompt_tab.py 新增 _auto_save + eventFilter）
2026-06-25  新增：标签2 管理模板增加重命名按钮（context_service.py + context_tab.py）

## v1.1.29 — 2026-06-25 19:09

2026-06-25  修复：标签1 新增提示词后编辑区不刷新为新建提示词（prompt_tab.py _on_new_prompt 参数 description→filename 错误）
2026-06-25  修复：标签1 复制新建后导航树未选中新提示词（prompt_tab.py _on_duplicate 缺少 _select_in_tree）

## v1.1.28 — 2026-06-25 18:24

例行发布

## v1.1.27 — 2026-06-25 18:04

例行发布

## v1.1.26 — 2026-06-25 17:57

例行发布

## v1.1.25 — 2026-06-25 17:53

2026-06-25  修复：模板装载后版本Tab不显示已装载状态和版本号，[保存]误创建新版本（context_tab.py _on_change_context 补 _applied_versions 同步，devlog-001）

## v1.1.24 — 2026-06-25 17:32

2026-06-25  变更：建立轻量变更通道（RELEASE_NOTES.txt 迁至项目根、dev-context 新增轻量变更规程、bump_version.py 适配新路径）
2026-06-25  变更：dev-context.md 首次激活（可见范围/进度表/§B-§D 全部就位）
2026-06-25  修复：save_to_current_context() 不再向 cos-context.md 写入 @DESC 哨兵，仅同步 section_meta.json（bug#1，devlog-001）
2026-06-25  修复：[保存为段库版本] 保存后同步 section_meta.json + 版本Tab双按钮拆分（bug#2，devlog-001）

## v1.1.23 — 2026-06-25 07:36

例行发布

## v1.1.22 — 2026-06-25 07:35

（在此填写本次发布的更新内容，留空则自动写"例行发布"）

## v1.1.21 — 2026-06-25 07:23
- 修复：自举打包后标签2只显示一个段（bootstrap_tab.py @SECTION 哨兵补全）
- 修复：导入 cos-context.md 闪退（context_service.py 补 logger）
- 新增：首次运行自动导入 cos-context.md 为基线模版
- 新增：打包时清理段库/模版/备份目录

## v1.1.20 — 2026-06-24
- 标签2 MSG:6 全局排版美化完成
- 版本Tab 预览/装载分离交互
- QSplitter 持久化 + 信号陷阱修复
- 标签3 QSplitter 把手可见 + addStretch 空白消除

## v1.1.19 及更早
- 标签2 v6 全线闭合（STB-1~STB-4）
- 标签3 全文搜索+可拖拽布局
- 标签3 规则名称概念全局落地
- Clarity v1.1 基础功能完成
