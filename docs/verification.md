# Verification record

Local verification was performed on macOS on 2026-10-24 using installed development tools. The results below cover the stated configurations; standalone Native builds are not yet provided for every collected chip.

The [Verify SDK workflow](../.github/workflows/verify-sdk.yml) passed all six jobs in [run 40079785622](https://github.com/kyorohiro/tetorica-soundchip-native/actions/runs/40079785622) at commit `175d20e1e2ca7397a267f3c8e3cd403669b9c989`: Windows MSVC, Linux GCC x64/ARM64, macOS Clang Intel/Apple Silicon source-archive builds, and Ubuntu YM2612 WASM build/archive rebuild. That run covers the existing YM2612 target. The newly added YM2151 target has local results recorded below; its remote platform validation awaits the next push.

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

## YM2151

- The standalone `tetorica::ym2151` target and public `<tetorica/ym2151.hpp>` header build in Release mode. Both YM2151 and YM2612 CTest self-tests passed.
- The OPM adapter uses a Native-owned explicit template provider, matching the Tauri link fix at `83bfba8cbbc272a02279aba250b13e4c0f6ca57b`. The only adapter amendment removes its redundant local `keyonoff` instantiation; ymfm vendor files, WASM recipes and exported Native ABI remain unchanged.
- The fixture exercises all eight channels with left/right/stereo routing, finite audible output, independent instances, non-advancing reads and snapshots, both timers/status/IRQ, clock limits, retained Stop/reset, CSM cancellation and deferred audition. It observed zero C++ `new`/`delete` calls during rendering and controls.
- Comparison against the deployed YM2151 Worklet/WASM passed 252 cases at 44,100, 48,000 and 96,000 Hz: 1,548,288 stereo frames with zero PCM/status/IRQ/read differences. This additional offline comparison used `scripts/check_native_extra_ym2151.mjs` in the original application repository with the SDK-built fixture; it is not a source-package build dependency.
- A C++14 consumer included both public headers and linked both static libraries together, producing finite audible output without duplicate symbols.
- Fresh source and WASM ZIPs passed manifest/provenance audits. From an independently extracted source ZIP, both Native libraries built in Release mode and both CTest fixtures passed; the ten JavaScript reference checks and the existing YM2612 WASM ABI smoke also passed. No sibling checkout or chip-source download was used by the archive checker.
- All 46 Python audit regression tests passed, including missing, duplicate, shared, escaped and unbuilt YM2151 fixture artifacts under single- and multi-configuration CMake layouts. Source validation checked 254 snapshot records across the existing 22 chip IDs and 27 WASM recipes.

This target implements OPM only. It does not include X68000 OKIM6258, sample banks, an audio device or playback-deadline guarantees. The existing WASM release and WASM CI job still select YM2612 only. This Native-only addition reused the previously built YM2612 WASM artifact; its recipe and recorded build inputs did not change.

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
