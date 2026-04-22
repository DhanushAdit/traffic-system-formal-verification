#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${ROOT_DIR}/output/phase_c"

mkdir -p "${OUT_DIR}"

cleanup_generated() {
    rm -f "${ROOT_DIR}/pan" \
          "${ROOT_DIR}/pan.b" \
          "${ROOT_DIR}/pan.c" \
          "${ROOT_DIR}/pan.h" \
          "${ROOT_DIR}/pan.m" \
          "${ROOT_DIR}/pan.pre" \
          "${ROOT_DIR}/pan.t" \
          "${ROOT_DIR}/_spin_nvr.tmp"
}

trap cleanup_generated EXIT

# Keep the output directory specific to the current infrastructure/i-group run.
find "${OUT_DIR}" -maxdepth 1 -type f -name '*.txt' -delete

run_ltl() {
    local model="$1"
    local prop="$2"
    local tag="$3"
    spin -run -ltl "${prop}" "${model}" > "${OUT_DIR}/${tag}.txt"
}

cd "${ROOT_DIR}"

# I-group safe vehicle properties
run_ltl phase_c_i_group_safe.pml no_uturn        i_group_safe_no_uturn
run_ltl phase_c_i_group_safe.pml no_red_light    i_group_safe_no_red_light
run_ltl phase_c_i_group_safe.pml no_collision    i_group_safe_no_collision
run_ltl phase_c_i_group_safe.pml no_wrong_way    i_group_safe_no_wrong_way
run_ltl phase_c_i_group_safe.pml car0_visits_all i_group_safe_car0_visits_all
run_ltl phase_c_i_group_safe.pml car1_visits_all i_group_safe_car1_visits_all

# Optional unsafe counterexamples for screenshots
run_ltl phase_c_i_group_unsafe.pml no_red_light  i_group_unsafe_no_red_light
run_ltl phase_c_i_group_unsafe.pml no_collision  i_group_unsafe_no_collision

echo "Phase C outputs written to ${OUT_DIR}"
