# Verification record

Verification was performed on macOS on 2026-10-24 using installed development tools. The results below cover the stated configurations. They do not establish Windows/Linux/ARM execution coverage or standalone Native targets for every chip.

The new [Verify SDK workflow](../.github/workflows/verify-sdk.yml) configures Windows MSVC, Linux GCC x64/ARM64, and macOS Clang Intel/Apple Silicon source-archive builds, plus an Ubuntu YM2612 WASM build and archive rebuild. Those platform results remain pending until the workflow is pushed and executed; a configured job is not recorded as a successful remote run.

## Source and release audits

`scripts/check_sdk.py` verifies 22 Playground chip IDs, 27 WASM recipes, two separate JavaScript reference engines, three pinned upstream ADPCM source snapshots, and their SHA-256 digests and source/license references. Captured cores and Native bridges retain their source bytes; include-path adaptations and documentation updates are recorded in the provenance inventory. Release-audit regression tests cover these checks.

Source and WASM archives were extracted outside the original repositories. The audits checked complete manifest coverage, hashes and byte sizes, safe relative paths, source catalogs, and the identity of the source ZIP embedded in the WASM release. CMake File API and compiler-command records confirmed that project sources and include paths stayed within the extracted SDK and its build directory.

```sh
python3 scripts/check_sdk.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/package_release.py --out-dir releases --wasm-dir build/verified-wasm
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip \
  --build-wasm ym2612
```

These checks use installed compilers, Node.js, Python and CMake. They do not download sound-chip sources or another application's checkout. Source and license records preserve the SDK's BSD-3-Clause original-code license and the component exceptions listed in [LICENSES.md](../LICENSES.md).

## YM2612

- Native Release builds and CTest passed both in the SDK checkout and in an independently extracted source archive.
- The Native OPN provider now explicitly instantiates the adapter's extern templates, carrying the verified Tauri link fix. Vendor core bytes, WASM recipes, and the exported Native ABI are retained. The amended Native adapter and provider passed another 198-case comparison against the deployed WASM with zero PCM/status/IRQ/read differences.
- The Native fixture covers independent instances, six FM channels, DAC, timers/status/IRQ, reads, observation, clock changes, Stop/reset, mute, audition and source cancellation. It observed zero C++ `new`/`delete` calls during rendering.
- Integration against the existing application's real WASM reference produced zero PCM, status, IRQ or read differences across 198 cases and 1,216,512 stereo frames. This larger comparison used the checker in the original application repository.
- Emscripten compiled the SDK sources using the included build recipe. The WASM release contains this newly generated artifact. `build-info.json` records compiler information and source/output hashes.
- Both the released WASM and the WASM rebuilt from the independently extracted sources passed the Node ABI smoke: synchronous reads/status, audible finite stereo PCM, reset, and exact PCM continuation after save/load.

The initial archives were checked again using the tests included in their source payload, including the Node ABI smoke. Repackaging identical inputs also produced matching archive hashes.

Emscripten optimization emits two existing array-bounds warnings in ymfm templates. This extraction retains that source snapshot unchanged.

## MSM5205 and OKIM6295 JavaScript references

The two engine files and component license texts match the imported Tetorica sources byte for byte. Component READMEs now describe the separately collected upstream sources and omitted dependencies. The two JavaScript references do not change the 22 Playground IDs or 27 WASM recipes. Both catalogs explicitly record their Native and WASM ports as `not-ported`.

All ten Node.js 22+ smoke checks passed, covering finite audible PCM, exact chunk continuity, mute progression, reset, MSM5205 external VCLK, OKIM6295 commands and voice completion, attachment gain and lifecycle, and standalone WAV generation. The synthetic-data example produced two seconds of 22,050 Hz PCM16 stereo audio for each chip, without npm dependencies or a game ROM.

The updated source and WASM ZIPs were independently extracted and audited. The JavaScript smoke ran against the extracted sources, including the example from a temporary working directory. The existing YM2612 WASM artifact passed its ABI smoke again. The unchanged C++ sources and WASM recipes were not recompiled for this JavaScript-reference addition.

```sh
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip \
  --audit-only --javascript-smoke --wasm-smoke
```

## Upstream ADPCM source references

Eight original C/C++ files are collected in three snapshots: libvgm MSM5205, libvgm OKIM6295/ADPCM, and MAME OKIM6295/ADPCM. Every file has an explicit BSD-3-Clause declaration. Immutable official commit pins and file SHA-256 hashes are checked against the snapshot manifests and source inventory. The JavaScript engine bytes and existing build recipes are unchanged.

The source and WASM release audits verify that these references survive packaging, including the exact source ZIP embedded with the WASM artifact. Regression tests reject missing references, mutable revision names, changed bytes, incomplete hash coverage, inconsistent catalogs, and accidental SDK port claims.

These snapshots have not been compiled as SDK targets. They deliberately omit MAME's framework and libvgm support files without explicit license declarations. The missing dependencies are recorded, and the audits do not claim header closure or a standalone C/C++ build for them. The runnable JavaScript examples and existing build targets do not use those omitted files.

## DX7 and remaining chips

A standalone DX7 WASM build also succeeded. Its generated `msfa.wasm` SHA-256 matched the existing reference artifact. The initial WASM release still contains YM2612 only.

For other chips, the audits verified source files, component licenses, build recipes and origin hashes. Standalone Native builds, execution of every WASM recipe, and playback comparisons will be added per chip. See [chip-specific differences](chip-differences.md) for backend behavior and integration prerequisites, including the Game Boy Native header adaptation.
