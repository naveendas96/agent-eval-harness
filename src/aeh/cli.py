from __future__ import annotations

import argparse
import sys

from .adapters import get_adapter
from .compare import compare
from .runner import run_suite


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("aeh")
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    r.add_argument("suite")
    r.add_argument("--agent", default="mock:v1")
    r.add_argument("--run-id", required=True)
    c = s.add_parser("compare")
    c.add_argument("base")
    c.add_argument("cand")
    c.add_argument("--fail-on-regression", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "run":
        res = run_suite(a.suite, get_adapter(a.agent), a.run_id)
        print(" ".join(f"{k}={v}" for k, v in res.items()))
        return 0
    res = compare(a.base, a.cand)
    print(f"| metric | {a.base} | {a.cand} | delta | regression |\n|---|---|---|---|---|")
    for m, x, y, d, reg in res["rows"]:
        print(f"| {m} | {x} | {y} | {d} | {'**YES**' if reg else 'no'} |")
    if res["regressions"]:
        print(f"\nREGRESSIONS: {', '.join(res['regressions'])}")
        if a.fail_on_regression:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
