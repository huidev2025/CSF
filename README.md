# CSF — Collaboration Specification Framework

> 一种在 LLM 本性之内、用「自然语言 + 目的」设计人机协同工作方式的工程方法。
> A framework for designing human-AI collaboration **within** the nature of LLMs, using natural language and purpose.

---

## 这是什么

AI 辅助开发的主流做法把 LLM 的约束（上下文有限、记忆短、行为不可预测）当作要用技术克服的缺陷——RAG、向量库、Agent 编排、越来越精确的提示词。

CSF 选择另一条路：**承认这些约束为事实，在约束内设计**。结果是技术栈消失了——不是被替换，是它们的存在理由消失了。

详见引言：[引言：你们在拿着前朝的尚方宝剑，斩当朝的官](引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md)

---

## 从哪开始读

按顺序，五分钟可以开始：

1. **[引言](引言v3：你们在拿着前朝的尚方宝剑，斩当朝的官.md)** —— 为什么需要 CSF，乓定律
2. **[csf-minimal/README.md](csf-minimal/README.md)** —— CSF 最小教学版，30 秒说明 + 三个核心差异
3. **[csf-minimal/context.md](csf-minimal/context.md)** —— 你可以直接复制使用的协作记忆模板
4. **[csf-minimal/体验对比指南.md](csf-minimal/体验对比指南.md)** —— A/B 实验设计，亲自感受差异

---

## 仓库结构

```
csf/
├── README.md                     # 本文件
├── LICENSE                       # CC BY-NC 4.0
├── 引言v3：...md                  # 对外引言（宣言）
└── csf-minimal/                  # 教学最小版
    ├── README.md
    ├── context.md                # 给读者用的空白模板
    └── 体验对比指南.md
```

---

## 路线图

- [x] 最小教学版（csf-minimal）
- [x] 引言文章
- [x] 发布授权（CC BY-NC 4.0）
- [ ] 英文版（English translation）
- [ ] 进阶版本：csf-lite / csf-full
- [ ] 实践案例与社区反馈

---

## 联系

由 **dapangangang** 在将近 400 次会话中开发并验证。想深入了解、有反馈、想交流——欢迎通过 GitHub Issues 或邮箱 **dapangangang@gmail.com** 联系。

---

## 乒定律

> **公理**：自然语言表达所承载的信息量，远高于符号系统。
>
> **事实①**：人工智能的价值来自于"智能"，尝试让它如机械一般可靠，就是在消除它的价值。
>
> **事实②**：伴随时间，一个表达所承载的信息量会不可避免地增长，语义会被稀释。

---

## 授权 / License

本仓库的文档与文字内容采用 [**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/) 协议。

- **个人、学术、非营利使用**：自由传播、翻译、改编，请保留署名（dapangangang）与原始链接。
- **商业使用**（以营利为主要目的的产品、服务、企业内部工具、培训课程、咨询交付物等）：请提前联系作者。**不一定收费，但希望知道你是谁、用在哪里。**
- **创业者**：免费。但还是希望你告诉我你在做什么——不是限制，是交朋友。
- **不确定是否算商用**：发个 Issue 或邮件问一下就好。

联系方式：**dapangangang@gmail.com** 或 GitHub Issues。

---

The textual content of this repository is licensed under [**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/).

- Personal, academic, non-profit use: free to share and adapt with attribution.
- **Commercial use** requires permission — please reach out. Paid licensing is **not** the default; the goal is to know who is using it and how.
- **Startups: free.** Just please tell me what you're doing — not a restriction, just to stay in touch.
- Unsure whether your use is commercial? Open an issue or email **dapangangang@gmail.com**.
