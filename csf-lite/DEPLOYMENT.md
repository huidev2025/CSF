# 部署方案 — CSF Lite v1.1

> 版本: v1.0 / 创建: 2026-06-21 / session-033
> 本文件记录 CSF Lite 的最终发布目录布局、打包流程、发布清单。

---

## §1 发布目录布局

### 最终交付结构（zip 给用户）

```
project-workspace/               ← 压缩此文件夹，发给用户
├── csf-lite/                    ← CSF 内核 + 应用入口
│   ├── clarity.exe              ← 双击启动（单文件，~133MB）
│   ├── core/                    ← CSF 方法论内核（5文件）
│   │   ├── 参谋长-instructions.md
│   │   ├── 参谋长-方法论.md
│   │   ├── 开发者-instructions.md
│   │   ├── 守则.md
│   │   └── 协作规范.md
│   ├── protocols/               ← 操作规程（13文件）
│   ├── knowledge/               ← 经验库
│   │   ├── methods/
│   │   ├── redlines/
│   │   └── crafts/
│   ├── cos-context.md           ← 参谋长引擎（出厂模板）
│   ├── dev-context.md           ← 开发者引擎
│   ├── README.md                ← 面向用户的入门说明
│   ├── QUICKSTART.md            ← 新项目初始化指南
│   └── workspace/               ← 用户默认工作区（空目录）
└── csf-clarity/                 ← 应用运行时数据（首次启动自动填充）
    ├── file_meta.json           ← 空 {}（首次启动创建）
    ├── prompts/                 ← 出厂预置提示词（首次启动自动生成）
    ├── sections/.versions/      ← 段版本快照
    ├── templates/               ← 模板文件
    └── backups/                 ← 备份（files/baselines）
```

### 路径判定逻辑（config.py）

| 模式 | CSF_LITE_ROOT | CSF_CLARITY_DIR |
|---|---|---|
| 发布（frozen） | `exe所在目录`（即 csf-lite/） | `exe所在目录的父目录 / csf-clarity` |
| 开发 | `clarity-app/../csf-lite` | `clarity-app/../csf-clarity` |

> 约束：clarity.exe 必须放在 csf-lite/ 内。csf-clarity/ 必须与 csf-lite/ 同级。
> 此逻辑当前已满足，v1.1 不修改。

---

## §2 出厂内容清单

### 出厂 cos-context.md（干净的 CSF 模板）

- §A 保留完整的框架说明（项目背景/角色/加载链/引擎机构/触发索引/全局红线）
- §B 清空为模板状态（空全景图、空三元组指针）
- `triplets/` 目录仅含 `_index.md`（空索引），首次会话由参谋长建立第一个三元组文件
- §C 清空（标注"等待首次会话"）
- §D 清空（标注"等待首次会话"）
- §收件箱 清空

### 出厂预置提示词（首次启动自动生成 5组7条）

| 分组 | 提示词 | 用途 |
|---|---|---|
| 开局 | 标准开局 | 标准CSF开局协议 |
| 开局 | 聚焦式开局 | 聚焦特定关注点的开局 |
| 收尾 | 标准收尾 | 标准CSF收尾协议 |
| 收尾 | 快速收尾 | 精简收尾 |
| 立项 | 快速立项 | 触发立项协议 |
| 修复 | Bug修复 | 触发BugFix协议 |
| 复盘 | 会话复盘 | 回顾会话沉淀经验 |

### 出厂 csf-lite/ 内核文件（只读，来自 CSF v4-live 模板）

所有 core/、protocols/、knowledge/ 下的文件标记为 `is_factory=True`，Clarity 标签3中禁止删除。

---

## §3 构建与发布流程

### 发布前检查清单

- [ ] cos-context.md 已替换为干净出厂模板
- [ ] csf-clarity/ 已清空（无开发残留）
- [ ] csf-lite/workspace/ 已创建（空目录）
- [ ] 全量测试通过（397/397）
- [ ] build.bat 执行成功
- [ ] clarity.exe 已部署到 csf-lite/
- [ ] 在 pws-demo 中完成首次启动验证

### 构建命令

```batch
cd clarity-app
build.bat
```

### 打包命令（zip）

```powershell
Compress-Archive -Path project-workspace\* -DestinationPath CSF-Lite-v1.1.zip
```

---

## §4 用户首次启动流程

```
用户解压 project-workspace.zip
  → 进入 csf-lite/ 文件夹
  → 双击 clarity.exe
  → 自动创建 csf-clarity/ 完整目录树
  → 自动生成 5组7条 出厂提示词
  → 三标签就绪：
      标签1「提示词」— 7条预设可立即使用
      标签2「当前context」— cos-context.md 模板待用户填写
      标签3「CSF规范」— 出厂内核文件可浏览
  → 用户按 QUICKSTART.md 指引，在标签2中填写项目信息
  → 开始首次 CSF 会话
```

---

## §5 v1.1 待修改项

> 详见 TP-033 README
