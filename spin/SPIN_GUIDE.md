# SPIN Installation and Usage Guide
# ECEN 723 Phase B — Task B.2

---

## 1. Installation

### macOS (recommended — Homebrew)

```bash
brew install spin
```

Verify:

```bash
spin -V
```

Expected output: `Spin Version 6.x.x`

### macOS (manual — no Homebrew)

Download the binary from http://spinroot.com/spin/Src/index.html

```bash
# extract and place on PATH
tar -xzf spin.tar.gz
sudo cp spin /usr/local/bin/spin
sudo chmod +x /usr/local/bin/spin
```

### Linux (apt)

```bash
sudo apt-get install spin
spin -V
```

### Linux (yum / dnf)

```bash
sudo yum install spin
spin -V
```

---

## 2. Files in this directory

| File | Purpose |
|---|---|
| `example_safe.pml` | Safe model — SPIN verifies both properties hold |
| `example_unsafe.pml` | Unsafe model — SPIN finds counterexample traces |

---

## 3. How to run verification

All commands are run from the `spin/` directory:

```bash
cd traffic-system-formal-verification/spin
```

---

### 3.1 Quick simulation (sanity check — one random execution path)

```bash
spin example_safe.pml
```

This prints one execution trace. Use it to confirm the model parses correctly
before running full verification.

---

### 3.2 Full LTL verification — Method A (one command)

```bash
spin -run -ltl no_collision example_safe.pml
spin -run -ltl no_red_light example_safe.pml
```

`-run` compiles and runs the verifier in one step.
SPIN will report either `no errors found` or produce a counterexample trail.

---

### 3.3 Full LTL verification — Method B (compile then run)

This is the standard workflow used in papers and reports.

```bash
# Step 1: generate the verifier source from the model
spin -a example_safe.pml

# Step 2: compile the verifier
cc -O2 -o pan pan.c

# Step 3: run the verifier
./pan -a
```

`-a` tells the verifier to check all acceptance cycles (liveness).
For pure safety properties you can omit it:

```bash
./pan
```

---

### 3.4 Verify the unsafe model (expect errors)

```bash
spin -run -ltl no_collision example_unsafe.pml
spin -run -ltl no_red_light example_unsafe.pml
```

SPIN will output something like:

```
pan:1: assertion violated  (at depth N)
pan: wrote example_unsafe.pml.trail
```

---

### 3.5 Replay a counterexample trail

When SPIN finds an error it writes a `.trail` file.  Replay it to see the
exact sequence of steps that leads to the violation:

```bash
spin -t -p example_unsafe.pml
```

`-t` reads the trail, `-p` prints each step with process and variable state.

---

## 4. What the output means

### Safe model — expected output

```
(Spin Version 6.x.x)
        + Partial Order Reduction

Full statespace search for:
        never claim         + (no_collision)
        assertion violations + (if within scope of claim)
...
State-vector 28 byte, depth reached 18, errors: 0
      96 states, stored
      48 states, matched
...
unreached in proctype Car ...
pan: elapsed time 0 seconds
```

Key line: `errors: 0` — the property holds for all reachable states.

### Unsafe model — expected output

```
pan:1: assertion violated  (at depth 6)
pan: wrote example_unsafe.pml.trail
...
errors: 1
```

Key line: `errors: 1` — SPIN found a state where the property is violated
and wrote the counterexample trace to disk.

---

## 5. Connection to the Python traffic system

| Python system | Promela model |
|---|---|
| `light_control.py` rotating phases | `Light()` process cycling GREEN/RED |
| `checks.py` red-light detection | LTL `no_red_light` property |
| `checks.py` collision detection | LTL `no_collision` property |
| Car at slot 29 crossing to slot 0 | `in_intersection++` / `--` |
| Safe protocol in `step.py` | `light == GREEN && intersection_free` guard |
| `--unsafe-rate 0.05` mode | `example_unsafe.pml` (no guard) |

The Promela model is an abstraction — it captures the logical safety
invariants of the Python simulation in a form that SPIN can exhaustively verify
over all possible interleavings.

---

## 6. Report checklist for Task B.2

- [ ] State which model checker you chose (SPIN) and why
- [ ] Include `example_safe.pml` in the appendix
- [ ] Show the `errors: 0` output for the safe model
- [ ] Show the `errors: 1` / trail output for the unsafe model
- [ ] Map the two LTL properties back to the Python checks (`checks.py`)
- [ ] Include the exact commands used to run SPIN
