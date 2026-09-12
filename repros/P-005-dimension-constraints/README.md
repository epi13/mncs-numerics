# P-005 — No dimension-equality constraints

Full report: `docs/LANGUAGE_PRESSURES.md#P-005`.

`repro.mncs` calls the library's `trace_g<2, 3>` on a 2x3 matrix;
`corpus.json` expects the silent partial `6.0` (= m[0][0] + m[1][1]).

```bash
export MNCS_LIBRARY_PATH=$PWD/src
cargo run -q -p mncs-cli -- experiment run repros/P-005-dimension-constraints/repro.mncs \
  --backend mncs-research-bytecode --corpus repros/P-005-dimension-constraints/corpus.json
```

There is no spelling for "M == N", so squareness is a doc comment and
wide inputs silently sum a diagonal prefix. (Tall inputs trap
fail-closed; only the wide case is silent.) If the language ever
gains dimension constraints, this corpus must be rewritten to expect
a refusal.
