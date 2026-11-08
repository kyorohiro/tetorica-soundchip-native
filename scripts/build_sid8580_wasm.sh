#!/bin/sh
# SPDX-License-Identifier: BSD-3-Clause
# CPU-free Rust only. No Cargo resolution, C64 CPU, network or JS factory.
set -eu
SID8580_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SID8580_OUT="${1:-$SID8580_ROOT/dist/wasm}"
SID8580_RUSTC="${RUSTC:-rustc}"
mkdir -p "$SID8580_OUT"
SID8580_OUT=$(CDPATH= cd -- "$SID8580_OUT" && pwd)
"$SID8580_RUSTC" --edition=2021 -C opt-level=3 -C panic=abort -C codegen-units=1 \
  --remap-path-prefix "$SID8580_ROOT=tetorica" --target wasm32-unknown-unknown \
  --crate-name sidera --crate-type rlib "$SID8580_ROOT/vendor/sidera/adapted/src/lib.rs" \
  -o "$SID8580_OUT/libsidera-sid8580.rlib"
"$SID8580_RUSTC" --edition=2021 -C opt-level=3 -C panic=abort -C codegen-units=1 \
  --remap-path-prefix "$SID8580_ROOT=tetorica" --target wasm32-unknown-unknown \
  --crate-name tetorica_sid8580 --crate-type cdylib "$SID8580_ROOT/vendor/tetorica-sid8580/lib.rs" \
  --extern "sidera=$SID8580_OUT/libsidera-sid8580.rlib" -o "$SID8580_OUT/sid8580_wasm.wasm"
# Only the standalone WASM is a product artifact. The rlib is an intermediate.
rm "$SID8580_OUT/libsidera-sid8580.rlib"
