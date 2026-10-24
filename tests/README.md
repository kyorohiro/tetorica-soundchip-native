# Standalone release verification

The Python checker uses only the standard library. Native compilation needs CMake 3.20+ and a C++14 compiler. The JavaScript reference smoke, included in a normal verification run, needs Node.js 22+. The optional WASM rebuild needs an installed Emscripten toolchain; the WASM ABI smoke alone works with Node.js 18.3+.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip \
  --work-dir build/standalone-check \
  --build-wasm ym2612
```

The work directory must be empty. Its source tree is extracted from the ZIP, not copied from another checkout. Manifest inventories, hashes, source/license references, Native provenance, all 22 public chips, all 27 WASM recipes and both JavaScript references are checked before building. MSM5205 and OKIM6295 are a separate JavaScript-only set: their entry points and source hashes must be present, their metadata must agree in both catalogs, and their Native/WASM status must remain `not-ported`. CMake File API and compiler-command paths reject outside project sources/includes. Downloading build recipes, external CMake fetches, archive symlinks and escaping paths are rejected. This is not an operating-system network sandbox; installed compiler/system headers and Emscripten's toolchain cache remain toolchain dependencies.

The initial compiled Native target and released WASM artifact are YM2612/ymfm. Other chips retain source recipes and their explicitly recorded verification/license status. The Node smoke tests synchronous reads, audible finite stereo output, reset and exact PCM continuation after save/load. It loads the supplied loader unchanged through a temporary `.mjs` file, with explicit WASM bytes and no npm dependencies.

The checker selects Release explicitly for single- and multi-configuration CMake generators. It reads the fixture location from CMake's File API, supports Windows `.exe` paths and spaces, and audits relative compiler paths and MSVC include options. `--work-dir` may be absolute or relative to the invocation directory. The directory must be empty.

The [CI workflow](../.github/workflows/verify-sdk.yml) runs the source-only Native/JavaScript verification on Windows, Linux, and macOS, including Linux ARM64 and both Mac architectures. A separate Ubuntu job builds and audits the YM2612 WASM release and repeats the WASM build/smoke using its extracted source ZIP.

The JavaScript smoke imports the copied engines from the extracted source tree and checks audible finite stereo output, exact chunk continuity, mute progression, reset, MSM5205 external VCLK, OKIM6295 sample/voice commands, stop/end behavior and attachment gain. It also runs the synthetic rendering example from a temporary directory and verifies both PCM16 WAV files. No npm installation, browser or audio device is used.

To recheck unchanged releases without compiling again, pass `--audit-only --wasm-smoke --javascript-smoke`. With just `--audit-only`, no compiler or Node process is started. To run either smoke directly:

```sh
node tests/wasm_smoke.mjs /path/to/extracted-release/wasm
node tests/javascript_reference_smoke.mjs /path/to/extracted-source/reference/javascript
```
