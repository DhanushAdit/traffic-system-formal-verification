/*
 * ECEN 723 Phase C — V-Group signal system verification (SAFE)
 *
 * Abstracts the deterministic rotating LightController from light_control.py.
 *
 * DIR_CYCLE       = [N, W, S, E]
 * PHASE_DURATIONS = (8, 7, 8, 7)   cycle_span = 30 steps
 *
 * One abstract intersection, 4 directional approaches.  The controller
 * advances deterministically: N for 8 steps, then W for 7, S for 8, E for 7,
 * then back to N.  Exactly one direction is green at every step.
 *
 * Python mapping:
 *   light_control.py  : LightController.decide_signals / cycle_green
 *   state.py          : IntersectionLight.color_for_approach
 *   checks.py         : red_light_violations counter
 *
 * Properties verified:
 *   liveness_N/W/S/E  every approach direction gets green infinitely often
 *                     (P1: vehicles eventually get their turn;
 *                      P2: fairness — no direction is ever starved)
 *   mutex             never more than one direction green at any instant  (P3)
 *   no_phase_skip     signal always advances in the prescribed N->W->S->E
 *                     order — never skips or reverses a phase             (P4, self-choice)
 */

#define DIR_N  0
#define DIR_W  1
#define DIR_S  2
#define DIR_E  3

/* Phase durations from DEFAULT_PHASE_DURATIONS = (8, 7, 8, 7) */
#define DUR_N  8
#define DUR_W  7
#define DUR_S  8
#define DUR_E  7

/* One boolean flag per direction so LTL can reference them directly */
bool g_N = true;
bool g_W = false;
bool g_S = false;
bool g_E = false;

byte cur_dir        = DIR_N;
byte steps_in_phase = 0;

bool mutex_violation     = false;
bool order_violation     = false;

active proctype SignalController() {
    byte dur;
    byte nd;
    byte cnt;

    do
    :: atomic {

        /* determine how long the current phase lasts */
        if
        :: cur_dir == DIR_N -> dur = DUR_N
        :: cur_dir == DIR_W -> dur = DUR_W
        :: cur_dir == DIR_S -> dur = DUR_S
        :: cur_dir == DIR_E -> dur = DUR_E
        fi;

        if
        :: steps_in_phase < dur - 1 ->
            steps_in_phase++

        :: else ->
            /* compute the next direction in the N->W->S->E->N cycle */
            if
            :: cur_dir == DIR_N -> nd = DIR_W
            :: cur_dir == DIR_W -> nd = DIR_S
            :: cur_dir == DIR_S -> nd = DIR_E
            :: cur_dir == DIR_E -> nd = DIR_N
            fi;

            /* P4 check: nd must equal (cur_dir + 1) % 4 */
            if
            :: nd != ((cur_dir + 1) % 4) -> order_violation = true
            :: else -> skip
            fi;

            /* transition: set exactly one green flag */
            if :: nd == DIR_N -> g_N = true :: else -> g_N = false fi;
            if :: nd == DIR_W -> g_W = true :: else -> g_W = false fi;
            if :: nd == DIR_S -> g_S = true :: else -> g_S = false fi;
            if :: nd == DIR_E -> g_E = true :: else -> g_E = false fi;

            /* P3 check: count active greens — must be exactly 1 */
            cnt = 0;
            if :: g_N -> cnt++ :: else -> skip fi;
            if :: g_W -> cnt++ :: else -> skip fi;
            if :: g_S -> cnt++ :: else -> skip fi;
            if :: g_E -> cnt++ :: else -> skip fi;
            if :: cnt > 1 -> mutex_violation = true :: else -> skip fi;

            cur_dir = nd;
            steps_in_phase = 0
        fi
    }
    od
}

/*
 * P1 / P2 — liveness and fairness:
 *   [] <> g_X means direction X is green infinitely often.
 *   This simultaneously proves:
 *     - P1: any vehicle waiting at X will eventually get a green
 *     - P2: the scheduler grants green unconditionally and repeatedly to
 *           every direction (strong fairness, cycle = 30 steps)
 */
ltl liveness_N    { [] <> (g_N) }
ltl liveness_W    { [] <> (g_W) }
ltl liveness_S    { [] <> (g_S) }
ltl liveness_E    { [] <> (g_E) }

/* P3 — mutual exclusion: never two directions green simultaneously */
ltl mutex         { [] (!mutex_violation) }

/* P4 — self-choice: signal always advances in the prescribed N->W->S->E order */
ltl no_phase_skip { [] (!order_violation) }
