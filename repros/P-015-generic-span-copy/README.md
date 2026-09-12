# P-015 — `copy_span` refuses symbolic-bound destinations

Full report: `docs/LANGUAGE_PRESSURES.md#P-015`.

`repro.mncs` rotates `[1.0, 2.0, 3.0, 4.0]` left by one with two
chained `copy_span` calls; `corpus.json` expects `[2.0, 3.0, 4.0,
1.0]` back from `rot_sym<4>`.

```bash
export MNCS_LIBRARY_PATH=$PWD/src   # run from the repo root, CLI in mncs-language/
cargo run -q -p mncs-cli -- experiment run repros/P-015-generic-span-copy/repro.mncs \
  --backend mncs-research-bytecode --corpus repros/P-015-generic-span-copy/corpus.json
```

Elaboration fails with `MNB142: functional span copy requires an
exact-bound destination; views refuse` (plus `MNB146`/`MNB147`/
`MNB148` on the instantiation): the `[f64; N]` destination counts as
a view while `N` is symbolic, even though the identical value accepts
`replace` in the identical position. The concrete-bound spelling
(`[f64; 4]`, same positions, same self-copy shape) compiles and runs
bit-exact on all five backends — verified during reduction.

Library workaround: `rotate_left` in
`src/numerics/vec_float_build.mncs` spells the rotation as a
per-lane `replace` traversal with modular index arithmetic
(committed, all backends). Cost: the bulk move stays a lane loop;
only the slow path is open in generic code.
