# P-006 — Cranelift SIGSEGV on arity-mismatched execution request

Full report: `docs/LANGUAGE_PRESSURES.md#P-006`.

`repro.mncs` is a two-argument `f64` minimum; `corpus.json` calls it
with ONE argument.

```bash
cargo run -q -p mncs-cli -- experiment run repros/P-006-cranelift-arity-crash/repro.mncs \
  --backend mncs-cranelift --corpus repros/P-006-cranelift-arity-crash/corpus.json
echo "exit: $?"
```

**RESOLVED (2026-09-12).** Expected: `invalid_request` on all five
backends. Was: SIGSEGV, exit 139, empty stdout on Cranelift only
(bisected from a 150-case corpus; NaN inputs were suspected and
exonerated — correct-arity NaN is fine). The audit also found the
C11/LLVM retained-session paths (and C11 one-shot) missing the gate:
extra arguments were silently ignored there. All native paths now
refuse with one shared value-contract message; kept as a
reproducer.
