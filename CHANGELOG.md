# Changelog

## Unreleased

- Add one standalone YM2610/YM2610B library with `tetorica::ym2610` / `tetorica::ym2610b` aliases and public forwarders retaining `native_ym2610b_*`. Both require explicit immutable constructor variants: four physical FM slots 1/2/4/5 or all six, with SSG and ADPCM-A/B. Preserve both profiles, dense primary ROM copies, externally owned immutable additional pages, observational status and retained Stop/reset behavior.
- Add `tetorica_neogeo_wav <output.wav>`, a three-second 48 kHz stereo PCM16 example using one four-FM primary YM2610 with three SSG voices and original synthetic ADPCM-A/B samples. Program 256-byte ROM ranges rather than OPNA's fixed rhythm/32-byte RAM mode; no external hardware/game ROMs are required.
- Add the standalone YM2608 OPNA target `tetorica::ym2608`, public `<tetorica/ym2608.hpp>` forwarder and existing C ABI/state layouts, reusing the Native OPN provider. Preserve FM/SSG/rhythm/ADPCM-B, bounded memory copies and both reset profiles: primary clears outer output history; additional retains it. Both retain uploaded ROM/RAM, clock and source mute settings. Observational snapshots remain separate from hardware reads with side effects.
- Add `tetorica_pc98_ym2608_wav <output.wav>`, a three-second 48 kHz stereo PCM16 example combining FM/SSG with locally generated ADPCM-A percussion and an ADPCM-B pluck. It uploads an original synthetic 8 KiB rhythm ROM and encoded sample RAM, with no external assets or hardware ROM sounds.
- Add the standalone YM2203 OPN+SSG target `tetorica::ym2203`, public `<tetorica/ym2203.hpp>` forwarder and existing `native_ym2203_*` ABI. Preserve the primary/additional constructor profiles: primary reset retains output-rate remainder/held PCM, while additional reset clears them. The shared Native OPN provider owns the helper templates without changing vendor DSP or the ABI.
- Add `tetorica_pc98_ym2203_wav <output.wav>`, a three-second 48 kHz stereo PCM16 example using all three FM and three SSG voices, shared noise and envelope at the standard 4 MHz clock/prescaler. It uses the YM2203 SSG master/2 effective clock, mono output on both channels and no YM2608 rhythm/ADPCM assets.
- Add the standalone AY-3-8910 target `tetorica::ay8910`, public `<tetorica/ay8910.hpp>` forwarder and unchanged `native_ay8910_*` ABI, preserving three tones, shared noise/envelope, synchronous observation, retained levels, Stop/reset and audition. Keep the Native type 0 / flags 1 configuration, three-channel averaging and mono output; YM2149/type/flags selection remains outside this ABI.
- Add `tetorica_msx_wav <output.wav>`, a three-second 48 kHz stereo PCM16 example combining real AY tones/noise/hardware envelope with an OPLL flute melody. It represents an MSX plus MSX-MUSIC sound configuration, without machine emulation or a motherboard analog mix model.
- Add the standalone YM2413 OPLL target `tetorica::ym2413`, public `<tetorica/ym2413.hpp>` forwarder and existing `native_ym2413_*` ABI, preserving the cached Native adapter's Stop/reset, observation and audition semantics. Support nine melodic channels or six FM plus five rhythm voices sharing physical channels 6–8, with mono output on both stereo channels.
- Add `tetorica_master_system_wav <output.wav>`, a three-second 48 kHz stereo PCM16 example combining OPLL's built-in piano/rhythm and Sega PSG through the real libraries. Preserve the Genesis WAV example and the shared optional example-build switch.
- Add the independent Sega PSG target `tetorica::segapsg`, forwarding `<tetorica/segapsg.hpp>` to the unchanged `native_game_gear_*` ABI, with three tone channels, noise and Game Gear stereo. Genesis/Master System output retains stereo `0xff`; no OPLL core is included.
- Add `tetorica_genesis_wav <output.wav>`, an optional offline example rendering three seconds of 48 kHz stereo PCM16 with the real YM2612 and PSG libraries, synthetic notes/noise and fixed mix headroom.
- Extend source-archive checks to require eight Native fixtures and six WAV examples, validate their output, and run the same checks in the configured Native CI matrix. Nine chip IDs use eight static libraries because YM2610/YM2610B share one library. The full Native OPL template provider and its support dependencies serve YM2413 only; other OPL standalone targets remain pending. Vendor core bytes and WASM recipes remain unchanged.
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
