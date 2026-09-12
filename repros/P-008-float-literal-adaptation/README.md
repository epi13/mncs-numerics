# P-008 — Integer literals do not adapt to `f64` → RESOLVED (migrated)

Full report: `docs/LANGUAGE_PRESSURES.md#P-008`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-008-float-literal-adaptation/repro.mncs --node-id repro
```

`xs[i] * 2` over `[f64; N]` now elaborates cleanly: the integer
literal `2` adapts to `f64` exactly (language repair 2026-09-12;
lossless below 2^53, refused beyond). The only remaining
diagnostics are `CMP301` unresolved-obligation notes (conservative
fallbacks the harness already accepts), not errors. Before the
repair this failed with `MNE118: integer literal cannot satisfy a
non-integer type` + `MNE119`.

Exponent notation (`1.5e3`, `1e-12`, `1e16`) parses with correct
rounding in the same repair tranche.

Migration: `src/` now uses the adapted spelling where it is
load-bearing — e.g. `(2 * a)` in `quadratic`
(`src/numerics/scalar_float.mncs`, pinned bit-identical to `2.0 * a`
by the committed corpus) — and the mat_float/scalar/reduce suites
exercise adaptation on all five backends (language-side
`pressure_literal_symmetry`: left/right-literal symmetry,
exact integer-to-float adaptation, non-adaptable mismatches still
refused via MNE119).
