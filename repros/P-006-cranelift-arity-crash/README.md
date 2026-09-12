# P-006 — Cranelift SIGSEGV on arity-mismatched execution request

Full report: `docs/LANGUAGE_PRESSURES.md#P-006`.

`repro.mncs` is a two-argument `f64` minimum; `corpus.json` calls it
with ONE argument.

```bash
cargo run -q -p mncs-cli -- experiment run repros/P-006-cranelift-arity-crash/repro.mncs \
  --backend mncs-cranelift --corpus repros/P-006-cranelift-arity-crash/corpus.json
echo "exit: $?"
```

Expected: `invalid_request` (bytecode/WASM/C11/LLVM all return one).
Actual: SIGSEGV, exit 139, empty stdout. Bisected from a 150-case
corpus; NaN inputs were suspected and exonerated (correct-arity NaN
is fine — the original bad-arity cases happened to carry NaN).
