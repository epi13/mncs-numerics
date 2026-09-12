# P-002 — Host seeding drops repeated generic spellings

Full report: `docs/LANGUAGE_PRESSURES.md#P-002`.

`repro.mncs` is `matvec_into<M, N>` (two Nat params); `corpus.json`
names `(2, 2)` (expects `[17.0, 39.0]`) and `(3, 2)` (expects
`[23.0, 53.0, 83.0]`) via `type_arguments`.

```bash
cargo run -q -p mncs-cli -- experiment run repros/P-002-host-multi-generic/repro.mncs \
  --backend mncs-research-bytecode --corpus repros/P-002-host-multi-generic/corpus.json
```

**RESOLVED (2026-09-12).** Native artifacts resolve through
`args_spellings`, which the seed merge used to mangle (`sort`+`dedup`
in `mncs-model/src/generics.rs` treated positional arguments as a
set): on C11 the two cases reported `compiled instantiations: [(2),
(2, 3)]` — `(2, 2)` collapsed by dedup, `(3, 2)` reordered by sort.
The language repair keeps positional spelling addresses whole
(first-seen order, unioned per instantiation), so both cases now
return on bytecode/C11/Cranelift. LLVM/WASM still fail this repro,
but with the honest P-001 construction symptoms (LLVM float-`replace`
miscompile, WASM float-`replace` refusal) — mis-addressing is gone.
Library workaround (`tests/drivers/`) retired; `mat_float` corpora
name multi-param instantiations directly.

Kept as a reproducer: on the repaired toolchain the addressing half
passes wherever P-001 permits construction.
