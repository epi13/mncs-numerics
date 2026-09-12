#!/usr/bin/env python3
"""Deterministic oracle for mncs-numerics execution corpora.

Generates tests/corpora/*.json from independent Python reference
computations. Run from the repository root:

    python3 scripts/gen_corpora.py

Rules:
- Integer expectations are exact Python ints (asserted in-range).
- Float expectations are exact IEEE-754 bit patterns. Python floats
  are binary64, and MNCS + - * / evaluate per IEEE-754 in program
  order, so mirroring the MNCS operation order in the oracle pins the
  exact bits. The oracle never imports MNCS output: every value is
  recomputed here, and algorithmic choices (Newton iteration count,
  stable quadratic form, Neumaier compensation) are mirrored
  step-for-step AND validated against closed forms (math.sqrt, residual
  checks) so a shared transcription bug cannot hide behind agreement.
- Trap cases carry no `expected` value, only
  `"expected_status": "runtime_failure"`.
- Committed corpora must match generator output byte-for-byte; the
  runner never edits them.

Single-parameter generics are named directly from the corpus with
`type_arguments`. Multi-parameter instantiations go through the
in-language drivers in tests/drivers (pressure P-002).
"""

import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mncs_lib import (  # noqa: E402
    boolean,
    case,
    fbits,
    finite,
    fj,
    ij,
    record,
    seq,
    targs,
    write_corpus,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "corpora")

I64_MIN = -(2 ** 63)
I64_MAX = 2 ** 63 - 1
I32_MIN = -(2 ** 31)
I32_MAX = 2 ** 31 - 1
U64_MAX = 2 ** 64 - 1


def sq(*xs):
    """Sequence of f64 lanes."""
    return seq([fj(x) for x in xs])


def si(*xs):
    """Sequence of i64 lanes."""
    return seq([ij(x) for x in xs])


def nest(*rows):
    """Nested float matrix: each row is a tuple of Python floats."""
    return seq([sq(*row) for row in rows])


# ---------------------------------------------------------------------------
# Float oracle mirrors: same operations, same order as the .mncs sources.
# ---------------------------------------------------------------------------

def o_fmin(a, b):
    return a if a <= b else b


def o_fmax(a, b):
    return a if a >= b else b


def o_fclamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def o_fsign(x):
    if x < 0.0:
        return -1.0
    if x > 0.0:
        return 1.0
    return 0.0


def o_trunc(x):
    assert abs(x) < 2.0 ** 63, "oracle: out of trunc domain"
    return float(math.trunc(x))


def o_floor(x):
    t = o_trunc(x)
    got = t - 1.0 if t > x else t
    assert got == math.floor(x), (x, got)
    return got


def o_ceil(x):
    t = o_trunc(x)
    got = t + 1.0 if t < x else t
    assert got == math.ceil(x), (x, got)
    return got


def o_round_half_away(x):
    if x >= 0.0:
        return o_floor(x + 0.5)
    return o_ceil(x - 0.5)


def o_newton_sqrt(x):
    """Mirror of sqrt_newton: bucketed start, 32 Newton steps."""
    assert x >= 0.0
    if x == 0.0:
        return 0.0
    guess = x if x > 1.0 else 1.0
    start = 1000000000000.0 if guess > 1000000000000.0 else guess
    y = start
    for _ in range(32):
        y = 0.5 * (y + x / y)
    return y


def check_sqrt_domain(cases):
    """Every sqrt oracle value must be within 1e-12 relative of math."""
    for x, _ in cases:
        if x == 0.0:
            continue
        got = o_newton_sqrt(x)
        ref = math.sqrt(x)
        assert abs(got - ref) / ref < 1e-12, (x, got, ref)


def o_quadratic(a, b, c):
    """Mirror of quadratic: (n, r0, r1) with ascending roots."""
    if a == 0.0:
        if b == 0.0:
            return (-1, 0.0, 0.0)
        return (1, (0.0 - c) / b, 0.0)
    disc = b * b - 4.0 * a * c
    assert math.isfinite(disc), "oracle: discriminant overflow"
    if disc < 0.0:
        return (0, 0.0, 0.0)
    if disc == 0.0:
        return (1, (0.0 - b) / (2.0 * a), 0.0)
    s = o_newton_sqrt(disc)
    sb = -1.0 if b < 0.0 else 1.0
    q = (0.0 - 0.5) * (b + sb * s)
    r0 = q / a
    r1 = c / q
    return (2, o_fmin(r0, r1), o_fmax(r0, r1))


def check_quadratic(a, b, c):
    n, r0, r1 = o_quadratic(a, b, c)
    if n == 2:
        for r in (r0, r1):
            resid = abs(a * r * r + b * r + c)
            scale = abs(a * r * r) + abs(b * r) + abs(c)
            assert resid <= 1e-9 * scale + 1e-300, (a, b, c, r, resid)
        assert r0 <= r1
    return (n, r0, r1)


def o_neumaier(xs):
    """Mirror of neumaier_sum."""
    total, comp = 0.0, 0.0
    for x in xs:
        t = total + x
        sa = -total if total < 0.0 else total
        xa = -x if x < 0.0 else x
        c = (total - t) + x if sa >= xa else (x - t) + total
        total, comp = t, comp + c
    return total + comp


def o_sum(xs):
    """Naive left-to-right sum: mirrors the MNCS kernels exactly.

    NOTE: never use builtin sum() here: since Python 3.12 it
    compensates internally and would hide the very cancellation the
    plain-sum kernels exhibit.
    """
    acc = 0.0
    for x in xs:
        acc = acc + x
    return acc


def o_variance(xs):
    m = o_sum(xs) / len(xs)
    return o_sum([(x - m) * (x - m) for x in xs]) / len(xs)


# ---------------------------------------------------------------------------
# scalar_int
# ---------------------------------------------------------------------------

def gen_scalar_int():
    mod = "mncs.numerics.scalar_int.v1"
    c = []

    def sc(fn, args, exp):
        c.append(case("i-" + fn + "-" + str(len(c)), mod, fn, args, exp))

    # abs_checked: exact on everything but MIN, which traps.
    for x in (0, 1, -1, 5, -5, 123456789, I64_MAX, I64_MIN + 1):
        sc("abs_checked", [ij(x)], [ij(abs(x))])
    c.append(case("i-abs_checked-min-trap", mod, "abs_checked",
                  [ij(I64_MIN)], expected_status="runtime_failure"))
    # abs_wrap: MIN wraps to itself.
    for x in (0, 7, -7, I64_MAX, I64_MIN):
        sc("abs_wrap", [ij(x)], [ij(abs(x) if x != I64_MIN else I64_MIN)])
    # abs_sat: MIN saturates to MAX.
    for x in (0, 7, -7, I64_MAX, I64_MIN + 1, I64_MIN):
        sc("abs_sat", [ij(x)],
           [ij(abs(x) if x != I64_MIN else I64_MAX)])
    # min/max/clamp incl. extremes and equal inputs.
    triples = [(3, 7), (7, 3), (-5, -5), (I64_MIN, I64_MAX),
               (I64_MAX, I64_MIN), (0, 0)]
    for a, b in triples:
        sc("min_i64", [ij(a), ij(b)], [ij(min(a, b))])
        sc("max_i64", [ij(a), ij(b)], [ij(max(a, b))])
    clamps = [(5, 0, 10), (-3, 0, 10), (30, 0, 10), (0, 0, 10),
              (10, 0, 10), (I64_MIN, I64_MIN, I64_MAX),
              (I64_MAX, I64_MIN, I64_MAX)]
    for v, lo, hi in clamps:
        sc("clamp_i64", [ij(v), ij(lo), ij(hi)], [ij(min(max(v, lo), hi))])
    for x in (-9, 0, 9, I64_MIN, I64_MAX):
        sc("sign_i64", [ij(x)], [ij((x > 0) - (x < 0))])
    # pow_checked: exact powers, 0^0 == 1, overflow traps, exp bound.
    pows = [(2, 0), (2, 10), (3, 5), (-2, 3), (-2, 4), (10, 0),
            (0, 0), (0, 5), (5, 1), (2, 62), (1, 64), (-1, 64)]
    for base, exp in pows:
        sc("pow_checked", [ij(base), ij(exp, 64, False)],
           [finite(mod, "PowOutcome", "Value", 0,
                   [("value", ij(pow(base, exp)))])])
    c.append(case("i-pow_checked-overflow-trap", mod, "pow_checked",
                  [ij(2), ij(63, 64, False)],
                  expected_status="runtime_failure"))
    c.append(case("i-pow_checked-exp-too-large", mod, "pow_checked",
                  [ij(2), ij(65, 64, False)],
                  [finite(mod, "PowOutcome", "ExpTooLarge", 1)]))
    # gcd incl. zeros and larger pairs.
    for x, y in ((48, 18), (18, 48), (0, 5), (5, 0), (0, 0),
                 (1071, 462), (13, 13), (100, 75), (17, 5)):
        sc("gcd", [ij(x), ij(y)], [ij(math.gcd(x, y))])
    # i32 + u64 extrema.
    for x in (0, 1, -1, I32_MAX, I32_MIN + 1):
        sc("abs_checked_i32", [ij(x, 32, True)], [ij(abs(x), 32, True)])
    c.append(case("i-abs_checked_i32-min-trap", mod, "abs_checked_i32",
                  [ij(I32_MIN, 32, True)],
                  expected_status="runtime_failure"))
    for a, b in ((3, 7), (7, 3), (I32_MIN, I32_MAX)):
        sc("min_i32", [ij(a, 32, True), ij(b, 32, True)],
           [ij(min(a, b), 32, True)])
        sc("max_i32", [ij(a, 32, True), ij(b, 32, True)],
           [ij(max(a, b), 32, True)])
    sc("clamp_i32", [ij(99, 32, True), ij(0, 32, True), ij(10, 32, True)],
       [ij(10, 32, True)])
    umax = U64_MAX
    for a, b in ((3, 7), (7, 3), (0, umax), (umax, umax)):
        sc("min_u64", [ij(a, 64, False), ij(b, 64, False)],
           [ij(min(a, b), 64, False)])
        sc("max_u64", [ij(a, 64, False), ij(b, 64, False)],
           [ij(max(a, b), 64, False)])
    sc("clamp_u64",
       [ij(umax, 64, False), ij(0, 64, False), ij(100, 64, False)],
       [ij(100, 64, False)])

    write_corpus(os.path.join(OUT, "scalar_int.json"),
                 "mncs-numerics-scalar-int", c)
    return c


# ---------------------------------------------------------------------------
# scalar_float
# ---------------------------------------------------------------------------

def gen_scalar_float():
    mod = "mncs.numerics.scalar_float.v1"
    c = []

    def sc(name, fn, args, exp, status="returned", budget=4096):
        c.append(case("f-%s-%s-%d" % (fn, name, len(c)), mod, fn, args,
                      exp, expected_status=status, step_budget=budget))

    # fabs / fneg incl. signed zeros.
    for x in (0.0, -0.0, 3.5, -3.5, 1e300, -1e300, 5e-324):
        sc("v", "fabs", [fj(x)], [fj(abs(x))])
        # fneg mirrors 0.0 - x exactly (NOT unary minus): +0.0 stays
        # +0.0 instead of becoming -0.0 (pressure P-007). In IEEE,
        # 0.0 - 0.0 == +0.0 while -(+0.0) == -0.0; the language offers
        # no exact negation, so the deviation is pinned, not hidden.
        sc("v", "fneg", [fj(x)], [fj(0.0 - x)])
    # fmin/fmax mirror the branch (NaN-free inputs; NaN traps).
    for a, b in ((3.0, 7.0), (7.0, 3.0), (-0.0, 0.0), (0.0, -0.0),
                 (-2.5, -2.5), (1e300, 1e-300)):
        sc("v", "fmin", [fj(a), fj(b)], [fj(o_fmin(a, b))])
        sc("v", "fmax", [fj(a), fj(b)], [fj(o_fmax(a, b))])
    # NaN input traps on the comparison (fail-closed, by design).
    nan = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000001))[0]
    nan_args = {"fabs": [fj(nan)], "fmin": [fj(nan), fj(1.0)],
                "fmax": [fj(nan), fj(1.0)],
                "fclamp": [fj(nan), fj(0.0), fj(1.0)],
                "fsign": [fj(nan)]}
    for fn, args in nan_args.items():
        sc("nan-trap", fn, args, None, status="runtime_failure")
    # Infinity traps as well.
    inf = float("inf")
    sc("inf-trap", "fabs", [fj(inf)], None, status="runtime_failure")
    sc("inf-trap", "fmin", [fj(inf), fj(1.0)], None,
       status="runtime_failure")
    # fclamp incl. edges.
    for v, lo, hi in ((0.5, 0.0, 1.0), (-1.0, 0.0, 1.0), (2.0, 0.0, 1.0),
                      (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (-0.0, 0.0, 1.0)):
        sc("v", "fclamp", [fj(v), fj(lo), fj(hi)],
           [fj(o_fclamp(v, lo, hi))])
    # fsign incl. both zeros.
    for x in (-2.5, -0.0, 0.0, 2.5):
        sc("v", "fsign", [fj(x)], [fj(o_fsign(x))])
    # approx_abs / approx_rel / approx.
    sc("t", "approx_abs", [fj(1.0), fj(1.05), fj(0.1)],
       [boolean(True)])
    sc("f", "approx_abs", [fj(1.0), fj(1.2), fj(0.1)],
       [boolean(False)])
    sc("zero-tol", "approx_abs", [fj(1.0), fj(1.0), fj(0.0)],
       [boolean(True)])
    sc("neg-tol", "approx_abs", [fj(1.0), fj(1.0), fj(-1.0)],
       [boolean(False)])
    sc("t", "approx_rel", [fj(100.0), fj(101.0), fj(0.05)],
       [boolean(True)])
    sc("f", "approx_rel", [fj(100.0), fj(110.0), fj(0.05)],
       [boolean(False)])
    sc("near-zero", "approx", [fj(0.0), fj(1e-9), fj(1e-8), fj(1e-6)],
       [boolean(True)])
    sc("far", "approx", [fj(1.0), fj(2.0), fj(1e-9), fj(1e-9)],
       [boolean(False)])
    sc("rel", "approx", [fj(1000.0), fj(1001.0), fj(1e-9), fj(0.01)],
       [boolean(True)])
    # safe_div: quotient or explicit refusal (0/0 refuses, never traps).
    for n, d in ((7.0, 2.0), (-7.0, 2.0), (0.0, 5.0), (1.0, 0.0),
                 (0.0, 0.0), (-0.0, 0.0)):
        if d == 0.0:
            sc("refuse", "safe_div", [fj(n), fj(d)],
               [finite(mod, "FDiv", "DivByZero", 1)])
        else:
            sc("v", "safe_div", [fj(n), fj(d)],
               [finite(mod, "FDiv", "Value", 0,
                       [("value", fj(n / d))])])
    # trunc/floor/ceil/frac/round incl. negatives and integral values.
    for x in (3.7, -3.7, 3.0, -3.0, 0.7, -0.7, 2.5, -2.5,
              123456789.123, -123456789.987, 1e15 + 0.7):
        sc("v", "ftrunc", [fj(x)], [fj(o_trunc(x))])
        sc("v", "ffloor", [fj(x)], [fj(o_floor(x))])
        sc("v", "fceil", [fj(x)], [fj(o_ceil(x))])
        sc("v", "ffrac", [fj(x)], [fj(x - o_trunc(x))])
        sc("v", "fround", [fj(x)], [fj(o_round_half_away(x))])
    # Out-of-domain conversion traps in the cast.
    sc("toobig", "ftrunc", [fj(1e19)], None, status="runtime_failure")
    sc("toosmall", "ftrunc", [fj(-1e19)], None, status="runtime_failure")
    sc("toobig", "ffloor", [fj(1e19)], None, status="runtime_failure")
    # pow_int incl. 0^0, negative base, overflow trap, exp bound.
    for base, exp in ((2.0, 10), (1.5, 2), (-2.0, 3), (0.0, 0),
                      (5.0, 0), (1.0, 1024), (1.5, 100)):
        sc("v", "pow_int", [fj(base), ij(exp, 64, False)],
           [finite(mod, "FPow", "Value", 0,
                   [("value", fj(base ** exp))])],
           budget=131072)
    # 2.0^1024 overflows to infinity, so the trap rule fires.
    sc("overflow", "pow_int", [fj(2.0), ij(1024, 64, False)], None,
       status="runtime_failure", budget=131072)
    sc("overflow", "pow_int", [fj(10.0), ij(309, 64, False)], None,
       status="runtime_failure", budget=131072)
    sc("exp-too-large", "pow_int", [fj(2.0), ij(1025, 64, False)],
       [finite(mod, "FPow", "ExpTooLarge", 1)], budget=131072)
    # sqrt_newton incl. domain edges; oracle quality pre-checked.
    sqrt_inputs = [0.0, 1.0, 2.0, 0.25, 0.5, 100.0, 1e-6, 1e-12,
                   1e12, 1e24, 123456789.0, 2.25]
    check_sqrt_domain([(x, None) for x in sqrt_inputs if x >= 1e-12
                       and x <= 1e24 and x != 0.0])
    for x in sqrt_inputs:
        sc("v", "sqrt_newton", [fj(x)],
           [finite(mod, "FSqrt", "Value", 0,
                   [("value", fj(o_newton_sqrt(x)))])],
           budget=16384)
    sc("neg", "sqrt_newton", [fj(-1.0)],
       [finite(mod, "FSqrt", "DomainError", 1)])
    sc("negzero-ok", "sqrt_newton", [fj(-0.0)],
       [finite(mod, "FSqrt", "Value", 0, [("value", fj(0.0))])])
    sc("v", "sqrt_value", [fj(2.0)],
       [fj(o_newton_sqrt(2.0))])
    sc("neg-trap", "sqrt_value", [fj(-4.0)], None,
       status="runtime_failure")
    # quadratic incl. the cancellation showcase x^2 - 1e8 x + 1.
    quads = [(1.0, -5.0, 6.0), (1.0, 0.0, 1.0), (1.0, -4.0, 4.0),
             (1.0, 0.0, -4.0), (1.0, -100000000.0, 1.0),
             (0.0, 2.0, -4.0), (0.0, 0.0, 1.0), (2.0, -7.0, 3.0)]
    for a, b, c_ in quads:
        n, r0, r1 = check_quadratic(a, b, c_)
        sc("v", "quadratic", [fj(a), fj(b), fj(c_)],
           [record(mod, "QuadRoots",
                   [("n", "i64"), ("r0", "f64"), ("r1", "f64")],
                   {"n": ij(n), "r0": fj(r0), "r1": fj(r1)})],
           budget=16384)

    write_corpus(os.path.join(OUT, "scalar_float.json"),
                 "mncs-numerics-scalar-float", c)
    return c


# ---------------------------------------------------------------------------
# vec_int
# ---------------------------------------------------------------------------

def gen_vec_int():
    mod = "mncs.numerics.vec_int.v1"
    c = []

    def sc(fn, n, args, exp, status="returned", budget=8192):
        c.append(case("v-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      expected_status=status, step_budget=budget,
                      type_args=targs(n)))

    a4 = si(1, 2, 3, 4)
    b4 = si(5, 6, 7, 8)
    sc("sum_checked", 4, [a4], [ij(10)])
    sc("sum_wrap", 4, [a4], [ij(10)])
    sc("dot_wrap", 4, [a4, b4],
       [ij(1 * 5 + 2 * 6 + 3 * 7 + 4 * 8)])
    sc("dot_checked", 4, [a4, b4],
       [ij(1 * 5 + 2 * 6 + 3 * 7 + 4 * 8)])
    sc("min", 4, [si(9, -2, 4, 0)], [ij(-2)])
    sc("max", 4, [si(9, -2, 4, 0)], [ij(9)])
    sc("mean_checked", 4, [a4], [ij(2)])  # 10/4 truncates toward zero
    sc("mean_checked", 4, [si(-1, -2, -3, -4)], [ij(-2)])  # -10/4 = -2
    sc("dist2_wrap", 4, [a4, b4], [ij(4 * 16)])
    sc("l1_wrap", 4, [si(-3, 0, 4, -1)], [ij(8)])
    sc("count_eq", 4, [si(5, 1, 5, 2), ij(5)], [ij(2)])
    sc("all_nonneg", 4, [a4], [boolean(True)])
    sc("all_nonneg", 4, [si(1, -1, 2, 3)], [boolean(False)])
    sc("any_zero", 4, [a4], [boolean(False)])
    sc("any_zero", 4, [si(1, 0, 2, 3)], [boolean(True)])
    # One-lane windows.
    sc("sum_checked", 1, [si(42)], [ij(42)])
    sc("min", 1, [si(-7)], [ij(-7)])
    sc("mean_checked", 1, [si(-7)], [ij(-7)])
    sc("dot_wrap", 1, [si(6), si(7)], [ij(42)])
    # Eight lanes incl. negatives.
    a8 = si(1, -2, 3, -4, 5, -6, 7, -8)
    sc("sum_wrap", 8, [a8], [ij(-4)])
    sc("min", 8, [a8], [ij(-8)])
    sc("max", 8, [a8], [ij(7)])
    # Overflow traps (checked) vs wrapping.
    big = si(I64_MAX, 1, 0, 0)
    sc("sum_checked", 4, [big], None, status="runtime_failure")
    sc("sum_wrap", 4, [big], [ij(I64_MIN)])  # MAX+1 wraps to MIN
    sc("dot_checked", 4, [si(I64_MAX, 0, 0, 0), si(2, 0, 0, 0)],
       None, status="runtime_failure")
    sc("dot_wrap", 4, [si(I64_MAX, 0, 0, 0), si(2, 0, 0, 0)],
       [ij(-2)])  # MAX*2 wraps to -2
    c.append(case("v-mean-sum-overflow-trap", mod, "mean_checked",
                  [si(I64_MAX, 1, 0, 0)], None,
                  expected_status="runtime_failure", step_budget=8192,
                  type_args=targs(4)))
    # i32 duplication exhibit.
    def s32(*xs):
        return seq([ij(x, 32, True) for x in xs])

    c.append(case("v-sum_i32", mod, "sum_i32", [s32(1, 2, 3, 4)],
                  [ij(10, 32, True)], step_budget=8192,
                  type_args=targs(4)))
    c.append(case("v-dot_i32", mod, "dot_i32",
                  [s32(1, 2, 3, 4), s32(5, 6, 7, 8)],
                  [ij(70, 32, True)], step_budget=8192,
                  type_args=targs(4)))
    c.append(case("v-sum_i32-overflow-trap", mod, "sum_i32",
                  [s32(I32_MAX, 1, 0, 0)], None,
                  expected_status="runtime_failure", step_budget=8192,
                  type_args=targs(4)))

    write_corpus(os.path.join(OUT, "vec_int.json"),
                 "mncs-numerics-vec-int", c)
    return c


# ---------------------------------------------------------------------------
# vec_float_reduce
# ---------------------------------------------------------------------------

def gen_vec_float_reduce():
    mod = "mncs.numerics.vec_float_reduce.v1"
    c = []

    def sc(fn, n, args, exp, status="returned", budget=8192):
        c.append(case("r-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      expected_status=status, step_budget=budget,
                      type_args=targs(n)))

    a4 = sq(1.0, 2.0, 3.0, 4.0)
    b4 = sq(5.0, 6.0, 7.0, 8.0)
    sc("sum", 4, [a4], [fj(10.0)])
    sc("dot", 4, [a4, b4], [fj(70.0)])
    sc("norm2", 4, [a4], [fj(30.0)])
    sc("mean", 4, [a4], [fj(2.5)])
    sc("min", 4, [sq(9.0, -2.0, 4.0, 0.0)], [fj(-2.0)])
    sc("max", 4, [sq(9.0, -2.0, 4.0, 0.0)], [fj(9.0)])
    sc("dist2", 4, [a4, b4], [fj(64.0)])
    sc("l1", 4, [sq(-3.0, 0.0, 4.0, -1.0)], [fj(8.0)])
    sc("linf", 4, [sq(-3.0, 0.5, 4.0, -4.5)], [fj(-4.5)])
    # Cancellation trio: plain sum loses, Neumaier keeps.
    trio = sq(1e16, 1.0, -1e16)
    assert o_sum((1e16, 1.0, -1e16)) == 0.0
    sc("sum", 3, [trio], [fj(0.0)])
    assert o_neumaier((1e16, 1.0, -1e16)) == 1.0
    sc("neumaier_sum", 3, [trio], [fj(1.0)])
    sc("neumaier_sum", 4, [a4], [fj(10.0)])
    # Two-pass variance on eight lanes (oracle value, sanity-bounded).
    eight = (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 8.0)
    var8 = o_variance(eight)
    assert 3.0 < var8 < 3.2, var8
    sc("variance", 8, [sq(*eight)], [fj(var8)])
    shifted = (100000001.0, 100000002.0, 100000003.0)
    sc("variance", 3, [sq(*shifted)], [fj(o_variance(shifted))])
    sc("mean", 3, [sq(*shifted)], [fj(o_sum(shifted) / 3)])
    # Norm: 3-4-5 triangle pins the Newton path end to end.
    assert o_newton_sqrt(25.0) == 5.0
    sc("norm", 2, [sq(3.0, 4.0)], [fj(5.0)])
    sc("norm", 4, [a4], [fj(o_newton_sqrt(30.0))], budget=16384)
    # Cosine: orthogonal, parallel, and the zero-norm refusal.
    sc("cosine", 2, [sq(1.0, 0.0), sq(0.0, 1.0)],
       [finite(mod, "CosOutcome", "Value", 0, [("value", fj(0.0))])],
       budget=16384)
    par = o_newton_sqrt(2.0)
    cos1 = 2.0 / (par * par)
    sc("cosine", 2, [sq(1.0, 1.0), sq(1.0, 1.0)],
       [finite(mod, "CosOutcome", "Value", 0, [("value", fj(cos1))])],
       budget=16384)
    sc("cosine", 2, [sq(0.0, 0.0), sq(1.0, 2.0)],
       [finite(mod, "CosOutcome", "ZeroNorm", 1)], budget=16384)
    # One-lane windows.
    sc("sum", 1, [sq(42.0)], [fj(42.0)])
    sc("mean", 1, [sq(-7.0)], [fj(-7.0)])
    sc("variance", 1, [sq(5.0)], [fj(0.0)])
    # Overflow traps instead of infinities.
    sc("sum", 2, [sq(1e308, 1e308)], None, status="runtime_failure")
    sc("norm2", 2, [sq(1e200, 1e200)], None, status="runtime_failure")
    # Views incl. the empty view.
    sc("sum_view", 4, [sq(1.0, 2.0, 3.0)], [fj(6.0)])
    sc("sum_view", 4, [seq([])], [fj(0.0)])
    sc("mean_view", 4, [sq(1.0, 2.0, 3.0, 4.0)],
       [finite(mod, "FMean", "Value", 0, [("value", fj(2.5))])])
    sc("mean_view", 4, [seq([])],
       [finite(mod, "FMean", "Empty", 1)])

    write_corpus(os.path.join(OUT, "vec_float_reduce.json"),
                 "mncs-numerics-vec-float-reduce", c)
    return c


# ---------------------------------------------------------------------------
# vec_float_build
# ---------------------------------------------------------------------------

def gen_vec_float_build():
    mod = "mncs.numerics.vec_float_build.v1"
    c = []

    def sc(fn, n, args, exp, status="returned", budget=8192):
        c.append(case("b-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      expected_status=status, step_budget=budget,
                      type_args=targs(n)))

    a4 = sq(1.0, 2.0, 3.0, 4.0)
    b4 = sq(5.0, 6.0, 7.0, 8.0)
    sc("scaled", 4, [a4, fj(2.0)], [sq(2.0, 4.0, 6.0, 8.0)])
    sc("scaled", 4, [a4, fj(0.0)], [sq(0.0, 0.0, 0.0, 0.0)])
    sc("scaled", 4, [a4, fj(-1.0)], [sq(-1.0, -2.0, -3.0, -4.0)])
    sc("add", 4, [a4, b4], [sq(6.0, 8.0, 10.0, 12.0)])
    sc("sub", 4, [a4, b4], [sq(-4.0, -4.0, -4.0, -4.0)])
    sc("mul_elem", 4, [a4, b4], [sq(5.0, 12.0, 21.0, 32.0)])
    sc("axpy", 4, [fj(2.0), a4, b4], [sq(7.0, 10.0, 13.0, 16.0)])
    sc("axpy", 4, [fj(0.0), a4, b4], [sq(5.0, 6.0, 7.0, 8.0)])
    sc("abs_elem", 4, [sq(-1.5, 2.5, -0.0, 0.0)],
       [sq(1.5, 2.5, 0.0, 0.0)])
    sc("clamped_elem", 4, [sq(-1.0, 0.5, 2.0, 1.0), fj(0.0), fj(1.0)],
       [sq(0.0, 0.5, 1.0, 1.0)])
    # prefix4 is concrete (see the module note on generic records), so
    # its corpus entries name no instantiation.
    c.append(case("b-prefix4-0", mod, "prefix4", [a4],
                  [sq(1.0, 3.0, 6.0, 10.0)], step_budget=8192))
    c.append(case("b-prefix4-1", mod, "prefix4",
                  [sq(2.0, -2.0, 2.0, -2.0)],
                  [sq(2.0, 0.0, 2.0, 0.0)], step_budget=8192))
    sc("reversed", 4, [a4], [sq(4.0, 3.0, 2.0, 1.0)])
    sc("reversed", 1, [sq(9.0)], [sq(9.0)])
    sc("broadcast_like", 4, [a4, fj(7.0)], [sq(7.0, 7.0, 7.0, 7.0)])
    sc("zeros_like", 4, [a4], [sq(0.0, 0.0, 0.0, 0.0)])
    sc("ones_like", 4, [a4], [sq(1.0, 1.0, 1.0, 1.0)])
    # Eight lanes incl. a sign flip.
    a8 = sq(1.0, -2.0, 3.0, -4.0, 5.0, -6.0, 7.0, -8.0)
    sc("scaled", 8, [a8, fj(0.5)],
       [sq(0.5, -1.0, 1.5, -2.0, 2.5, -3.0, 3.5, -4.0)])
    sc("reversed", 8, [a8],
       [sq(-8.0, 7.0, -6.0, 5.0, -4.0, 3.0, -2.0, 1.0)])

    write_corpus(os.path.join(OUT, "vec_float_build.json"),
                 "mncs-numerics-vec-float-build", c)
    return c


# ---------------------------------------------------------------------------
# mat_float_small
# ---------------------------------------------------------------------------

def gen_mat_float_small():
    mod = "mncs.numerics.mat_float_small.v1"
    c = []

    def sc(fn, args, exp, status="returned", budget=8192):
        c.append(case("m-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      expected_status=status, step_budget=budget))

    m2 = sq(1.0, 2.0, 3.0, 4.0)  # [[1,2],[3,4]] row-major
    x2 = sq(5.0, 6.0)
    sc("mat2", [fj(1.0), fj(2.0), fj(3.0), fj(4.0)], [m2])
    sc("vec2", [fj(5.0), fj(6.0)], [x2])
    sc("identity2", [], [sq(1.0, 0.0, 0.0, 1.0)])
    # rot2(0) is exactly the identity in every libm.
    sc("rot2", [fj(0.0)], [sq(1.0, 0.0, 0.0, 1.0)])
    th = 0.5
    sc("rot2", [fj(th)],
       [sq(math.cos(th), -math.sin(th), math.sin(th), math.cos(th))])
    # Rotation preserves the norm: det(rot2(t)) == cos^2+sin^2 ~ 1.
    # Pinned exactly (same-order oracle); closeness to 1 is asserted.
    det_rot = math.cos(th) * math.cos(th) + math.sin(th) * math.sin(th)
    assert abs(det_rot - 1.0) < 3e-16, det_rot
    sc("det2", [sq(math.cos(th), -math.sin(th), math.sin(th),
                    math.cos(th))], [fj(det_rot)])
    sc("transpose2", [m2], [sq(1.0, 3.0, 2.0, 4.0)])
    sc("trace2", [m2], [fj(5.0)])
    sc("det2", [m2], [fj(-2.0)])
    sc("matvec2", [m2, x2], [sq(17.0, 39.0)])
    sc("matmul2", [m2, m2], [sq(7.0, 10.0, 15.0, 22.0)])
    # Identity laws.
    sc("matmul2", [m2, sq(1.0, 0.0, 0.0, 1.0)], [m2])
    sc("matvec2", [sq(1.0, 0.0, 0.0, 1.0), x2], [x2])
    sc("transpose2", [sq(1.0, 0.0, 0.0, 1.0)],
       [sq(1.0, 0.0, 0.0, 1.0)])
    # Inverse of [[4,7],[2,6]] (det 10) and the singular refusal.
    sc("inv2", [sq(4.0, 7.0, 2.0, 6.0)],
       [finite(mod, "Inv2", "Value", 0,
               [("value", sq(6.0 / 10.0, (0.0 - 7.0) / 10.0,
                                 (0.0 - 2.0) / 10.0, 4.0 / 10.0))])])
    sc("inv2", [sq(1.0, 2.0, 2.0, 4.0)],
       [finite(mod, "Inv2", "Singular", 1)])
    # Solve [[3,1],[1,2]] x = [9,8] -> [2,3]; singular refuses.
    sc("solve2", [sq(3.0, 1.0, 1.0, 2.0), sq(9.0, 8.0)],
       [finite(mod, "Solve2", "Value", 0,
               [("value", sq((9.0 * 2.0 - 1.0 * 8.0) / 5.0,
                             (3.0 * 8.0 - 9.0 * 1.0) / 5.0))])])
    sc("solve2", [sq(1.0, 2.0, 2.0, 4.0), sq(1.0, 2.0)],
       [finite(mod, "Solve2", "Singular", 1)])
    # 3x3.
    m3 = sq(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    x3 = sq(1.0, 0.0, -1.0)
    sc("identity3", [],
       [sq(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)])
    sc("transpose3", [m3],
       [sq(1.0, 4.0, 7.0, 2.0, 5.0, 8.0, 3.0, 6.0, 9.0)])
    sc("trace3", [m3], [fj(15.0)])
    sc("det3", [sq(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)],
       [fj(1.0)])
    sc("det3", [sq(1.0, 2.0, 3.0, 0.0, 1.0, 4.0, 5.0, 6.0, 0.0)],
       [fj(1.0)])
    sc("matvec3", [m3, x3], [sq(-2.0, -2.0, -2.0)])
    sc("matmul3", [m3, sq(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)],
       [m3])
    # A*B with small exact lanes, mirrored left-assoc order.
    a = (1.0, 2.0, 0.0, -1.0, 3.0, 1.0, 2.0, -2.0, 1.0)
    b = (3.0, 1.0, 2.0, 0.0, -1.0, 4.0, 1.0, 0.0, -2.0)

    def mm3(i, j):
        row = 3 * i
        return ((a[row] * b[j] + a[row + 1] * b[3 + j])
                + a[row + 2] * b[6 + j])

    expect = [mm3(i, j) for i in range(3) for j in range(3)]
    sc("matmul3", [sq(*a), sq(*b)], [sq(*expect)], budget=16384)

    write_corpus(os.path.join(OUT, "mat_float_small.json"),
                 "mncs-numerics-mat-float-small", c)
    return c


# ---------------------------------------------------------------------------
# mat drivers (multi-parameter generics via in-language wrappers)
# ---------------------------------------------------------------------------

def gen_mat_float_drivers():
    mod = "mncs.numerics.test.mat_float_drivers.v1"
    c = []

    def sc(fn, args, exp, budget=16384):
        c.append(case("d-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      step_budget=budget))

    sc("d_trace_2x2", [nest((1.0, 2.0), (3.0, 4.0))], [fj(5.0)])
    sc("d_trace_3x3",
       [nest((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0))],
       [fj(15.0)])
    sc("d_frob_2x2", [nest((1.0, 2.0), (3.0, 4.0))], [fj(30.0)])
    sc("d_frob_2x3", [nest((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))],
       [fj(91.0)])
    sc("d_sum_2x3", [nest((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))],
       [fj(21.0)])
    sc("d_max_3x2", [nest((-1.0, 5.0), (3.0, 2.0), (0.0, -7.0))],
       [fj(5.0)])
    sc("d_max_2x2", [nest((-4.0, -2.0), (-9.0, -3.0))], [fj(-2.0)])

    write_corpus(os.path.join(OUT, "mat_float_drivers.json"),
                 "mncs-numerics-mat-float-drivers", c)
    return c


def gen_mat_float_build_drivers():
    mod = "mncs.numerics.test.mat_float_build_drivers.v1"
    c = []

    def sc(fn, args, exp, budget=32768):
        c.append(case("e-%s-%d" % (fn, len(c)), mod, fn, args, exp,
                      step_budget=budget))

    a22 = nest((1.0, 2.0), (3.0, 4.0))
    sc("d_matvec_2x2", [a22, sq(5.0, 6.0)], [sq(17.0, 39.0)])
    sc("d_matvec_3x2",
       [nest((1.0, 2.0), (3.0, 4.0), (5.0, 6.0)), sq(2.0, 3.0)],
       [sq(8.0, 18.0, 28.0)])
    sc("d_matmul_2x2x2", [a22, a22],
       [nest((7.0, 10.0), (15.0, 22.0))])
    # 2x3 times 3x2 -> 2x2, mirrored program order per cell.
    a23 = ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    b32 = ((7.0, 8.0), (9.0, 10.0), (11.0, 12.0))
    # Mirrors the kernel accumulation cell = ((0 + t0) + t1) + t2.
    expect = tuple(
        tuple(((0.0 + a23[i][0] * b32[0][j]) + a23[i][1] * b32[1][j])
              + a23[i][2] * b32[2][j] for j in range(2))
        for i in range(2))
    sc("d_matmul_2x3x2", [nest(*a23), nest(*b32)],
       [nest(*expect)])
    sc("d_transpose_2x3", [nest((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))],
       [nest((1.0, 4.0), (2.0, 5.0), (3.0, 6.0))])
    sc("d_diag_3x3",
       [nest((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0))],
       [sq(1.0, 5.0, 9.0)])

    write_corpus(os.path.join(OUT, "mat_float_build_drivers.json"),
                 "mncs-numerics-mat-float-build-drivers", c)
    return c


# ---------------------------------------------------------------------------
# examples (consumer-integration)
# ---------------------------------------------------------------------------

def gen_examples():
    made = []

    def emit(name, cases):
        write_corpus(os.path.join(OUT, "examples_%s.json" % name),
                     "mncs-numerics-examples-%s" % name, cases)
        made.extend(cases)

    def sc(name, mod, fn, args, exp, budget=8192):
        return case("x-%s" % name, mod, fn, args, exp,
                    step_budget=budget)

    stats = "mncs.numerics.examples.stats.v1"
    w4 = (1.0, 3.0, 5.0, 7.0)
    eight = (2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 8.0)
    emit("stats", [
        sc("report4", stats, "report4", [sq(*w4)],
           [sq(o_sum(w4) / 4, o_variance(w4), 1.0, 7.0)], budget=16384),
        sc("report8", stats, "report8", [sq(*eight)],
           [sq(o_sum(eight) / 8, o_variance(eight), 2.0, 8.0)],
           budget=16384),
        sc("l1_linf4", stats, "l1_linf4", [sq(-3.0, 0.5, 4.0, -4.5)],
           [sq(o_sum((3.0, 0.5, 4.0, 4.5)), -4.5)]),
    ])

    trap = "mncs.numerics.examples.trapezoid.v1"
    pi = 3.141592653589793
    h = pi / 64.0
    acc = 0.0
    for i in range(1, 64):
        acc = acc + math.sin(i * h)
    integral = h * acc
    assert abs(integral - 2.0) < 1e-3, integral
    emit("trapezoid", [
        sc("sin_integral_64", trap, "sin_integral_64", [],
           [fj(integral)], budget=32768),
    ])

    solv = "mncs.numerics.examples.solve_demo.v1"
    emit("solve_demo", [
        sc("solve_ok", solv, "solve_and_residual",
           [sq(3.0, 1.0, 1.0, 2.0), sq(9.0, 8.0)], [sq(0.0, 0.0)]),
        sc("solve_singular", solv, "solve_and_residual",
           [sq(1.0, 2.0, 2.0, 4.0), sq(1.0, 2.0)], [sq(1.0, 2.0)]),
    ])

    logi = "mncs.numerics.examples.logistic.v1"

    def traj(r, x0, steps=64):
        x = x0
        for _ in range(steps):
            x = r * x * (1.0 - x)
        return x

    stable = traj(2.5, 0.2)
    assert abs(stable - 0.6) < 1e-9, stable
    emit("logistic", [
        sc("stable", logi, "trajectory", [fj(2.5), fj(0.2)],
           [fj(stable)], budget=16384),
        sc("chaotic37", logi, "trajectory", [fj(3.7), fj(0.2)],
           [fj(traj(3.7, 0.2))], budget=16384),
        sc("chaotic40", logi, "trajectory", [fj(4.0), fj(0.3)],
           [fj(traj(4.0, 0.3))], budget=16384),
    ])
    return made


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for gen in (gen_scalar_int, gen_scalar_float, gen_vec_int,
                gen_vec_float_reduce, gen_vec_float_build,
                gen_mat_float_small, gen_mat_float_drivers,
                gen_mat_float_build_drivers, gen_examples):
        cases = gen()
        print("%-28s %4d cases" % (gen.__name__, len(cases)))
        total += len(cases)
    print("%-28s %4d cases" % ("TOTAL", total))


if __name__ == "__main__":
    main()

