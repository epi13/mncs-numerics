# MNCS language pressure ledger

Reports from building real numerical software in MNCS. Each entry has a
reproducer under `repros/P-XXX-*/` (or a committed corpus case) that a
future `mncs-language` agent can run without rediscovering the problem.

**Toolchain under test:** `mncs-language` at `68492c0` (2026-09-11),
`mncs-cli` debug build, rustc 1.97.1, Linux x86_64. Source profile
`0.16` (current) unless a repro says otherwise. All five executable
backends: `mncs-research-bytecode`, `mncs-portable-wasm-mvp`,
`mncs-c11`, `mncs-llvm-ir`, `mncs-cranelift`.

**How to run a repro** (from this repository root; `LANG` is an
`mncs-language` checkout at the revision above):

```bash
export MNCS_LIBRARY_PATH=$PWD/src
cargo run -q -p mncs-cli -- experiment run repros/P-001-float-replace/repro.mncs \
  --backend <backend> --corpus repros/P-001-float-replace/corpus.json   # execution repros
cargo run -q -p mncs-cli -- source-study repros/P-003-symbolic-fill/repro.mncs \
  --node-id repro                                                        # compile repros
```

Run the CLI from the `mncs-language` directory (`cargo run` resolves
the workspace there).

## Index

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| P-001 | Float `SequenceReplace` miscompiled on LLVM, refused on WASM | correctness blocker | confirmed |
| P-002 | Host seeding drops repeated generic spellings (`(2,2)` → `(2)`) | expressiveness blocker | confirmed, root-caused |
| P-003 | No fill for symbolic bounds (`[x; N]` refused) | expressiveness blocker | confirmed |
| P-004 | No generic records or enums | expressiveness blocker | confirmed |
| P-005 | No dimension-equality constraints (silent wide trace) | safety issue | confirmed |
| P-006 | Cranelift SIGSEGV on arity-mismatched execution request | correctness blocker | confirmed |
| P-007 | No exact negation (`fneg(+0.0) == +0.0`) | correctness edge | confirmed, worked around |
| P-008 | No literal adaptation / exponent notation for `f64` | ergonomics | confirmed, worked around |
| P-009 | No generic numeric arithmetic; misleading MNE120 | expressiveness blocker | confirmed, worked around |
| P-010 | No float vectors (`vec<f64, N>` refused) | expressiveness blocker | confirmed, worked around |
| P-011 | Stale profile docs over-claim float-sequence/record limits | tooling/docs | confirmed |
| P-012 | No correctly-rounded FMA | accuracy note | confirmed |
| P-013 | No callable values/closures for elementwise kernels | expressiveness | acknowledged constraint |
| P-014 | Loop lowering is vectorization-hostile (C11 state machine, per-lane fail edges) | performance | confirmed |

Severity scale: correctness blocker > expressiveness blocker >
safety issue > diagnostics issue > ergonomics > accuracy note >
tooling/docs. "Acknowledged constraint" means the language documents
the gap as an explicit non-goal; the report measures its cost rather
than asking for a surprise feature.

## Revisited pre-existing topics

The previous ledger held only topic bullets, not reports. Their
disposition after re-running against the current toolchain:

- **Float sequences refused** — SUPERSEDED for reads/reductions:
  `[f64; N]` parameters, traversal, generics, views, nested matrices,
  and corpus boundary-crossing all execute on all five backends
  (356 committed cases). The refusal survives ONLY for `replace`-based
  construction (now P-001) and `vec<f64, N>` (now P-010).
- **NaN payload/propagation policy** — CLARIFIED, not resolved: the
  trap rule (any non-finite input/result fails closed) is real and
  pinned by 20+ trap cases, but "payload policy" is moot because NaN
  never survives an operation boundary. No report: the behavior is
  specified, tested, and depended upon (see `docs/NUMERICAL_SEMANTICS.md`).
- **Signed zero / subnormals** — PARTIALLY resolved: signed zeros and
  subnormals flow through arithmetic correctly (pinned cases), but
  exact negation of `+0.0` is inexpressible (now P-007).
- **Overflow/underflow semantics** — CONFIRMED working: checked ints
  trap, wrapping/saturating intents are total, float overflow traps.
  Pinned, no report needed.
- **FMA / reassociation control** — CONFIRMED absent (now P-012).
- **Deterministic reductions / parallel scheduling** — CONFIRMED
  working: left-to-right program order is bit-identical on all five
  backends (Neumaier trio, logistic chaos trajectories). No report.
- **SIMD lane semantics** — integer `vec`/`mask` work; float lanes
  absent (now P-010). No native-SIMD selection claimed or tested.
- **CPU vs CUDA differences** — NOT TESTED: no CUDA target was
  available in this run. Left open, not closed.
- **Optimization-level reproducibility** — NOT TESTED as a separate
  axis (one compiler profile). Left open.
- **High-precision interoperability** — OPEN: the oracle is Python
  binary64, not MPFR; Newton residuals are validated but no decimal/
  arbitrary-precision boundary exists. Not a defect report.
- **Interval/error-bound representations** — OPEN by design (no
  interval type). Not filed: acknowledged future, no blocking use hit
  in v1.
- **Compile-time vs runtime evaluation parity** — no divergence
  observed on constant-heavy kernels (repeat literals, literal
  matrices agree everywhere). No report.
- **Machine-readable numeric contracts** — the experiment-result JSON
  (identities, obligations, per-case status) proved sufficient for a
  full file-driven harness (this repository). Resolved in practice.

---

## P-001 — Float `SequenceReplace` miscompiled on LLVM, refused on WASM

- **Severity:** correctness blocker. **Status:** confirmed.
- **Affects:** every constructive float kernel
  (`src/numerics/vec_float_build.mncs`, `mat_float_build.mncs`).
- **Repro:** `repros/P-001-float-replace/` (`repro.mncs` + `corpus.json`).
- **Invocation:** `experiment run repro.mncs --backend <be> --corpus corpus.json`
  (expects `scaled` demo = 20.0).
- **Expected:** the traversal with `replace(out, i, xs[i] * s)` lowers
  the float lane as `double` on every backend, or refuses honestly.
- **Actual:**
  - `mncs-llvm-ir`: `clang failed: module.ll:409:13: error:
    '%relem35_v9' defined with type 'double' but expected 'i64'` —
    the replacement lane is stored into an `i64` slot. The failure
    poisons the WHOLE artifact: entrypoints that never touch `replace`
    (e.g. a pure pass-through in the same file) report `unsupported`
    with the same clang error.
  - `mncs-portable-wasm-mvp`: honest per-entrypoint refusal —
    `CGN302 ... float sequences are not supported`; other entrypoints
    in the same file still run.
  - bytecode, C11, Cranelift: correct value, all cases pass.
- **Why it matters:** functional update is THE construction primitive
  for bounded sequences; without it on LLVM there is no generic
  `scaled`/`axpy`/`matvec` on the optimizing backend, and the
  whole-artifact poisoning means one constructive function disables
  LLVM for every other function in the file.
- **Workaround:** split construction from reduction at module
  granularity (`vec_float_build` vs `vec_float_reduce`,
  `mat_float_build` vs `mat_float`), and pin LLVM+WASM as
  expected-refusals for the build modules in `scripts/run_tests.py`.
  Cost: two parallel module hierarchies, seeded-construction APIs (see
  P-003), and no LLVM coverage for any constructive kernel.
- **Direction:** fix the LLVM `SequenceReplace` element-type lowering
  to use the element's lowered type (the WASM refusal message shows
  the frontend already knows the operation is float-typed); scope the
  poisoning to the refusing entrypoint as WASM already does.
- **Regression test:** any corpus case calling `scaled<4>` on
  `mncs-llvm-ir` (committed: `vec_float_build.json`, currently pinned
  refused).
- **Depends on:** none. Blocks: LLVM coverage of P-003 workarounds.

## P-002 — Host seeding drops repeated generic spellings

- **Severity:** expressiveness blocker (harness + host-driven use).
  **Status:** confirmed, root-caused (no language change made here).
- **Affects:** every multi-parameter generic called directly from a
  corpus (`matvec_into<M,N>`, `matmul_into<M,K,N>`, `trace_g<M,N>`…).
- **Repro:** `repros/P-002-host-multi-generic/`; corpus names
  `matvec_into` with `type_arguments: [{nat 2}, {nat 2}]`.
- **Expected:** the `(2,2)` specialization compiles in and runs.
- **Actual:** with two corpus cases, `(2,2)` and `(3,2)`, every
  native backend reports `compiled instantiations: [(2), (2, 3)]` —
  the first collapsed by dedup, the second reordered by sort. The
  emitted artifact row for the `(2,2)` seed carries
  `args_spellings: ["2"]` while `canonical_args` is the correct
  `"value:2|value:2"` (inspected in the backend artifact JSON): the
  specialization is RIGHT, its host address is truncated. Bytecode
  (which resolves through `canonical_args`) passes both cases, which
  is why the existing single-argument suites never caught it.
- **Root cause (for the language repair campaign):**
  `crates/mncs-model/src/generics.rs` merges host seeds per
  instantiation and then runs `spellings.sort(); spellings.dedup();`
  on the spelling LIST. The dedup treats positional arguments as a
  set: equal values (`2,2` → `2`) collapse, and the sort additionally
  breaks any unsorted-but-distinct spelling (`(3,2)` is recorded as
  `(2,3)` and will not match a `(3,2)` request). The square-matrix
  case — the most common multi-parameter shape — always hits this.
- **Why it matters:** host-driven instantiation is the REPL/scripting
  path into generic numerical code; silently requiring distinct
  sorted arguments makes corpus-driven testing of square
  multi-parameter kernels impossible.
- **Workaround:** in-language driver wrappers
  (`tests/drivers/mat_*_drivers.mncs`) with exact `<2, 2>`
  instantiation; corpora call the wrappers. Cost: one thin wrapper
  per tested shape, and the wrappers must be maintained alongside the
  API.
- **Direction:** keep spellings positional (no sort/dedup across
  argument positions); dedup only byte-identical full seed keys,
  which the merge map already does.
- **Regression test:** the P-002 repro corpus itself (two cases:
  `(2,2)` pins the dedup half, `(3,2)` pins the sort half; both
  expect `returned` on bytecode today and on all backends after the
  repair).
- **Depends on:** none.

## P-003 — No fill for symbolic bounds

- **Severity:** expressiveness blocker. **Status:** confirmed.
- **Affects:** every constructor (`broadcast`, `zeros`, `identity`,
  `matmul` result allocation).
- **Repro:** `repros/P-003-symbolic-fill/repro.mncs` — `return [x; N];`
  for symbolic `N`.
- **Expected:** an N-fold sequence, or a precise "symbolic repeat
  refuses" diagnostic.
- **Actual:** parse refusal `MNP203: expected repeat count after ';'`
  plus cascade diagnostics (MNP016/MNP017/MNP006/MNP007) that bury the
  root cause: none names the real rule (repeat counts must be
  literals).
- **Why it matters:** without fill, no generic kernel can RETURN a
  fresh sequence; `matmul<M,K,N>(a, b)` is inexpressible and every
  constructive API threads an exemplar (`matmul_into(a, b, out)`).
  Exemplars are honest but infectious: every caller must own a
  correctly-shaped value first.
- **Workaround:** seeded construction (`*_into`, `broadcast_like`,
  `zeros_like`); repeat literals (`[1.0; 256]`) cover benchmarks and
  tests where the bound is manifest. Cost: API-wide `out`/`seed`
  parameters + documentation burden.
- **Direction:** admit `[x; N]` for symbolic `N` (the traversal
  machinery already iterates symbolic bounds), or provide an
  exemplar-free `fill<N>(x)` intrinsic with identical semantics.
- **Regression test:** a `broadcast_like` corpus case (committed) plus
  the P-003 compile repro.
- **Depends on:** none. Interacts with P-001 (construction envelope).

## P-004 — No generic records or enums

- **Severity:** expressiveness blocker. **Status:** confirmed.
- **Affects:** generic carried state (`prefix<N>`, any multi-scalar
  generic fold) and generic outcome types (`normalized<N>` returning
  `Value { value: [f64; N] }` vs `ZeroNorm`).
- **Repro:** `repros/P-004-generic-records/repro.mncs` —
  `record Box<N: Nat> { lane: [f64; N] }`; `repro_enum.mncs` —
  `enum Outcome<N: Nat> { Value { value: [f64; N] }, Empty }`.
- **Expected:** Nat-parameterized records/enums, or a precise
  diagnostic.
- **Actual:** parse refusals (`MNP123` for records, `MNP072` for
  enums) plus cascades that name everything except the real rule.
- **Why it matters:** a traversal carries exactly one state value, so
  multi-scalar generic folds need a record; without generic records,
  `prefix<N>` and friends are concrete-width-only (`prefix4` + a
  `[f64; 4]`-specialized `Pref` record). Without generic enums,
  fallible constructors cannot return typed payloads
  (`normalized` traps on the zero vector instead of returning
  `ZeroNorm`, because `ZeroNorm` has nowhere to live).
- **Workaround:** concrete-width records per width (`Pref` for 4);
  trap-on-degenerate instead of outcome enums for generic widths.
  Cost: one record + one function per supported width; generic
  callers cannot abstract over width; degenerate inputs trap where
  an enum would inform.
- **Direction:** admit `record Name<N: Nat> { ... }` and
  `enum Name<N: Nat> { ... }` with substitution mirroring generic
  functions (0.10 machinery already substitutes sequence bounds in
  signatures).
- **Regression test:** committed `prefix4`/`normalized` cases + the
  P-004 compile repros.
- **Depends on:** none.

## P-005 — No dimension-equality constraints

- **Severity:** safety issue. **Status:** confirmed.
- **Affects:** `trace_g`, `diag_into`, any square-only kernel.
- **Repro:** `repros/P-005-dimension-constraints/` — `trace_g<2, 3>`
  over `[[1,2,3],[4,5,6]]` returns `6.0` (partial diagonal) with no
  diagnostic. (Tall inputs trap fail-closed; only wide is silent.)
- **Expected:** a type-level way to require `M == N`, or at minimum a
  runtime complaint on shape mismatch.
- **Actual:** squareness is a doc comment; wide inputs silently sum a
  prefix of the diagonal.
- **Why it matters:** silent wrong-shape acceptance is the classic
  scientific-computing footgun (MATLAB-style). Fail-closed on tall
  but silent on wide is the worst combination: half the mistakes are
  caught, so the other half is trusted.
- **Workaround:** documented preconditions + square-only committed
  corpora. Cost: vigilance; no mechanical enforcement available.
- **Direction:** dimension-arithmetic constraints on Nat parameters
  (`fn trace<N: Nat>(m: [[f64; N]; N])`), or a `square` witness
  argument the compiler checks.
- **Regression test:** the P-005 repro (expects the silent 6.0 TODAY;
  must be rewritten to expect a refusal when the language changes).
- **Depends on:** none.

## P-006 — Cranelift SIGSEGV on arity-mismatched execution request

- **Severity:** correctness blocker (compiler crash). **Status:** confirmed.
- **Affects:** any harness/client that sends a malformed request to
  the Cranelift backend.
- **Repro:** `repros/P-006-cranelift-arity-crash/` — two-argument `f64`
  function called with ONE argument.
- **Expected:** `invalid_request` (what the other four backends
  return: bytecode `argument count does not match SSA inputs`, WASM
  value-contract mismatch, C11/LLVM `invalid native observation`).
- **Actual:** the CLI process dies with SIGSEGV (exit 139, empty
  stdout). Bisected from a 150-case corpus: NaN inputs were first
  suspected and exonerated (correct-arity NaN is fine); a normal
  `1.0` with wrong arity crashes deterministically.
- **Why it matters:** a fuzzer, a REPL typo, or a stale corpus must
  never kill the compiler process. `experiment run` is also the
  narrow runtime boundary for Fabric packaging: a crash there is a
  reliability hole, not a cosmetic diagnostic gap.
- **Workaround:** none needed in-library (committed corpora never
  mismatch arity); harness authors must treat exit 139 as possible
  until repaired.
- **Direction:** arity-check the request against the entrypoint value
  contract before lowering (the check exists on every other backend).
- **Regression test:** the P-006 repro (expects `invalid_request` on
  all five backends; today it crashes one).
- **Depends on:** none.

## P-007 — No exact negation

- **Severity:** correctness edge. **Status:** confirmed, worked around
  (pinned, not hidden).
- **Affects:** `fneg` (`src/numerics/scalar_float.mncs`).
- **Repro:** committed corpus case `f-fneg-v-1` (`fneg(+0.0)`,
  expects `+0.0`) + `repros/P-007-exact-negation/README.md`.
- **Expected (IEEE):** `-(+0.0) == -0.0`.
- **Actual:** `0.0 - 0.0 == +0.0`, and no available operation produces
  `-0.0` from `+0.0` without trapping (comparisons equate the zeros;
  division traps). So `fneg(+0.0) == +0.0`: a one-bit deviation from
  IEEE negation, pinned in the corpus with this report as its
  justification. Every other finite input negates exactly
  (`fneg(-0.0) == +0.0` is exact).
- **Why it matters:** signed-zero discipline is load-bearing in
  branch cuts, complex arithmetic, and interval endpoints. A library
  that cannot spell negation cannot promise IEEE Annex behavior.
- **Workaround:** documented deviation; `fabs` uses `<=` (exact for
  all inputs including `-0.0`, found during this run).
- **Direction:** a `neg(x)` intrinsic (exact, total on finite inputs),
  or unary `-x` for non-literal operands.
- **Regression test:** `f-fneg-v-1` (must be UPDATED to `-0.0` when
  exact negation lands).
- **Depends on:** none.

## P-008 — Integer literals do not adapt to `f64`; no exponent notation

- **Severity:** ergonomics. **Status:** confirmed, worked around.
- **Affects:** every float kernel with a whole-number constant.
- **Repro:** `repros/P-008-float-literal-adaptation/repro.mncs` —
  `xs[i] * 2` inside an `[f64; N]` traversal.
- **Expected:** `2` adapts to `2.0` (Profile 0.6 gives integer
  literals symmetric adaptation across int widths).
- **Actual:** `MNE118: integer literal cannot satisfy a non-integer
  type` + `MNE119` (operands must share a type). The diagnostic is
  accurate; the missing rule is the asymmetry: ints adapt, floats do
  not. Compounding it, there is NO exponent notation at all: `1.5e3`,
  `1.5e-3`, and `1e16` all fail at parse time (MNP016/MNP017/MNP007
  cascade), so `1e-12` must be spelled as twelve zeros after a dot
  and `1e100` cannot be spelled directly at all — magnitudes are
  computed (`1.0 / 100000000000000000000.0`-style) or spelled out
  longhand (see `prop_norm_nonneg` in `tests/drivers/`).
- **Why it matters:** numerical code is dense with 2/0/1 constants
  (a paper cut on every line) and lives on extreme magnitudes
  (tolerances like `1e-12`, scales like `1e16`): forcing `.0` plus
  zero-counting on every one invites transcription bugs in exactly
  the constants correctness depends on.
- **Workaround:** spell every constant longhand (done throughout
  `src/` and `tests/`). Cost: pervasive, minor, but real.
- **Direction:** extend literal adaptation to `f64` targets (exact
  for |lit| < 2^53; refuse or round explicitly beyond) and admit
  `digits[.digits]e[+-]digits` spellings with correct rounding.
- **Regression test:** the P-008 compile repro.
- **Depends on:** none.

## P-009 — No generic numeric arithmetic; misleading MNE120

- **Severity:** expressiveness blocker + diagnostics issue.
  **Status:** confirmed, worked around.
- **Affects:** any attempt at one kernel for many element types.
- **Repro:** `repros/P-009-generic-arithmetic/repro.mncs` —
  `fn gdot<T, N: Nat>(xs: [T; N], ys: [T; N])` with `+`/`*` inside.
- **Expected:** a trait/constraint mechanism, or at least a
  diagnostic naming the missing capability.
- **Actual:** `MNE120: arithmetic operands must have an integer type`
  — doubly wrong: it says "integer" although `f64` supports `+`/`*`,
  and it blames the operand rather than the missing constraint
  system. (A second error, `MNE102` on the carried binding, is pure
  cascade.)
- **Why it matters:** without element-generic arithmetic, `sum`/`dot`
  are duplicated per width (`sum_i32`/`dot_i32` in `vec_int.mncs`
  exist precisely to measure this: line-for-line copies with the type
  changed). The duplication scales with widths × intents × kernels.
- **Workaround:** per-width duplication, labeled as such in-source.
  Cost: linear code growth; every algorithmic fix must be applied N
  times.
- **Direction:** numeric traits with `+`/`*`/zero/one, or
  profile-gated operator constraints; at minimum reword MNE120 for
  generic operands ("arithmetic over a type parameter requires a
  numeric constraint, which profiles ≤ 0.16 do not offer").
- **Regression test:** committed `sum_i32`/`dot_i32` cases (the
  duplication exhibit) + the P-009 compile repro.
- **Depends on:** none (traits are the missing feature, not a bug).

## P-010 — No float vectors

- **Severity:** expressiveness blocker. **Status:** confirmed, worked around.
- **Affects:** lane/predicated float kernels.
- **Repro:** `repros/P-010-float-vectors/repro.mncs` —
  `vec<f64, 4>` parameter.
- **Expected:** float lanes with `vec_*` operations, or a roadmap
  diagnostic.
- **Actual:** `MNE105` (only integer `vec<T, N>`/`mask<N>`) +
  downstream `MNE206`. Integer vectors work (used in `l2_squared4`
  style code); float lanes do not exist at any level: no type, no
  construction, no arithmetic, no `vec_min`/`vec_max`/`select` blend.
- **Why it matters:** branchless float selection, masked updates, and
  short-vector float math must be spelled as scalar branches or
  sequence traversals instead. The sequence kernels in this repo prove
  the semantics are expressible; only the lane/predication vocabulary
  is missing.
- **Workaround:** `[f64; N]` sequences + `select` (done throughout).
  Cost: no lane parallelism vocabulary; predication is manual.
- **Direction:** admit float element types in `vec<T, N>` with lane-wise
  trap-rule semantics matching scalar floats.
- **Regression test:** the P-010 compile repro.
- **Depends on:** none. Related to P-001 (float lane storage).

## P-011 — Stale profile docs over-claim limits

- **Severity:** tooling/docs. **Status:** confirmed (against
  `mncs-language` docs, not its code).
- **Affects:** library design decisions made from docs alone.
- **Evidence:**
  - `docs/source-profile-0.12.md` §"Binary64…": "Mixed int/float
    arithmetic, float sequences/vectors, and checked float arithmetic
    stay refused". Re-run 2026-09-12: float sequences (params,
    traversal, generics, views, nesting, corpus boundary) execute on
    ALL FIVE backends; only `vec<f64,_>` (P-010) and float-`replace`
    construction (P-001) still refuse. The doc's blanket claim
    misdirected early design toward scalar-only float APIs.
  - `docs/source-profile-0.5.md` backend matrix: records
    "UNSUPPORTED" on LLVM/C11/Cranelift and intra-function-only on
    WASM. Re-run: record params/results between in-module functions
    AND record returns to the host execute on all five backends
    (probes 12–13; committed `quadratic` record cases pass
    everywhere).
  - `lower.rs` still comments "Float sequences stay refused in C1"
    above code paths that now accept them.
- **Why it matters:** stale refusals are as costly as real ones while
  believed (entire API families get designed around them), and stale
  permissions erode trust in the matrices that remain accurate.
- **Workaround:** this repository probes every claimed limit before
  designing around it; results above are the current ground truth.
- **Direction:** regenerate (or version-stamp) the per-profile
  capability matrices from passing backend tests rather than
  hand-editing; mark 0.12-era float paragraphs superseded.
- **Regression test:** this repository's suites ARE the regression
  tests for the lifted limits.
- **Depends on:** none.

## P-012 — No correctly-rounded FMA

- **Severity:** accuracy note. **Status:** confirmed absence.
- **Affects:** `matmul` cells, `dot`, `quadratic` discriminant —
  anywhere `a * b + c` appears.
- **Evidence:** the float intrinsic inventory is `sin`/`cos` only
  (Profile 0.12 gate); `a +% b` on floats is refused (MNE248), and no
  `fma` spelling exists. Every fused computation in `src/` therefore
  rounds twice. No repro file: absence of a spelling is established
  by the inventory, and double-rounding is IEEE-standard behavior,
  not a bug.
- **Why it matters (bounded):** dot-product/matmul accuracy and the
  `b * b - 4 * a * c` discriminant would each save a rounding with
  FMA; wider compensated algorithms (e.g. 2Prod-based summation)
  NEED an exact-product primitive to reach their published error
  bounds — without FMA or `two_prod`, error-free transformations are
  inexpressible. Filed as a note, not a blocker: the v1 library is
  correct without it, merely less accurate than hardware allows.
- **Workaround:** none offered deliberately: an `fma(a,b,c)` spelled
  as `a*b+c` would pretend single-rounding. The gap stays visible.
- **Direction:** an `fma(x, y, z)` intrinsic with the trap rule, or
  `two_prod`/`two_sum` error-free-transformation primitives.
- **Depends on:** none.

## P-013 — No callable values/closures for elementwise kernels

- **Severity:** expressiveness (acknowledged constraint).
  **Status:** confirmed; documented non-goal in Profile 0.13
  ("unrestricted callable values … out of scope").
- **Affects:** `vec_float_build.mncs` — `scaled`/`add`/`sub`/
  `mul_elem`/`axpy`/`abs_elem`/`clamped_elem` are seven near-identical
  traversals differing in one lane expression.
- **Why it is filed anyway:** the cost is measurable in-repo
  (7× ~7 lines + 7× corpus coverage for one traversal shape), and a
  future `map<N>(xs, f)` would collapse it. The report asks for no
  surprise: when callable values land, this module is the first
  consumer and its duplication is the migration checklist.
- **Workaround:** concrete kernels per operation (done). No
  higher-order vocabulary is invented in-library.
- **Depends on:** none.

## P-014 — Loop lowering is vectorization-hostile

- **Severity:** performance issue. **Status:** confirmed (observed
  artifacts, one compiler profile).
- **Affects:** every hot loop (`dot`, `sum`, `axpy`, `matvec`,
  `matmul` cells, Newton iterations).
- **Repro:** `repros/P-014-loop-lowering/` — a 4-lane float dot
  product plus the compiler's own emitted C11 and LLVM IR for it
  (regenerate: `experiment run repro.mncs --backend <be> --corpus
  <empty-corpus> --output-dir DIR`).
- **Expected:** a well-structured bounded traversal lowers to a
  countable loop over plain lane loads that downstream optimizers
  (clang -O2, LLVM loop-vectorize) can reason about.
- **Actual:**
  - C11: `for (;;) switch (mncs_pc)` state machine; per-lane opaque
    `mncs_slot_load64(mncs_arena, …)` calls (no alias information);
    finite checks as `(v - v) == 0.0` self-subtractions per operand
    and per result. No C auto-vectorizer handles this shape.
  - LLVM IR: real CFG with plain GEP lane loads, but two
    arena-guard fail branches plus six `fsub`-self + `fcmp`-to-fail
    edges per lane, and every value round-tripping through `alloca`
    slots. Per-lane fail edges block loop vectorization without
    predication the vectorizer will not invent.
- **Why it matters:** numerical loops live or die by vectorization.
  The trap rule's checks are semantically required, but their
  current density (six check-branches per lane for one
  multiply-add) and placement (fail edges inside the lane body, not
  hoisted speculations) plus opaque addressing on the C11 path mean
  ordinary MNCS numerical code cannot reach lane parallelism no
  matter how cleanly it is written. This was NOT worked around: no
  benchmark was hand-tuned, and `docs/BENCHMARKS.md` reports
  compiler-dominated wall times honestly.
- **Workaround:** none in-library. The module split (P-001) at least
  keeps reductions compiling on LLVM where the IR shape is
  comparatively cleaner.
- **Direction:** canonicalize bounded traversals to countable loops
  before emission; hoist loop-invariant bounds/finite guards where
  the bound analysis permits; prefer a single `isnan`-style check
  over repeated self-subtraction; document which optimization levels
  (if any) recover vectorization.
- **Regression test:** re-emit the P-014 exhibits after backend work
  and diff the lane body; benchmark steps/wall for `dot_256`
  (committed harness) should move, not just the IR text.
- **Depends on:** none. Related to P-001 (which backend can even run
  the loop) and P-010 (no lane vocabulary to bypass scalar loops).
