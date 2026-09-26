# Numeric vs Math ownership boundary

Record of what `mncs-numerics` owns, what `mncs-math` owns, and where
the two currently overlap. Sources: the Atlas capability registry
(`mncs-atlas/registry/capability-claims.json`), the in-repository
manifest (`.mncs/project.json`), and read-only inspection of the
`mncs-math` tree at `cb1d32b` (wave-2 science push, under active
development — not modified by this campaign).

## Registry position

- `numeric-primitives` — **exclusive**, `mncs-numerics` is the
  canonical authority. Covers reusable numeric types, arithmetic
  kernels, reductions, masks, and bounded numeric operations.
  `mncs-math`, `mncs-geometry`, `mncs-physics`, and `mncs-signal`
  are registered as consumers.
- `numeric-algorithms` — **shared**, both `mncs-numerics` and
  `mncs-math` are primary implementations. The registry note is
  explicit: math owns broader scientific mathematics **built over**
  numeric primitives.

## What Numeric owns

Foundational, representation-level concerns with machine-checked
contracts in this repository:

- integer families (`i64`, `i32`, `u64`) and their checked /
  wrapping / saturating operator intents;
- the single float type (`f64`) and the trap rule (non-finite
  input/result fails closed);
- ranges, bounds, signedness, min/max/clamp, sign;
- conversions: widening, narrowing, truncation, exact vs inexact
  (including the 2^53 exactness boundary), float/int casts;
- overflow/underflow behavior: checked traps vs total intents;
- outcome enums for foreseeable domain edges (`DivByZero`,
  `Empty`, `ZeroNorm`, `DomainError`, `Singular`, `ExpTooLarge`);
- generic numeric traversal and construction over bounded sequences
  and views (reductions, masked reductions, elementwise builds,
  rotation, prefix);
- flat small matrices (2x2/3x3) and nested generic MxN containers
  as *representation* (layout, trace/det/matvec/matmul/transpose/
  diag, Cramer 2x2 solve);
- tolerance-comparison vocabulary (`approx_abs`, `approx_rel`,
  `approx`) as consumer API;
- the numerical contract itself (`docs/NUMERICAL_SEMANTICS.md`)
  and its two verification paths (corpus bit-exactness across five
  backends; native in-language contracts via `mncs test`).

## What Math owns instead

Everything in `mncs-math/src/math/`, built over (not beside) the
layer above: exact integer/rational/fixed-point tiers, bigint,
complex, vectors/matrices/linalg through 6x6, tensors, interval
arithmetic, dual-number autodiff, deterministic randomness,
statistics with covariance, optimization, modular arithmetic/NTT,
sparse structures, ODE solvers, transcendental `float`/`poly`
function tiers. In particular `exp`/`log`/trig beyond the shared-libm
`rot2` helper, decompositions, solvers with pivoting, FFTs, and
special functions are Math's — Numeric deliberately withholds them
(see "deliberately absent" in `docs/ARCHITECTURE.md` and pressure
P-017).

## Known overlap (coordination pressure, not a migration)

`mncs-math` currently carries its own foundational tiers
(`scalar`, `float`, `vector`, `matrix`, `statistics`,
`numerical`) that intersect Numeric's primitive ground. That
duplication dates to Math's independent wave campaigns, which are
still running. Direction of travel per the registry: Math's
higher tiers should consume Numeric primitives where the contracts
match, and the two repositories should not grow a second
authoritative checked-arithmetic or conversion contract.

No cross-repository migration is attempted in this campaign: Math
is read-only for us and mid-campaign. The coordination item is
recorded in the pressure ledger so a future joint pass can dedupe
without either side breaking mid-flight.

## Consumer rule for future agents

- Need a machine-representation contract (checked arithmetic,
  conversion, bounds, reductions, trap behavior)? Use or extend
  `mncs.numerics.*` here.
- Need a mathematical method (a solver, a transform, a
  distribution, an optimizer)? It belongs in `mncs-math`.
- Tempted to add a second implementation of something the other
  repository already contracts? Stop and file a coordination
  pressure instead.
