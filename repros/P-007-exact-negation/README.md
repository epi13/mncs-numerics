# P-007 — No exact negation

Full report: `docs/LANGUAGE_PRESSURES.md#P-007`.

No repro binary: the behavior is pinned by committed corpus case
`f-fneg-v-1` (`fneg(+0.0)` expects `+0.0`, i.e. bits `0x0000000000000000`).
`fneg` is necessarily spelled `0.0 - x`, and `0.0 - 0.0 == +0.0`
while IEEE `-(+0.0) == -0.0`. No available operation produces `-0.0`
from `+0.0` without trapping, so exact negation is inexpressible.
When a `neg` intrinsic (or unary `-x`) lands, update that corpus case
to `-0.0` and close this pressure.
