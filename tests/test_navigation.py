import unittest

from uifocus.core import Focus


def grid():
    focus = Focus()
    for row, names in enumerate((("a", "b", "c"), ("d", "e", "f"))):
        for col, name in enumerate(names):
            focus.add(name, col * 10, row * 10)
    return focus


class DirectionTest(unittest.TestCase):
    def test_down_moves_to_element_below(self):
        self.assertEqual(grid().move("a", "down"), "d")

    def test_only_elements_on_that_side_are_candidates(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("left", -10, 0)
        focus.add("right", 10, 0)
        self.assertEqual(focus.move("o", "right"), "right")
        self.assertEqual(focus.move("o", "left"), "left")

    def test_along_distance_beats_perpendicular_distance(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("near-off-axis", 5, 100)
        focus.add("far-on-axis", 50, 0)
        self.assertEqual(focus.move("o", "right"), "near-off-axis")

    def test_overlap_ranks_first_within_same_along_distance(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("overlap", 10, 0)
        focus.add("offset", 10, 3)
        self.assertEqual(focus.move("o", "right"), "overlap")

    def test_id_breaks_ties(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("b", 10, 0)
        focus.add("a", 10, 0)
        self.assertEqual(focus.move("o", "right"), "a")

    def test_up_and_left_use_strict_side(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("same", 0, 0)
        focus.add("up", 0, -10)
        self.assertEqual(focus.move("o", "up"), "up")
        self.assertEqual(focus.move("o", "down"), "o")


class DisabledTest(unittest.TestCase):
    def test_move_skips_disabled(self):
        focus = grid()
        focus.by_id["b"]["enabled"] = False
        self.assertEqual(focus.move("a", "right"), "e")

    def test_move_skips_hidden(self):
        focus = grid()
        focus.by_id["b"]["hidden"] = True
        self.assertEqual(focus.move("a", "right"), "e")

    def test_disabled_never_becomes_next_focus(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0, enabled=False)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("b", "right"), "b")

    def test_result_is_usable_or_current(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0, enabled=False)
        result = focus.move("a", "right")
        self.assertEqual(result, "a")

    def test_disabled_at_same_coordinate_falls_to_next_id(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("a", 10, 0, enabled=False)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("o", "right"), "b")

    def test_hidden_at_same_coordinate_falls_to_next_id(self):
        focus = Focus()
        focus.add("o", 0, 0)
        focus.add("a", 10, 0, hidden=True)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("o", "right"), "b")


class WrapTest(unittest.TestCase):
    def test_wrap_cycles_back_to_opposite_edge(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("c", "right"), "a")

    def test_wrap_skips_disabled(self):
        focus = Focus(wrap=True)
        focus.add("a", 0, 0, enabled=False)
        focus.add("b", 10, 0)
        focus.add("c", 20, 0)
        self.assertEqual(focus.move("c", "right"), "b")

    def test_no_wrap_keeps_current(self):
        focus = Focus()
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        self.assertEqual(focus.move("b", "right"), "b")

    def test_wrap_vertical(self):
        focus = Focus(wrap=True)
        focus.add("top", 0, 0)
        focus.add("bottom", 0, 10)
        self.assertEqual(focus.move("bottom", "down"), "top")


class MemoryTest(unittest.TestCase):
    def make_two_groups(self):
        focus = Focus()
        focus.add("a", 0, 0, group="left")
        focus.add("b", 0, 10, group="left")
        focus.add("c", 20, 0, group="right")
        focus.add("d", 20, 10, group="right")
        return focus

    def test_each_group_remembers_its_own_focus(self):
        focus = self.make_two_groups()
        focus.set_focus("b")
        focus.set_focus("d")
        self.assertEqual(focus.focus("left"), "b")
        self.assertEqual(focus.focus("right"), "d")

    def test_set_focus_writes_only_owning_group(self):
        focus = self.make_two_groups()
        focus.set_focus("d")
        self.assertEqual(focus.focus("left"), "a")
        self.assertEqual(focus.focus("right"), "d")

    def test_unusable_memory_falls_back_to_first_usable(self):
        focus = self.make_two_groups()
        focus.set_focus("b")
        focus.by_id["b"]["enabled"] = False
        self.assertEqual(focus.focus("left"), "a")

    def test_missing_memory_falls_back_to_first_usable(self):
        focus = self.make_two_groups()
        focus.set_focus("b")
        del focus.by_id["b"]
        self.assertEqual(focus.focus("left"), "a")


class InvariantTest(unittest.TestCase):
    def test_repeated_moves_are_deterministic(self):
        focus = grid()
        first = [focus.move("a", "right") for _ in range(3)]
        self.assertEqual(first, ["b", "b", "b"])

    def test_scanned_does_not_grow_with_item_count(self):
        small = Focus()
        for index in range(3000):
            small.add("i-%d" % index, index * 10, 0)
        for _ in range(3000):
            small.move("i-1500", "right")
        self.assertLessEqual(small.scanned, 6000)

        big = Focus()
        for index in range(30000):
            big.add("i-%d" % index, index * 10, 0)
        for _ in range(3000):
            big.move("i-15000", "right")
        self.assertLessEqual(big.scanned, 6000)


if __name__ == "__main__":
    unittest.main()
