#!/usr/bin/env python3
"""Run mncs-numerics native contract suites through `mncs test`.

Usage:
    python3 scripts/run_native_tests.py [--suites int,float] [--evidence-dir DIR]

Each suite is a Profile 0.18 test module under tests/native/ that exercises
the 0.16 numerics library through the canonical mncs-test entrypoint
(`mncs test`), using the compiler-owned declaration inventory directly.
There is no corpus, no oracle, and no host-side expectation table here:
every expectation is an in-language assertion, and the result envelope
carries stable test-case identities, inventory identity, and run identity.

Division of labor with scripts/run_tests.py: the corpus harness remains
the authority for cross-backend bit-exactness (five backends) and for
every trapping behavior (`expected_status: runtime_failure`), which a
`test` declaration cannot express. This runner is the authority for
in-language contracts: boundary values, outcome enums, conversion
rules, operator semantics, and deterministic generative properties.

Exit code is 0 unless some suite fails to verify.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mncs_lib import resolve_mncs_bin  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NATIVE = os.path.join(ROOT, "tests", "native")

SUITES = [
    {"name": "contract_int", "source": os.path.join(NATIVE, "contract_int.mncs")},
    {"name": "contract_float", "source": os.path.join(NATIVE, "contract_float.mncs")},
]


def library_path():
    roots = [
        os.path.join(ROOT, "src"),
        os.path.join(os.path.dirname(ROOT), "mncs-test", "native"),
        lang_library(),
    ]
    return ":".join(roots)


def lang_library():
    lang_dir = os.environ.get("MNCS_LANGUAGE_DIR")
    if not lang_dir:
        lang_dir = os.path.join(os.path.dirname(ROOT), "mncs-language")
    return os.path.join(lang_dir, "library")


def git_rev(path):
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=path).stdout.strip()
    except OSError:
        return "unknown"


def run_suite(suite):
    cmd = resolve_mncs_bin() + ["test", suite["source"], "--format", "json"]
    env = dict(os.environ)
    env["MNCS_LIBRARY_PATH"] = library_path()
    lang_dir = os.environ.get("MNCS_LANGUAGE_DIR")
    if not lang_dir:
        lang_dir = os.path.join(os.path.dirname(ROOT), "mncs-language")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=lang_dir, env=env)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"suite": suite["name"], "status": "ERROR",
                "detail": (proc.stdout[-1500:] + proc.stderr[-1500:])}
    summary = result.get("summary") or {}
    verdict = summary.get("verdict", result.get("classification", "unknown"))
    return {"suite": suite["name"], "status": verdict,
            "passed": summary.get("passed"), "failed": summary.get("failed"),
            "total": summary.get("total"),
            "run_id": result.get("run_id"),
            "test_identities": (result.get("selection") or {}).get(
                "selected_test_identities", [])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suites", default=",".join(s["name"] for s in SUITES))
    parser.add_argument("--evidence-dir", default=None)
    args = parser.parse_args()

    wanted = set(args.suites.split(","))
    outcomes = [run_suite(s) for s in SUITES if s["name"] in wanted]

    failed = [o for o in outcomes if o["status"] != "PASS"]
    for outcome in outcomes:
        print("%-16s %-6s passed=%s failed=%s total=%s run=%s" % (
            outcome["suite"], outcome["status"], outcome.get("passed"),
            outcome.get("failed"), outcome.get("total"),
            (outcome.get("run_id") or "-")[:8]))

    evidence = {
        "schema_version": "mncs-numerics.native-evidence/1",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "numerics_rev": git_rev(ROOT),
        "language_rev": git_rev(os.path.join(os.path.dirname(ROOT), "mncs-language")),
        "test_rev": git_rev(os.path.join(os.path.dirname(ROOT), "mncs-test")),
        "suites": outcomes,
    }
    evidence_dir = args.evidence_dir or os.path.join(ROOT, "target")
    os.makedirs(evidence_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(evidence_dir, "native-evidence-%s.json" % stamp)
    with open(path, "w") as handle:
        json.dump(evidence, handle, indent=1)
        handle.write("\n")
    print("evidence=%s" % path)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
