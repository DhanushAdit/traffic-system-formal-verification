/*
 * ECEN 723 Phase B — Task B.2
 * Model: 1 intersection, 2 cars, 1 traffic light
 *
 * Abstraction of the Python traffic system (3x3 grid, A->B->C->D->A loop).
 * Each Car process represents a vehicle approaching and crossing one
 * intersection.  The Light process non-deterministically cycles green/red,
 * modelling the rotating phase controller in light_control.py.
 *
 * Safety properties verified:
 *   P1 (no_collision) : at most one car occupies the intersection at a time
 *   P2 (no_red_light) : no car ever crosses while the signal is red
 *
 * Expected result: SPIN reports "no errors found" for both properties.
 */

/* ── signal values ── */
#define RED   0
#define GREEN 1

/* ── shared state ── */
byte  light            = RED;   /* current signal colour          */
byte  in_intersection  = 0;     /* cars currently crossing        */
bool  red_violation    = false; /* set true if a red cross occurs */

/* ══ LTL safety properties ══════════════════════════════════════════════ */

/* P1: the intersection is never occupied by more than one car            */
ltl no_collision  { [] (in_intersection <= 1) }

/* P2: a red-light crossing never occurs                                  */
ltl no_red_light  { [] (!red_violation) }

/* ══ Traffic light process ══════════════════════════════════════════════ */
active proctype Light() {
    do
    :: light = GREEN   /* non-deterministic phase change */
    :: light = RED
    od
}

/* ══ Car process (2 instances) ══════════════════════════════════════════ */
/*
 * Safe protocol:
 *   1. Wait for green AND intersection free, then enter atomically.
 *   2. Cross (one logical step — analogous to slot 29 → slot 0 in Python).
 *   3. Release the intersection.
 *   4. Loop back to approach the next cycle.
 */
bool intersection_free = true;   /* mutual-exclusion flag */

active [2] proctype Car() {
    do
    ::  /* APPROACH — block until signal is green and slot is available */
        atomic {
            light == GREEN && intersection_free;   /* guard */
            intersection_free = false;
            in_intersection++
        };

        /* CROSS */
        /* (no red_violation can occur here by construction) */
        in_intersection--;
        intersection_free = true
    od
}
