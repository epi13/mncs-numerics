# mncs-numerics

Foundational numerical computing in MNCS, built to be depended upon —
and built in a way that pressures the language into revealing what it
cannot yet express.

`mncs-numerics` is a real numerical library written in MNCS (scalars,
generic reductions, elementwise kernels, small and generic matrices,
stability showcases) together with the adversarial harness that
executes it: a deterministic Python oracle generates 384 execution
cases, and `scripts/run_tests.py` runs every suite on all five
compiler backends with a pinned refusal matrix. When the language
cannot express a reasonable API, the gap is filed as a pressure
report with a minimal reproducer (`docs/LANGUAGE_PRESSURES.md`,
`repros/`), worked around narrowly, and never hidden.

## Layout

- `src/numerics/` — the library (`.mncs` only, no host numerics)
- `tests/corpora/` — committed deterministic execution corpora
- `tests/drivers/` — in-language wrappers for multi-param generics (P-002)
- `examples/` — consumer-integration programs (also executed)
- `benches/` + `scripts/bench.py` — steps + wall-clock harness
- `scripts/` — oracle (`gen_corpora.py`), runner (`run_tests.py`), shared lib
- `repros/` — minimal pressure reproducers
- `docs/` — architecture, numerical semantics, pressure ledger, benchmarks, RFC

## Quick start

Requires an `mncs-language` checkout (sibling `../mncs-language` by
default, or set `MNCS_LANGUAGE_DIR`; a prebuilt CLI binary is used
when present, else `cargo run`).

```bash
python3 scripts/gen_corpora.py              # regenerate corpora from the oracle
python3 scripts/run_tests.py                # full suite x all backends
python3 scripts/run_tests.py --backends mncs-research-bytecode   # fast loop
python3 scripts/run_tests.py --suites scalar_float
python3 scripts/bench.py --backends mncs-research-bytecode --kernels bench_sum_256
```

`MNCS_LIBRARY_PATH` is set to `src/` by the runners; set it yourself
for direct CLI use (the library resolves as `mncs.numerics.*`).

## Status

v1 library: integer + float scalars, generic int/float reductions,
elementwise construction, 2x2/3x3 + generic MxN matrices, four
examples — 384 committed cases green on all backends except the
P-001 construction envelope (LLVM miscompile, WASM honest refusal),
which is pinned as confirmed refusals, not passes. Thirteen language
pressures filed, two of them correctness blockers (P-001, P-006).

See `docs/ARCHITECTURE.md`, `docs/NUMERICAL_SEMANTICS.md`,
`docs/LANGUAGE_PRESSURES.md`, `docs/BENCHMARKS.md`.
