"""UI 焦点导航：按方向找下一个可聚焦元素，并记住每个分组上次的焦点。

缺陷：只按列表下一个来导航、不看禁用与隐藏、所有分组共用一个记忆、
循环不生效、每次导航扫描全部元素。
"""


class Focus:
    """焦点导航。"""

    def __init__(self, wrap=False):
        self.wrap = wrap
        self.items = []
        self.by_id = {}
        self.memory = None
        self.scanned = 0

    def add(self, item_id, x, y, group="main", enabled=True, hidden=False):
        item = {"id": item_id, "x": x, "y": y, "group": group,
                "enabled": enabled, "hidden": hidden}
        self.items.append(item)
        self.by_id[item_id] = item
        return item

    def move(self, current, direction):
        """按方向返回下一个焦点元素。"""
        self.scanned += len(self.items)
        ids = [item["id"] for item in self.items]
        if current not in ids:
            return current
        index = ids.index(current)
        if index + 1 < len(ids):
            return ids[index + 1]
        if self.wrap:
            return ids[0]
        return current

    def set_focus(self, item_id):
        """记住当前焦点。"""
        self.memory = item_id

    def focus(self, group):
        """恢复某个分组的焦点。"""
        if self.memory is not None:
            return self.memory
        for item in self.items:
            if item["group"] == group and item["enabled"] and not item["hidden"]:
                return item["id"]
        return None
