# P-018 — Inference does not flow through view bounds

Full report: `docs/LANGUAGE_PRESSURES.md#P-018`.

`repro.mncs` defines `vsum<N>` over `[f64; up_to N]` and calls it
from `vmean<N>` without explicit arguments:

```bash
cargo run -q -p mncs-cli -- source-study repros/P-018-inference-view-bounds/repro.mncs --node-id repro
```

The call fails with `MNE220: generic function 'vsum' requires 1
generic argument(s); cannot infer N; supply explicit <...>`, even
though `N` is in scope and the argument carries it. Constraints
flow through exact sequence structure and direct generic positions,
but not through `up_to` capacity bounds.

Library workaround: the one affected call site
(`mean_view` → `sum_view<N>` in
`src/numerics/vec_float_reduce.mncs`) keeps its explicit `<N>`,
labeled in-source. Every other call site in the library migrates to
inferred arguments; this is the only one that cannot.
