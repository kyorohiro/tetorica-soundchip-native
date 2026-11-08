#!/bin/sh
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, kyorohiro
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUT_DIR="${1:-$ROOT_DIR/dist/wasm}"
python3 "$ROOT_DIR/vendor/chips-m6581/prepare.py" --check
mkdir -p "$OUT_DIR"
"${EMXX:-em++}" "$ROOT_DIR/vendor/tetorica-sid/sid.cpp" \
  -I"$ROOT_DIR/native/include" -std=c++17 -O2 -DNDEBUG -ffp-contract=off \
  -sSTANDALONE_WASM=1 -sALLOW_MEMORY_GROWTH=1 -sINITIAL_MEMORY=2097152 \
  -sSTACK_SIZE=65536 -sFILESYSTEM=0 --no-entry \
  -sEXPORTED_FUNCTIONS='["_sid_create","_sid_destroy","_sid_reset","_sid_write","_sid_read","_sid_output","_sid_render","_sid_cycles","_sid_envelope","_sid_phase"]' \
  -o "$OUT_DIR/sid_wasm.wasm"
