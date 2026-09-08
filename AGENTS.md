# Agent and contributor contract

- Treat surprising numerical differences as findings to explain, not noise to suppress.
- Prefer minimal reproductions and independently trustworthy reference results.
- Record compiler flags, backend, hardware class, precision mode and tolerance policy with results.
- Implement harness code in `mncs-language` where feasible so the harness pressures the language itself.
- Never broaden tolerances merely to make a test green without scientific justification.
- Separate language semantics, compiler optimization bugs, backend differences and genuinely ill-conditioned algorithms.
- Record concrete MNCS gaps in `docs/LANGUAGE_PRESSURES.md`.
