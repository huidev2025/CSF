# CSF Lite — 发布与自举包

> 版本: v1.0 | 日期: 2026-06-26
> 仓库: https://github.com/huidev2025/CSF

---

## 自举包是什么

**自举包**（`CSF-lite-*.zip`）是一个解压即用的完整 CSF Lite 工作环境。它包含：

- **csf-lite/** — 完整方法论框架（引擎 + 三元组 + 协议库 + 经验库 + 守则）
- **csf-clarity/** — Clarity 桌面程序的运行数据目录（含出厂预设提示词）
- **README.txt** — 快速开始指南
- **安装与配置.pdf** — 图文安装指南
- **LICENSE-Clarity.txt** — Clarity 程序的 MIT 许可证

> 💡 **自举 + 自复制**：拿到自举包 → 开始使用 → 你的 CSF 环境积累经验和改进 → 在 Clarity 中点击「打包CSF环境」→ 导出新 zip → 分享给他人。**每个用户都能成为分发者。** 这就是 csf-lite 的自复制闭环——不依赖中心化发布，知识在传播中自我进化。

---

## 下载

从 [GitHub Releases](../../releases/latest) 页面下载最新版本：

```
CSF-lite-v1.0.zip
```

> **不需要 Git、不需要克隆仓库。** 下载 zip → 解压 → 开始。

---

## 三步开始

### 1. 解压

将 zip 解压到你的项目文件夹。目录结构如下：

```
你的项目/
├── csf-lite/           ← 框架（引擎 + 核心文件）
│   ├── cos-context.md  ← 交给 AI 的第一个文件
│   ├── core/           ← 角色规范
│   ├── protocols/      ← 操作规程
│   ├── knowledge/      ← 经验库
│   └── ...
├── csf-clarity/        ← Clarity 数据目录（首次启动自动填充）
└── 安装与配置.pdf      ← 图文指南
```

### 2. 填写项目名

打开 `csf-lite/cos-context.md`，找到这一行：

```
**项目**：你的项目名 — 一句话描述
```

这是你唯一需要手动编辑的地方。

### 3. 启动 AI 参谋长

打开你的 LLM 对话窗口（VS Code Copilot Chat / ChatGPT / Claude / …），输入：

> **「阅读 cos-context.md，开局」**

AI 会自动：
1. 加载引擎 → 建立角色认知（"我是参谋长……"）
2. 识别这是新项目 → 进入初始化流程
3. 向你提问（项目目的、性质、起点）
4. 建立第一个三元组 + 填写全景图
5. 开始和你一起推进项目

之后每次新会话，都从「阅读 cos-context」开始。AI 会自动接上上次进度。

> 📖 详细图文指南见压缩包内的 `安装与配置.pdf`，或仓库中的 [安装与配置.md](csf-lite-doc/安装与配置.md)。

---

## 自举：csf-lite 如何管理自己

这个仓库本身就是自举的活证据。下面这张图展示了 csf-lite 的"自己管自己"循环：

```
┌─────────────────────────────────────────────────────┐
│                  GitHub 仓库 (CSF)                    │
│                                                       │
│  ┌─────────────┐      ┌──────────────────────┐      │
│  │  csf-lite/  │──▶──│   AI 参谋长 (CoS)      │      │
│  │  (方法论)    │      │   阅读 cos-context    │      │
│  └─────────────┘      │   建立角色认知         │      │
│                        │   管理仓库、写文档     │      │
│  ┌─────────────┐      │   维护 README/发布     │      │
│  │  产出物      │◀──│   记录 session log     │      │
│  │  README.md  │      └──────────────────────┘      │
│  │  文档/页面   │                                     │
│  │  Release    │                                     │
│  └─────────────┘                                     │
└─────────────────────────────────────────────────────┘
```

**每次会话**：AI 读 `cos-context.md` → 知道自己是谁、在哪、要做什么 → 产出文档/决策 → 收尾时覆写 §C/§D 为下次会话做准备。

**跨会话连续性**：不靠 AI 记忆，靠文件。`cos-context.md` 只保留最新状态（覆写式），`sessions/coslog-NNN.md` 保留完整过程（追加式）。下次会话的 AI 读到的是"脱水"后的高浓度信息。

---

## Clarity：配套桌面工具（可选）

[Clarity](clarity-dev/) 是一个轻量级 Windows 桌面应用（PyQt6），辅助你：

- 管理和编辑提示词（标签1）
- 编辑 `cos-context.md` 的各个区段（标签2）
- 浏览和编辑规范文件（标签3）
- 版本快照与备份

**Clarity 不是必选项**——你可以用任何文本编辑器操作 csf-lite 的文件。它只是让操作更顺手。

> 📖 [Clarity 使用手册](csf-lite-doc/Clarity-使用手册.md) | [Clarity 开发者参考](clarity-dev/DEVELOPER.md)

---

## 版本历史

| 版本 | 日期 | 说明 |
|---|---|---|
| v1.0 | 2026-06-26 | 首次公开发布。csf-lite 框架 + Clarity 桌面程序 + 安装指南。 |

---

## 下一步

- 📖 阅读 [csf-lite/README.md](csf-lite/README.md) 了解框架全貌
- 🚀 跟着 [安装与配置.md](csf-lite-doc/安装与配置.md) 完成环境搭建
- 💬 有问题？[GitHub Issues](https://github.com/huidev2025/CSF/issues)
- 📧 邮件：dapangangang@gmail.com

---

> ✍️ 本文件由 AI 参谋长在 csf-lite 框架内维护。自举进行中。
