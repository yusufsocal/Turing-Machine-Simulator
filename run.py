#!/usr/bin/env python3
"""
Convenience launcher for the Turing machines in `Turing Machines/`.

Refer to a machine by a short, case-insensitive fragment of its filename
instead of typing out the full path:

    python run.py ripple_carry 101+110
    python run.py dec_inc 101+110 --trace
    python run.py dec_inc 101+110 --visual

Run with no arguments to list the available machines.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from tm_simulator import ParseError, parse_tm, print_result, run

ROOT = Path(__file__).resolve().parent
MACHINES_DIR = ROOT / "Turing Machines"


def list_machines():
    return sorted(MACHINES_DIR.glob("*.txt"))


def resolve_machine(name):
    path = Path(name)
    if path.is_file():
        return path

    needle = name.lower()
    matches = [p for p in list_machines() if needle in p.stem.lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(
            f"No machine matches {name!r}. Available machines:\n"
            + "\n".join(f"  {p.stem}" for p in list_machines())
        )
    raise SystemExit(
        f"{name!r} matches multiple machines, be more specific:\n"
        + "\n".join(f"  {p.stem}" for p in matches)
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run (or visualize) a machine from 'Turing Machines/' by short name."
    )
    parser.add_argument("machine", nargs="?", help="short name (or path) of the machine, e.g. ripple_carry")
    parser.add_argument("input_str", nargs="?", default="", help="input string for the tape")
    parser.add_argument("--trace", action="store_true", help="print every step")
    parser.add_argument("--visual", action="store_true", help="open the pygame visualizer instead")
    parser.add_argument("--speed", type=float, default=3.0, help="--visual only: steps per second")
    args = parser.parse_args()

    if not args.machine:
        print("Available machines:")
        for p in list_machines():
            print(f"  {p.stem}")
        return

    machine_path = resolve_machine(args.machine)

    if args.visual:
        subprocess.run([
            sys.executable, str(ROOT / "tm_visualizer.py"),
            str(machine_path), args.input_str, "--speed", str(args.speed),
        ])
        return

    tm = parse_tm(machine_path.read_text())
    result = run(tm, args.input_str, trace=args.trace)
    print_result(args.input_str, result, args.trace)


if __name__ == "__main__":
    try:
        main()
    except ParseError as e:
        print(f"Error: {e}")
        sys.exit(1)
