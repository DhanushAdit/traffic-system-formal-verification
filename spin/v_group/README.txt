V-Group Signal System Formal Verification Package

This folder contains the Phase C formal verification artifacts for the
v-group (signal / infrastructure verification).

Files:

  phase_c_v_group_safe.pml
    Safe Promela model of the deterministic rotating LightController.
    Verifies all four required v-group properties.

  phase_c_v_group_unsafe.pml
    Intentionally broken model to generate counterexample traces for the
    mutex and no_phase_skip properties.

  run_phase_c_v_group_checks.sh
    Runs all SPIN checks and writes results to output/phase_c/.

How to run:

  cd <path-to-repo>/spin/v_group
  chmod +x run_phase_c_v_group_checks.sh
  ./run_phase_c_v_group_checks.sh 2>&1 | tee spin_out.txt

Check verdicts only:

  grep -Rni "errors:" output/phase_c

Expected results:

  Safe checks  -> errors: 0   (all 6 properties hold)
  Unsafe checks -> errors: 1  (mutex and no_phase_skip produce counterexamples)

Properties and their mapping to course requirements:

  liveness_N/W/S/E  [] <> g_X
    P1: every vehicle eventually gets a green signal
    P2: green granted unconditionally fairly among all directions
        (each direction gets green every 30 steps, infinitely often)

  mutex             [] (!mutex_violation)
    P3: at any moment only one direction is green

  no_phase_skip     [] (!order_violation)
    P4 (self-choice): signal always advances in the prescribed
        N->W->S->E->N order — never skips or reverses a phase

Python model mapping:

  light_control.py  LightController / cycle_green
    DIR_CYCLE = [N, W, S, E]
    DEFAULT_PHASE_DURATIONS = (8, 7, 8, 7)  cycle = 30 steps
    At every step exactly one direction is green (no all-red period).

  state.py          IntersectionLight.color_for_approach
    The abstract g_N/g_W/g_S/g_E booleans correspond to the
    green_approach field of IntersectionLight.

  checks.py         red_light_violations counter
    The mutex property proves the invariant that underpins the
    checks.py red-light detection logic.
