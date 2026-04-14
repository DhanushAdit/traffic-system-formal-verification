/*
 * ECEN 723 Phase B — Task B.2  (UNSAFE variant)
 * Model: 1 intersection, 2 cars, 1 traffic light — with deliberate flaws
 *
 * This file intentionally removes the safety guards so that SPIN finds
 * counterexample traces, mirroring the --unsafe-rate mode in the Python
 * simulation (traffic_vehicles --unsafe-rate 0.05).
 *
 * Flaws introduced:
 *   - Cars cross without checking the signal  →  red-light violations
 *   - No mutual exclusion on the intersection  →  collisions possible
 *
 * Expected result: SPIN reports errors and produces counterexample trails
 *   for both no_collision and no_red_light.
 */

#define RED   0
#define GREEN 1

byte  light           = RED;
byte  in_intersection = 0;
bool  red_violation   = false;

ltl no_collision  { [] (in_intersection <= 1) }
ltl no_red_light  { [] (!red_violation) }

active proctype Light() {
    do
    :: light = GREEN
    :: light = RED
    od
}

/* UNSAFE Car — no signal check, no mutex */
active [2] proctype Car() {
    do
    ::  /* record a red-light violation if the signal happens to be red */
        if
        :: light == RED  -> red_violation = true
        :: light == GREEN -> skip
        fi;

        in_intersection++;   /* enter without waiting */
        in_intersection--    /* exit */
    od
}
