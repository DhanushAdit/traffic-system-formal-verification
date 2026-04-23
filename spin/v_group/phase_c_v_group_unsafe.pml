/*
 * ECEN 723 Phase C — V-Group signal system verification (UNSAFE / counterexample)
 *
 * Intentionally broken signal controller used to generate concrete SPIN
 * counterexample traces for the report.  Two violations are forced:
 *
 *   step 0 — mutex violation:
 *     Both g_N and g_W are set to true simultaneously, so cnt == 2 and
 *     mutex_violation is flagged.
 *
 *   step 1 — phase-order violation:
 *     The signal jumps directly from N to S, skipping W entirely.
 *     DIR_S (2) != (DIR_N + 1) % 4  (1), so order_violation is flagged.
 */

#define DIR_N  0
#define DIR_W  1
#define DIR_S  2
#define DIR_E  3

bool g_N = true;
bool g_W = false;
bool g_S = false;
bool g_E = false;

byte cur_dir = DIR_N;

bool mutex_violation = false;
bool order_violation = false;

active proctype System() {
    byte step_no = 0;
    byte cnt;

    do
    :: atomic {
        if
        :: step_no == 0 ->
            /* Force two greens at once: N and W both true */
            g_N = true;
            g_W = true;
            cnt = 0;
            if :: g_N -> cnt++ :: else -> skip fi;
            if :: g_W -> cnt++ :: else -> skip fi;
            if :: g_S -> cnt++ :: else -> skip fi;
            if :: g_E -> cnt++ :: else -> skip fi;
            if :: cnt > 1 -> mutex_violation = true :: else -> skip fi

        :: step_no == 1 ->
            /* Phase skip: N jumps directly to S (bypasses W) */
            if
            :: DIR_S != ((DIR_N + 1) % 4) -> order_violation = true
            :: else -> skip
            fi;
            g_N = false; g_W = false; g_S = true; g_E = false;
            cur_dir = DIR_S

        :: else -> skip
        fi;
        step_no++
    }
    od
}

ltl mutex         { [] (!mutex_violation) }
ltl no_phase_skip { [] (!order_violation) }
