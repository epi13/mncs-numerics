# mncs-numerics

Adversarial numerical correctness and reproducibility infrastructure for MNCS.

`mncs-numerics` is not primarily a broad math library. It is the torture harness that asks whether MNCS-language, its compiler, runtime, CPU backends, and CUDA backends preserve declared numerical semantics under difficult workloads.

## Initial scope

- IEEE-754 edge-case corpus
- ULP/tolerance comparison tools
- cancellation, conditioning and loss-of-significance cases
- deterministic/reordered reductions
- stiff and chaotic numerical workloads
- cross-optimization and cross-backend comparison
- high-precision/reference-oracle integration
- evidence and regression artifacts

## Repository layout

- `docs/ARCHITECTURE.md`
- `docs/rfcs/0001-foundation.md`
- `docs/LANGUAGE_PRESSURES.md`
- `AGENTS.md`
