"""UI 焦点导航：按方向找下一个可聚焦元素，并记住每个分组上次的焦点。

只在 enabled 且未隐藏的元素之间导航；按沿方向距离、垂直方向距离、id
字典序选择；无候选时按 wrap 决定绕行或保持；每个分组独立记忆焦点。

双层坐标网格索引在 add 之后懒构建：外层按运动轴坐标分线，内层按垂直轴
坐标分线；导航沿最近坐标行走、内层二分，单次导航只碰真正邻近的元素。
"""

from bisect import bisect_left, bisect_right


class Focus:
    """焦点导航。"""

    def __init__(self, wrap=False):
        self.wrap = wrap
        self.items = []
        self.by_id = {}
        self.memory = {}
        self.scanned = 0
        self._dirty = True
        self._grid = {}
        self._axis_coords = {}
        self._cross_coords = {}
        self._ids_by_group = {}

    def add(self, item_id, x, y, group="main", enabled=True, hidden=False):
        item = {"id": item_id, "x": x, "y": y, "group": group,
                "enabled": enabled, "hidden": hidden}
        self.items.append(item)
        self.by_id[item_id] = item
        self._dirty = True
        return item

    def _build_index(self):
        grid = {"x": {}, "y": {}}
        ids_by_group = {}
        for item in self.items:
            if not item["enabled"] or item["hidden"]:
                continue
            grid["x"].setdefault(item["x"], {}) \
                .setdefault(item["y"], []).append(item)
            grid["y"].setdefault(item["y"], {}) \
                .setdefault(item["x"], []).append(item)
            ids_by_group.setdefault(item["group"], []).append(item["id"])
        for outer in grid.values():
            for line in outer.values():
                for members in line.values():
                    members.sort(key=lambda it: it["id"])
        for ids in ids_by_group.values():
            ids.sort()
        self._grid = grid
        self._axis_coords = {axis: sorted(outer)
                             for axis, outer in grid.items()}
        self._cross_coords = {
            axis: {coord: sorted(line) for coord, line in outer.items()}
            for axis, outer in grid.items()
        }
        self._ids_by_group = ids_by_group
        self._dirty = False

    @staticmethod
    def _usable(item):
        return item["enabled"] and not item["hidden"]

    @staticmethod
    def _first_usable(members):
        for item in members:
            if item["enabled"] and not item["hidden"]:
                return item
        return None

    def _best_in_line(self, axis, axis_coord, line, cross_value):
        """在线内按 |垂直坐标 - cross_value| 升序、id 升序挑最佳可用元素。"""
        cross_list = self._cross_coords[axis][axis_coord]
        right = bisect_left(cross_list, cross_value)
        left = right - 1
        while left >= 0 or right < len(cross_list):
            left_gap = (cross_value - cross_list[left]
                        if left >= 0 else None)
            right_gap = (cross_list[right] - cross_value
                         if right < len(cross_list) else None)
            take_left = left_gap is not None and (
                right_gap is None or left_gap <= right_gap)
            take_right = right_gap is not None and (
                left_gap is None or right_gap <= left_gap)
            best = None
            best_key = None
            if take_left:
                item = self._first_usable(line[cross_list[left]])
                if item is not None:
                    key = (left_gap, item["id"])
                    if best_key is None or key < best_key:
                        best = item
                        best_key = key
            if take_right:
                item = self._first_usable(line[cross_list[right]])
                if item is not None:
                    key = (right_gap, item["id"])
                    if best_key is None or key < best_key:
                        best = item
                        best_key = key
            if best is not None:
                return best
            if take_left:
                left -= 1
            if take_right:
                right += 1
        return None

    def _nearest(self, axis, axis_value, cross_value, forward, far=False):
        """在 axis 轴严格一侧找最近一条含可用元素的网格线，返回最佳元素。

        forward 为真找大于 axis_value 的最小坐标，否则找小于 axis_value
        的最大坐标；far 为真时从对侧远端找起（wrap 绕行）。
        """
        if self._dirty:
            self._build_index()
        outer = self._grid[axis]
        coords = self._axis_coords[axis]
        if far:
            if forward:
                positions = range(len(coords) - 1,
                                  bisect_right(coords, axis_value) - 1, -1)
            else:
                positions = range(0, bisect_left(coords, axis_value))
        elif forward:
            positions = range(bisect_right(coords, axis_value), len(coords))
        else:
            positions = range(bisect_left(coords, axis_value) - 1, -1, -1)
        for pos in positions:
            coord = coords[pos]
            self.scanned += 1
            found = self._best_in_line(axis, coord, outer[coord],
                                       cross_value)
            if found is not None:
                return found
        return None

    def move(self, current, direction):
        """按方向返回下一个焦点元素。"""
        item = self.by_id.get(current)
        if item is None:
            return current
        setup = {
            "right": ("x", "y", True),
            "left": ("x", "y", False),
            "down": ("y", "x", True),
            "up": ("y", "x", False),
        }.get(direction)
        if setup is None:
            return current
        axis, cross, forward = setup
        nxt = self._nearest(axis, item[axis], item[cross], forward)
        if nxt is None and self.wrap:
            nxt = self._nearest(axis, item[axis], item[cross],
                                not forward, far=True)
        if nxt is None:
            return current
        return nxt["id"]

    def set_focus(self, item_id):
        """记住当前焦点（只写所属分组）。"""
        item = self.by_id.get(item_id)
        if item is not None:
            self.memory[item["group"]] = item_id

    def focus(self, group):
        """恢复某个分组的焦点，记忆失效时退回该分组第一个可用元素。"""
        remembered = self.memory.get(group)
        if remembered is not None:
            item = self.by_id.get(remembered)
            if item is not None and item["group"] == group \
                    and self._usable(item):
                return remembered
        if self._dirty:
            self._build_index()
        ids = self._ids_by_group.get(group)
        return ids[0] if ids else None
