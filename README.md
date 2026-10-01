# ui-focus

UI 焦点导航：手柄/键盘方向键在元素之间移动焦点，并记住每个分组上次的位置。
只用 Python 标准库。

```
python3 -m uifocus.cli --sample direction
python3 -m uifocus.cli --sample disabled
python3 -m uifocus.cli --sample memory
python3 -m uifocus.cli --sample wrap
python3 -m uifocus.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **候选元素**：只有 `enabled` 为真且没有隐藏的元素可以被聚焦；禁用和隐藏的元素
  永远不能成为下一个焦点。
- **方向匹配**：`move(current, direction)` 只在当前元素该方向一侧的元素里挑；
  该元素在垂直于方向的轴上与当前元素有重叠时排在最前。
- **选择顺序**：先按沿该方向的距离升序，再按垂直方向的距离升序，最后按元素 id
  字典序升序；没有候选时按 `wrap` 决定是绕到另一侧还是保持原焦点。
- **循环**：`wrap` 为真时允许绕到对侧最近的可用元素；绕行结果同样不能是禁用或
  隐藏的元素。
- **分组记忆**：每个分组各自记住上次的焦点；`set_focus` 只写该元素所属分组，
  `focus(group)` 恢复该分组的记忆；记忆里的元素已禁用、隐藏或不存在时退回该分组
  的第一个可用元素（按 id 升序）。
- **不变量**：任何一次导航返回的元素要么是可用元素，要么就是原来的 `current`；
  同一串操作重复执行结果相同。
- **查询代价**：单次导航不许遍历全部元素，`scanned` 不随元素数线性增长。
- **规模**：10 万个元素、每秒 10 万次导航，单次摊还 O(1)。

## 输出契约（不改格式）

```
next=..
left=..
scanned=..
```

## 目录

```
uifocus/core.py   方向导航与分组记忆
uifocus/cli.py    命令行入口
tests/            unittest 用例
```
