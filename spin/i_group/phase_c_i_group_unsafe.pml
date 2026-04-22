/*
 * ECEN 723 Phase C — Infrastructure / I-Group unsafe counterexample model
 *
 * This model is intentionally broken so the infrastructure team can generate
 * concrete SPIN counterexamples for the report.  It is not meant to model the
 * final software faithfully:
 *   - it allows cars to cross on red
 *   - it can force both cars into the same abstract slot
 */

#define CARS 2
#define EDGE_COUNT 4
#define LAST_SLOT 1

#define PHASE_N 0
#define PHASE_W 1
#define PHASE_S 2
#define PHASE_E 3

byte phase = PHASE_N;
byte edge[CARS];
byte slot[CARS];
byte step_no = 0;

bool collision_violation = false;
bool red_violation = false;

active proctype System() {
    /* Both cars begin at the end of different edges. */
    edge[0] = 0; slot[0] = 1;
    edge[1] = 2; slot[1] = 1;

    do
    :: atomic {
        if
        :: step_no == 0 ->
            /* Immediate red-light violation from car 1. */
            if
            :: phase != edge[1] -> red_violation = true
            :: else -> skip
            fi;
            edge[1] = (edge[1] + 1) % EDGE_COUNT;
            slot[1] = 0
        :: step_no == 1 ->
            /* Force a collision by placing both cars in the same slot. */
            edge[0] = 1; slot[0] = 0;
            edge[1] = 1; slot[1] = 0;
            collision_violation = true
        :: else ->
            skip
        fi;

        step_no++;
        phase = (phase + 1) % 4
    }
    od
}

ltl no_red_light { [] (!red_violation) }
ltl no_collision { [] (!collision_violation) }
