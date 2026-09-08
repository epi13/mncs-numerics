# RFC 0001: Numerical pressure foundation

Status: Draft

## Purpose

Establish a reproducible adversarial numerical test system for MNCS.

## Principles

- Every test declares what kind of equality or tolerance is meaningful.
- Reference truth and implementation-under-test are kept distinct.
- Hardware/backend/optimization metadata is part of the result.
- NaN, infinity, signed zero, subnormals, overflow and rounding behavior are tested deliberately.
- Fast-math behavior must be opt-in and distinguishable from strict/reproducible behavior.
- Regressions should shrink toward minimal reproducers.

## Pressure objectives

Floating-point semantics, optimizer reassociation, FMA control, reductions, SIMD, CUDA parity, generic numerics, high-precision interoperability, deterministic execution, compiler diagnostics and machine-readable execution evidence.
