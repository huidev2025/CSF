---
title: CSF — 协作规范框架 (Collaboration Specification Framework)
permalink: /index.html
layout: default
---

# CSF — Collaboration Specification Framework

**简体中文** | [English](README_en.md)

> 一种在 LLM 本性之内、用「自然语言 + 目的」设计人机协同工作方式的工程方法。
> A human-AI collaboration framework that works **with** LLM nature, not around it. Built on natural language and purpose — making RAG, agent orchestration, and elaborate prompt engineering **unnecessary, not unavailable**. Home of the Pang Principle.

📖 **网页阅读 / Read on the web**：<https://huidev2025.github.io/CSF/>

---

## 这是什么

AI 辅助开发的主流做法把 LLM 的约束（上下文有限、记忆短、行为不可预测）当作要用技术克服的缺陷——RAG、向量库、Agent 编排、越来越精确的提示词。

CSF 选择另一条路：**承认这些约束为事实，在约束内设计**。结果是技术栈消失了——不是被替换，是它们的存在理由消失了。

详见引言：[引言：你们在拿着前朝的尚方宝剑，斩当朝的官](引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md)

---

## 从哪开始读

按顺序，五分钟可以开始：

1. **[引言](引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md)** —— 为什么需要 CSF，乓定律
2. **[QUICKSTART.md](QUICKSTART.md)** —— 上手指引（中英文）：你不需要会代码，只需要把目标说清楚
3. **[csf-minimal/README.md](csf-minimal/README.md)** —— CSF 最小教学版，30 秒说明 + 三个核心差异
4. **[csf-minimal/context.md](csf-minimal/context.md)** —— 你可以直接复制使用的协作记忆模板
5. **[csf-minimal/体验对比指南.md](csf-minimal/体验对比指南.md)** —— A/B 实验设计，亲自感受差异

想读思想原稿 / Deeper Theory:

6. **[essays/ — CSF 旗舰专栏书架](essays/README.md)** —— 《与智能共事》中英双语旗舰连载，深度剖析四大工程系统及协作哲学

想看 CSF 在真实项目里是什么样子的 / Want to see CSF in action：

7. **[cases/bang-v3/ — 实战案例：375 次会话节选](cases/bang-v3/README.md)** —— 三段原始对话日志，展示 AI 拒绝错误决策、自主安排复杂计划、用语义日志快速定位根因的四个具体证据

> **第一次来？** 直接看 **[QUICKSTART.md](QUICKSTART.md)** 就够了。
> **First time here?** Read **[QUICKSTART.md](QUICKSTART.md)** first.

---

## 可视化导图 / Visual Guides

两张交互式图谱，帮你在 2 分钟内理解 CSF 在 AI 编程领域的位置：

| 图谱 | 中文 | English |
|---|---|---|
| **AI 编程演进版图**（5 阶段时间线：从补全工具 → 自主 Agent → CSF） | [查看](https://huidev2025.github.io/CSF/visuals/ai-coding-landscape-zh.html) | [View](https://huidev2025.github.io/CSF/visuals/ai-coding-landscape-en.html) |
| **三流派对比与 CSF 定位图谱**（Autonomous Agent / SDD / CSF 三条路线的假设与瓶颈） | [查看](https://huidev2025.github.io/CSF/visuals/csf-positioning-zh.html) | [View](https://huidev2025.github.io/CSF/visuals/csf-positioning-en.html) |

---

## 仓库结构

```
csf/
├── README.md                     # 本文件
├── QUICKSTART.md                 # 上手指引（中英双栏）
├── LICENSE                       # CC BY-NC 4.0
├── CONTACT.md                    # 联系方式（中英双栏）
├── 引言v3：...md                  # 对外引言（宣言）
├── Manifesto-v3-You-Are-Fighting-the-Wrong-War.md   # 英文版宣言
├── assets/                       # 对外资源（二维码等）
├── _dlog/                        # 公开的真实工作日志（协作示范）
├── cases/                        # 实战案例（原始对话日志节选）
├── essays/                       # 旗舰专栏（中英双语连载《与智能共事》 + 历史学术手稿）
└── csf-minimal/                  # 教学最小版
    ├── README.md
    ├── context.md                # 给读者用的空白模板
    └── 体验对比指南.md
```

---

## CSF 全景 / The CSF Stack

CSF 不是单一文档，是一套**有纵深、已迭代到第三版**的体系。按使用门槛与投入深度分三档：

| 档位 | 适合谁 |
|---|---|
| **csf-minimal** | 任何人，5 分钟体验差异 |
| **csf-lite** | 个人 / 小团队，真实项目落地 |
| **csf-full** | 中小研发团队 / 企业级工程化落地 |

**csf-full 是什么**：约 **60 个**核心规程与经验文件构成的**工程化人机协作管理系统**——四层工程架构（语义管理 / 协作通信 / 质量保障 / 演化系统）+ 三角色协作（Owner / 参谋长 / 开发者）+ W-协议三档质检 + E8 五阶段经验升迁 + D3 三谱系知识路由。

### 三个工程级设计：放在行业坐标里看

CSF v3 在 **不写一行代码、纯文本** 的前提下，构建了一个 **高内聚、低耦合的软件工程管理系统**。其核心由三个工程设计支撑：

#### ① 自举与自持（Self-Sustaining）

**行业现状**：使用 LLM 时，人必须充当"调度器"——翻 SOP、提醒 AI 该读什么、该用哪个工具，心智负担极重。

**CSF v3 的解法**：AI 实现了**全能力自持**。`context.md` 的"引擎机构"定义了严密的开局协议（L1 加载 → L2 任务级宏观对齐 → L3 具体计划），AI 读完 `context.md` 自己就知道加载哪些链路、去哪里取资源、如何建立 `session-NNN.md` 记录、何时校准、何时收尾。**控制权从人脑移交给了 AI 的"自我规程"**——人的角色从"调度器"压缩为"司令官"，只负责确认与纠偏。

#### ② 基线-Log 分离（Hot/Cold Separation in Filesystem）

**行业现状**：普通 AI 对话把新旧信息混在一条长聊天记录里，触发"Lost in the Middle"——上下文越长，注意力越涣散。

**CSF v3 的解法**：在文件系统层面实现**冷热分离**——

- **基线层**（`context.md` 等，**覆写式**）：永远只保留最新的当前状态。
- **Log 层**（`session-NNN.md`，**追加式**）：保留完整讨论过程，需要时回溯。

每次新会话启动，AI 读到的都是"脱水"后的高浓度有用信息，从根上规避了大模型注意力涣散的工程缺陷。

#### ③ 多角色物理隔离 + 异步文件通信（Industrial-Grade Multi-Agent）

**行业现状**：CrewAI / AutoGen 这类多 Agent 框架让 AI 之间互相对话——结果是"无限套娃讨论""无效信息轰炸""幻觉互相加强"。

**CSF v3 的解法**：参谋长（设计态）和开发者（执行态）**完全不直接对话**。

- 参谋长把设计转化为 **STB（任务书）**，开发者只读 STB，**禁止**读上游 domain/arch；
- 开发者用**三栏自检**（✅已读懂 / 🟡不确定 / 🔵准备假设）标记理解状态，任一非空 → PENDING 回参谋长，绝不动键盘；
- 通信通过文件落盘（`@MSG:N` 哨兵格式），不是对话。

“隔断 + 确定性反馈”是成熟的工业级软件工程思想，被迁移到了 AI 协作场景上：AI 不在对话中互相启动幻觉，人不在对话中被迫仲裁。

---

### 已被实战验证的事实（不夸大）

CSF v3 在一个**真实双端商业产品的重构项目**（微信小程序 + H5 + 云函数后端）中被持续打磨与验证：

| 维度 | 数字 / 事实 |
|---|---|
| 项目 | 微信小程序 + H5 + 云函数后端，**双端商业产品** |
| 起点 | 仅 **2 份**输入：旧版业务文档 + UI 截图 |
| 过程 | **395 次会话**，Owner **全程不碰代码**（不是"少写"，是"不写"） |
| 已完成 | 架构重新设计 → 主题分包 → 业务切片 → 设计规格 → **底座（除插件外）开发 → 测试验证** |
| 产物 | **44 个**云函数 + **532 个**前后端源码文件 + **132 份**业务计划/规格 + **116 份**业务设计文档 |
| 交付 | 整体底座转交研发继续插件开发和完善 |
| **同时** | CSF 的全套理论与工程方案（**三次版本迭代** v1→v2→v3）在过程中被**同步产出** |

**Owner 的角色一直停留在"目的与判断"这一层**：表达业务真相、校准方向、做价值取舍。架构、分包、设计、编码、测试——CSF 在过程中接管了从"目的"到"可运行代码"之间的全部工程协调。

### 边界——同样诚实地说

- CSF 还**不能**让一个完全不懂软件工程的人独立完成商业产品。Owner 需具备业务判断力与系统性思维，但**不需要会写代码**。
- CSF 揭示了方法论的可能性，**但不表示成熟到可直接使用**。并未经历足够多、不同类型项目的实践验证，所以欢迎参与一起完善。
- CSF 并不替代研发团队——它是一套**让研发团队的人机协作规范化、质量可控、效率提升**的方法。

### 已被证明的事情

1. **它能主动建立并跟踪计划** —— 你眼前看到的这个仓库本身（README、Manifesto、CONTACT、_dlog、commit 历史），就是 CSF 在管理它自己的发布过程。
2. **它能在执行中发现问题，回头复查设计、重新制定修复计划并执行到收敛** —— 见实战案例 dlog-373 到 375。
3. 极高提升了我个人的设计、开发、测试效率和质量。我不懂代码，不写文档。过程中几次严重的设计缺陷都是我自己偷懒导致的，但也都是AI（或CSF规程）发现并修复的。
4. 计划可以变更，AI在整个过程中有很好的延续性：能抬头看路，也能低头干活儿。

#### 看图说话：AI 自己维护、给自己看的项目状态

下面这张图，是 **AI 在 `context.md` 中自己维护、给自己（下次开会话的自己）看的**项目全景图与当前红点。不是给人看的看板，不是事后整理的汇报材料——是 AI 持续在工作流里写、读、覆写的活产物：

<p align="center">
  <img src="assets/project-panorama-and-red-dot.png" alt="CSF v3 项目全景图与当前任务红点（AI 自维护）" width="780" />
</p>

读这张图时，注意几件事：

- 整个项目从 S1 到 M4，主线 + 多次「打岔」（CSF 自身重建、回归试运行、节点统计层、扫描矩阵……）+ 多次计划变更，**AI 始终知道自己现在在哪、来自哪、还要去哪**——位置、来路、去向三维度全程没有丢。
- "🔴 开发红点 / 参谋红点 / 产出位置" 三行让任意一次新会话**零搜索**就能续上工作——这正是基线-Log 分离 + 触发索引的工程效果。
- 项目历经数百次会话、跨工作日、跨主题包、跨人机轮转，**这张图始终是干净、有结构、可信的**——这是 AI 在 CSF 规程之下能稳定持有"项目记忆"的实证。

行业现状对照：当下绝大多数 LLM 工程实践，做不到让 AI 在长周期、多变更、多角色协作中**持续维护一份给自己用的、可信的项目状态**。CSF 把这件事做出来了。

---

### 理论独立性

CSF 体系的 6 个可能的独立创新点已成体系，可单独抽出供研究者参考或者帮我修正：

1. 消费侧 / 供应侧的通用分析框架
2. 目的驱动的注意力工程（不是 prompt engineering）
3. **工程层能力增长独立于模型层** —— 同模型 + 更好的工程组织 → 更好的结果
4. 文件系统作为延伸认知系统（extended cognition）的工程实例
5. D3 三谱系作为知识路由系统
6. 业务语言放大机制（W-协议核心：跨语言翻译会放大误解，业务直觉是检测仪器）

如果你是企业决策者或研发团队负责人，正在为 RAG 复杂度爆炸 / Agent 编排维护成本 / AI 工程化落地困难而困惑——值得读完[引言](引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md)和 [csf-minimal](csf-minimal/README.md) 后联系作者。

---

## 路线图

- [x] 最小教学版（csf-minimal）
- [x] 引言文章（中文 + 英文宣言）
- [x] 发布授权（CC BY-NC 4.0）
- [x] 联系说明（CONTACT.md，中英双栏）
- [x] 小白用户上手指引（[QUICKSTART.md](QUICKSTART.md)，中英双栏）
- [ ] csf-lite 公开介绍（不含具体内容）
- [ ] 实践案例与社区反馈

### 未来

我会持续在这个仓库里回答大家的问题（GitHub Issues / 邮件），并在合适的时候整理一些**专栏式的长文**发布在这里，提供更系统的帮助。如果你有问题，**就来问**——这是这件事最自然的下一步。

---

## 联系

由 **dapangangang** 在 395 次会话的真实重构项目中开发并验证。

- **中文用户**：主要落地点是知识星球「一个人走」（含 csf-lite、进阶经验、案例分享，付费社群）。日常反馈走 GitHub Issues，邮箱用于商用咨询。
- **English speakers**: email is the most direct way; GitHub Issues for public discussion.

👉 详细联系方式：[CONTACT.md](CONTACT.md)

邮箱 / Email：**dapangangang@gmail.com**

---

## 如何引用

如果 CSF 或「乓定律」帮到了你，欢迎复制下面任意一段使用。

**一句话引用（中文）**

```markdown
[CSF · 乓定律](https://github.com/huidev2025/CSF) — dapangangang, 2026
```

**完整引用块**

```markdown
> “The value of AI comes from its intelligence.
> Trying to make it as reliable as a machine is exactly the act of destroying that value.”
> — The Pang Principle, dapangangang (CSF, 2026)
> https://github.com/huidev2025/CSF
```

**在你项目的 `context.md` 末尾**（推荐）

```html
<!-- Built with CSF · https://github.com/huidev2025/CSF -->
```

---

## 授权 / License

本仓库的文档与文字内容采用 [**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/) 协议。

- **个人、学术、非营利使用**：自由传播、翻译、改编，请保留署名（dapangangang）与原始链接。
- **商业使用**（以营利为主要目的的产品、服务、企业内部工具、培训课程、咨询交付物等）：请提前联系作者。**不一定收费，但希望知道你是谁、用在哪里。**
- **创业者**：免费。
- **不确定是否算商用**：发个 Issue 或邮件问一下就好。

---

## 比 License 更想说的话

法律上，CC BY-NC 要求署名。但比署名更让我开心的是：

- 用上了，告诉我你在做什么——一个 Issue、一封邮件、社交媒体 @ 一下都行。
- 不是要求，是交朋友。
- 创业者免费；如果它真帮到你，等你跑出来了，记得回来打个招呼。

---

> ✍️ **署名说明**
>
> 本仓库的文章，我习惯署名为 *by dapangangang with AI*。
> 虽然作者是两位，**通讯作者只有我**——
> AI 很健忘，你知道的 :)
