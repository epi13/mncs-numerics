"""Shared helpers for mncs-numerics corpora generation and test execution.

Stdlib only. All floating-point oracle values are exact IEEE-754 binary64
bit patterns produced by Python floats (which are binary64 on every
platform this harness runs on).
"""

import json
import os
import struct
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Backends in a stable display order.
ALL_BACKENDS = [
    "mncs-research-bytecode",
    "mncs-portable-wasm-mvp",
    "mncs-c11",
    "mncs-llvm-ir",
    "mncs-cranelift",
]


def fbits(x):
    """Bit pattern of a Python float as an unsigned 64-bit int."""
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def from_bits(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def fj(x):
    """Corpus value for an f64."""
    return {"float": {"bits": fbits(x), "type": {"bits": 64}}}


def ij(value, bits=64, signed=True):
    """Corpus value for an integer."""
    return {"integer": {"value": value, "type": {"bits": bits, "signed": signed}}}


def seq(values):
    """Corpus value for a sequence."""
    return {"sequence": {"values": values}}


def finite(module, type_name, variant, discriminant, payload=()):
    """Corpus value for a finite/enum value with optional payload."""
    return {
        "finite": {
            "type_identity": "mncs:0.2:finite-type:%s::%s" % (module, type_name),
            "variant_identity": "mncs:0.2:finite-variant:%s::%s::%s"
            % (module, type_name, variant),
            "discriminant": discriminant,
            "payload": [[name, value] for name, value in payload],
        }
    }


def boolean(value):
    """Corpus value for a bool."""
    return {"boolean": {"value": bool(value)}}


def record(module, type_name, field_types, values):
    """Corpus value for a record.

    field_types: [(name, semantic_type)] in any order, e.g.
    [("n", "i64"), ("r0", "f64")]. values: {name: encoded_value}.
    The type_identity carries the canonical sorted field digest, which
    the backend comparison requires to match exactly.
    """
    import urllib.parse

    joined = "".join("%s:%s;" % (n, t) for n, t in sorted(field_types))
    digest = urllib.parse.quote(joined, safe="")
    return {
        "record": {
            "type_identity": "mncs:0.2:record-type:%s::%s::%s"
            % (module, type_name, digest),
            "name": type_name,
            "fields": [[name, values[name]] for name, _ in sorted(field_types)],
        }
    }


def targs(*nats):
    """type_arguments for a generic instantiation, e.g. targs(4)."""
    return [{"kind": "nat", "value": n} for n in nats]


def case(case_id, module, function, args, expected=None,
         expected_status="returned", step_budget=4096, type_args=None):
    """One corpus case. Trap cases pass expected=None."""
    c = {
        "id": case_id,
        "request": {
            "schema_version": "0.1",
            "target": {"module": module, "function": function},
            "arguments": args,
            "step_budget": step_budget,
        },
        "expected_status": expected_status,
    }
    if type_args is not None:
        c["request"]["type_arguments"] = type_args
    if expected is not None:
        c["expected"] = expected
    return c


def write_corpus(path, name, cases):
    with open(path, "w") as handle:
        json.dump(
            {"schema_version": "0.2", "name": name, "cases": cases},
            handle,
            indent=1,
        )
        handle.write("\n")


def resolve_mncs_bin():
    """Locate the mncs-language CLI binary.

    Prefers an explicit MNCS_BIN, then a sibling ../mncs-language checkout,
    then MNCS_LANGUAGE_DIR.
    """
    direct = os.environ.get("MNCS_BIN")
    if direct and os.path.isfile(direct):
        return [direct]
    lang_dir = os.environ.get("MNCS_LANGUAGE_DIR")
    if not lang_dir:
        lang_dir = os.path.join(os.path.dirname(REPO_ROOT), "mncs-language")
    candidate = os.path.join(lang_dir, "target", "debug", "mncs")
    if os.path.isfile(candidate):
        return [candidate]
    # Fall back to cargo run inside the language checkout.
    return ["cargo", "run", "-q", "-p", "mncs-cli", "--"]


def run_experiment(source, backend, corpus_path, out_path=None, lang_dir=None):
    """Run one experiment; return the parsed result JSON."""
    cmd = resolve_mncs_bin() + [
        "experiment", "run", source,
        "--backend", backend,
        "--corpus", corpus_path,
    ]
    if lang_dir is None:
        lang_dir = os.environ.get("MNCS_LANGUAGE_DIR")
        if not lang_dir:
            lang_dir = os.path.join(os.path.dirname(REPO_ROOT), "mncs-language")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=lang_dir)
    if out_path is not None:
        with open(out_path, "w") as handle:
            handle.write(proc.stdout)
    try:
        return proc.returncode, json.loads(proc.stdout), proc.stderr
    except json.JSONDecodeError:
        return proc.returncode, None, proc.stdout[-2000:] + proc.stderr[-2000:]


def check_result(result):
    """Split an experiment result into (met, failed, error) case lists.

    Mirrors the language's own suite semantics: a trap case carries no
    `expected` value, so its contract is the trap status itself
    (status == runtime_failure and status_met); a valued case needs
    both expectation_met and status_met.
    """
    met, failed, errors = [], [], []
    if result is None or "cases" not in result:
        return met, failed, [("<run>", "no-cases-envelope")]
    for item in result["cases"]:
        case_id = item.get("case_id")
        status = item.get("status")
        status_met = item.get("status_met")
        status_ok = status_met is True or status_met is None
        expected = item.get("expected")
        if expected is None:
            if status == "runtime_failure" and status_ok:
                met.append(case_id)
            elif status in ("unsupported",):
                errors.append((case_id, "unsupported: %s"
                               % item.get("failure_reason")))
            else:
                failed.append((case_id,
                               "%s status_met=%s reason=%s returned=%s" % (
                                   status, status_met,
                                   item.get("failure_reason"),
                                   json.dumps(item.get("returned"))[:160])))
        elif item.get("expectation_met") and status_ok:
            met.append(case_id)
        elif status in ("unsupported",):
            errors.append((case_id, "unsupported: %s"
                           % item.get("failure_reason")))
        else:
            failed.append((case_id,
                           "%s met=%s status_met=%s reason=%s returned=%s" % (
                               status, item.get("expectation_met"),
                               status_met, item.get("failure_reason"),
                               json.dumps(item.get("returned"))[:160])))
    return met, failed, errors
