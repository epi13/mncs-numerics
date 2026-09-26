# P-019 — Nat arguments are not inferred from sequence literals

Full report: `docs/LANGUAGE_PRESSURES.md#P-019`.

```bash
export MNCS_LIBRARY_PATH=$PWD/src
cargo run -q -p mncs-cli -- source-study repros/P-019-literal-generic-inference/repro.mncs --node-id probe
```

(run the CLI from the `mncs-language` directory.)

`take_sum([1.0, 2.0], 1)` — a literal whose length (2) determines the
only Nat argument — is refused with one precise diagnostic:

```text
MNE183 | sequence literals require an exact or bounded-view sequence expected type
```

The literal is checked before generic-argument inference runs, so the
call never gets the chance to infer `N = 2` from the two lanes. The
workaround is a typed binding first (`let xs: [f64; 2] = [1.0, 2.0];`
then `take_sum(xs, 1)`), which is what every call site in
`tests/native/*.mncs` does. Cost: one named binding per literal at
every generic call site, including inside tests.

Relation to neighboring pressures: P-018 is inference not flowing
through `up_to` view bounds (explicit `<N>` kept); this is the dual —
inference not flowing *from* a literal *into* a Nat parameter. Fixing
either narrows the other: literal-length inference would subsume the
common `take_sum`/reduction call shapes, while view-bound inference
covers the callee side.
