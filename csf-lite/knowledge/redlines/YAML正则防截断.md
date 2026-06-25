# YAML 嵌入 Markdown 时正则提取防截断

> 红线 · 工艺类 | 来源: coslog-012 | 触发词: YAML、正则、截断、代码围栏、fenced code block

## 原则

**Markdown 中用正则提取 YAML 代码块时，闭合 ` ``` ` 必须锚定行首。否则 YAML 内容中的缩进 ` ``` ` 会导致非贪婪匹配提前截断。**

## 原因

YAML 的 `|` 块标量常承载 Markdown/代码内容。当 YAML 嵌在 Markdown 的 fenced code block 中时：

```markdown
```yaml
replacement: |
  ```
  这段会被误匹配
  ```
```
```

正则 `r'```yaml\s*\n(.*?)```'` 的 `(.*?)``` ` 会匹配到**第一个** ` ``` `——即 YAML 内容内部的缩进围栏，而非 Markdown 层的闭合围栏。

## 正确做法

```python
# ❌ 错误：非贪婪匹配第一个 ```，不区分缩进
re.search(r'```yaml\s*\n(.*?)```', text, re.DOTALL)

# ✅ 正确：\n 锚定闭合 ``` 必须顶格（行首无空白）
re.search(r'```yaml\s*\n(.*?)\n```', text, re.DOTALL)
```

YAML 内容内的围栏通常有缩进（`        ``` `），不会匹配 `\n``` `（要求换行后紧跟三个反引号）。

## 案例

| # | 会话 | 触发场景 |
|---|---|---|
| 1 | coslog-012 | CSF打包协议.md 的 YAML `replacement: |` 内容含 ` ``` ` 代码围栏，正则截断导致 `csf_clarity` 段和 `dev-context.md` 规则全部丢失，打包输出 csf-clarity 为空 |
