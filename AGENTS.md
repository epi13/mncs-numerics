# Agent and contributor contract

- Treat surprising numerical differences as findings to explain, not noise to suppress.
- Prefer minimal reproductions and independently trustworthy reference results.
- Record compiler flags, backend, hardware class, precision mode and tolerance policy with results.
- Implement harness code in `mncs-language` where feasible so the harness pressures the language itself.
- Implement numerical functionality in `.mncs` first. Host code (Python/Rust) is
  oracle and tooling only; never move library semantics into it to dodge a
  language inconvenience — file a pressure instead.
- Never broaden tolerances merely to make a test green without scientific justification.
- Committed corpora assert exact bits. The oracle (`scripts/gen_corpora.py`) mirrors
  MNCS operation order AND validates algorithmic quality with asserts at generation
  time. If the oracle is wrong, fix the oracle; if MNCS is wrong, file a pressure.
- Separate language semantics, compiler optimization bugs, backend differences and genuinely ill-conditioned algorithms.
- Record concrete MNCS gaps in `docs/LANGUAGE_PRESSURES.md` with a runnable
  reproducer under `repros/`. Never delete a pressure because a workaround exists;
  never keep one after it reproduces green — re-run repros against the current
  toolchain and update status.
- Backend refusals are pinned, not passed: add them to `expected_refusals` in
  `scripts/run_tests.py` with the pressure ID, and flag any unexpected pass.
- Workflow: `python3 scripts/gen_corpora.py` then
  `python3 scripts/run_tests.py [--backends ...] [--suites ...]` with
  `MNCS_LIBRARY_PATH=src` (set automatically by the runners).
