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
├── CONTACT.md                    # 联系方式（中英双栏）
├── 引言v3：...md                  # 对外引言（宣言）
├── Manifesto-v3-Fighting-the-Wrong-War.md   # 英文版宣言
├── assets/                       # 对外资源（二维码等）
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

## 联系 / Contact

由 **dapangangang** 在将近 400 次会话中开发并验证。

- **中文用户**：主要落地点是知识星球「一个人走」（含 csf-lite、进阶经验、案例分享，付费社群）。日常反馈走 GitHub Issues，邮箱用于商用咨询。
- **English speakers**: email is the most direct way; GitHub Issues for public discussion. There's a paid Chinese-language community as an option, but it's Chinese + WeChat-only — email is usually faster.

👉 详细联系方式 / Full contact details：[CONTACT.md](CONTACT.md)

邮箱 / Email：**dapangangang@gmail.com**

---

## 如何引用 / How to cite

如果 CSF 或「乓定律」帮到了你，欢迎复制下面任意一段使用。

**一句话引用（中文）**

```markdown
[CSF · 乓定律](https://github.com/huidev2025/CSF) — dapangangang, 2026
```

**One-line citation (English)**

```markdown
[CSF — The Pang Principle](https://github.com/huidev2025/CSF) — dapangangang, 2026
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

The textual content of this repository is licensed under [**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/).

- Personal, academic, non-profit use: free to share and adapt with attribution.
- Commercial use requires permission — please reach out. Paid licensing is **not** the default.
- **Startups: free.**
- Unsure whether your use is commercial? Open an issue or email **dapangangang@gmail.com**.

---

## 比 License 更想说的话 / A note beyond the license

法律上，CC BY-NC 要求署名。但比署名更让我开心的是：

- 用上了，告诉我你在做什么——一个 Issue、一封邮件、社交媒体 @ 一下都行。
- 不是要求，是交朋友。
- 创业者免费；如果它真帮到你，等你跑出来了，记得回来打个招呼。

Legally, CC BY-NC asks for attribution. What I'd actually love more:

- If you use it, tell me what you're building — an issue, an email, a social-media @ all work.
- Not a requirement. Just to stay in touch.
- Startups are free; if it ends up helping you, come say hi when you've made it.

联系 / Contact: see [CONTACT.md](CONTACT.md) · **dapangangang@gmail.com** · GitHub Issues
