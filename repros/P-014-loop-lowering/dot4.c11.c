/* MNCS C11 realization 0.2. Not MNCS semantics. No C undefined behavior for integers. */
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>

/* Canonical composite cell arena (MNCS cell layout v0.1). Defined
   whenever the call-file driver may copy an arena image, including
   mask-only modules that never allocate cells. */
#define MNCS_ARENA_BYTES (16777216u)
unsigned char mncs_arena[MNCS_ARENA_BYTES];
uint64_t mncs_bump = 0;
/* Sticky arena-exhaustion flag: allocation arithmetic cannot wrap
   (every addition is range-checked before it happens), loads and stores
   bounds-check their address (corrupted or externally restored offsets
   fail closed instead of touching out-of-bounds memory), and each
   function converts a set flag into status=1 at its return points.
   Never SIGSEGV/SIGBUS/poison: exhaustion is a deterministic language
   runtime failure. Reset at every function entry. */
uint64_t mncs_failed = 0;
/* Allocation-cap exhaustion reports distinctly: alloc sites set
   mncs_exhausted alongside mncs_failed so return points surface status=3
   (budget_exhausted) with an attributed resource reason instead of a bare
   status=1. Reset at every function entry alongside mncs_failed. */
uint64_t mncs_exhausted = 0;
uint64_t mncs_cell_alloc(uint64_t bytes) {
  uint64_t base;
  if (mncs_failed) return 0;
  if (bytes > MNCS_ARENA_BYTES) { mncs_failed = 1; mncs_exhausted = 1; return 0; }
  if (mncs_bump > MNCS_ARENA_BYTES) { mncs_failed = 1; mncs_exhausted = 1; return 0; }
  base = (mncs_bump + 7u) & ~(uint64_t)7u;
  if (base > MNCS_ARENA_BYTES - bytes) { mncs_failed = 1; mncs_exhausted = 1; return 0; }
  mncs_bump = base + bytes;
  return base;
}
void mncs_slot_store32(unsigned char *a, uint64_t at, uint32_t v) {
  if (mncs_failed) return;
  if (at > MNCS_ARENA_BYTES - 4u) { mncs_failed = 1; return; }
  memcpy(a + at, &v, sizeof v);
}
void mncs_slot_store64(unsigned char *a, uint64_t at, uint64_t v) {
  if (mncs_failed) return;
  if (at > MNCS_ARENA_BYTES - 8u) { mncs_failed = 1; return; }
  memcpy(a + at, &v, sizeof v);
}
uint32_t mncs_slot_load32(const unsigned char *a, uint64_t at) {
  uint32_t v = 0;
  if (mncs_failed) return 0;
  if (at > MNCS_ARENA_BYTES - 4u) { mncs_failed = 1; return 0; }
  memcpy(&v, a + at, sizeof v);
  return v;
}
uint64_t mncs_slot_load64(const unsigned char *a, uint64_t at) {
  uint64_t v = 0;
  if (mncs_failed) return 0;
  if (at > MNCS_ARENA_BYTES - 8u) { mncs_failed = 1; return 0; }
  memcpy(&v, a + at, sizeof v);
  return v;
}

void mncs_ir_probe__dot4(uint64_t, uint64_t, int32_t*, int64_t*, uint64_t);

void mncs_ir_probe__dot4(uint64_t v0, uint64_t v1, int32_t *mncs_status, int64_t *mncs_value, uint64_t mncs_depth) {
  int64_t v2;
  double v3;
  double v4;
  int64_t v5;
  int64_t v6;
  int32_t v7;
  int64_t v8;
  double v9;
  double v10;
  double v11;
  double v12;
  int64_t v13;
  int64_t v14;
  double v15;
  if (mncs_depth > 1024u) { *mncs_status = 3; *mncs_value = 0; return; }
  if (mncs_depth == 0) { mncs_failed = 0; mncs_exhausted = 0; }
  int32_t mncs_pc = 0;
  for (;;) {
    switch (mncs_pc) {
    case 0: {
      v2 = (int64_t)4ULL;
      { uint64_t mncs_bits = 0ULL; memcpy(&v3, &mncs_bits, sizeof(v3)); }
      v4 = v3;
      v5 = v2;
      mncs_pc = 1; continue;
    }
    case 1: {
      v6 = (int64_t)0;
      v7 = (int32_t)((uint64_t)v5 > (uint64_t)v6);
      if (v7) {
        mncs_pc = 2; continue;
      } else {
      v15 = v4;
        mncs_pc = 3; continue;
      }
    }
    case 2: {
      v8 = (int64_t)((uint64_t)((uint64_t)v2 - (uint64_t)v5) & UINT64_MAX);
      { uint64_t mncs_bits = mncs_slot_load64(mncs_arena, v0 + (uint64_t)v8 * 8u); memcpy(&v9, &mncs_bits, sizeof(mncs_bits)); }
      { uint64_t mncs_bits = mncs_slot_load64(mncs_arena, v1 + (uint64_t)v8 * 8u); memcpy(&v10, &mncs_bits, sizeof(mncs_bits)); }
      v11 = v9 * v10;
      if (!((v9 - v9) == 0.0) || !((v10 - v10) == 0.0) || !((v11 - v11) == 0.0)) { *mncs_status = 1; *mncs_value = 0; return; }
      v12 = v4 + v11;
      if (!((v4 - v4) == 0.0) || !((v11 - v11) == 0.0) || !((v12 - v12) == 0.0)) { *mncs_status = 1; *mncs_value = 0; return; }
      v13 = (int64_t)1;
      { unsigned __int128 mncs_wide = (unsigned __int128)(uint64_t)v5 - (unsigned __int128)(uint64_t)v13; if (mncs_wide > 18446744073709551615ULL || mncs_wide < 0ULL) { *mncs_status = 1; *mncs_value = 0; return; } v14 = (int64_t)mncs_wide; }
      v4 = v12;
      v5 = v14;
      mncs_pc = 1; continue;
    }
    case 3: {
      if (mncs_failed) { *mncs_status = mncs_exhausted ? 3 : 1; *mncs_value = 0; return; }
      *mncs_status = 0;
      memcpy(mncs_value, &v15, sizeof(v15));
      return;
    }
    case 4: {
      *mncs_status = 1;
      *mncs_value = 0;
      return;
    }
    default:
      *mncs_status = 1;
      *mncs_value = 0;
      return;
    }
  }
}

