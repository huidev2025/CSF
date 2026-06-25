# scenarios/ — 场景模版库

> 版本: v0.1 / 建立: coslog-007
> 每个场景一个文件夹。内含该场景专属的角色 instruction 文件和可选专属协议。
> 场景适配时，参谋长从本目录取对应文件覆盖默认配置。

---

## 场景清单

| 场景 | 文件夹 | 状态 | 说明 |
|---|---|---|---|
| 开发 | `dev/` | ✅ 已建立 | 默认场景，最大用户群。使用 core/开发者-instructions.md |
| 写作 | `author/` | ✅ 已建立 | 长篇小说/文档写作场景。含写作者角色文件 + 写作 STB 规范 |
| 研究 | `researcher/` | ⬜ 待建 | 学术/调研场景 |

---

## 文件夹结构规范

```
scenarios/{场景名}/
├── {角色名}-instructions.md    ← 覆盖 core/开发者-instructions.md
└── {协议名}.md                 ← 场景专属协议（可选，0-N个）
```

---

## 新场景建立步骤

1. 在 scenarios/ 下建文件夹
2. 写角色 instruction 文件（参考 `core/开发者-instructions.md` 的结构：你是谁 + 核心责任 + 专业判断力 + 边界）
3. 如有场景专属协议，放入该文件夹
4. 更新本文件的场景清单表
5. 更新 `protocols/场景适配协议.md` §5 归属矩阵

---

## 与 core/ 的关系

- `core/开发者-instructions.md` 是默认角色文件。场景适配时，用 scenarios/ 下的对应文件覆盖它。
- `core/守则.md`、`core/参谋长-instructions.md`、`core/参谋长-方法论.md` 永不被场景模版覆盖——它们是 CSF 的定义。
