# Benchmarks

Kernels in `benches/` (`bench_reduce.mncs` and `bench_build.mncs`,
both on all backends since the P-001 repair; the build file was
bytecode/C11/Cranelift-only while the P-001 envelope held — the
baseline below is marked per cell), measured by `scripts/bench.py`.
Every number below is gated on the kernel returning its exact
expected scalar first; a benchmark of wrong code would not be
recorded.

## What the numbers mean (read this before quoting them)

- **Wall time includes the whole toolchain**: process spawn, frontend,
  lowering, native compile (cc/clang/cranelift), and execution — on a
  debug-built CLI. It measures the harness round-trip, NOT kernel
  speed. Do not cite these as MNCS-vs-anything performance; they are
  a reproducible ceiling for the development loop.
- **Steps are backend-incommensurable**: bytecode counts fine-grained
  interpreter steps (the only series that scales with work), WASM
  counts something ~300× denser (and superlinear — see below),
  natives report `1` (no instrumentation). Compare steps only
  within one backend column.
- Machine: Linux x86_64, `mncs-language` debug build at `68492c0`.

## Baseline 2026-09-12 (`target/bench-20260912T061431Z.json` historical; `target/bench-20260912T185322Z.json` current)

Wall seconds per kernel (compile + run); bytecode steps in parentheses.
Historical cells are debug-build at `68492c0`; current cells are
debug-build at `a7a8c05` (same machine class, same harness — wall
comparisons across the two runs still measure the round-trip, not
the kernel).

| kernel | bytecode | wasm | c11 | llvm | cranelift |
|---|---|---|---|---|---|
| sum_256 | 17.2 (2315) | 8.4 (683353) | 9.6 (1) | 12.7 (1) | 21.4 (1) |
| sum_1024 | 17.2 (9227) | 11.6 (10597465) | 9.8 (1) | 12.7 (1) | 21.2 (1) |
| dot_256 | 17.0 (2829) | 8.6 (1348957) | 9.7 (1) | 12.7 (1) | 21.5 (1) |
| masked_dot_256 | 17.4 (3599) | 8.9 (2155105) | 9.8 (1) | 12.9 (1) | 21.5 (1) |
| axpy_256 | 22.8 (5397) | 11.7 (3212203) | 11.8 (1) | 14.8 (1) | 28.0 (1) |
| rotate_256 | 23.0 (5141) | 11.6 (2546101) | 11.9 (1) | 14.5 (1) | 28.1 (1) |
| matvec_8 | 23.1 (983) | 11.0 (80063) | 12.2 (1) | 15.1 (1) | 32.1 (1) |
| matmul_8 | 28.4 (8135) | 13.8 (801815) | 14.4 (1) | 16.9 (1) | 33.6 (1) |

All 40 cells correct (`ok=True`). The old table's `— (P-001)`
cells are gone: axpy/matvec/matmul now run on WASM and LLVM, so
the construction envelope is unified in the numbers, not just in
prose.

## Findings

1. **Wall time is workload-independent** (sum_256 ≈ matmul_8 on every
   backend): the toolchain round-trip dominates by orders of
   magnitude over kernel execution at these sizes. Kernel-speed
   comparisons need either much larger workloads (bounded by the 1024
   sequence cap — a real ceiling for benchmarking) or a build that
   separates compile from execution. Not pursued: chasing leaderboard
   numbers through a debug harness was never the point.
2. **Bytecode steps scale linearly**: 2315 → 9227 for 4× lanes
   (4.0×), dot costs ~1.2× sum per lane, axpy ~2.3×. The reference
   interpreter is the only backend where steps are a usable cost
   model.
3. **WASM step accounting scales superlinearly**: 683K → 10.6M steps
   for 4× lanes (15.5×). Per-lane cost grows ~4× with N. Whether this
   is step-accounting granularity or genuinely superlinear lowering
   (e.g. copy-per-lane sequence handling) is UNRESOLVED from these
   numbers alone — wall time grows only 1.3× over the same range, so
   execution is not obviously quadratic, but the accounting deserves
   a language-side look before anyone uses WASM steps as a cost
   model. Recorded as an observation, not a pressure: no correctness
   impact, values agree bit-exactly.
4. **Native steps are uninformative** (`1` everywhere): there is no
   native cost model to optimize against. Any future "make it faster"
   work on C11/LLVM/Cranelift needs instrumentation first.
5. **LLVM reductions recovered by file separation**: the first matrix
   (combined bench file) failed `sum_256`/`dot_256` on LLVM with the
   P-001 miscompile from `axpy`'s presence in the same artifact; the
   split files pass LLVM on all reductions. This is the second
   independent confirmation of P-001's whole-artifact poisoning
   (the first: `probe9` ident-vs-replace).
6. **New-kernel costs (bytecode steps, the only commensurable
   column):** `masked_dot_256` costs 3599 steps vs 2829 for
   `dot_256` (1.27× — the lazy-match branch chain per lane vs
   straight accumulation); `rotate_256` costs 5141, at the
   `axpy_256` scale (5397) as expected for a replace-traversal
   construction kernel. WASM steps for the P-001-era kernels now
   exist (axpy 3.2M, matvec 80K, matmul 802K); the superlinear
   WASM accounting note above still stands uninvestigated.

## Workflow

```bash
python3 scripts/bench.py                                   # full matrix (~10 min, debug CLI)
python3 scripts/bench.py --backends mncs-research-bytecode --kernels bench_sum_256
python3 scripts/bench.py --kernels bench_dot_256,bench_matmul_8
```

Evidence lands in `target/bench-<timestamp>.json` (git-ignored; copy
numbers here when updating the baseline). A release-built CLI cuts
wall times substantially; the committed numbers are debug-build and
labeled as such — do not mix release numbers into this table without
saying so.
