# Standalone release verification

The Python checker uses only the standard library. Native compilation needs CMake 3.20+ and a C++14 compiler. The optional WASM rebuild needs an installed Emscripten toolchain; the ABI smoke needs Node.js 18.3+.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip \
  --work-dir /tmp/tetorica-sdk-check \
  --build-wasm ym2612
```

The work directory must be empty. Its source tree is extracted from the ZIP, not copied from another checkout. Manifest inventories, hashes, source/license references, Native provenance, all 22 public chips and all 27 WASM recipes are checked before building. CMake File API and compiler-command paths reject outside project sources/includes. Downloading build recipes, external CMake fetches, archive symlinks and escaping paths are rejected. This is not an operating-system network sandbox; installed compiler/system headers and Emscripten's toolchain cache remain toolchain dependencies.

The initial compiled Native target and released WASM artifact are YM2612/ymfm. Other chips retain source recipes and their explicitly recorded verification/license status. The Node smoke tests synchronous reads, audible finite stereo output, reset and exact PCM continuation after save/load. It loads the supplied loader unchanged through a temporary `.mjs` file, with explicit WASM bytes and no npm dependencies.

To recheck unchanged compiled releases without compiling again, pass `--audit-only --wasm-smoke`. To run the low-level ABI smoke directly:

```sh
node tests/wasm_smoke.mjs /path/to/extracted-release/wasm
```
