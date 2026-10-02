"""UI 焦点导航：按方向找下一个可聚焦元素，并记住每个分组上次的焦点。

候选只包含 enabled 且未隐藏的元素；方向选择先优先在垂直轴上与
当前元素重叠（垂直距离 0）的候选，再按沿方向距离、垂直方向距离、
id 字典序排序；无候选时按 wrap 决定绕到对侧还是保持原焦点；
每个分组独立记忆上次焦点。

查询走按坐标轴建立的排序索引（bisect）：重叠候选从“同一行/列”的
沿轴序列里取最近槽，非重叠候选只取沿轴最近的若干槽，单次导航
不遍历全部元素，scanned 不随元素数线性增长；索引在增删元素后的
下一次查询时惰性重建。
"""

from bisect import bisect_left, bisect_right

_DIRECTIONS = {
    "right": ("x", "y"),
    "left": ("x", "y"),
    "down": ("y", "x"),
    "up": ("y", "x"),
}


class Focus:
    """焦点导航。"""

    def __init__(self, wrap=False):
        self.wrap = wrap
        self.items = []
        self.by_id = {}
        self.memory = {}
        self.scanned = 0
        self._dirty = True
        # axis -> dict with:
        #   coords: sorted unique along coordinates
        #   buckets: {coord: (perp_values, ids)} 同槽内按 (perp, id) 排序
        #   rows: {perp: (along_values, ids)} 同行/列内按 (along, id) 排序
        self._axes = {}
        self._group_ids = {}

    def add(self, item_id, x, y, group="main", enabled=True, hidden=False):
        item = {"id": item_id, "x": x, "y": y, "group": group,
                "enabled": enabled, "hidden": hidden}
        self.items.append(item)
        self.by_id[item_id] = item
        self._dirty = True
        return item

    def _usable(self, item_id):
        self.scanned += 1
        item = self.by_id[item_id]
        return item["enabled"] and not item["hidden"]

    def _ensure_index(self):
        if not self._dirty:
            return
        raw = {"x": {}, "y": {}}
        group_ids = {}
        for item in self.items:
            raw["x"].setdefault(item["x"], []).append(item)
            raw["y"].setdefault(item["y"], []).append(item)
            group_ids.setdefault(item["group"], []).append(item["id"])
        axes = {}
        for axis, buckets in raw.items():
            cross = "y" if axis == "x" else "x"
            prepared = {}
            rows = {}
            for coord, bucket in buckets.items():
                bucket.sort(key=lambda it, c=cross: (it[c], it["id"]))
                prepared[coord] = ([it[cross] for it in bucket],
                                   [it["id"] for it in bucket])
                for it in bucket:
                    rows.setdefault(it[cross], []).append((coord, it["id"]))
            row_index = {}
            for perp, entries in rows.items():
                entries.sort()
                row_index[perp] = ([along for along, _ in entries],
                                   [item_id for _, item_id in entries])
            axes[axis] = {"coords": sorted(buckets), "buckets": prepared,
                          "rows": row_index}
        self._axes = axes
        self._group_ids = {group: sorted(ids) for group, ids in group_ids.items()}
        self._dirty = False

    def _aligned_pick(self, axis, perp, along, sign, current_id):
        """同一行/列（垂直距离 0）里沿方向最近的可用元素。"""
        row = self._axes[axis]["rows"].get(perp)
        if row is None:
            return None
        alongs, ids = row
        if sign > 0:
            start = bisect_right(alongs, along)
            positions = range(start, len(alongs))
        else:
            positions = range(bisect_left(alongs, along) - 1, -1, -1)
        for pos in positions:
            item_id = ids[pos]
            if item_id != current_id and self._usable(item_id):
                return item_id
        return None

    def _nearest_pick(self, axis, along, sign, perp, current_id):
        """非重叠回退：沿方向最近槽里垂直距离最小的可用元素。"""
        coords = self._axes[axis]["coords"]
        buckets = self._axes[axis]["buckets"]
        if sign > 0:
            slots = range(bisect_right(coords, along), len(coords))
        else:
            slots = range(bisect_left(coords, along) - 1, -1, -1)
        for slot in slots:
            perps, ids = buckets[coords[slot]]
            start = bisect_left(perps, perp)
            left, right = start - 1, start
            while left >= 0 or right < len(perps):
                dl = perp - perps[left] if left >= 0 else None
                dr = perps[right] - perp if right < len(perps) else None
                if dl is None:
                    dist, side = dr, 1
                elif dr is None:
                    dist, side = dl, -1
                elif dr <= dl:
                    dist, side = dr, 1
                else:
                    dist, side = dl, -1
                chosen = None
                k = left
                while k >= 0 and perp - perps[k] == dist:
                    if ids[k] != current_id and self._usable(ids[k]):
                        chosen = ids[k] if chosen is None or ids[k] < chosen \
                            else chosen
                    k -= 1
                k = right
                while k < len(perps) and perps[k] - perp == dist:
                    candidate = ids[k]
                    if candidate != current_id and self._usable(candidate):
                        if chosen is None or candidate < chosen:
                            chosen = candidate
                    k += 1
                if chosen is not None:
                    return chosen
                if side < 0:
                    left -= 1
                else:
                    right += 1
        return None

    def _search(self, current_id, direction_name, sign):
        axis, cross = _DIRECTIONS[direction_name]
        current = self.by_id[current_id]
        along, perp = current[axis], current[cross]
        aligned = self._aligned_pick(axis, perp, along, sign, current_id)
        if aligned is not None:
            return aligned
        return self._nearest_pick(axis, along, sign, perp, current_id)

    def move(self, current, direction):
        """按方向返回下一个焦点元素。"""
        if current not in self.by_id:
            return current
        self._ensure_index()
        sign = 1 if direction in ("right", "down") else -1
        result = self._search(current, direction, sign)
        if result is None and self.wrap:
            result = self._search(current, direction, -sign)
        return result if result is not None else current

    def set_focus(self, item_id):
        """记住当前焦点，只写该元素所属分组。"""
        item = self.by_id.get(item_id)
        if item is not None:
            self.memory[item["group"]] = item_id

    def focus(self, group):
        """恢复某分组的焦点；记忆失效时退回该分组第一个可用元素。"""
        remembered = self.memory.get(group)
        if remembered is not None:
            item = self.by_id.get(remembered)
            if item is not None and item["group"] == group \
                    and item["enabled"] and not item["hidden"]:
                return remembered
        self._ensure_index()
        for item_id in self._group_ids.get(group, []):
            item = self.by_id[item_id]
            if item["enabled"] and not item["hidden"]:
                return item_id
        return None
