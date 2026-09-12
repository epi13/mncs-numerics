; MNCS LLVM IR realization 0.1
; not MNCS semantics; selected SSA identity is retained in the artifact envelope
source_filename = "mncs-llvm-ir"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Canonical composite cell arena (v0.1)
@mncs_arena = global [16777216 x i8] zeroinitializer
@mncs_bump = global i64 0

declare {i8, i1} @llvm.sadd.with.overflow.i8(i8, i8)
declare {i8, i1} @llvm.uadd.with.overflow.i8(i8, i8)
declare {i8, i1} @llvm.ssub.with.overflow.i8(i8, i8)
declare {i8, i1} @llvm.usub.with.overflow.i8(i8, i8)
declare {i8, i1} @llvm.smul.with.overflow.i8(i8, i8)
declare {i8, i1} @llvm.umul.with.overflow.i8(i8, i8)
declare {i16, i1} @llvm.sadd.with.overflow.i16(i16, i16)
declare {i16, i1} @llvm.uadd.with.overflow.i16(i16, i16)
declare {i16, i1} @llvm.ssub.with.overflow.i16(i16, i16)
declare {i16, i1} @llvm.usub.with.overflow.i16(i16, i16)
declare {i16, i1} @llvm.smul.with.overflow.i16(i16, i16)
declare {i16, i1} @llvm.umul.with.overflow.i16(i16, i16)
declare {i32, i1} @llvm.sadd.with.overflow.i32(i32, i32)
declare {i32, i1} @llvm.uadd.with.overflow.i32(i32, i32)
declare {i32, i1} @llvm.ssub.with.overflow.i32(i32, i32)
declare {i32, i1} @llvm.usub.with.overflow.i32(i32, i32)
declare {i32, i1} @llvm.smul.with.overflow.i32(i32, i32)
declare {i32, i1} @llvm.umul.with.overflow.i32(i32, i32)
declare {i64, i1} @llvm.sadd.with.overflow.i64(i64, i64)
declare {i64, i1} @llvm.uadd.with.overflow.i64(i64, i64)
declare {i64, i1} @llvm.ssub.with.overflow.i64(i64, i64)
declare {i64, i1} @llvm.usub.with.overflow.i64(i64, i64)
declare {i64, i1} @llvm.smul.with.overflow.i64(i64, i64)
declare {i64, i1} @llvm.umul.with.overflow.i64(i64, i64)
declare i8 @llvm.sadd.sat.i8(i8, i8)
declare i8 @llvm.uadd.sat.i8(i8, i8)
declare i8 @llvm.ssub.sat.i8(i8, i8)
declare i8 @llvm.usub.sat.i8(i8, i8)
declare i16 @llvm.sadd.sat.i16(i16, i16)
declare i16 @llvm.uadd.sat.i16(i16, i16)
declare i16 @llvm.ssub.sat.i16(i16, i16)
declare i16 @llvm.usub.sat.i16(i16, i16)
declare i32 @llvm.sadd.sat.i32(i32, i32)
declare i32 @llvm.uadd.sat.i32(i32, i32)
declare i32 @llvm.ssub.sat.i32(i32, i32)
declare i32 @llvm.usub.sat.i32(i32, i32)
declare i64 @llvm.sadd.sat.i64(i64, i64)
declare i64 @llvm.uadd.sat.i64(i64, i64)
declare i64 @llvm.ssub.sat.i64(i64, i64)
declare i64 @llvm.usub.sat.i64(i64, i64)
declare double @llvm.sin.f64(double)
declare double @llvm.cos.f64(double)

define void @mncs_ir_probe__dot4(i64 %arg0, i64 %arg1, ptr %mncs_status, ptr %mncs_value, i64 %mncs_depth) {
entry:
  %v7_slot = alloca i32
  %v6_slot = alloca i64
  %v5_slot = alloca i64
  %v4_slot = alloca double
  %v9_slot = alloca double
  %v10_slot = alloca double
  %v11_slot = alloca double
  %v12_slot = alloca double
  %v14_slot = alloca i64
  %v8_slot = alloca i64
  %v13_slot = alloca i64
  %v15_slot = alloca double
  %v3_slot = alloca double
  %v2_slot = alloca i64
  %v0_slot = alloca i64
  %v1_slot = alloca i64
  %mncs_depth_over = icmp ugt i64 %mncs_depth, 1024
  br i1 %mncs_depth_over, label %mncs_exhausted, label %mncs_depth_ok
mncs_depth_ok:
  store i64 %arg0, ptr %v0_slot
  store i64 %arg1, ptr %v1_slot
  br label %b0
b0:
  %sl1 = add i64 4, 0
  store i64 %sl1, ptr %v2_slot
  %fk2 = fadd double 0x0000000000000000, 0.0
  store double %fk2, ptr %v3_slot
  %xfer3_v3 = load double, ptr %v3_slot
  store double %xfer3_v3, ptr %v4_slot
  %xfer4_v2 = load i64, ptr %v2_slot
  store i64 %xfer4_v2, ptr %v5_slot
  br label %b1
b1:
  %k5 = add i64 0, 0
  store i64 %k5, ptr %v6_slot
  %lhs6_v5 = load i64, ptr %v5_slot
  %rhs7_v6 = load i64, ptr %v6_slot
  %cmp_v7 = icmp ugt i64 %lhs6_v5, %rhs7_v6
  %cmpz_v7 = zext i1 %cmp_v7 to i32
  store i32 %cmpz_v7, ptr %v7_slot
  %cnd8_v7 = load i32, ptr %v7_slot
  %c_v7 = icmp ne i32 %cnd8_v7, 0
  br i1 %c_v7, label %br9_then, label %br9_else
br9_then:
  br label %b2
br9_else:
  %xfer10_v4 = load double, ptr %v4_slot
  store double %xfer10_v4, ptr %v15_slot
  br label %b3
b2:
  %lhs11_v2 = load i64, ptr %v2_slot
  %rhs12_v5 = load i64, ptr %v5_slot
  %bin13 = sub i64 %lhs11_v2, %rhs12_v5
  store i64 %bin13, ptr %v8_slot
  %idx14_v8 = load i64, ptr %v8_slot
  %seq15_v0 = load i64, ptr %v0_slot
  %idxw16 = shl i64 %idx14_v8, 3
  %soff16 = add i64 %seq15_v0, %idxw16
  %ag17 = icmp ugt i64 %soff16, 16777208 ; arena-guard:seq-project
  br i1 %ag17, label %mncs_fail, label %ag17_ok
ag17_ok:
  %sgep17 = getelementptr inbounds [16777216 x i8], ptr @mncs_arena, i64 0, i64 %soff16
  %v9_v64 = load i64, ptr %sgep17
  store i64 %v9_v64, ptr %v9_slot
  %idx18_v8 = load i64, ptr %v8_slot
  %seq19_v1 = load i64, ptr %v1_slot
  %idxw20 = shl i64 %idx18_v8, 3
  %soff20 = add i64 %seq19_v1, %idxw20
  %ag21 = icmp ugt i64 %soff20, 16777208 ; arena-guard:seq-project
  br i1 %ag21, label %mncs_fail, label %ag21_ok
ag21_ok:
  %sgep21 = getelementptr inbounds [16777216 x i8], ptr @mncs_arena, i64 0, i64 %soff20
  %v10_v64 = load i64, ptr %sgep21
  store i64 %v10_v64, ptr %v10_slot
  %fl22_v9 = load double, ptr %v9_slot
  %fr23_v10 = load double, ptr %v10_slot
  %fsub24 = fsub double %fl22_v9, %fl22_v9
  %ffinite24 = fcmp oeq double %fsub24, 0.0
  br i1 %ffinite24, label %ffinite24_ok, label %mncs_fail
ffinite24_ok:
  %fsub25 = fsub double %fr23_v10, %fr23_v10
  %ffinite25 = fcmp oeq double %fsub25, 0.0
  br i1 %ffinite25, label %ffinite25_ok, label %mncs_fail
ffinite25_ok:
  %fbin26 = fmul double %fl22_v9, %fr23_v10
  store double %fbin26, ptr %v11_slot
  %fsub27 = fsub double %fbin26, %fbin26
  %ffinite27 = fcmp oeq double %fsub27, 0.0
  br i1 %ffinite27, label %ffinite27_ok, label %mncs_fail
ffinite27_ok:
  %fl28_v4 = load double, ptr %v4_slot
  %fr29_v11 = load double, ptr %v11_slot
  %fsub30 = fsub double %fl28_v4, %fl28_v4
  %ffinite30 = fcmp oeq double %fsub30, 0.0
  br i1 %ffinite30, label %ffinite30_ok, label %mncs_fail
ffinite30_ok:
  %fsub31 = fsub double %fr29_v11, %fr29_v11
  %ffinite31 = fcmp oeq double %fsub31, 0.0
  br i1 %ffinite31, label %ffinite31_ok, label %mncs_fail
ffinite31_ok:
  %fbin32 = fadd double %fl28_v4, %fr29_v11
  store double %fbin32, ptr %v12_slot
  %fsub33 = fsub double %fbin32, %fbin32
  %ffinite33 = fcmp oeq double %fsub33, 0.0
  br i1 %ffinite33, label %ffinite33_ok, label %mncs_fail
ffinite33_ok:
  %k34 = add i64 1, 0
  store i64 %k34, ptr %v13_slot
  %lhs35_v5 = load i64, ptr %v5_slot
  %rhs36_v13 = load i64, ptr %v13_slot
  %ov37 = call {i64, i1} @llvm.usub.with.overflow.i64(i64 %lhs35_v5, i64 %rhs36_v13)
  %ov37_v = extractvalue {i64, i1} %ov37, 0
  %ov37_f = extractvalue {i64, i1} %ov37, 1
  br i1 %ov37_f, label %mncs_fail, label %ov37_ok
ov37_ok:
  store i64 %ov37_v, ptr %v14_slot
  %xfer38_v12 = load double, ptr %v12_slot
  store double %xfer38_v12, ptr %v4_slot
  %xfer39_v14 = load i64, ptr %v14_slot
  store i64 %xfer39_v14, ptr %v5_slot
  br label %b1
b3:
  %retv40_v15 = load double, ptr %v15_slot
  %ret_bits_v15 = bitcast double %retv40_v15 to i64
  store i64 %ret_bits_v15, ptr %mncs_value
  store i32 0, ptr %mncs_status
  ret void
b4:
  br label %mncs_fail
mncs_fail:
  store i32 1, ptr %mncs_status
  store i64 0, ptr %mncs_value
  ret void
mncs_exhausted:
  store i32 3, ptr %mncs_status
  store i64 0, ptr %mncs_value
  ret void
mncs_propagate:
  store i64 0, ptr %mncs_value
  ret void
}

