# Clarity 使用手册

> 个人参考 · 打包/部署/使用/数据全景
> 版本: 2026-06-25

---

## 一、路径关系

### 核心三角

```
{workspace}/                    ← 项目根（各种尝试/）
├── csf-lite/                   ← 运行目录（exe 在此，内核文件在此）
│   ├── clarity.exe             ← 主程序
│   ├── cos-context.md          ← 参谋长引擎（标签2操作对象）
│   ├── dev-context.md          ← 开发者引擎
│   ├── core/                   ← 角色/规范内核（5文件）
│   ├── protocols/              ← 操作规程（13文件）
│   ├── knowledge/              ← 经验库（methods/redlines/crafts）
│   ├── staging/                ← AI中转目录（pending.md）
│   ├── workspace/              ← 用户工作区（空目录，预留给客户项目）
│   ├── README.md + QUICKSTART.md
│
├── csf-clarity/                ← 私有数据目录（运行时产物，AI不可访问）
│   ├── prompts/                ← 标签1：提示词
│   ├── sections/               ← 标签3：段库（版本快照）
│   ├── templates/              ← 标签2：上下文模板
│   ├── backups/                ← 标签2/3：备份（files/baselines）
│   ├── draft.json              ← 标签2：草稿数据
│   ├── file_meta.json          ← 标签3：文件元信息
│   ├── section_meta.json       ← 标签2：段元信息
│   └── scenes.json             ← 标签1：场景变量
│
└── clarity-app/                ← 源码目录（开发用，不参与运行）
    ├── src/                    ← Python 源码
    ├── build.bat               ← 构建脚本
    └── clarity.spec            ← PyInstaller 配置
```

### 路径判定（config.py）

| 模式 | `_APP_DIR` | `CSF_LITE_ROOT` | `CSF_CLARITY_DIR` |
|---|---|---|---|
| 开发 | `clarity-app/` | `../csf-lite` | `../csf-clarity` |
| 发布（exe） | `csf-lite/`（exe所在目录） | `csf-lite/` | `../csf-clarity` |

> **关键约束**：`clarity.exe` 必须放在 `csf-lite/` 内。`csf-clarity/` 必须与 `csf-lite/` 同级。

### 交付包结构（project-workspace/）

```
project-workspace/              ← 压缩此文件夹发给用户
├── csf-lite/                   ← 内核 + exe
│   ├── clarity.exe
│   ├── core/ protocols/ knowledge/
│   ├── cos-context.md（干净出厂模板，含完整 @SECTION 哨兵）
│   ├── dev-context.md / README.md / QUICKSTART.md
│   └── workspace/（空）
└── csf-clarity/                ← 首次启动自动填充
    ├── prompts/                ← 用户预置提示词（如为空则自动生成7条出厂预设）
    ├── sections/               ← 空目录（首次运行自动导入基线模版时填充）
    ├── templates/              ← 空目录（首次运行自动导入基线模版时填充）
    ├── backups/                ← 空目录（首次运行创建 v1-出厂基线）
    ├── file_meta.json          ← 空 {}
    └── scenes.json             ← 默认场景
```

---

## 二、构建与发布

### 构建命令

```batch
cd clarity-app
build.bat
```

### 构建流程（4步）

```
[1/4] pytest 全量测试 → 不通过则中止
[2/4] bump_version.py 自动递增小版本号
        ├─ 读 main.py 当前版本（如 1.1.23）
        ├─ patch +1 → 写入 main.py
        ├─ 读 项目根目录 RELEASE_NOTES.txt（空则写"例行发布"）
        └─ 追加 clarity-dev/RELEASE.md（版本号 + 日期 + 更新内容）
[3/4] PyInstaller 打包 → dist/clarity.exe（单文件 ~34MB）
[4/4] copy dist/clarity.exe → csf-lite/clarity.exe
```

> **版本号**：每次构建自动从 `main.py` 读取并 +0.0.1。发布记录见 `clarity-dev/RELEASE.md`。
> **RELEASE_NOTES.txt**：位于项目根目录。开发者每次改动后追加一行（日期 + 类型 + 说明）。参谋长开局扫此文件了解累积变更。构建时自动收割到 RELEASE.md 后清空。

### 打包为 zip

```powershell
Compress-Archive -Path release\project-workspace\* -DestinationPath CSF-Lite-v1.x.zip
```

---

## 三、首次运行：数据初始化全景

### 启动时序

```
clarity.exe 启动
  │
  ├─ 1. ensure_directories()     ← 创建目录树（幂等）
  │     ├─ csf-clarity/sections/.versions/
  │     ├─ csf-clarity/backups/files/ + baselines/
  │     ├─ csf-clarity/templates/
  │     ├─ csf-clarity/prompts/
  │     ├─ csf-clarity/file_meta.json（空 {}）
  │     ├─ csf-lite/staging/
  │     └─ 自动创建 v1-出厂基线（遍历 csf-lite/ 下出厂文件 → 入备份库）
  │
  ├─ 2. 组装依赖（FileSystemOps、BackupEngine、PromptStore…）
  │
  ├─ 3. 标签1 初始化（PromptTab）
  │     ├─ list_groups() → prompts/ 下无目录 → 空
  │     ├─ initialize_factory_presets() 触发！
  │     │     └─ 创建 5 分组 7 条提示词（开局×2/收尾×2/立项×1/修复×1/复盘×1）
  │     └─ _rebuild_tree() 渲染导航树
  │
  ├─ 4. 标签2 初始化（ContextTab）
  │     ├─ 读取 cos-context.md → 解析 @SECTION 哨兵对
  │     ├─ 首次运行：templates/ 为空 → 自动导入 cos-context.md 为基线模版
  │     │     └─ 解析 @SECTION 哨兵 → 各段入库（sections/.versions/）→ 生成模版 JSON
  │     ├─ 读取 section_meta.json + draft.json
  │     └─ 渲染段列表（含基线模版）、版本Tab、草稿Tab
  │
  └─ 5. 标签3 初始化（SpecsTab）
        ├─ 读取 file_meta.json
        ├─ 按 FACTORY_ROOTS 判定出厂文件（core/ protocols/ knowledge/ ...）
        └─ 渲染规范文件树
```

### 各标签数据来源

| 标签 | 读取（磁盘 → 内存） | 写入（内存 → 磁盘） | 数据格式 |
|---|---|---|---|
| **标签1 提示词** | `prompts/{分组}/*.md` | 同左，原子写（tmp→replace） | .md（YAML frontmatter + 正文） |
| **标签1 收藏** | `prompts/_favorites.json` | 同左 | JSON 数组 |
| **标签1 分组排序** | `prompts/_group_order.json` | 同左（拖拽产生） | JSON 数组 |
| **标签1 场景** | `scenes.json` | 同左 | JSON |
| **标签2 段列表** | `cos-context.md`（@SECTION 哨兵） | `cos-context.md`（原地改写哨兵对） | Markdown + HTML注释哨兵 |
| **标签2 草稿** | `draft.json` | 同左 | JSON |
| **标签2 模板** | `templates/*.json` | 同左（导入/存为模版） | JSON（TemplateData） |
| **标签2 版本** | `sections/.versions/{段名}.v{N}.md` | 同左 + `backups/files/` | .md（YAML frontmatter + @SEC:CONTENT） |
| **标签2 staging** | `staging/pending.md` | 同左 | .md（含 @STAGING 指令） |
| **标签3 规范文件** | `csf-lite/core/ protocols/ knowledge/` | 标签3编辑器 → `csf-lite/` 原路径 | .md |
| **标签3 元信息** | `file_meta.json` | 同左 | JSON |
| **标签3 备份** | `backups/baselines/` `backups/files/` | 同左 | .md + JSON |

---

## 四、数据变迁历史

### 版本演进中的关键路径迁移

| 版本 | 变更 | 旧路径 | 新路径 |
|---|---|---|---|
| V1→V2 | 数据库→纯文件 | `clarity.db`（SQLite） | `csf-clarity/` 文件树 |
| V2→V3 | csf-clarity 移出 csf-lite | `csf-lite/csf-clarity/` | `csf-clarity/`（与 csf-lite 平级） |
| V3→V4 | 标签2 重构 | 旧 service 层（版本链+sqlite） | 新 service（纯文件+哨兵） |

### 当前数据生命周期

```
[出厂状态]                        [首次运行后]                    [日常使用中]
csf-lite/                        csf-lite/                      csf-lite/
  core/          ──不变──→         core/          ──用户编辑──→    core/（可能修改）
  protocols/     ──不变──→         protocols/     ──用户编辑──→    protocols/
  cos-context.md ──模板──→         cos-context.md ──每次会话──→    cos-context.md（持续增长）
                                   
csf-clarity/                      csf-clarity/                   csf-clarity/
  file_meta.json  {}              file_meta.json  元信息         file_meta.json
  (无 prompts/)                   prompts/         7条预设        prompts/        用户创建+拖拽
  (无 sections/)                  sections/        基线模版段库   sections/       版本快照累积
  (无 backups/)                   backups/         v1-出厂基线    backups/        基线+快照累积
  (无 templates/)                 templates/       基线模版       templates/      用户模板（含自动导入的基线）
  (无 draft.json)                 draft.json       空             draft.json       草稿数据
  (无 scenes.json)                scenes.json      空             scenes.json      场景变量
```

---

## 五、关键文件说明

### csf-lite/ — 运行目录

| 文件 | 性质 | 说明 |
|---|---|---|
| `clarity.exe` | 主程序 | PyInstaller 单文件，含 Python+PyQt6+源码 |
| `cos-context.md` | 读写 | 参谋长 context，标签2的操作对象。含 @SECTION 哨兵对 |
| `dev-context.md` | 只读 | 开发者 context（可选角色） |
| `core/` | 出厂只读 | 5 文件：守则、协作规范、参谋长/开发者 instructions、方法论 |
| `protocols/` | 出厂只读 | 13 操作规程（立项/修复/收尾/E8/FLDD...） |
| `knowledge/` | 出厂 | 经验库（methods/redlines/crafts） |
| `staging/` | 运行时 | AI 中转文件 `pending.md` |
| `workspace/` | 预留 | 用户项目文件存放处 |

### csf-clarity/ — 私有数据目录

| 文件/目录 | 产生时机 | 说明 |
|---|---|---|
| `prompts/` | 首次启动 | 提示词分组目录。每条一个 .md。`_favorites.json` + `_group_order.json` |
| `sections/` | 首次启动 | 段版本快照。`{段名}.v{N}.md` 存储在 `.versions/` 下 |
| `templates/` | 首次启动 | 上下文模板 JSON。首次运行自动导入 cos-context.md 生成基线模版 `cos-context（导入）.json` |
| `backups/files/` | 首次备份 | 文件版本快照 |
| `backups/baselines/` | 首次启动 | `v1-出厂基线.md` + 后续基线 |
| `draft.json` | 首次草稿 | 标签2 草稿系统数据 |
| `file_meta.json` | 首次启动 | 标签3 文件元信息（出厂标记等） |
| `section_meta.json` | 首次操作 | 标签2 段说明信息 |
| `scenes.json` | 首次操作 | 标签1 场景变量。格式：`{"current": "场景名", "scenes": {"default": {"变量": "值"}, ...}}`。打包分发前应清理——保留 `default` 场景，删除其余自用场景（见 §六·场景变量清理） |

### 出厂文件判定（FACTORY_ROOTS）

以下路径的文件被标记为出厂文件（标签3 中禁止删除，首次启动纳入 v1-出厂基线）：

```
core/                     ← 5 角色/规范文件
protocols/                ← 13 操作规程
knowledge/methods/        ← 经验库·方法
knowledge/redlines/       ← 经验库·红线
knowledge/crafts/         ← 经验库·工艺
cos-context.md            ← 参谋长引擎
dev-context.md            ← 开发者引擎
README.md / QUICKSTART.md ← 入门文档
```

---

## 六、多客户/多场景分发

### 核心思路

不改源码，仅替换 `project-workspace/` 中的文件，即可为不同客户打包不同版本。

### 两层定制

| 定制层 | 位置 | 首次启动效果 | 需要重打包？ |
|---|---|---|---|
| **规则与模板** | `csf-lite/core/` `protocols/` `knowledge/` `cos-context.md` | 客户看到你的行业规则、操作规程、初始 context | ❌ 不改源码 |
| **初始提示词** | `csf-clarity/prompts/{分组}/*.md` | 客户看到你的预置提示词（跳过程序硬编码的 7 条出厂预设） | ❌ 不改源码 |

### 为什么放 prompts 就能跳过出厂预设？

```python
# prompt_service.py — 仅在 prompts/ 为空时才生成出厂预设
def initialize_factory_presets(self):
    groups = self._store.get_groups()
    if groups:              # ← 只要 prompts/ 下有任意目录，就跳过
        return False
    # ... 创建 5组7条 ...
```

### 发布包模板

```
project-workspace/                    ← 压缩这个文件夹
├── csf-lite/                         ← 规则层（可自由定制）
│   ├── clarity.exe                   ← 主程序（不改）
│   ├── core/                         ← 守则/协作规范/角色定义
│   ├── protocols/                    ← 操作规程
│   ├── knowledge/                    ← 经验库
│   ├── cos-context.md                ← 参谋长初始引擎
│   ├── dev-context.md                ← 开发者引擎（可选）
│   ├── README.md                     ← 面向客户的说明
│   └── workspace/                    ← 空目录，客户的项目文件放这里
│
└── csf-clarity/                      ← 数据层（可自由定制）
    ├── prompts/                      ← 预置提示词
    └── scenes.json                   ← 场景变量（仅保留 default，见下方清理方法）
        ├── 日常/
        │   ├── 晨会检查清单.md
        │   └── 日报模板.md
        ├── 项目/
        │   └── 快速立项.md
        └── _favorites.json           ← 可选：预置收藏列表
```

> **注意**：`csf-clarity/` 下只需要放你想预置的内容。`sections/`、`backups/`、`templates/` 等会由首次运行自动创建。

### 三种典型场景

#### 场景 A：通用分发（不改任何内容）

直接打包 → 客户首次启动自动生成 7 条通用预设提示词。

#### 场景 B：行业定制（替换规则+预置提示词）

```
1. 把该行业 CSF 规则文件放入 csf-lite/core/ protocols/ knowledge/
2. 把该行业的初始提示词放入 csf-clarity/prompts/
3. 修改 csf-lite/README.md 写清行业说明
4. 压缩 project-workspace/ → 发给客户
```

#### 场景 C：空白启动（让客户从零开始）

```
放入一个空的 csf-clarity/prompts/（或放一个隐藏文件如 .gitkeep）→ 出厂预设被跳过
→ 客户打开是空白提示词 + 空白 context → 完全自主填写
```

### 场景变量清理

分发前清理 `csf-clarity/scenes.json`：**保留 `default` 场景中的变量，删除其他自用场景**。

```json
// 清理前（你的开发环境）
{
  "current": "我的测试场景",
  "scenes": {
    "default": { "project_name": "MyProject" },
    "我的测试场景": { "project_name": "test", "debug": "true" },
    "客户A场景": { "project_name": "ClientA" }
  }
}

// 清理后（发给用户）— 只保留 default，current 改回 default
{
  "current": "default",
  "scenes": {
    "default": { "project_name": "MyProject" }
  }
}
```

> 如果 `default` 中也没有需要预置的变量，保留空对象 `"default": {}` 即可。

### 三步发布清单

```batch
# 1. 构建最新 clarity.exe（自动递增版本号 + 写 RELEASE.md）
cd clarity-app && build.bat

# 2. 按需替换 csf-lite/ 下的规则文件和 csf-clarity/prompts/ 下的提示词
#    清理 csf-clarity/scenes.json（保留 default，删其余场景，见上方清理方法）

# 3. 打包 zip 或使用标签4「自举」一键打包
Compress-Archive -Path release\project-workspace\* -DestinationPath MyProduct.zip
```

> 也可以直接在 Clarity 中点击标签4「凡人皆知己所欲」→「打包CSF环境」按钮，一键完成步骤 2+3。

---

## 七、常见操作速查

```batch
# 打包发布（全量测试 → 版本号+1 → PyInstaller → 部署）
cd clarity-app && build.bat

# 预览下一版本号（不实际修改）
cd clarity-app && python bump_version.py --dry-run

# 查看当前版本号
cd clarity-app && python bump_version.py --current

# 填写发布说明后打包
notepad clarity-app\RELEASE_NOTES.txt   # 写更新内容
cd clarity-app && build.bat              # 自动写入 RELEASE.md

# 跳过测试，仅打包（需要先清理 build/）
cd clarity-app && python -m PyInstaller clarity.spec --noconfirm
copy dist\clarity.exe ..\csf-lite\

# 重置所有数据（删除 csf-clarity/，下次启动自动重建）
rmdir /s /q csf-clarity

# 仅重置标签1数据
rmdir /s /q csf-clarity\prompts

# 仅重置场景变量（保留 default 空场景）
echo {"current":"default","scenes":{"default":{}}} > csf-clarity\scenes.json

# 打 zip 发布包
Compress-Archive -Path release\project-workspace\* -DestinationPath CSF-Lite.zip
```

---

## 附录：待开发需求

### 需求A：配置窗口（暂缓）

在「置顶」按钮旁增加「配置」按钮，点击弹出配置窗口，承载未来的所有可配置项。

- **当前状态**：暂无实际配置需求，UI 和数据路径均已自洽
- **开发条件**：等第一个真实配置需求出现时一步到位实现

---

### 需求B：标签4「自举」— 用户自助打包CSF环境 ✅ 已开发

#### 概述

标签栏第4个标签「凡人皆知己所欲」。包含个人宣传资料/联系方式（静态文字）+「打包CSF环境」按钮。点击按钮后，自动将当前工程的 CSF 环境打包为一个干净的 zip，用户可以发给他人分享。

#### 实现方式

- **代码**：`clarity-app/src/ui/bootstrap_tab.py`（BootstrapTab 类）
- **打包函数**：`_package_csf()` — 在临时目录中组装，不修改磁盘原文件
- **清理函数**：`clean_context_file()` — 截断 §B 之后内容，替换为干净模板（含正确 @SECTION 哨兵）

#### 打包流程（运行时）

```
点击「打包CSF环境」
  │
  ├─ 1. 弹出保存对话框 → 用户选择 .zip 路径
  ├─ 2. 创建临时目录
  ├─ 3. 复制 csf-lite/（排除 staging/）
  ├─ 4. 复制 csf-clarity/prompts/（保留用户提示词）
  ├─ 5. 清理段库和模版：创建空的 sections/、templates/、backups/ 目录
  ├─ 6. 清洁 cos-context.md（§B-§收件箱 替换为干净模板，保留 @SECTION 哨兵）
  ├─ 7. 清洁 dev-context.md（同上）
  ├─ 8. 重置 JSON：file_meta.json、section_meta.json、scenes.json
  └─ 9. 压缩为 zip → 清理临时目录
```

#### 打包输出

```
{时间戳}.zip
├── csf-lite/
│   ├── clarity.exe
│   ├── core/ protocols/ knowledge/       ← 原样保留
│   ├── cos-context.md                    ← 清理后（§A保留，§B-收件箱空白模板，含完整 @SECTION 哨兵）
│   ├── dev-context.md                    ← 清理后
│   ├── README.md / QUICKSTART.md
│   └── workspace/                        ← 空目录
│
└── csf-clarity/
    ├── prompts/                          ← 保留（用户的提示词集合）
    ├── sections/                         ← 空目录（首次运行自动导入基线模版时填充）
    ├── templates/                        ← 空目录（首次运行自动导入基线模版时填充）
    ├── backups/                          ← 空目录
    ├── file_meta.json                    ← {}（空）
    ├── section_meta.json                 ← {}（空）
    └── scenes.json                       ← {"current":"default","scenes":{"default":{}}}
```

#### cos-context.md 清理规则

| 段 | 操作 |
|---|---|
| §A 角色与规范 | 保留（CSF 框架，含 @SECTION:A 哨兵对） |
| §B 任务窗口 | 替换为空白模板（含 @SECTION:B 哨兵对） |
| §C 上次会话 | 替换为空白模板（含 @SECTION:C 哨兵对） |
| §D 下次会话 | 替换为空白模板（含 @SECTION:D 哨兵对） |
| §收件箱 | 替换为空白模板（含 @SECTION:INBOX 哨兵对） |

> ⚠️ **关键**：清理后的 cos-context.md 必须保留完整的 @SECTION 哨兵对（A/B/C/D/INBOX），否则标签2 只能显示 §A 一个段。

#### 首次运行：基线模版自动导入

打包后的环境首次启动时，标签2 检测到 `templates/` 为空，自动将 `cos-context.md` 导入为基线模版：

```
首次启动
  └─ ContextService.load_templates() → []（空）
       └─ import_context(cos-context.md)
            ├─ 解析 @SECTION 哨兵对 → 5个段
            ├─ 各段入库 → sections/.versions/{段名}.v1.md
            └─ 生成模版 → templates/cos-context（导入）.json
```

> 这与标签3 的行为一致：标签3 自动发现文件系统中的 CSF 规则文件，标签2 自动发现并导入 cos-context.md。用户无需手动操作。

#### 排除列表

| 排除 | 原因 |
|---|---|
| `csf-clarity/sections/` | 用户段版本快照，私密（打包时创建空目录，首次运行由基线模版填充） |
| `csf-clarity/templates/` | 用户模板（打包时创建空目录，首次运行自动导入基线模版） |
| `csf-clarity/backups/` | 用户备份历史（打包时创建空目录） |
| `csf-clarity/draft.json` | 用户草稿（不打包，运行时自动创建） |
| `csf-clarity/file_meta.json` | 重置为空 `{}` |
| `csf-clarity/section_meta.json` | 重置为空 `{}` |
| `csf-clarity/scenes.json` | 重置为默认场景 |
| `csf-lite/staging/` | 用户中转文件 |
