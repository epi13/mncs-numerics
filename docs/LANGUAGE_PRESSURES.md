# MNCS language pressure ledger

Each item should include workload, observed behavior, expected contract, minimal reproducer, affected target/backend, likely owner, workaround and verification.

## Initial pressure targets

- strict IEEE behavior and documented deviations
- NaN payload/propagation policy
- signed zero and subnormal handling
- overflow/underflow semantics
- FMA and expression reassociation control
- deterministic reductions and parallel scheduling
- SIMD lane semantics
- CPU versus CUDA differences
- optimization-level reproducibility
- arbitrary/high precision interoperability
- interval/error-bound representations
- compile-time versus runtime numeric evaluation parity
- machine-readable compiler/backend numeric contracts

Passing a relaxed tolerance is not sufficient evidence that a language pressure is resolved.
