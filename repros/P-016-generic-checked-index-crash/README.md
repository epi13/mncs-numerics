# P-016 — Generic `checked_index` panics four backends

Full report: `docs/LANGUAGE_PRESSURES.md#P-016`.

`repro.mncs` sums `[10.0, 20.0, 30.0]` through the permutation
`[2, 0, 1]` with one `checked_index` per lane; `corpus.json` calls
`gather_sum<3>` and expects `60.0` back.

```bash
export MNCS_LIBRARY_PATH=$PWD/src   # run from the repo root, CLI in mncs-language/
cargo run -q -p mncs-cli -- experiment run repros/P-016-generic-checked-index-crash/repro.mncs \
  --backend mncs-c11 --corpus repros/P-016-generic-checked-index-crash/corpus.json
```

The CLI process dies instead of answering: `internal error:
entered unreachable code: generic SequenceBound must be specialized
before backend lowering` — at `crates/mncs-codegen/src/c11.rs:1692`
(C11), `lower.rs:2927` (WASM), `llvm.rs:1979` (LLVM),
`cranelift_backend.rs:1414` (Cranelift). Only
`mncs-research-bytecode` lowers the operation (returns `60.0`,
correct). P-006-class crash: a fuzzer, a REPL typo, or a stale
corpus kills the compiler process instead of receiving a refusal.

No library workaround exists that keeps the checked-index
discharge: any `checked_index` over a symbolic-bound sequence
crashes the four backends even for a pure read, so gather/permute
kernels stay out of `src/` until the repair lands. The language's
own `pressure-checked-index` example covers concrete bounds only,
which is why the generic shape was never exercised.
