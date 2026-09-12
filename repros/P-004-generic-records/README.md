# P-004 — No generic record declarations

Full report: `docs/LANGUAGE_PRESSURES.md#P-004`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-004-generic-records/repro.mncs --node-id repro
```

`record Box<N: Nat> { lane: [f64; N] }` (`repro.mncs`) is refused at
parse time: `MNP123: expected '{' after record name` (plus
MNP127/MNP128/MNP007 cascade). `enum Outcome<N: Nat> { ... }`
(`repro_enum.mncs`) fails likewise with `MNP072`. A traversal
carries one state value, so multi-scalar generic folds (e.g. generic
prefix sums) are inexpressible; the library ships concrete-width
records instead (`Pref` for `prefix4` in
`src/numerics/vec_float_build.mncs`), and `normalized` traps on zero
instead of returning a `ZeroNorm` outcome.
