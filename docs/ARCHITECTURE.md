# Architecture

## Layers

1. **Cases** — small adversarial scalar/vector/matrix and algorithmic workloads.
2. **Execution matrix** — precision modes, optimization levels, CPU targets and CUDA targets.
3. **Reference oracles** — analytic results, arbitrary/high precision or trusted external vectors.
4. **Comparison** — exact, ULP, relative/absolute tolerance, interval and invariant checks.
5. **Evidence** — machine-readable run metadata, divergences, reproduction inputs and regression identity.
6. **Campaigns** — grouped suites for compiler releases, backends and hardware generations.

## First milestones

1. Floating-point edge corpus and comparison primitives.
2. Reduction-order and optimization tests.
3. Ill-conditioned linear/numerical cases.
4. Chaotic/stiff workload suite.
5. CPU/CUDA and cross-generation evidence runs.
