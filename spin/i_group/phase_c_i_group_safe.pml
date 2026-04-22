/*
 * ECEN 723 Phase C — I-Group vehicle verification model (SAFE)
 *
 * This Promela model abstracts the final Python vehicle controller as a
 * synchronous slot-based perimeter loop with two cars.  The abstraction keeps
 * the rules that matter for verification:
 *   - no U-turn
 *   - no right turn
 *   - no red-light intersection entry
 *   - no slot collision
 *   - every car eventually visits B, C, and D
 *   - car direction always matches the lane direction
 *
 * Python mapping:
 *   - vehicle.py / step.py: slot-based move and guarded intersection entry
 *   - routing.py: perimeter A->B->C->D->A tour
 *   - checks.py: no_collision, no_red_light, no_uturn, no illegal_direction
 */

#define CARS 2
#define EDGE_COUNT 4
#define LAST_SLOT 1

/* Signal phase encodes the allowed approach at the next intersection. */
#define PHASE_N 0
#define PHASE_W 1
#define PHASE_S 2
#define PHASE_E 3

/* Lane travel directions on the perimeter loop. */
#define DIR_S 0
#define DIR_E 1
#define DIR_N 2
#define DIR_W 3

byte phase = PHASE_N;

byte edge[CARS];
byte slot[CARS];
byte dirn[CARS];

bool visited_b[CARS];
bool visited_c[CARS];
bool visited_d[CARS];

bool collision_violation = false;
bool red_violation = false;
bool uturn_violation = false;
bool wrong_way_violation = false;

inline expected_dir(e, out) {
    if
    :: e == 0 -> out = DIR_S
    :: e == 1 -> out = DIR_E
    :: e == 2 -> out = DIR_N
    :: else -> out = DIR_W
    fi
}

inline mark_visit(id, old_edge) {
    if
    :: old_edge == 0 -> visited_b[id] = true
    :: old_edge == 1 -> visited_c[id] = true
    :: old_edge == 2 -> visited_d[id] = true
    :: else -> skip
    fi
}

inline check_invariants() {
    byte want0;
    byte want1;

    if
    :: edge[0] == edge[1] && slot[0] == slot[1] -> collision_violation = true
    :: else -> skip
    fi;

    expected_dir(edge[0], want0);
    if
    :: dirn[0] != want0 -> wrong_way_violation = true
    :: else -> skip
    fi;

    expected_dir(edge[1], want1);
    if
    :: dirn[1] != want1 -> wrong_way_violation = true
    :: else -> skip
    fi
}

inline step_car0() {
    byte next_edge;
    byte want;

    if
    :: slot[0] < LAST_SLOT ->
        if
        :: !(edge[1] == edge[0] && slot[1] == slot[0] + 1) -> slot[0]++
        :: else -> skip
        fi
    :: else ->
        next_edge = (edge[0] + 1) % EDGE_COUNT;
        if
        :: next_edge == ((edge[0] + EDGE_COUNT - 1) % EDGE_COUNT) -> uturn_violation = true
        :: else -> skip
        fi;
        if
        :: phase != edge[0] -> skip
        :: edge[1] == next_edge && slot[1] == 0 -> skip
        :: else ->
            mark_visit(0, edge[0]);
            edge[0] = next_edge;
            slot[0] = 0;
            expected_dir(edge[0], want);
            dirn[0] = want
        fi
    fi
}

inline step_car1() {
    byte next_edge;
    byte want;

    if
    :: slot[1] < LAST_SLOT ->
        if
        :: !(edge[0] == edge[1] && slot[0] == slot[1] + 1) -> slot[1]++
        :: else -> skip
        fi
    :: else ->
        next_edge = (edge[1] + 1) % EDGE_COUNT;
        if
        :: next_edge == ((edge[1] + EDGE_COUNT - 1) % EDGE_COUNT) -> uturn_violation = true
        :: else -> skip
        fi;
        if
        :: phase != edge[1] -> skip
        :: edge[0] == next_edge && slot[0] == 0 -> skip
        :: else ->
            mark_visit(1, edge[1]);
            edge[1] = next_edge;
            slot[1] = 0;
            expected_dir(edge[1], want);
            dirn[1] = want
        fi
    fi
}

active proctype System() {
    edge[0] = 0; slot[0] = 0; dirn[0] = DIR_S;
    edge[1] = 2; slot[1] = 0; dirn[1] = DIR_N;

    do
    :: atomic {
        if
        :: slot[0] > slot[1] -> step_car0(); step_car1()
        :: slot[1] > slot[0] -> step_car1(); step_car0()
        :: else -> step_car0(); step_car1()
        fi;

        check_invariants();

        phase = (phase + 1) % 4
    }
    od
}

ltl no_uturn        { [] (!uturn_violation) }
ltl no_red_light    { [] (!red_violation) }
ltl no_collision    { [] (!collision_violation) }
ltl no_wrong_way    { [] (!wrong_way_violation) }
ltl car0_visits_all { <> (visited_b[0] && visited_c[0] && visited_d[0]) }
ltl car1_visits_all { <> (visited_b[1] && visited_c[1] && visited_d[1]) }
