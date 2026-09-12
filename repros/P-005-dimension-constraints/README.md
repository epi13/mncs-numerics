# P-005 — No dimension-equality constraints → RESOLVED (structural)

Full report: `docs/LANGUAGE_PRESSURES.md#P-005`.

`repro.mncs` calls the library's `trace_g<2, 3>` on a 2x3 matrix.
Before the fix this elaborated and silently returned the partial
diagonal `6.0` (= m[0][0] + m[1][1]). `trace_g` now takes a single
Nat parameter `N` naming both dimensions, so the seed is refused at
elaboration:

```bash
export MNCS_LIBRARY_PATH=$PWD/src
cargo run -q -p mncs-cli -- source-study repros/P-005-dimension-constraints/repro.mncs
# MNE221 | generic argument count mismatch for 'trace_g': expected 1, got 2
```

The stale `corpus.json` (which pinned the silent `6.0`) was removed;
a compile refusal has no experiment-run status vocabulary. The
positive path is pinned by the `g-trace-2x2`/`g-trace-3x3` cases in
`tests/corpora/mat_float.json` (single-argument seeds, green on all
five backends), and the arity refusal itself is pinned in the
language repo by `crates/mncs-compiler/tests/module_imports.rs`
(`count` → MNE221).

General dimension-arithmetic constraints (`M == N` as a bound) remain
open language design; this pressure is closed for `trace_g` by
making squareness structural.
