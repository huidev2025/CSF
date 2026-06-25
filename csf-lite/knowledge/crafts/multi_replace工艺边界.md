---
关键词: [multi_replace, 批量替换, 降级, emoji, Unicode, 工具边界]
来源: session-174/175/176/193/198/201/203 共 7 次复发
热度: 温
---

# multi_replace 工艺边界

## 工艺

multi_replace_string_in_file 有严格的适用边界。超出边界时必须降级为单次 replace_string_in_file 调用。

## 适用条件（三项全满足才可用）

| 条件 | 阈值 |
|---|---|
| 替换项数 | ≤ 3 项 |
| 单项体量 | ≤ 1KB |
| 字符构成 | 纯文本 / 无 emoji + Unicode + 中文标点混排 |

## 必须降级的场景

- FM 大段（> 2KB）
- 含 emoji / 全角标点 / 特殊 Unicode 字符混排
- FM-LAST / FM-OLD / §2.3 删尾详细段
- oldString 中含全角括号「（」与半角「(」易混淆的内容

## 原因

7 次复发证明：multi_replace 在复杂字符场景下失败率极高。半角/全角括号混淆（如 `(含` vs `（含`）、emoji 编码差异、长文本匹配偏移——任一触发即整批失败且难以定位具体哪项出错。

## 自检

动手前问：项数超 3？单项超 1KB？有 emoji/全角标点？任一为是 → 降级单调用。
