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

**当前阶段**：仓库骨架已建立并首发，英文版宣言完成首版。小白用户上手指引（QUICKSTART.md）上线。

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
- [x] 小白用户上手指引：QUICKSTART.md（中英双栏） + README 加入口
- [x] 内容预告简化为「未来」一段（README 路线图下，中英双语）
- [x] 首个公开 release：**v1.0.0**（annotated tag + GitHub Release页）
- [x] GitHub SEO 路径 ①：**About description** （“works *with* LLM nature, not around it… make RAG and agent orchestration unnecessary. Home of the Pang Principle.”）
- [x] GitHub SEO 路径 ②：**20 个 Topics 已填**（报接钩子 + 价值定位 + 品牌锚点三组）
- [x] GitHub SEO 路径 ③：README 顶部英文 tagline 重写（嵌入 6 个关键词，「unnecessary, not unavailable」点明“超越不是缺失”）- [x] **essays/ 上线**：CSF 理论体系 6 篇连载（来自 csf-222），去除 frontmatter，朴素索引页，根 README 加入口 —— **不为 SEO 改一字**- [ ] GitHub SEO 路径 ④：外部信号（知识星球开张 / Hacker News / 中文社区 / awesome-* PR）——Owner 将另开专题
- [ ] GitHub SEO 路径 ⑤：首篇专栏文章（题目未定，路径④完成后接上）
- [ ] 中文引言文件名是否保留原名（未决）
- [ ] 进阶版本：csf-lite / csf-full

**注意事项**：
- 这个仓库是对外门面，所有对外文案（引言 / README / 语气）修改前需 Owner 确认后再推送。
- 默认节奏：有进展 → commit → push。如是对外文案类修改，停下来确认。
- 仓库内中文文件名在 GitHub URL 中会被 URL 编码。

---

## §C 上次对话

- **日期**：2026-06-06（第六轮对话，主题：v1.0.0 发布 + GitHub SEO）
- **做了什么**：
  1. **push 第五轮变更**：QUICKSTART + README + dlog_003 + context.md——commit `77dc030`。
  2. **首个发布**：打了 annotated tag `v1.0.0`，含结构化 release notes。Owner 随后在 GitHub 网页手动创建了 Release 页。关键澄清：*tag 不会自动变成 release，需要独立创建*。
  3. **About description 定稿**：最终采用「变体 A」，Owner 加了「不是更便宜、是更对」的表达：*“works with LLM nature, not around it — natural language and purpose make RAG and agent orchestration unnecessary. Home of the Pang Principle.”* Owner 自行粘贴。
  4. **GitHub SEO 战略全景**：梳理 4 条路径（About / Topics / README 顶部关键词 / 外部信号 + 内容飞轮）。总原则：嫌接钩子（RAG/agent/prompt-engineering/…）+ 品牌锚点（Pang Principle/CSF）+ 品质贯穿（不是更便宜、是更对）。
  5. **20 个 Topics 清单**（已填）：ai-collaboration / human-ai-collaboration / llm / llm-engineering / prompt-engineering / context-engineering / agentic-workflow / ai-agents / multi-agent / **rag-alternative** / **no-rag** / ai-development / ai-methodology / software-engineering / dogfooding / manifesto / **pang-principle** / **csf** / collaboration-specification-framework / chinese。
  6. **README 顶部英文 tagline 重写**（`3527270`）：从 2 个关键词扩到 6 个（human-AI collaboration / LLM / RAG / agent orchestration / prompt engineering / Pang Principle），核心表达 “unnecessary, not unavailable”——语法上出「超越，不是缺失」。
- **关键选择**：
  - SEO 不走「造词」线路，走「嫌接 + 锚点」双重：让读者从熟词进来，从你的词出去。
  - 中文那句 tagline **不动** ——中文检索靠外部渠道（知识星球 / V2EX / 即刻）承担，不占这个顶部窄通道。
  - **不制定“刷 star”设想**：GitHub 算法会识别异常。前 50 颗 star 必须靠真实读者。
- **未推送**：无（所有类仓库内变更已 push）。本轮 Owner 将另开专题处理路径 ④ 外部信号；路径 ⑤ 首篇文章在 ④ 后接上。
- **dlog_003**：本会话未产出，已顺延到下一个话题收尾时一并产出。

---

## §D 下次对话

- **目的**：Owner 专题处理「外部信号」（SEO 路径 ④）后，连接路径 ⑤（首篇专栏文章）落地。

- **Owner 在本轮末得问题**：未来专栏文章发在哪里？仓库内 vs 外部平台。**下一轮详细诨**。

- **后续工作项**：

  1. ~~**英文版宣言**~~ — 完成。
  2. ~~**联系说明**~~ — 完成（CONTACT.md）。
  3. ~~**小白上手指引**~~ — 完成（QUICKSTART.md）。
  4. ~~**内容预告**~~ — 已简化为 README 路线图下「未来」一段。
  5. ~~**v1.0.0 首个公开发布**~~ — 完成（tag + Release）。
  6. ~~**SEO 路径 ①②③**~~ — 完成（About / Topics / README tagline）。
  7. **SEO 路径 ④ 外部信号**——Owner 另开专题处理。备选动作：知识星球开张 / Hacker News Show HN / V2EX-即刻-少数派 中文社区 / 给 awesome-* 类列表提 PR。
  8. **SEO 路径 ⑤ 首篇专栏文章**——题目未定，5 个备选：*Why your RAG keeps growing* / *Past prompt engineering* / *395 sessions on Lost in the Middle* / *The Pang Principle one-pager* / *CSF dogfoods this repo*。
  9. **csf-lite 导读页**（上轮遗留，可选）。

- **下轮开场必答**：“专栏文章发在哪里？”这个问题已被 Owner 提出。需提供平台对比（仓库内 articles/ / GitHub Pages / Substack / 知识星球 / 个人站点 / 多点同步）+ 推荐。

- **需要的资料**：现有仓库内容 + 「备忘·理论参考资料」。

---

## 备忘

- **远程**：https://github.com/huidev2025/CSF （main，账号 huidev2025）
- **本地路径**：d:\OneDrive\devSpace\csf\
- **Owner 邮箱**：dapangangang@gmail.com（商用咨询 / 交流使用，必要时在对外文案中使用）
- **License**：CC BY-NC 4.0；个人/学术/非营利免费，创业者免费但希望告知，企业商用需联系 Owner。
- **发布节奏**：有进展 → commit → push；对外文案类修改需 Owner 确认后再推。
- **未同步到 GitHub 的事项**：本轮本地仅调整 context.md（§C/§D + 进度），还未 push。本轮未产出 dlog_003，顺延。

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
