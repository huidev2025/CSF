# CSF Lite — 实战级人机协作框架

> 版本: v1.0 | 语言: 简体中文
> **CSF Lite = csf-minimal 的实战升级。** 如果你还没看过 csf-minimal，建议先花 5 分钟读 [csf-minimal/README.md](../csf-minimal/README.md)。

---

## 这是什么

**csf-lite** 是 CSF（协作规范框架）的**实战级版本**——面向个人和小团队，用于在真实项目中落地人机协作。

csf-minimal 让你**体验差异**（一个文件、5 分钟）。csf-lite 让你**跑真实项目**——它提供了一套完整的文件体系：引擎、三元组、协议库、经验库、守则。

**一句话**：把 `cos-context.md` 交给 AI，AI 就知道自己是谁、在做什么、怎么做、做完怎么收尾。你只需要表达业务真相、确认方向、做价值判断。

---

## 核心理念：自举

csf-lite 管 csf-lite 自己。你眼前这个 `csf-lite/` 目录，就是用 csf-lite 在维护的——包括它的介绍页、版本发布、问题跟踪。

这意味着：**你克隆这个仓库，就有了一个可以立刻开始工作的 AI 参谋长**。不需要配置、不需要注册、不需要 API key（除了你的 LLM 对话窗口）。

---

## 目录结构

```
csf-lite/
├── cos-context.md              ← 引擎（你交给 AI 的第一个文件）
├── dev-context.md              ← 开发者引擎（有开发者时使用）
├── QUICKSTART.md               ← 新项目初始化指南
├── README.md                   ← 本文件
├── core/                       ← 身份内核与规范
│   ├── 参谋长-instructions.md   ← AI 的角色定义
│   ├── 参谋长-方法论.md         ← AI 的工作方法
│   ├── 开发者-instructions.md   ← 开发者角色定义
│   ├── 守则.md                  ← 全员最高纲领（5 条元原则）
│   └── 协作规范.md              ← 多角色协作接口
├── triplets/                   ← 三元组文件（目的+方法+资源+进度）
│   ├── _index.md               ← 活跃三元组索引
│   └── _TEMPLATE.md            ← 新建三元组的模板
├── protocols/                  ← 操作规程（按需加载）
│   └── _index.md               ← 触发词 → 协议文件映射
├── knowledge/                  ← 经验库（按需检索）
│   └── _index.md               ← 触发词 → 经验文件映射
├── workspace/                  ← 项目运行文件
│   ├── DEVNOTES.md             ← 研发笔记（架构决策）
│   ├── bug-tracker.md          ← Bug 跟踪表
│   └── owner-inbox.md          ← Owner 收件箱
├── sessions/                   ← 会话日志（AI 创建和维护）
└── scenarios/                  ← 场景适配（可选）
```

---

## 核心机制：引擎机构

`cos-context.md` 是 csf-lite 的心脏。AI 读它，就进入工作状态。它定义了完整的会话工作流：

```
开局                               中段                         收尾
  │                                  │                            │
  ├─ 加载（读 §A + 加载链）           ├─ 按 L3 计划执行              ├─ 补全笔记
  ├─ 建 log（coslog-NNN.md）         ├─ 笔记伴随（每回合记录）       ├─ 覆写 §C（上次结论）
  ├─ L1 brief（确认身份+三元组）       ├─ 目的校准（每产出前自问）     ├─ 覆写 §D（下次计划）
  ├─ L2 brief（精读三元组→宏观判断）   ├─ 经验捕获（踩坑当场记）       ├─ 备忘区更新
  └─ L3 brief（精读资源→执行计划）     └─ DEVNOTES 实时更新          └─ 经验归位
```

**关键设计**：

- **基线-Log 分离**：context 只保留最新状态（覆写式），session 笔记保留完整过程（追加式）。AI 每次醒来读的是"脱水"后的高浓度信息。
- **触发索引**：协议和经验不预加载——遇到对应场景时才按触发词去读。上下文空间永远留给当前任务。
- **三元组对齐**：目的 + 方法 + 资源。任何时候都在问：目的是什么、方法对不对、资源够不够。

---

## 和 csf-minimal 的关系

| | csf-minimal | csf-lite |
|---|---|---|
| **定位** | 教学体验版 | 实战落地版 |
| **文件数** | 3 个 | ~30 个 |
| **机制** | 单文件 context.md | 完整引擎 + 三元组 + 协议库 + 经验库 |
| **适用** | 5 分钟感受差异 | 真实项目长期运行 |
| **角色** | Owner + AI 助手 | Owner + 参谋长（+ 可选开发者） |

**升级路径**：先用 csf-minimal 跑一个小任务感受一下 → 觉得有用 → 复制 csf-lite 到你的项目 → 告诉 AI「阅读 cos-context」→ 开始。

---

## 三步上手

### 1. 获取 csf-lite

**方式 A — 下载自举包**：从 [Releases](../../releases) 下载 `CSF-lite-*.zip`，解压到你的项目根目录。

**方式 B — 克隆仓库**：
```bash
git clone https://github.com/huidev2025/CSF.git
# csf-lite/ 目录即完整框架
```

### 2. 填写项目信息

打开 `csf-lite/cos-context.md`，找到 `§A > 项目与团队`，填入一行：

```
**项目**：你的项目名 — 一句话描述
```

这是唯一需要你手动编辑的地方。其余全部由 AI 在会话中维护。

### 3. 启动

打开你的 LLM 对话窗口（ChatGPT / Claude / Copilot Chat / …），说：

> **「阅读 cos-context」**

然后把 `cos-context.md` 的内容粘贴进去（或让 AI 读取文件）。AI 会：
1. 自报身份（"我是参谋长……"）
2. 判断这是新项目 → 进入初始化流程
3. 向你提几个问题（项目目的、性质、起点）
4. 建立第一个三元组 + 填写全景图
5. 开始和你一起推进项目

之后每次新会话，都从「阅读 cos-context」开始。AI 会自动接上上次的进度。

> 💡 **提示**：详细初始化流程见 [QUICKSTART.md](QUICKSTART.md)。

---

## 什么时候用 csf-lite

- 你有一个**需要跨多轮对话**才能完成的项目
- 你希望 AI **记住上下文**（架构决策、设计约定、进度状态）
- 你不想每次新会话都**重新解释一遍**项目背景
- 你在用 csf-minimal 觉得好用，但想要**更强的结构和纪律**

## 什么时候不需要

- 单次问答（"帮我写个函数"）→ 直接用 LLM 就行
- 项目非常小（1-2 次会话就结束）→ csf-minimal 可能更合适
- 你更喜欢自由对话、不想被结构约束 → CSF 不适合你

---

## 团队配置

csf-lite 支持两种模式：

| 模式 | 角色 | 说明 |
|---|---|---|
| **双人模式** | Owner + 参谋长 | 你表达业务真相、做决策；AI 理解、规划、设计。适合策划/设计/研究类项目。 |
| **三角模式** | Owner + 参谋长 + 开发者 | 增加一个开发者角色（可以是另一个 AI 会话），按参谋长出的任务书实现代码。适合软件开发项目。 |

**不需要开发者**：如果你的项目不涉及写代码（策划、研究、写作），直接用双人模式。忽略 `dev-context.md` 即可。

---

## Clarity：配套桌面程序

[Clarity](../clarity-dev/) 是一个轻量级 Windows 桌面应用（PyQt6），辅助你编辑 csf-lite 中的提示词和区段文件。它不是必选项——你完全可以用任何文本编辑器操作 csf-lite 的文件。Clarity 只是让操作更顺手。

详见 [Clarity 开发者参考](../clarity-dev/DEVELOPER.md) 和 [Clarity 使用手册](../csf-lite-doc/Clarity-使用手册.md)。

---

## 自举包与 Release

csf-lite 仓库本身就是一个**自举案例**：使用 csf-lite 管理 csf-lite 的开源发布。从 [Releases](../../releases) 页面可下载完整自举包（`CSF-lite-*.zip`），解压即用。

自举包内含：
- 完整 `csf-lite/` 框架（引擎 + 协议 + 经验）
- `Clarity` 桌面程序（可选）
- 示例项目结构，可直接作为新项目模板

详细发布说明见 [RELEASE.md](../RELEASE.md)（待补充）。

---

## 许可证

csf-lite 采用 [CC BY-NC 4.0](../LICENSE) 许可。个人/学术/非营利免费使用；企业商用需联系 Owner。

```
© 2025 zhanghui. CC BY-NC 4.0. https://github.com/huidev2025/CSF
```

---

## 下一步

- 📖 读完 [QUICKSTART.md](QUICKSTART.md) 了解初始化全流程
- 🔧 浏览 [core/](core/) 了解 AI 的身份内核与工作规范
- 📋 看 [triplets/_TEMPLATE.md](triplets/_TEMPLATE.md) 了解三元组结构
- 💬 有问题？[GitHub Issues](https://github.com/huidev2025/CSF/issues) 或邮件 dapangangang@gmail.com
