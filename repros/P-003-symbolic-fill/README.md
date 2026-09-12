# P-003 — No fill for symbolic bounds (diagnostic half resolved)

Full report: `docs/LANGUAGE_PRESSURES.md#P-003`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-003-symbolic-fill/repro.mncs --node-id repro
```

`return [x; N];` for symbolic `N` is refused with a single precise
diagnostic (language repair 2026-09-12):

```text
MNE256 | symbolic repeat count `N` is not supported; repeat counts must be Nat literals
```

Before the repair this was a parse refusal (`MNP203: expected
repeat count after ';'`) plus an MNP016/MNP017/MNP006/MNP007 cascade
that named everything except the real rule. The parser now carries a
bare-identifier count through (so the `]` still parses, no cascade)
and elaboration checks the count text before the expected-type check,
naming the Nat-literal rule once. The fill feature itself (symbolic
`[x; N]` materialization) remains open language design — it needs
runtime dynamic fill on every construction-capable backend.

Library workaround (unchanged): seeded construction (`*_into`,
`broadcast_like`, `zeros_like` in `src/numerics/vec_float_build.mncs`
and `mat_float_build.mncs`).
