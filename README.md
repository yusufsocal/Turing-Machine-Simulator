# Turing-Machine-Simulator

A Turing machine simulator with a two-way infinite tape, plus a pygame visualizer.

## Quick start

The easiest way to run a machine is `run.bat`, which lets you refer to a machine
by a short piece of its filename instead of the full path:

```bash
run.bat ripple_carry 101+110
run.bat dec_inc 101+110 --trace
run.bat prescan 101+110 --visual
```
Might need to add a `.\` before the running the commands.

Run it with no arguments to list the available machines:

```bash
run.bat
```

If a short name matches more than one machine, `run.bat` will tell you and list
the candidates so you can be more specific.

`run.bat` works even if `python` isn't on your PATH — it falls back to the
Python install it was set up with. If you reinstall Python somewhere else,
update the `PY_EXE` path at the top of `run.bat`.

## Running directly

You can also call the scripts yourself:

```bash
python tm_simulator.py "Turing Machines/binary_adder_ripple_carry.txt" "101+110" --trace
python tm_visualizer.py "Turing Machines/binary_adder_ripple_carry.txt" "101+110" --speed 5
```

- `tm_simulator.py` — CLI simulator. Reports accept/reject and the final tape;
  `--trace` prints every step.
- `tm_visualizer.py` — animated pygame view of the tape. Requires `pygame`
  (`pip install pygame`). Controls: `space` play/pause, `←`/`→` step,
  `↑`/`↓` speed, `r` reset, `esc` quit.
- `run.py` — the short-name launcher `run.bat` wraps; dispatches to either of
  the above.

## Machines

All machine files live in `Turing Machines/`:

- `binary_adder_ripple_carry.txt` — adds two binary numbers digit-by-digit
  with carry propagation (46 states).
- `binary_adder_decrement_increment.txt` — adds two binary numbers by
  repeatedly decrementing one operand and incrementing the other (6 states).
- `binary_adder_decrement_increment_prescan.txt` — same algorithm as above,
  but does an initial scan-and-rewind pass over the tape first (9 states).

## Machine file format

```
M=({"state1","state2",...}, {'0','1',...}, {'0','1','B',...}, d, "start_state", 'B', {"accept_state"})
d=[
    ("state",'symbol')->("newstate",'newsymbol',L),
    ...
]
```

Two-way infinite tape (blanks generated on demand in both directions).
`L`/`R` give the head's direction; `B` is blank.
