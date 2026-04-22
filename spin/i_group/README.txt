Infrastructure / I-Group Formal Verification Package

This folder contains the files needed for the infrastructure team's Phase C
formal verification work.

Files in this folder:

- `phase_c_i_group_safe.pml`
  Safe Promela model used to prove the required infrastructure properties.
- `phase_c_i_group_unsafe.pml`
  Intentionally broken model used to generate counterexamples for screenshots.
- `run_phase_c_checks.sh`
  Script that runs the i-group SPIN checks and writes fresh outputs.

Outputs:

- Running the script creates `output/phase_c/` under this folder.
- That output directory contains the final `.txt` verification results.

How to run:

```bash
cd "/run/user/1000/gvfs/sftp:host=olympus.ece.tamu.edu,user=dhanush_adithya/home/grads/d/dhanush_adithya/spr26/formal/traffic-system-formal-verification/spin/i_group"
chmod +x run_phase_c_checks.sh
./run_phase_c_checks.sh 2>&1 | tee spin_out.txt
```

How to summarize the final verdicts:

```bash
grep -Rni "errors:\\|assertion violated" output/phase_c
```

Expected result pattern:

- safe files should show `errors: 0`
- unsafe files should show `errors: 1`

Safe properties checked:

- `no_uturn`
- `no_red_light`
- `no_collision`
- `no_wrong_way`
- `car0_visits_all`
- `car1_visits_all`

Unsafe counterexamples generated:

- `no_red_light`
- `no_collision`
