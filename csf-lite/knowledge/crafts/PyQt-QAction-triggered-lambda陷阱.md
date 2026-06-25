---
关键词: [PyQt, QAction, triggered, lambda, checked, 信号传参, 默认参数覆盖, 右键菜单]
来源: csf-v4-live session-044 / 纳入: coslog-011
热度: 冷
适用: PyQt 项目
---

# PyQt QAction.triggered 信号 lambda 传参陷阱

> ⚠️ 适用域：PyQt/PySide 项目。非 PyQt 项目可跳过。

## 原则

PyQt 中 `QAction.triggered` 信号会**自动传递 `checked: bool` 作为第一个参数**。使用 lambda 绑定菜单回调时，该参数会覆盖 lambda 的第一个默认参数值——如果不显式声明 `checked=False` 吞掉它。

## 原因

PyQt 信号机制：`QAction.triggered` 签名是 `triggered(checked: bool = False)`。当菜单项被点击时，Qt 调用 `triggered.emit(False)`，这个 `False` 会作为第一个位置参数传入 lambda。

```python
# ❌ 错误写法
lambda g=group, f=filename: self._send_by_menu(g, f, False)
# Qt 调用时：lambda(checked=False, g=group, f=filename)
# 结果：g = False（checked 吞掉了 g），f = group（移位）
# → 类型错误

# ✅ 正确写法
lambda checked=False, g=group, f=filename: self._send_by_menu(g, f, False)
# Qt 调用时：lambda(checked=False, g=group, f=filename)
# checked=False（被正确吞掉），g=group, f=filename ✓
```

**关键**：`checked=False` 必须是 lambda 参数列表的**第一项**，否则仍会被覆盖。

## 操作手法

| 场景 | 做法 |
|---|---|
| QAction.triggered 连接 lambda | **始终**在 lambda 参数列表首位加 `checked=False` |
| QAction.triggered 连接普通方法 | 方法签名加 `checked=False` 参数 |
| 右键菜单批量绑定时 | 每个 lambda 独立检查，不复制粘贴 |
| 排查闪退/TypeError | 检查 traceback 中的类型异常（`Path / bool`、`str / bool` 等），这是信号传参覆盖的典型指纹 |

**检查单**（右键菜单收尾前）：
- [ ] 所有 `triggered.connect(lambda ...)` 首位有 `checked=False`
- [ ] 如有 `toggled` 信号连接，同样处理（`toggled` 传 `checked: bool`）
- [ ] 如用 `functools.partial` 替代 lambda —— 不受影响（推荐方案）

## 案例概述

| # | 会话 | 触发场景 | 简述 |
|---|---|---|---|
| 1 | csf-v4-live 046 | 右键菜单多项报类型错误 | `QAction.triggered` 传 `checked=False` 覆盖 lambda 第一个默认参数 → 类型错误。双击路径不受影响（用不同信号传不同参数），导致根因定位延迟 |
