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

find "${OUT_DIR}" -maxdepth 1 -type f -name '*.txt' -delete

run_ltl() {
    local model="$1"
    local prop="$2"
    local tag="$3"
    spin -run -ltl "${prop}" "${model}" > "${OUT_DIR}/${tag}.txt"
}

cd "${ROOT_DIR}"

# V-group safe signal properties (P1/P2: liveness/fairness, P3: mutex, P4: phase order)
run_ltl phase_c_v_group_safe.pml liveness_N    v_group_safe_liveness_N
run_ltl phase_c_v_group_safe.pml liveness_W    v_group_safe_liveness_W
run_ltl phase_c_v_group_safe.pml liveness_S    v_group_safe_liveness_S
run_ltl phase_c_v_group_safe.pml liveness_E    v_group_safe_liveness_E
run_ltl phase_c_v_group_safe.pml mutex         v_group_safe_mutex
run_ltl phase_c_v_group_safe.pml no_phase_skip v_group_safe_no_phase_skip

# V-group unsafe counterexamples
run_ltl phase_c_v_group_unsafe.pml mutex         v_group_unsafe_mutex
run_ltl phase_c_v_group_unsafe.pml no_phase_skip v_group_unsafe_no_phase_skip

echo "V-Group Phase C outputs written to ${OUT_DIR}"
