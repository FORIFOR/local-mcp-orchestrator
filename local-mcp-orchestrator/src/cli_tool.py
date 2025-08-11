from __future__ import annotations

import argparse
import sys
from typing import Optional


def _cmd_greet(args: argparse.Namespace) -> int:
    name = args.name or "world"
    print(f"Hello, {name}!")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    from .adder import add

    try:
        a = float(args.a)
        b = float(args.b)
    except Exception:
        print("error: a and b must be numbers", file=sys.stderr)
        return 2
    res = add(a, b)
    # Show as int if integral
    if res.is_integer():
        print(int(res))
    else:
        print(res)
    return 0


def _cmd_divide(args: argparse.Namespace) -> int:
    from .calc import divide

    try:
        a = float(args.a)
        b = float(args.b)
    except Exception:
        print("error: a and b must be numbers", file=sys.stderr)
        return 2
    try:
        res = divide(a, b)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if res.is_integer():
        print(int(res))
    else:
        print(res)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cli-tool", description="Sample CLI tool with greet/add/divide")
    sub = p.add_subparsers(dest="cmd", required=True)

    pg = sub.add_parser("greet", help="Print greeting")
    pg.add_argument("--name", default="world")
    pg.set_defaults(func=_cmd_greet)

    pa = sub.add_parser("add", help="Add two numbers")
    pa.add_argument("a")
    pa.add_argument("b")
    pa.set_defaults(func=_cmd_add)

    pd = sub.add_parser("divide", help="Divide two numbers")
    pd.add_argument("a")
    pd.add_argument("b")
    pd.set_defaults(func=_cmd_divide)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 2
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())

