#!/usr/bin/env python3
"""
Faithful Python reimplementation of bikeiser/turing-sim's Turing.hs semantics (From course IN3130 in UiO, 2026).

Tape model: two-way infinite (blanks generated on demand in either direction).
Format: same M=(...) / d=[...] syntax as the assignment's Figure 1 / README.
"""
import re
import sys


class ParseError(Exception):
    pass


def split_top_level(s):
    """Split s on top-level commas, respecting {}, (), '' , "" nesting."""
    parts = []
    depth = 0
    cur = []
    in_squote = False
    in_dquote = False
    for ch in s:
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
        elif ch == '"' and not in_squote:
            in_dquote = not in_dquote
        if not in_squote and not in_dquote:
            if ch in "{(":
                depth += 1
            elif ch in "})":
                depth -= 1
        if ch == "," and depth == 0 and not in_squote and not in_dquote:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts]


def parse_tm(text):
    text = text.strip()

    m_start = text.find("M")
    eq = text.find("=", m_start)
    open_paren = text.find("(", eq)
    if open_paren == -1:
        raise ParseError("Could not find 'M=(' in the description.")

    # find matching close paren for open_paren
    depth = 0
    close_paren = None
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                close_paren = i
                break
    if close_paren is None:
        raise ParseError("Unbalanced parentheses in M=(...).")

    inner = text[open_paren + 1:close_paren]
    fields = split_top_level(inner)
    if len(fields) != 7:
        raise ParseError(f"Expected 7 fields in M=(...), found {len(fields)}: {fields}")

    states_raw, input_alpha_raw, tape_alpha_raw, d_field, start_raw, blank_raw, accept_raw = fields

    def parse_states(s):
        return set(re.findall(r'"([^"]*)"', s))

    def parse_chars(s):
        return set(re.findall(r"'([^'])'", s))

    states = parse_states(states_raw)
    input_alphabet = parse_chars(input_alpha_raw)
    tape_alphabet = parse_chars(tape_alpha_raw)
    start_state = re.findall(r'"([^"]*)"', start_raw)[0]
    blank = re.findall(r"'([^'])'", blank_raw)[0]
    accept_states = parse_states(accept_raw)

    d_match = re.search(r'd\s*=\s*\[(.*)\]\s*$', text, re.DOTALL)
    if not d_match:
        raise ParseError("Could not parse the d=[...] transition list.")
    d_body = d_match.group(1)

    transitions = {}
    trans_pattern = re.compile(
        r'\(\s*"([^"]*)"\s*,\s*\'([^\'])\'\s*\)\s*->\s*\(\s*"([^"]*)"\s*,\s*\'([^\'])\'\s*,\s*([LR])\s*\)'
    )
    for tm in trans_pattern.finditer(d_body):
        in_state, in_char, out_state, out_char, direction = tm.groups()
        transitions[(in_state, in_char)] = (out_state, out_char, direction)

    if not transitions:
        raise ParseError("No transitions parsed, check the d=[...] syntax.")

    # well-formedness checks (mirroring Turing.hs's wellFormed)
    if start_state not in states:
        raise ParseError(f"Start state {start_state!r} not in states.")
    for a in accept_states:
        if a not in states:
            raise ParseError(f"Accept state {a!r} not in states.")
    for a in input_alphabet:
        if a not in tape_alphabet:
            raise ParseError(f"Input symbol {a!r} not in tape alphabet.")
    for (s_in, c_in), (s_out, c_out, _d) in transitions.items():
        if s_in not in states or s_out not in states:
            raise ParseError(f"Transition references unknown state near {(s_in, c_in)}.")
        if c_in not in tape_alphabet or c_out not in tape_alphabet:
            raise ParseError(f"Transition references unknown tape symbol near {(s_in, c_in)}.")

    return {
        "states": states,
        "input_alphabet": input_alphabet,
        "tape_alphabet": tape_alphabet,
        "transitions": transitions,
        "start_state": start_state,
        "blank": blank,
        "accept_states": accept_states,
    }


def run(tm, input_str, max_steps=200000, trace=False):
    blank = tm["blank"]
    transitions = tm["transitions"]
    accept_states = tm["accept_states"]

    if input_str == "":
        left, head_char, right = [], blank, []
    else:
        for c in input_str:
            if c not in tm["input_alphabet"]:
                raise ParseError(f"Input symbol {c!r} not in input alphabet.")
        left, head_char, right = [], input_str[0], list(input_str[1:])

    state = tm["start_state"]
    steps = 0
    trace_lines = []

    leading_blanks_re = re.compile("^" + re.escape(blank) + r"{2,}")
    trailing_blanks_re = re.compile(re.escape(blank) + r"{2,}$")

    def render():
        tape_str = "".join(left) + head_char + "".join(right)
        tape_str = leading_blanks_re.sub(blank, tape_str)
        tape_str = trailing_blanks_re.sub(blank, tape_str)
        return tape_str + f"   [state={state}]"

    if trace:
        trace_lines.append(render())

    while True:
        if state in accept_states:
            tape = list(left) + [head_char] + right
            # prune leading/trailing blanks, like Turing.hs's pruneTape
            while tape and tape[0] == blank:
                tape.pop(0)
            while tape and tape[-1] == blank:
                tape.pop()
            return {
                "accept": True,
                "final_tape": "".join(tape),
                "steps": steps,
                "trace": trace_lines,
            }

        key = (state, head_char)
        if key not in transitions:
            tape = list(left) + [head_char] + right
            while tape and tape[0] == blank:
                tape.pop(0)
            while tape and tape[-1] == blank:
                tape.pop()
            return {
                "accept": False,
                "final_tape": "".join(tape),
                "steps": steps,
                "trace": trace_lines,
                "rejected_at": key,
            }

        new_state, write_char, direction = transitions[key]
        state = new_state
        head_char = write_char
        steps += 1

        if direction == "L":
            if left:
                new_head = left.pop()
            else:
                new_head = blank
            right.insert(0, head_char)
            head_char = new_head
        else:  # R
            if right:
                new_head = right.pop(0)
            else:
                new_head = blank
            left.append(head_char)
            head_char = new_head

        if trace:
            trace_lines.append(render())

        if steps > max_steps:
            raise ParseError(f"Exceeded {max_steps} steps, likely an infinite loop.")


def main():
    if len(sys.argv) < 3:
        print("Usage: tmsim.py <machine_file> <input_string> [--trace]")
        sys.exit(1)
    path = sys.argv[1]
    input_str = sys.argv[2]
    trace = "--trace" in sys.argv[3:]

    with open(path) as f:
        text = f.read()

    tm = parse_tm(text)
    result = run(tm, input_str, trace=trace)

    if trace:
        print("\n".join(result["trace"]))
        print("---")

    print(f"input:      {input_str}")
    print(f"steps:      {result['steps']}")
    print(f"result:     {'accept' if result['accept'] else 'reject'}")
    print(f"final tape: {result['final_tape']!r}")
    if not result["accept"]:
        print(f"rejected at (state, symbol): {result['rejected_at']}")


if __name__ == "__main__":
    main()
