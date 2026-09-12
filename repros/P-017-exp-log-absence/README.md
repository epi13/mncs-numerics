# P-017 — No `exp`/`log`/real-power intrinsics

Full report: `docs/LANGUAGE_PRESSURES.md#P-017`.

`repro.mncs` spells the softplus `log(1.0 + exp(x))`:

```bash
cargo run -q -p mncs-cli -- source-study repros/P-017-exp-log-absence/repro.mncs --node-id repro
```

Both calls fail with `MNE131: call target does not resolve to a
function in this module`: the float intrinsic inventory is
`sin`/`cos`/`neg` only. No `exp`, no `log`, no real `pow`, no
spelling for any of them.

Why it matters: an entire numerical family is inexpressible —
softmax, log-sum-exp, cross-entropy, Gaussian densities, geometric
means, any likelihood. The statistics/logistic examples in this
repository stop exactly where exponentiation starts. A Taylor-series
`exp` hand-roll was considered and rejected: without `ldexp`/`frexp`
range reduction is crude, and the error analysis for a correctly
rounded argument reduction needs exactly the error-free
transformations that are also absent (pressure P-012) — the
workaround would pretend a rigor the language cannot back.
