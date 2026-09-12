# Numerical semantics

The exact contract behind every `mncs.numerics` primitive. Where the
language leaves a choice, this document records which choice the
library took and why, so a future consumer (geometry, signal,
physics, FEM, control) never has to guess.

## Integer arithmetic

Default operators (`+ - * / %`) are **checked**: overflow, `MIN / -1`,
`MIN % -1`, and division/modulo by zero are deterministic runtime
failures (`runtime_failure` in corpora), never wraps. Suffixed
operators are total by definition: wrapping (`+% -% *%`) reduces
modulo 2^N, saturating (`+| -| *|`) clamps at the bound. Shifts take
counts modulo the width; signed `>>` is arithmetic.

Per-function policy is explicit in `src/numerics/scalar_int.mncs`:

- `abs_checked` traps on `MIN`; `abs_wrap(MIN) == MIN`;
  `abs_sat(MIN) == MAX`.
- `min/max/clamp` are comparison-only: no arithmetic, no trap, no
  obligation on any input.
- `clamp` requires `lo <= hi` (unchecked precondition).
- `pow_checked` allows `exp <= 64` (larger exponents return
  `ExpTooLarge`, never a silent prefix); value overflow traps.
  `0^0 == 1` (empty product).
- `gcd` requires non-negative inputs; `gcd(0, 0) == 0` by convention.
- `mean_checked` truncates toward zero; the divisor is the static
  length (`N >= 1`), so only the sum can trap.

Reductions (`vec_int.mncs`) traverse once, left to right. `_checked`
kernels trap on the first overflowing step; `_wrap` kernels never
trap. `N >= 1` everywhere (empty exact sequences are outside every
contract here).

## Floating point

`f64` is the only float. The **trap rule** governs everything: any
non-finite input or result — NaN, ±infinity, division by zero,
`0.0 / 0.0`, overflow to infinity — is a deterministic runtime
failure, never a value. Consequences the library depends on:

- There is no NaN-propagating `min`/`max`: `fmin(NaN, 1.0)` traps on
  the comparison. Callers classify first; the library never branches
  on NaN-quietly-false.
- `safe_div`/`mean_view`/`cosine`/`sqrt_newton`/`quadratic`/`inv2`/
  `solve2` return explicit outcome enums (`DivByZero`, `Empty`,
  `ZeroNorm`, `DomainError`, `Singular`, …) instead of trapping on
  *foreseeable* domain edges. Overflow of a genuinely computed value
  still traps — the enums cover empty/zero/singular inputs, not
  infinities.
- `select` evaluates both arms eagerly: a trapping expression must
  never hide in a discarded arm. Guards use statement-level `if`,
  never `select` over a maybe-trapping value.
- Comparisons trap on non-finite inputs rather than returning false,
  so every branch in `src/` is NaN-intolerant by construction.

Signed zeros: `+0.0 == -0.0` in every comparison; `fabs` normalizes
both to `+0.0` (via `<=`); `fmin(-0.0, +0.0) == -0.0` (first arm
wins); `fneg` is exact IEEE negation via the `neg(x)` intrinsic
(`neg(+0.0) == -0.0`, pinned in the corpus; pressure P-007,
repaired).

Subnormals flow through arithmetic normally (pinned: `5e-324`
cases); conversions `as` truncate float→int (trapping out of range)
and round int→float per IEEE-754.

## Reductions and order

Every reduction accumulates **in program order, left to right**, and
the oracle mirrors that order operation-for-operation, so committed
cases assert exact bit patterns, not tolerances. Consequence: the
same source is bit-identical on all five backends — verified by the
Neumaier trio (`[1e16, 1.0, -1e16]` sums to exactly `0.0` plain,
exactly `1.0` compensated) and by chaotic logistic trajectories that
would amplify any 1-ulp backend divergence within a dozen steps.

`mean` divides by `(len as f64)`; `variance` is two-pass (mean,
then mean of squared deviations) — never the sum-of-squares
shortcut, which cancels on shifted data (pinned shifted case).
`norm` goes through the Newton square root; `cosine` notes that
`|cos|` can exceed 1.0 by an epsilon (independent roundings) and
provides no `acos` to misuse it with.

`sqrt_newton` accuracy is guaranteed only on `1e-12 <= x <= 1e24`
(hand-rolled range reduction: start at `min(max(x, 1.0), 1e12)`, 32
Newton steps; the generator asserts < 1e-12 relative error against
`math.sqrt` before pinning bits). Outside the domain it terminates
but may not have converged — documented, not tested.

`quadratic` uses the stable `q`-form (pinned: `x² - 1e8·x + 1` keeps
both roots; the naive form loses the small one), returns roots
ascending, and reports `n ∈ {2, 1, 0, -1}` (`-1` = degenerate
`0 == 0`, constraining nothing).

## Matrices

Small matrices are **flat row-major** sequences (`Mat2 = [f64; 4]`,
`Mat3 = [f64; 9]`); generic matrices are **nested row-major**
(`[[f64; N]; M]`). Flat literals and `replace`-construction build on
every backend (pressure P-001, repaired); the build modules still
live separately and take exemplar seeds because no kernel can RETURN
a fresh symbolic-bound sequence (pressure P-003, open). Squareness
is structural, not a documented precondition (pressure P-005,
resolved): `trace_g<N>` names both dimensions with one parameter,
so a non-square seed is an MNE221 elaboration refusal, not a silent
partial diagonal.

`solve2`/`inv2` are Cramer's rule (exact singularity test
`det == 0.0`, no pivoting — documented, not a general solver).
`rot2` uses the shared-libm `sin`/`cos`, bit-exact across backends
(CPython-oracle bits pass everywhere on this machine).

## Tolerances

Committed corpora use **exact bit equality**, never tolerances: the
oracle mirrors operation order, so agreement is checkable exactly.
Approximate equality exists as library API (`approx_abs`,
`approx_rel`, `approx` = absolute arm for near-zero + relative arm
for magnitude) for consumers that need it. Negative tolerances never
match. Test code outside this repository that needs fuzzy comparison
belongs above this layer, with its tolerance budget stated.
