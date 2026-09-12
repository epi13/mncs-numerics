# P-003 — No fill for symbolic bounds

Full report: `docs/LANGUAGE_PRESSURES.md#P-003`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-003-symbolic-fill/repro.mncs --node-id repro
```

`return [x; N];` for symbolic `N` is refused at parse time:
`MNP203: expected repeat count after ';'` (plus MNP016/MNP017/MNP006/
MNP007 cascade that names everything except the real rule: repeat
counts must be literals). Library workaround: seeded construction
(`*_into`, `broadcast_like`, `zeros_like` in
`src/numerics/vec_float_build.mncs` and `mat_float_build.mncs`).
