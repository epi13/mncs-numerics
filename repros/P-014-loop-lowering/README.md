# P-014 — Loop lowering is vectorization-hostile

Full report: `docs/LANGUAGE_PRESSURES.md#P-014`.

`repro.mncs` is a 4-lane float dot product. The exhibits are the
compiler's own artifacts for it (regenerate with `experiment run
--output-dir`, any empty corpus):

- `dot4.c11.c` — the C11 translation unit: the traversal becomes a
  `for (;;) switch (mncs_pc)` state machine with per-lane opaque
  `mncs_slot_load64` calls and per-operand finite checks. No C
  compiler auto-vectorizes a switch-dispatched loop with opaque calls
  in the lane body.
- `dot4.module.ll` — the LLVM IR: a real CFG with plain GEP lane
  loads (better), but each lane still carries two arena-guard fail
  branches plus six `fsub`-self/`fcmp`-to-fail finite checks, and
  every value round-trips through `alloca` slots. Per-lane fail
  edges block loop vectorization absent predication support the
  vectorizer will not invent from this shape.

The finite checks are the documented trap-rule cost (correctness, not
waste); the report is about the SHAPE around them. Whether an
optimization pipeline canonicalizes any of this is untested (one
compiler profile in this run).
