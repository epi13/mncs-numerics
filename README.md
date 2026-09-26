# mncs-numerics

Foundational numerical computing in MNCS, built to be depended upon —
and built in a way that pressures the language into revealing what it
cannot yet express.

`mncs-numerics` is a real numerical library written in MNCS (scalars,
generic reductions, guarded/masked reductions, elementwise kernels,
rotation, small and generic matrices, stability showcases) together
with the adversarial harness that executes it: a deterministic
Python oracle generates 418 execution cases, and
`scripts/run_tests.py` runs every suite on all five compiler
backends with no refusal pins. A second, native verification path
runs in-language contracts through `mncs test` (mncs-test):
`tests/native/` holds Profile 0.18 `test` declarations over the
0.16 library, executed by `scripts/run_native_tests.py`. When the
language cannot express a reasonable API, the gap is filed as a
pressure report with a minimal reproducer
(`docs/LANGUAGE_PRESSURES.md`, `repros/`), worked around narrowly,
and never hidden.

Numeric owns foundational representation-level contracts (integer
intents, the float trap rule, conversions, bounds, reductions,
construction, matrix representation); higher-level mathematics
lives in `mncs-math`. See `docs/NUMERIC_MATH_BOUNDARY.md`.

## Layout

- `src/numerics/` — the library (`.mncs` only, no host numerics)
- `tests/corpora/` — committed deterministic execution corpora
- `tests/native/` — in-language contracts via `mncs test` (21 int + 36 float `test` declarations)
- `tests/drivers/` — nullary property programs (P-002 multi-param seeding wrappers retired)
- `examples/` — consumer-integration programs (also executed)
- `benches/` + `scripts/bench.py` — steps + wall-clock harness
- `scripts/` — oracle (`gen_corpora.py`), runners (`run_tests.py`, `run_native_tests.py`), shared lib
- `repros/` — minimal pressure reproducers
- `docs/` — architecture, numerical semantics, pressure ledger, benchmarks, Numeric/Math boundary, RFC

## Quick start

Requires an `mncs-language` checkout (sibling `../mncs-language` by
default, or set `MNCS_LANGUAGE_DIR`; a prebuilt CLI binary is used
when present, else `cargo run`). Native tests additionally resolve
`mncs-test/native` (sibling `../mncs-test` by default).

```bash
python3 scripts/gen_corpora.py              # regenerate corpora from the oracle
python3 scripts/run_tests.py                # full suite x all backends
python3 scripts/run_tests.py --backends mncs-research-bytecode   # fast loop
python3 scripts/run_tests.py --suites scalar_float
python3 scripts/run_native_tests.py         # in-language contracts via mncs test
python3 scripts/bench.py --backends mncs-research-bytecode --kernels bench_sum_256
```

`MNCS_LIBRARY_PATH` is set to `src/` by the runners; set it yourself
for direct CLI use (the library resolves as `mncs.numerics.*`).

## Verification paths

| Path | Runner | What it proves |
|------|--------|----------------|
| Corpus bit-exactness | `scripts/run_tests.py` | 418 committed cases green on all five backends; every trap pinned as `runtime_failure` |
| Native contracts | `scripts/run_native_tests.py` | 57 in-language `test` declarations (boundaries, enums, conversions, operator semantics, generative properties) via `mncs test` |

A `test` declaration cannot express an expected trap, so trap
coverage stays in the corpora by design; bit-level float checks
(signed zeros, NaN policy) stay there too, since the assertion
vocabulary is i64/bool. The native suites instead pin behaviors the
corpora never covered: shift semantics, negative division
truncation, remainder signs, the 2^53 conversion boundary, and
min/max duality properties.

## Status

v1 library: integer + float scalars, generic int/float reductions,
guarded (masked) reductions, elementwise construction, rotation,
2x2/3x3 + generic MxN matrices, four examples — 418 committed cases
green on all five backends with no refusal pins, plus 57 native
contract tests green via `mncs test`. Nineteen language pressures
filed. P-001 (float construction on LLVM/WASM), P-002 (host
multi-param seeding), and P-006 (Cranelift arity crash) are
repaired; the P-002 driver wrappers are retired. Earlier additions:
`vec_float_mask` (lazy-match guarded kernels), `rotate_left`,
generic-argument inference at ~35 call sites, and pressures P-015
(generic `copy_span`), P-016 (generic `checked_index` backend
panic), P-017 (no `exp`/`log`), P-018 (inference through view
bounds). New in this campaign: the native contract suites, pressure
P-019 (Nat inference from literals), and `docs/NUMERIC_MATH_BOUNDARY.md`.

See `docs/ARCHITECTURE.md`, `docs/NUMERICAL_SEMANTICS.md`,
`docs/LANGUAGE_PRESSURES.md`, `docs/BENCHMARKS.md`,
`docs/NUMERIC_MATH_BOUNDARY.md`.
