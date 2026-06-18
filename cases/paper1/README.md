---
title: 案例分析：CSF 论文写作全过程 (Case Study - Paper 1)
layout: default
---

# 案例：CSF 论文写作全过程

**简体中文** &#124; [English](README_en.md)

> 这是一次使用 CSF minimal 版本（`context.md` 模板）完成的学术论文写作。16 轮对话日志 + 中英文投稿稿 + 协作记忆文件，展示了从"讨论骨架"到"arXiv 投稿"再到"数据分析与修订"的完整过程。

---

## 项目背景

**《这篇文章由AI写就》**是一篇学术论文（投稿中）。它研究的恰恰是 CSF 本身——**长程人机协作中的语义漂移问题**，并提出了"索引病"和"乓定律"两个核心概念。

论文的写作过程本身就是对论文论点的**演示**：所有文字由 AI 协作者生成，Owner 只做方向性判断。协作过程使用了 [csf-minimal](../../csf-minimal/) 中的 `context.md` 模板——每次会话开始时 AI 读取它来重建项目状态，会话结束时更新它来保持连续性。这个文件本身也是协作的记录和实证。

---

## 产出物

| 文件 | 说明 |
|---|---|
| [context.md](context.md) | 写论文时使用的协作记忆文件（csf-minimal 模板实例） |
| [arxiv_submission_zh.md](arxiv_submission_zh.md) | 中文 arXiv 投稿稿（主稿，已定稿） |
| [arxiv_submission_en.md](arxiv_submission_en.md) | 英文 arXiv 投稿稿（v1.6，与中文稿同步） |
| [dlog/](dlog/) | 16 轮原始会话记录 + 数据分析脚本 + 投稿笔记 |

---

## 16 轮会话做了什么

| 文件 | 核心事件 |
|---|---|
| dlog_1 | 第一次讨论骨架——确定叙事线、核心概念、目标会议 |
| dlog_2 | 初步收集资料——文献检索、案例材料整理 |
| dlog_3 | 第一次尝试写作——结构有点乱，但素材到位 |
| dlog_4 | 换一个更稳重的 AI 角色继续 |
| dlog_5 | Chrome + Gemini 辅助综述 |
| dlog_6 | 初步整合综述进入论文 |
| dlog_7 | 精修第一遍——语言、逻辑、引用 |
| dlog_8 | 翻译并推出英文版 |
| dlog_9 | 修改论述结构——引言重组、贡献重排 |
| dlog_10 | 全局审查 + 模拟审稿人角色扮演（DeepSeek） |
| dlog_11 | 再次中文修改 |
| dlog_12 | 英文版定稿 + 上传 arXiv |
| dlog_13 | 系统性数据挖掘——纠偏密度、上下文增长率、两轮简化对比 |
| dlog_14 | 将数据分析发现纳入论文正文（v1.5 → v1.6） |
| dlog_15 | 模拟严苛审稿人反馈 + Owner 逐条回应 |
| dlog_16 | arXiv update 上传（v1.6 定稿） |
| dlog_paper1_issues | 问题追踪日志（14 个 issue 的判定与处理） |
| [data-analysis/](dlog/data-analysis/) | 分析脚本（Python）、统计结果、论文增强建议 |
| _notes_ | 投稿目标笔记（IEEE Software / ICSE 等） |

---

## 协作方式

论文写作使用了 [csf-minimal](../../csf-minimal/) 的基础模式：

- **`context.md` 作为协作记忆**：每次会话开始时读取，结束时更新。16 轮对话中，AI 不需要 Owner 重复交代背景。
- **每轮一个目的**：收集素材就纯收集，改结构就纯改结构，不混。
- **会话日志独立保存**：dlog/ 中的文件是每次会话的完整记录，与正文分离。

没有使用多角色模拟、物理隔离或其他进阶机制。就是一个 `context.md` 模板 + 正常的对话协作。论文最终产出的质量来自这个最简模式。

---

## 关于 dlog 文件的可读性

原始会话记录**保留了 Copilot 工具调用痕迹**（`Read`、`Searched`、`Created` 等行）和部分 AI 中间推理输出。这些未经清理，因为它们本身就是**可核查的证据**——第三方可以验证论文中引用的案例和论证是否确实来自对应的会话记录。

如果你只是想了解过程，读本页就够了。如果你想核查证据，去 dlog 里翻原始记录。

---

## 相关链接

- [CSF 仓库首页](https://github.com/huidev2025/CSF)
- [帮找 v3 开发案例](../bang-v3/) —— CSF 在软件开发中的实战
- [《与智能共事》专栏](https://huidev2025.github.io/CSF/essays/) —— CSF 理论体系
