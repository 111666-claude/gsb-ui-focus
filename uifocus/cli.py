"""命令行入口：跑焦点导航样例。"""

import argparse

from .core import Focus


def build_parser():
    parser = argparse.ArgumentParser(prog="ui-focus", description="UI 焦点导航")
    parser.add_argument("--sample", default="direction",
                        help="direction / disabled / memory / wrap / scan")
    return parser


def grid():
    focus = Focus()
    for row, names in enumerate((("a", "b", "c"), ("d", "e", "f"))):
        for col, name in enumerate(names):
            focus.add(name, col * 10, row * 10)
    return focus


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "direction":
        focus = grid()
        print("next=%s" % focus.move("a", "down"))
    elif args.sample == "disabled":
        focus = grid()
        focus.by_id["b"]["enabled"] = False
        print("next=%s" % focus.move("a", "right"))
    elif args.sample == "memory":
        focus = Focus()
        focus.add("a", 0, 0, group="left")
        focus.add("b", 0, 10, group="left")
        focus.add("c", 20, 0, group="right")
        focus.add("d", 20, 10, group="right")
        focus.set_focus("b")
        focus.set_focus("d")
        print("left=%s" % focus.focus("left"))
    elif args.sample == "wrap":
        focus = Focus(wrap=True)
        focus.add("a", 0, 0)
        focus.add("b", 10, 0)
        focus.add("c", 20, 0)
        focus.by_id["a"]["enabled"] = False
        print("next=%s" % focus.move("c", "right"))
    elif args.sample == "scan":
        focus = Focus()
        for index in range(3000):
            focus.add("i-%d" % index, index * 10, 0)
        for _ in range(3000):
            focus.move("i-1500", "right")
        print("scanned=%d" % focus.scanned)
    else:
        raise SystemExit("需要 --sample direction|disabled|memory|wrap|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
