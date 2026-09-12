# P-008 — Integer literals do not adapt to `f64`

Full report: `docs/LANGUAGE_PRESSURES.md#P-008`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-008-float-literal-adaptation/repro.mncs --node-id repro
```

`xs[i] * 2` over `[f64; N]` fails with `MNE118: integer literal
cannot satisfy a non-integer type` + `MNE119`. Integer literals adapt
symmetrically across int widths (Profile 0.6) but never to `f64`, so
every whole-number float constant in `src/` spells its `.0`.
