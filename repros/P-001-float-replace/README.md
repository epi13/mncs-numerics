# P-001 — Float `SequenceReplace` miscompiled on LLVM, refused on WASM

Full report: `docs/LANGUAGE_PRESSURES.md#P-001`.

`repro.mncs` scales `[1.0, 2.0, 3.0, 4.0]` by 2.0 with `replace` in a
traversal; `corpus.json` expects `20.0` back from `demo`.

```bash
export MNCS_LIBRARY_PATH=$PWD/src   # run from the repo root, CLI in mncs-language/
cargo run -q -p mncs-cli -- experiment run repros/P-001-float-replace/repro.mncs \
  --backend mncs-llvm-ir --corpus repros/P-001-float-replace/corpus.json
```

- bytecode / C11 / Cranelift: `returned`, expectation met.
- WASM: per-entrypoint `CGN302` refusal (`float sequences are not supported`).
- LLVM: `clang failed: ... '%relem35_v9' defined with type 'double' but
  expected 'i64'`; the whole artifact (including unrelated entrypoints) is poisoned.
