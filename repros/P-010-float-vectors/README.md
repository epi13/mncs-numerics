# P-010 — No float vectors

Full report: `docs/LANGUAGE_PRESSURES.md#P-010`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-010-float-vectors/repro.mncs --node-id repro
```

A `vec<f64, 4>` parameter fails with `MNE105` (integer lanes only)
plus downstream `MNE206`. There is no float lane type, no float lane
construction, and no float lane arithmetic/mask vocabulary anywhere.
Library workaround: `[f64; N]` sequences + `select` (all of
`src/numerics/vec_float_*.mncs`).
