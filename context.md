# CONTEXT

> 这是你的 AI 助手的"记忆文件"。每次对话开始时让 AI 读它，结束时让 AI 更新它。

---

## 你是谁

你是我的项目助手。我们通过这个文件保持连续性——你没有记忆，但这个文件替你记住一切。

**工作方式**：
- 每次对话开始：读这个文件，告诉我当前状态和你的建议
- 工作中：做完一步就简要汇报，我确认后继续
- 每次对话结束：更新下面的 §C 和 §D

**三条规则**：
1. 不凭印象——所有判断必须基于你真正读过的内容
2. 不确定就说——不要猜，不要编
3. 目的优先——做任何事之前想"这是在朝目的走吗"

---

## 项目信息

**项目名称**：<!-- 填入 -->
csf在github上的发布和维护

**项目目标**：<!-- 一句话描述这个项目要做什么 -->
在github上发布csf的一些基础的资料，希望能够帮到有需要的人。

**当前阶段**：仓库骨架已建立并首发，英文版宣言完成首版。下一步进入「小白用户上手指引 + 联系说明 + 内容预告」。

---

## 当前在做什么

**目的**：让 csf 仓库在 GitHub 上可被阅读、可被复用，帮到有需要的人。

**进度**：
- [x] csf-minimal 三件套（README / context / 体验对比指南）
- [x] 引言 v3 文章
- [x] 仓库根 README 第一版
- [x] git 初始化 + 首次推送到 https://github.com/huidev2025/CSF
- [x] LICENSE 选型：CC BY-NC 4.0，README 有补充说明（个人/创业者免费 + 商用联系）
- [x] 英文版宣言首版：Manifesto-v3-You-Are-Fighting-the-Wrong-War.md
- [x] 词典定档：Pang Principle / intelligence / purpose / discern · carry out / drift / dynasty's sword·law·official 三层隐喻
- [x] README 新增「如何引用 / How to cite」与「比 License 更想说的话」两段
- [x] csf-minimal/context.md 模板尾部加 attribution 标识行
- [x] typo 修复：README 里一次「乒」、本轮意外的「吓」均已修为「乓」
- [x] 联系说明：CONTACT.md（中英双栏）、assets/zsxq-qrcode.jpg（知识星球二维码）、README 联系段重写为短入口
- [x] _dlog/ 决定公开（作为对外示范的一部分，计划公开 dlog_001/002/003）
- [x] README 重定位：「CSF 全景 / The CSF Stack」三层表格 + 三个工程级设计支柱 + 行业对照（中英同步）
- [x] 项目全景图 + 任务红点截图进 README（「看图说话」小节 / Look at it）、文件名改为 ASCII：assets/project-panorama-and-red-dot.png
- [x] Manifesto 改名：Manifesto-v3-You-Are-Fighting-the-Wrong-War.md（消歧义）
- [ ] 中文引言文件名是否保留原名（未决）
- [ ] 小白用户上手指引（QUICKSTART / FAQ / 示例，中英文）
- [ ] 内容预告（后期进阶路线）
- [ ] 进阶版本：csf-lite / csf-full

**注意事项**：
- 这个仓库是对外门面，所有对外文案（引言 / README / 语气）修改前需 Owner 确认后再推送。
- 默认节奏：有进展 → commit → push。如是对外文案类修改，停下来确认。
- 仓库内中文文件名在 GitHub URL 中会被 URL 编码。

---

## §C 上次对话

- **日期**：2026-06-06（第四轮对话，以「README 重定位 + 项目全景图为活证据」为主轴）
- **做了什么**：
  1. 两个问题讨论：（小）Manifesto 文件名歧义→重命名为 Manifesto-v3-You-Are-Fighting-the-Wrong-War.md（`git mv` 保史）；（大）如何「亮肜肉」让 csf-full 能变现。
  2. 回看 plan-csf-v2/context.md，修正表达中「1 人无代码」的单一卖点，重新定位 CSF 为「人机协作规范化、质量可控、效率提升」的工程级体系。
  3. README 大重写「CSF 全景 / The CSF Stack」中英两段：三层表格（Manifesto / csf-minimal / csf-lite-full）+ 三个工程设计支柱（Self-Sustaining / Hot-Cold Separation / Multi-Role Physical Isolation）+ 行业对照（CrewAI / AutoGen / Lost in the Middle）+ 事实表 + 边界。
  4. “已被证明的事情”从 2 项增至 4 项（Owner 手动补 #3/#4），英文同步补齐。
  5. 项目全景图 + 任务红点截图加进 README，中英各一小节。原名含「中文 + + 空格」→改为 `assets/project-panorama-and-red-dot.png`（避 URL 编码风险）。图说明采用 Owner 原话「AI 自己维护、给自己看的项目状态」，三维度（位置 / 来路 / 去向）。
  6. 样本量诚实化：删除中英两处「数量级 / order of magnitude」描述，换为描述性提法（「AI 不在对话中互相启动幻觉，人不在跳裁中被迫仲裁」）。
  7. 集中 push为一个 commit（`4f47275`）：4 files changed, 309 insertions(+), 7 deletions(-)。
- **结论**：README 从「会说会叫」进化为「能拿出工程证据」；项目全景图是其中最关键的一张活证据。

---

## §D 下次对话

- **目的**：启动「小白上手指引」（Owner 已定为下一个话题）。

- **Owner 预告的后续工作项**：

  1. ~~**英文版宣言**~~ — 已完成首版。
  2. ~~**社交媒体与联系说明**~~ — 已交付（CONTACT.md + README 联系段）。
  3. **小白用户上手指引**（中英文）——**下一个话题**。主题：“只要有基础沟通能力 + 好想法就能用”；重点包含“给非中文用户一个快速翻译并理解案例的说明”。开场需 Owner 决定「面向谁讲」（偏产品经理 / 偏开发者 / 偏货主 / 或全部分层）。
  4. **内容预告**。后期会在仓库中陆续提供的进阶内容。

- **建议下次开场**：Owner 已选「先做 3」。开场先问「面向谁讲」，再定调、定长度、定交付件（QUICKSTART / FAQ / 示例）。如需先产出 dlog_003，本轮收尾时产出。

- **需要的资料**：现有仓库内容 + 下面「备忘·理论参考资料」中记录的原始文件。小白上手指引需要明确「面向谁讲」（偏产品经理 / 偏开发者 / 偏货主）。

---

## 备忘

- **远程**：https://github.com/huidev2025/CSF （main，账号 huidev2025）
- **本地路径**：d:\OneDrive\devSpace\csf\
- **Owner 邮箱**：dapangangang@gmail.com（商用咨询 / 交流使用，必要时在对外文案中使用）
- **License**：CC BY-NC 4.0；个人/学术/非营利免费，创业者免费但希望告知，企业商用需联系 Owner。
- **发布节奏**：有进展 → commit → push；对外文案类修改需 Owner 确认后再推。
- **未同步到 GitHub 的事项**：本轮已 push（4f47275），清空。本轮未产出 dlog_003，顺延到下一个话题收尾时产出（将记录：Manifesto 改名 + README 重定位 + 全景图进场 + 小白指引开展）。

---

### 备忘·理论参考资料（下次会话可随时调取）

这些是 Owner 事先在另一个工作区产出的 CSF 理论原始文件，是本仓库对外表达的“底本”。不要反向写入，不要依赖其存在作为对外文案的依据。

- **csf-222（六篇正式产出）**。路径：`d:\huiDev\bang\bang-v3\plan-csf-v2\csf-iteration\csf-222\`
  - `01-csf-要解决的问题.md` — 第一性公理 + 推导链
  - `02-承认约束-csf的前提立场.md` — 两条被接受的事实 + 供应侧/消费侧
  - `03-目的-语义系统的控制单元.md` — 目的理论
  - `04-工程实现-三元组架构与滑动窗口.md` — 三个核心工程机制
  - `05-角色协作与能力增长.md` — 三角色 + E8 反馈
  - `06-csf的定位.md` — 与主流范式的区别与边界
- **csf-v3-394（总览与创新点清单）**。路径：`d:\huiDev\bang\bang-v3\plan-csf-v2\csf-iteration\csf-v3-394\CSF理论体系总览.md`
  - 包含：一句话定义、理论演绎链、四层工程架构、两类涌现、六个创新点、脆弱点分析、发展方向。

<!-- 需要跨对话记住但不是当前在做的事 -->
