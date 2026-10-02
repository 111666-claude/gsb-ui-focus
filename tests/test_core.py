import unittest

from uifocus.core import Focus


class BasicTest(unittest.TestCase):
    def test_empty_group_has_no_focus(self):
        self.assertIsNone(Focus().focus("main"))

    def test_first_enabled_item_is_default_focus(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        self.assertEqual(focus.focus("main"), "a")

    def test_unknown_current_is_returned_unchanged(self):
        focus = Focus()
        focus.add("a", 0, 0)
        self.assertEqual(focus.move("ghost", "right"), "ghost")

    def test_set_focus_is_remembered(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.set_focus("a")
        self.assertEqual(focus.focus("main"), "a")


class DisabledTest(unittest.TestCase):
    def test_disabled_item_is_not_default(self):
        focus = Focus()
        focus.add("a", 0, 0, enabled=False)
        focus.add("b", 10, 0)
        self.assertEqual(focus.focus("main"), "b")

    def test_hidden_item_is_not_default(self):
        focus = Focus()
        focus.add("a", 0, 0, hidden=True)
        focus.add("b", 10, 0)
        self.assertEqual(focus.focus("main"), "b")


if __name__ == "__main__":
    unittest.main()


def grid_focus(**kwargs):
    focus = Focus(**kwargs)
    for row, names in enumerate((("a", "b", "c"), ("d", "e", "f"))):
        for col, name in enumerate(names):
            focus.add(name, col * 10, row * 10)
    return focus


class DirectionTest(unittest.TestCase):
    def test_vertical_movement_stays_in_column(self):
        focus = grid_focus()
        self.assertEqual(focus.move("a", "down"), "d")
        self.assertEqual(focus.move("d", "up"), "a")
        self.assertEqual(focus.move("c", "down"), "f")
        self.assertEqual(focus.move("f", "up"), "c")

    def test_horizontal_movement_stays_in_row(self):
        focus = grid_focus()
        self.assertEqual(focus.move("a", "right"), "b")
        self.assertEqual(focus.move("c", "left"), "b")
        self.assertEqual(focus.move("d", "right"), "e")
        self.assertEqual(focus.move("f", "left"), "e")

    def test_overlapping_axis_has_priority_over_closer_offset_item(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 5)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("a", "right"), "c")

    def test_non_overlapping_candidates_order_by_perp_distance_then_id(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 5)
        focus.add("c", 10, 3)
        self.assertEqual(focus.move("a", "right"), "c")
        focus.by_id["c"]["enabled"] = False
        self.assertEqual(focus.move("a", "right"), "b")

    def test_hidden_item_is_skipped(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0, hidden=True)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("a", "right"), "c")


class DisabledNavigationTest(unittest.TestCase):
    def test_disabled_item_is_skipped(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0, enabled=False)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("a", "right"), "c")

    def test_no_candidate_without_wrap_keeps_current(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0, enabled=False)
        self.assertEqual(focus.move("a", "right"), "a")
        self.assertEqual(focus.move("a", "down"), "a")

    def test_result_is_never_disabled_or_hidden(self):
        focus = Focus(wrap=True)
        coords = (("a", 0, 0), ("b", 10, 0), ("c", 20, 0),
                  ("d", 0, 10), ("e", 10, 10), ("f", 20, 10))
        for item_id, x, y in coords:
            focus.add(item_id, x, y)
        for target in ("b", "e"):
            focus.by_id[target]["enabled"] = False
        for direction in ("right", "left", "up", "down"):
            result = focus.move("c", direction)
            item = focus.by_id[result]
            self.assertTrue(item["enabled"] and not item["hidden"])

    def test_repeated_navigation_is_stable(self):
        focus = grid_focus()
        first = focus.move("a", "right")
        for _ in range(5):
            self.assertEqual(focus.move("a", "right"), first)


class WrapTest(unittest.TestCase):
    def test_wrap_skips_disabled_item_on_opposite_side(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0, enabled=False)
        focus.add("b", 10, 0)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("c", "right"), "b")

    def test_wrap_goes_to_nearest_item_on_opposite_side(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("a", "left"), "b")
        self.assertEqual(focus.move("c", "right"), "b")

    def test_wrap_keeps_current_when_opposite_side_all_unusable(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0, enabled=False)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("b", "right"), "b")

    def test_without_wrap_there_is_no_cycling(self):
        focus = Focus(wrap=False)
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("b", "right"), "b")


class GroupMemoryTest(unittest.TestCase):
    def _build(self):
        focus = Focus()
        focus.add("a", 0, 0, group="left")
        focus.add("b", 0, 10, group="left")
        focus.add("c", 20, 0, group="right")
        focus.add("d", 20, 10, group="right")
        return focus

    def test_each_group_keeps_its_own_memory(self):
        focus = self._build()
        focus.set_focus("b")
        focus.set_focus("d")
        self.assertEqual(focus.focus("left"), "b")
        self.assertEqual(focus.focus("right"), "d")

    def test_set_focus_does_not_write_other_groups(self):
        focus = self._build()
        focus.set_focus("b")
        self.assertEqual(focus.focus("right"), "c")

    def test_disabled_memory_falls_back_to_first_usable_by_id(self):
        focus = self._build()
        focus.set_focus("b")
        focus.by_id["b"]["enabled"] = False
        self.assertEqual(focus.focus("left"), "a")

    def test_hidden_memory_falls_back_to_first_usable_by_id(self):
        focus = self._build()
        focus.set_focus("b")
        focus.by_id["b"]["hidden"] = True
        self.assertEqual(focus.focus("left"), "a")

    def test_missing_memory_falls_back_to_first_usable(self):
        focus = self._build()
        focus.set_focus("b")
        del focus.by_id["b"]
        self.assertEqual(focus.focus("left"), "a")

    def test_group_without_usable_items_has_no_focus(self):
        focus = Focus()
        focus.add("a", 0, 0, group="g", enabled=False)
        focus.set_focus("a")
        self.assertIsNone(focus.focus("g"))


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_element_count(self):
        def build(count):
            focus = Focus()
            for index in range(count):
                focus.add("i-%d" % index, index * 10, 0)
            focus.move("i-0", "right")
            return focus.scanned
        small = build(1000)
        large = build(100000)
        self.assertLess(small, 10)
        self.assertEqual(large, small)
