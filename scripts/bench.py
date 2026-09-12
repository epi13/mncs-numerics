#!/usr/bin/env python3
"""Benchmark harness: steps + wall-clock per kernel per backend.

Usage:
    python3 scripts/bench.py [--backends a,b,...] [--kernels x,y,...]
                             [--evidence-dir DIR]

Each kernel returns a scalar the harness checks exactly before
recording any number: a benchmark of wrong code measures nothing.
Wall-clock time includes compiler work (the dominant term for small
kernels); `steps` is the backend-reported execution-step count and is
the stable comparator. See docs/BENCHMARKS.md.
"""

import argparse
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mncs_lib import ALL_BACKENDS, fj, run_experiment  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BENCH_REDUCE = os.path.join(ROOT, "benches", "bench_reduce.mncs")
BENCH_BUILD = os.path.join(ROOT, "benches", "bench_build.mncs")
MOD_REDUCE = "mncs.numerics.bench_reduce.v1"
MOD_BUILD = "mncs.numerics.bench_build.v1"

# kernel -> (source, module, expected_scalar, backends or None for all).
# Construction kernels once ran on a narrowed backend set (the P-001
# refusal envelope); P-001 is repaired, so every kernel runs
# everywhere. docs/BENCHMARKS.md keeps the historical baseline with
# the old envelope marked per cell.
KERNELS = {
    "bench_sum_256": (BENCH_REDUCE, MOD_REDUCE, 256.0, None),
    "bench_sum_1024": (BENCH_REDUCE, MOD_REDUCE, 1024.0, None),
    "bench_dot_256": (BENCH_REDUCE, MOD_REDUCE, 512.0, None),
    "bench_axpy_256": (BENCH_BUILD, MOD_BUILD, 1024.0, None),
    "bench_matvec_8": (BENCH_BUILD, MOD_BUILD, 64.0, None),
    "bench_matmul_8": (BENCH_BUILD, MOD_BUILD, 512.0, None),
}


def run_kernel(kernel, source, module, expected, backend):
    corpus = {"schema_version": "0.2", "name": "bench", "cases": [{
        "id": kernel,
        "request": {"schema_version": "0.1",
                    "target": {"module": module, "function": kernel},
                    "arguments": [], "step_budget": 1000000},
        "expected_status": "returned",
        "expected": [fj(expected)],
    }]}
    path = os.path.join("/tmp", "mncs-bench-%s.json" % kernel)
    with open(path, "w") as handle:
        json.dump(corpus, handle)
    start = time.monotonic()
    code, result, err = run_experiment(source, backend, path)
    wall = time.monotonic() - start
    if result is None or "cases" not in result or not result["cases"]:
        return {"kernel": kernel, "backend": backend, "ok": False,
                "wall_s": wall, "note": "no-cases-envelope"}
    item = result["cases"][0]
    ok = bool(item.get("expectation_met")) and item.get("status") == \
        "returned"
    return {"kernel": kernel, "backend": backend, "ok": ok,
            "wall_s": round(wall, 3),
            "steps": item.get("steps"),
            "status": item.get("status"),
            "reason": item.get("failure_reason")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backends", default=",".join(ALL_BACKENDS))
    parser.add_argument("--kernels", default=",".join(KERNELS))
    parser.add_argument("--evidence-dir",
                        default=os.path.join(ROOT, "target"))
    args = parser.parse_args()

    os.environ["MNCS_LIBRARY_PATH"] = SRC
    backends = [b for b in args.backends.split(",") if b]
    kernels = [k for k in args.kernels.split(",") if k]

    rows = []
    for kernel in kernels:
        source, module, expected, allowed = KERNELS[kernel]
        for backend in backends:
            if allowed is not None and backend not in allowed:
                continue
            row = run_kernel(kernel, source, module, expected, backend)
            rows.append(row)
            print("%-18s %-24s ok=%-5s wall=%7.3fs steps=%s %s" % (
                kernel, backend, row["ok"], row["wall_s"],
                row.get("steps"), row.get("reason") or ""))

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    path = os.path.join(args.evidence_dir, "bench-%s.json" % stamp)
    os.makedirs(args.evidence_dir, exist_ok=True)
    with open(path, "w") as handle:
        json.dump({"timestamp_utc": stamp, "rows": rows}, handle, indent=1)
    bad = [r for r in rows if not r["ok"]]
    print("kernels=%d failed=%d evidence=%s"
          % (len(rows), len(bad), path))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
