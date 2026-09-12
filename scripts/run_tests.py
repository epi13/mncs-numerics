#!/usr/bin/env python3
"""Execute mncs-numerics corpora across backends and report.

Usage:
    python3 scripts/run_tests.py [--backends a,b,...] [--suites x,y,...]
                                 [--evidence-dir DIR] [--list]

A case counts as PASS when expectation and status both meet. A case the
backend refuses (unsupported entrypoint, lowering refusal, or a compile
failure the pressure ledger already pins) counts as CONFIRMED when it
matches SUITES expected_refusals, otherwise FAIL. Real value mismatches
always FAIL: tolerances are never broadened to make green.

Exit code is 0 unless some case FAILs.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mncs_lib import ALL_BACKENDS, check_result, run_experiment  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
CORPORA = os.path.join(ROOT, "tests", "corpora")
DRIVERS = os.path.join(ROOT, "tests", "drivers")

NATIVE_ONLY_REFUSAL = (
    "float-replace construction: refused on WASM (CGN302), miscompiled "
    "on LLVM (P-001)"
)

SUITES = [
    {"name": "scalar_int",
     "source": os.path.join(SRC, "numerics", "scalar_int.mncs"),
     "corpus": os.path.join(CORPORA, "scalar_int.json"),
     "backends": ALL_BACKENDS},
    {"name": "scalar_float",
     "source": os.path.join(SRC, "numerics", "scalar_float.mncs"),
     "corpus": os.path.join(CORPORA, "scalar_float.json"),
     "backends": ALL_BACKENDS},
    {"name": "vec_int",
     "source": os.path.join(SRC, "numerics", "vec_int.mncs"),
     "corpus": os.path.join(CORPORA, "vec_int.json"),
     "backends": ALL_BACKENDS},
    {"name": "vec_float_reduce",
     "source": os.path.join(SRC, "numerics", "vec_float_reduce.mncs"),
     "corpus": os.path.join(CORPORA, "vec_float_reduce.json"),
     "backends": ALL_BACKENDS},
    {"name": "vec_float_build",
     "source": os.path.join(SRC, "numerics", "vec_float_build.mncs"),
     "corpus": os.path.join(CORPORA, "vec_float_build.json"),
     "backends": ["mncs-research-bytecode", "mncs-c11", "mncs-cranelift"],
     "expected_refusals": [
         ("mncs-portable-wasm-mvp", "", "P-001", NATIVE_ONLY_REFUSAL),
         ("mncs-llvm-ir", "", "P-001", NATIVE_ONLY_REFUSAL),
     ]},
    {"name": "mat_float_small",
     "source": os.path.join(SRC, "numerics", "mat_float_small.mncs"),
     "corpus": os.path.join(CORPORA, "mat_float_small.json"),
     "backends": ALL_BACKENDS},
    {"name": "mat_float_drivers",
     "source": os.path.join(DRIVERS, "mat_float_drivers.mncs"),
     "corpus": os.path.join(CORPORA, "mat_float_drivers.json"),
     "backends": ALL_BACKENDS},
    {"name": "mat_float_build_drivers",
     "source": os.path.join(DRIVERS, "mat_float_build_drivers.mncs"),
     "corpus": os.path.join(CORPORA, "mat_float_build_drivers.json"),
     "backends": ["mncs-research-bytecode", "mncs-c11", "mncs-cranelift"],
     "expected_refusals": [
         ("mncs-portable-wasm-mvp", "", "P-001", NATIVE_ONLY_REFUSAL),
         ("mncs-llvm-ir", "", "P-001", NATIVE_ONLY_REFUSAL),
     ]},
    {"name": "examples_stats",
     "source": os.path.join(ROOT, "examples", "stats.mncs"),
     "corpus": os.path.join(CORPORA, "examples_stats.json"),
     "backends": ALL_BACKENDS},
    {"name": "examples_trapezoid",
     "source": os.path.join(ROOT, "examples", "trapezoid.mncs"),
     "corpus": os.path.join(CORPORA, "examples_trapezoid.json"),
     "backends": ALL_BACKENDS},
    {"name": "examples_solve_demo",
     "source": os.path.join(ROOT, "examples", "solve_demo.mncs"),
     "corpus": os.path.join(CORPORA, "examples_solve_demo.json"),
     "backends": ALL_BACKENDS},
    {"name": "examples_logistic",
     "source": os.path.join(ROOT, "examples", "logistic.mncs"),
     "corpus": os.path.join(CORPORA, "examples_logistic.json"),
     "backends": ALL_BACKENDS},
    {"name": "props_reduce",
     "source": os.path.join(DRIVERS, "prop_drivers_reduce.mncs"),
     "corpus": os.path.join(CORPORA, "props_reduce.json"),
     "backends": ALL_BACKENDS},
    {"name": "props_build",
     "source": os.path.join(DRIVERS, "prop_drivers_build.mncs"),
     "corpus": os.path.join(CORPORA, "props_build.json"),
     "backends": ["mncs-research-bytecode", "mncs-c11", "mncs-cranelift"],
     "expected_refusals": [
         ("mncs-portable-wasm-mvp", "", "P-001", NATIVE_ONLY_REFUSAL),
         ("mncs-llvm-ir", "", "P-001", NATIVE_ONLY_REFUSAL),
     ]},
]


def git_rev(path):
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=path).stdout.strip()
    except OSError:
        return "unknown"


def refusal_expected(suite, backend, case_id, reason):
    for exp_backend, substr, pressure, _note in suite.get(
            "expected_refusals", []):
        if exp_backend == backend and substr in (case_id or ""):
            return pressure
    # Backend-wide entries use "" as the substring: any refused case on
    # that backend is covered.
    return None


def run_suite(suite, backends, evidence_cases):
    summary = {"suite": suite["name"], "backends": {}}
    # Refusal-pinned backends run too: a confirmed refusal is evidence,
    # and a backend that starts passing must show up as unlisted-pass.
    runnable = list(suite["backends"]) + [
        exp_backend for exp_backend, _s, _p, _n in suite.get(
            "expected_refusals", [])]
    for backend in backends:
        if backend not in runnable:
            continue
        _code, result, _err = run_experiment(
            suite["source"], backend, suite["corpus"])
        met, failed, errors = check_result(result)
        confirmed, still_failed = [], []
        for item in failed + [(c, r) for c, r in errors]:
            case_id, reason = item
            pressure = refusal_expected(suite, backend, case_id, reason)
            # A refused-looking outcome (unsupported status, refusal or
            # lowering diagnostics, missing specialization) that the
            # ledger pins is a confirmed refusal, not a pass.
            refused = any(key in (reason or "").lower() for key in (
                "unsupported", "refus", "not realized", "no compiled",
                "compiler failure", "no-cases-envelope", "outside the",
                "not supported"))
            if pressure and refused:
                confirmed.append({"case": case_id, "pressure": pressure,
                                  "reason": reason})
            else:
                still_failed.append({"case": case_id, "reason": reason})
        summary["backends"][backend] = {
            "passed": len(met),
            "confirmed_refusals": len(confirmed),
            "failed": still_failed,
        }
        for entry in confirmed:
            evidence_cases.append({"suite": suite["name"],
                                   "backend": backend,
                                   "outcome": "confirmed_refusal", **entry})
        for entry in still_failed:
            evidence_cases.append({"suite": suite["name"],
                                   "backend": backend,
                                   "outcome": "failed", **entry})
        surprise = (backend not in suite["backends"] and len(met) > 0)
        print("%-28s %-24s pass=%-4d confirmed=%-3d failed=%-3d%s" % (
            suite["name"], backend, len(met), len(confirmed),
            len(still_failed),
            "  <-- UNEXPECTED-PASS, pressure may be fixed" if surprise
            else ""))
        for entry in still_failed:
            print("    FAIL %-32s %s" % (entry["case"], entry["reason"]))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backends", default=",".join(ALL_BACKENDS))
    parser.add_argument("--suites", default="")
    parser.add_argument("--evidence-dir",
                        default=os.path.join(ROOT, "target"))
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        for suite in SUITES:
            print(suite["name"], "->", ", ".join(suite["backends"]))
        return 0

    backends = [b for b in args.backends.split(",") if b]
    wanted = set(args.suites.split(",")) if args.suites else None

    os.environ["MNCS_LIBRARY_PATH"] = SRC
    evidence_cases = []
    summaries = []
    for suite in SUITES:
        if wanted and suite["name"] not in wanted:
            continue
        summaries.append(run_suite(suite, backends, evidence_cases))

    failed = [e for e in evidence_cases if e["outcome"] == "failed"]
    evidence = {
        "timestamp_utc": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "mncs_numerics_rev": git_rev(ROOT),
        "suites": summaries,
        "failed": failed,
        "confirmed_refusals": [e for e in evidence_cases
                               if e["outcome"] == "confirmed_refusal"],
    }
    os.makedirs(args.evidence_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    path = os.path.join(args.evidence_dir, "evidence-%s.json" % stamp)
    with open(path, "w") as handle:
        json.dump(evidence, handle, indent=1)
    n_pass = sum(b["passed"] for s in summaries for b in s["backends"].values())
    n_conf = sum(b["confirmed_refusals"] for s in summaries
                 for b in s["backends"].values())
    print("passed=%d confirmed_refusals=%d failed=%d evidence=%s"
          % (n_pass, n_conf, len(failed), path))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
