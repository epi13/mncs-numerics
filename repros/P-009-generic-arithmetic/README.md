# P-009 — No generic numeric arithmetic

Full report: `docs/LANGUAGE_PRESSURES.md#P-009`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-009-generic-arithmetic/repro.mncs --node-id repro
```

`+`/`*` over a type parameter `T` fails with `MNE120: arithmetic
operands must have an integer type` — misleading twice over (`f64`
supports both operators; the missing piece is a constraint system,
not an integer operand). The `MNE102` on the carried binding is pure
cascade. Library workaround: per-width duplication (`sum_i32`/
`dot_i32` in `src/numerics/vec_int.mncs` are line-for-line copies kept
to measure the cost).
