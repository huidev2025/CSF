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

**当前阶段**：仓库骨架已建立并首次发布。下一步是与 Owner 商定结构、命名、中英文双语版本、LICENSE。

---

## 当前在做什么

**目的**：让 csf 仓库在 GitHub 上可被阅读、可被复用，帮到有需要的人。

**进度**：
- [x] csf-minimal 三件套（README / context / 体验对比指南）
- [x] 引言 v3 文章
- [x] 仓库根 README 第一版
- [x] git 初始化 + 首次推送到 https://github.com/huidev2025/CSF
- [ ] 中英文双语版本安排（目录结构 / 命名）
- [ ] LICENSE 选型
- [ ] 引言文件名是否保留原名
- [ ] 进阶版本：csf-lite / csf-full

**注意事项**：
- 这个仓库是对外门面，所有对外文案（引言 / README / 语气）修改前需 Owner 确认后再推送。
- 默认节奏：有进展 → commit → push。如是对外文案类修改，停下来确认。
- 远程账号：huidev2025（不是本地默认的 huiGiter）。
- 仓库内中文文件名在 GitHub URL 中会被 URL 编码。

---

## §C 上次对话

- **日期**：2026-06-06
- **做了什么**：
  1. 通读 csf-222 六篇 + csf-v3-394 总览，建立对 CSF 理论体系的认知。
  2. 创建仓库骨架：根 README.md、.gitignore。
  3. git init -b main → 首次 commit（7 个文件）→ 添加远程 origin。
  4. 清理 Windows 凭据管理器里的 huiGiter 旧凭据，OAuth 重新登录 huidev2025。
  5. 远程原有 GitHub stub README 被覆盖 (--force-with-lease)。
- **结论**：首版已发布到 https://github.com/huidev2025/CSF ，main 分支 commit `17d5003`。

---

## §D 下次对话

- **目的**：让仓库低门槛、原意完整、开始对外可讲。
- **建议先做**（二选一）：
  - **路径 A（商定结构）**：中英文双语目录如何布局（`/zh/` + `/en/`？还是文件名后缀 `.zh.md` / `.en.md`？）、引言文件名是否改短、LICENSE 选型。
  - **路径 B（先产出英文初稿）**：先翻译引言 + csf-minimal/README，结构问题边译边决。
- **需要的资料**：无（现有仓库内容足够）。如要发起诨论，可参考 bang-v3\plan-csf-v2\csf-iteration\csf-v3-394\CSF 理论体系总览.md。

---

## 备忘

- **远程**：https://github.com/huidev2025/CSF （main，账号 huidev2025）
- **本地路径**：d:\OneDrive\devSpace\csf\
- **待决 LICENSE**：Owner 选了“暂不加”，README 底部标为 *License: 待定 / TBD*
- **未同步到 GitHub 的事项**：无（本地 main 与 origin/main 持平）。

<!-- 需要跨对话记住但不是当前在做的事 -->
