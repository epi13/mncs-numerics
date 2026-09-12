# P-004 — No generic record declarations (diagnostic half resolved)

Full report: `docs/LANGUAGE_PRESSURES.md#P-004`.

```bash
cargo run -q -p mncs-cli -- source-study repros/P-004-generic-records/repro.mncs --node-id repro
```

`record Box<N: Nat> { lane: [f64; N] }` (`repro.mncs`) is refused
with a single precise diagnostic at the `<` (language repair
2026-09-12):

```text
MNP213 | generic record declarations are not supported; records cannot take type parameters
```

`enum Outcome<N: Nat> { ... }` (`repro_enum.mncs`) likewise:

```text
MNP214 | generic enum declarations are not supported; enums cannot take type parameters
```

Before the repair each died in a four-diagnostic cascade
(`MNP123`/`MNP072` + body/empty/trailing errors) naming everything
except the rule. The parser now reuses the shared generic-parameter
machinery and skips the balanced body, so a declaration AFTER the
refused one still parses (pinned language-side by
`pressure_generic_type_refusal`).

These repros deliberately go on to USE the generic type
(`-> (result: Box<N>)`, `Box<N> { lane: xs }`), so diagnostics after
the first are use-site cascade for a type that cannot exist yet —
the same documented-cascade status as P-009's second error. The
repros stay in that form on purpose: they exhibit the full
expressive gap (generic carried state, generic outcome types), not
just the declaration diagnostic.

Numerics impact (unchanged): a traversal carries one state value, so
multi-scalar generic folds (e.g. generic prefix sums) are
inexpressible; the library ships concrete-width records instead
(`Pref` for `prefix4` in `src/numerics/vec_float_build.mncs`), and
`normalized` traps on zero instead of returning a `ZeroNorm`
outcome.
