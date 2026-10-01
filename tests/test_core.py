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
