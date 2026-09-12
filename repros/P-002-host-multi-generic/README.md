# P-002 — Host seeding drops repeated generic spellings

Full report: `docs/LANGUAGE_PRESSURES.md#P-002`.

`repro.mncs` is `matvec_into<M, N>` (two Nat params); `corpus.json`
names `(2, 2)` (expects `[17.0, 39.0]`) and `(3, 2)` (expects
`[23.0, 53.0, 83.0]`) via `type_arguments`.

```bash
cargo run -q -p mncs-cli -- experiment run repros/P-002-host-multi-generic/repro.mncs \
  --backend mncs-research-bytecode --corpus repros/P-002-host-multi-generic/corpus.json
```

Bytecode resolves through `canonical_args` and passes both cases.
Native artifacts resolve through `args_spellings`, which the seed
merge mangles (`sort`+`dedup` in `mncs-model/src/generics.rs`
treats positional arguments as a set): on C11 the two cases report
`compiled instantiations: [(2), (2, 3)]` — `(2, 2)` collapsed by
dedup, `(3, 2)` reordered by sort. In-language `matvec_into<2, 2>`
works everywhere. Library workaround: `tests/drivers/`.
