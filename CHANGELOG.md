# Changelog

## Unreleased

- Add the independent Sega PSG target `tetorica::segapsg`, forwarding `<tetorica/segapsg.hpp>` to the unchanged `native_game_gear_*` ABI, with three tone channels, noise and Game Gear stereo. Genesis/Master System output retains stereo `0xff`; no OPLL core is included.
- Add `tetorica_genesis_wav <output.wav>`, an optional offline example rendering three seconds of 48 kHz stereo PCM16 with the real YM2612 and PSG libraries, synthetic notes/noise and fixed mix headroom.
- Extend source-archive checks to require three Native fixtures and the WAV example, validate its output, and run the same checks in the configured Native CI matrix. Vendor core bytes and WASM recipes remain unchanged.
- Add the standalone YM2151 OPM static target `tetorica::ym2151`, public `<tetorica/ym2151.hpp>` forwarder and existing C ABI, with an offline eight-channel PCM/pan, timers/status/IRQ, Stop/reset/cancellation and observation fixture. X68000's OKIM6258 integration remains reference-only.
- Import the Native OPM explicit-template provider fix from the same Tauri revision as the OPN fix, preserving the shared ymfm vendor bytes and WASM recipes.
- Import the Native YM2612 explicit OPN template-provider fix, retaining the original and amended provenance hashes and unchanged DSP/ABI.
- Add source-archive Release build and CTest/JavaScript CI on Windows, Linux x64/ARM64, and both Mac architectures; add a pinned-toolchain YM2612 WASM archive build/rebuild/smoke job.
- Audit CMake multi-configuration artifacts and Windows compiler paths; preserve exact source bytes across Git checkouts and include CI configuration in source releases.

## 0.1.0 — Initial SDK

- Collect source cores and existing Native C++ bridges for all 22 chips supported by Playground's additional-instance API.
- Consolidate shared ymfm sources and add chip catalogs, component licenses, origins and SHA-256 inventories.
- Add a standalone Native YM2612 CMake target and automated PCM tests. Retain other Native implementations as reference sources for subsequent integration.
- Add WASM build recipes, versioned source/WASM release archives and verification from independently extracted packages.
- Preserve existing npm and Playground Tauri dependency paths during the initial extraction; adopting SDK releases is a separate integration step.
- Document upstream adaptations, import changes and Native/WASM differences for all 22 chips and additional WASM artifacts, including six MSFA Native differences and the pending Game Boy Native header adaptation.
- Document the workflow for incorporating changes verified in the application repositories and distributing pinned SDK snapshots.
- License original Tetorica code under BSD-3-Clause, retaining third-party licenses and existing explicit file-level terms.
- Include the Analyzer's unchanged MSM5205 and OKIM6295 JavaScript references, BSD notices, provenance, a standalone synthetic-data WAV example, and source-archive verification. Record them separately from Native targets and WASM recipes.
- Collect separately pinned, BSD-declared upstream MSM5205/OKIM6295/ADPCM C/C++ originals with per-file hashes. Document missing framework dependencies and omit libvgm support/player files without explicit licenses; retain the JavaScript engines and existing build targets unchanged.
