# P-002 — Host seeding drops repeated generic spellings

Full report: `docs/LANGUAGE_PRESSURES.md#P-002`.

`repro.mncs` is `matvec_into<M, N>` (two Nat params); `corpus.json`
names `(2, 2)` via `type_arguments` and expects `[17.0, 39.0]`.

```bash
cargo run -q -p mncs-cli -- experiment run repros/P-002-host-multi-generic/repro.mncs \
  --backend mncs-research-bytecode --corpus repros/P-002-host-multi-generic/corpus.json
```

Bytecode resolves through `canonical_args` (`value:2|value:2`) and
passes. Native artifacts resolve through `args_spellings`, which the
seed merge records as `["2"]` (`sort`+`dedup` in
`mncs-model/src/generics.rs` collapses the positional pair), so every
native backend reports `no compiled specialization ... (2, 2);
compiled instantiations: [(2)]`. In-language `matvec_into<2, 2>`
works everywhere. Library workaround: `tests/drivers/`.
