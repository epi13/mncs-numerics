# P-007 — No exact negation

Full report: `docs/LANGUAGE_PRESSURES.md#P-007`.

**RESOLVED (2026-09-12):** the `neg(x)` intrinsic landed (Profile
0.12) — exact IEEE-754 negation on every backend, `fneg` redefined
as `neg(x)`, and `f-fneg-v-1` now expects `-0.0` (bits
`0x8000000000000000`). Was: `fneg` spelled `0.0 - x`, so
`fneg(+0.0)` was `+0.0` — a one-bit deviation, pinned, not hidden.
Kept as a record.
