# MSFA / DX7 origins and Native–WASM differences

This document describes the source snapshot included on 2026-10-24. See also the [chip-by-chip comparison](chip-differences.md). This location preserves the `../../docs/research.md` reference in `vendor/msfa/UPSTREAM.md`.

## Included versions

| Layer | Version or location | Relationship |
| --- | --- | --- |
| Upstream | Google music-synthesizer-for-android, `f67d41d313b7dc85f6fb99e79e515cc9d208cfff` | Original MSFA source; its Apache-2.0 text and copyright notices are retained |
| Shared Tetorica core | [vendor/msfa/](../vendor/msfa/) | Standalone adaptation with live controls; imported from `w/tetorica-msfa-dx7-wasm/vendor/msfa/` in the reference workspace |
| Native overrides | [native/reference/overrides/msfa/](../native/reference/overrides/msfa/) | The six files in Tauri's `src-tauri/native-dx7/` that differ from the shared core |
| WASM wrapper | [wasm/dx7/dx7.cc](../wasm/dx7/dx7.cc), [dx7.h](../wasm/dx7/dx7.h) | Existing standalone WASM interface using the shared core |
| Native wrapper | [native_genesis_dx7.cpp](../native/reference/tauri/native_genesis_dx7.cpp), [.h](../native/reference/tauri/native_genesis_dx7.h) | Slot control, output-rate conversion and panic; note-state observation belongs to the Tauri Rust host |

All 30 C/C++ files in the shared core match their import sources byte for byte. The six Native overrides also match their Tauri originals. The other 24 shared files match Tauri's copies. Individual origins and hashes are recorded in [source_inventory.json](../catalog/source_inventory.json) and [SOURCES.json](../native/reference/SOURCES.json).

In the reference Web repository, `web/msfa_dx7/vendor/msfa/` contains licensing and provenance documents. The C++ source comes from the standalone package checkout identified above. The reference Web implementation loads `web/msfa_dx7/wasm/msfa.wasm`.

## Changes from upstream to the shared core

The shared core includes existing Tetorica adaptations. This summary was checked against the import source's `docs/research.md`, `vendor/msfa/UPSTREAM.md` and current source files. A complete file-by-file comparison against Google's pinned commit was not repeated for this SDK snapshot.

- [synth.h](../vendor/msfa/synth.h): `MSFA_FORCE_SCALAR` selects the existing scalar path. This avoids comparing a Native ARM NEON approximation with a different WASM calculation.
- [synth_unit.h](../vendor/msfa/synth_unit.h) / [.cc](../vendor/msfa/synth_unit.cc): standalone includes, initialized state, ownership and destruction of 16 note objects, direct 155-byte voice loading, a null MIDI ring buffer and release-all support. The shared version already preallocates its 16 notes.
- `SynthUnit` also adds patch identities through `SelectVoice` / `EditVoice`. Live edits reach sounding notes and release tails belonging to the edited patch, while notes from a previously selected patch remain distinguishable.
- [dx7note.h](../vendor/msfa/dx7note.h) / [.cc](../vendor/msfa/dx7note.cc): operator output level, mode / coarse / fine / detune and feedback can change without reinitializing phase, envelopes or feedback history.
- [env.h](../vendor/msfa/env.h) / [.cc](../vendor/msfa/env.cc): a reference trajectory supports live level edits. Unedited notes keep the original envelope path; muting does not halt release progression or revive a completed release. General live editing of all envelope parameters is outside this implementation.
- [freqlut.cc](../vendor/msfa/freqlut.cc), [fm_core.cc](../vendor/msfa/fm_core.cc): shifts and phase wrap at extreme frequencies use defined arithmetic. Normal-range calculations are retained; ultrasonic frequencies are not clamped to an audible pitch.
- [aligned_buf.h](../vendor/msfa/aligned_buf.h): standard type includes support independent compilation with modern C++ toolchains.

The internal rate is 44,100 Hz and the DSP block contains 64 frames. The original operator kernels, output filter and Int16 clipping remain in use. Output-rate conversion belongs to the wrapper. General envelope and algorithm edits affect subsequent notes; live frequency and feedback edits add no smoothing or crossfade.

Frequency lookup tables and the LFO / pitch-envelope rate constants are shared within a process. Native initializes them once at the fixed 44,100 Hz rate; applications must not overwrite active shared state by calling `SynthUnit::Init` at another rate. Each WASM memory has its own shared state.

Known MSFA limitations remain: operator amplitude-modulation sensitivity / LFO amplitude depth, voice transpose and oscillator-key-sync are not applied to note synthesis. The LFO is shared by the synth, and output-rate conversion uses stateful linear interpolation. This implementation does not reproduce DX7 firmware, its analog output stage or every hardware behavior.

## The six Native overrides

These differences already exist in the reference Tauri implementation. Copying the files into this SDK introduced no additional DSP changes.

| File | Native change and reason | Audio or API effect |
| --- | --- | --- |
| [dx7note.cc](../native/reference/overrides/msfa/dx7note.cc) | Qualifies `min` / `max` as `::min` / `::max` to avoid GCC / libstdc++ name-resolution conflicts | Velocity, rate and level-scaling formulas remain the same |
| [env.cc](../native/reference/overrides/msfa/env.cc) | Qualifies `::min` / `::max` in the same way | The envelope model is unchanged |
| [ringbuffer.cc](../native/reference/overrides/msfa/ringbuffer.cc) | Replaces POSIX `nanosleep` with standard C++ `sleep_for(1ms)` | Supports Windows; ordinary Native DX7 uses a null ring buffer and does not normally enter this wait path |
| [synth.h](../native/reference/overrides/msfa/synth.h) | Replaces the undefined-platform `#warning` and empty barrier macro with `atomic_thread_fence(seq_cst)` | Provides a barrier and supports MSVC C++17; existing Apple / GNU branches remain |
| [synth_unit.cc](../native/reference/overrides/msfa/synth_unit.cc) | Adds partial-construction cleanup, `NativeNoteOn[Mask]`, slot release / kill and `NativePanic` without reallocation | Supports separate performance owners / Keyboard leases and stopping from the audio thread |
| [synth_unit.h](../native/reference/overrides/msfa/synth_unit.h) | Declares these Native APIs | Must replace the corresponding shared header when building the Native variant |

All six files retain Google's copyright notices and explicit Apache-2.0 headers. Their existing license remains in effect. Tetorica-authored SDK wrappers and headers without a separate explicit license use the SDK's [BSD-3-Clause default](../LICENSE); a missing per-file declaration is covered by that default. See [LICENSES.md](../LICENSES.md) and [native_inventory.json](../catalog/native_inventory.json) for the component records.

## Panic and note release

Native `NativePanic` reinitializes all 16 note gates, pending PCM, controllers, filter and LFO within the existing storage while preserving the selected voice. The Native wrapper also discards its prefetched PCM.

The WASM wrapper implements panic by deleting and recreating `SynthUnit`, then restoring the selected voice. Ordinary Note On uses the 16 preallocated note objects in both versions.

Native slot release / kill can leave samples in an already generated 64-frame block or in the shared filter. These APIs support host ownership control; they have different semantics from a full panic that clears the instance's pending output.

## Build combinations

[build_dx7_wasm.sh](../scripts/build_dx7_wasm.sh) compiles the shared `vendor/msfa/` core with `wasm/dx7/`. It uses `MSFA_FORCE_SCALAR`, `-fwrapv`, `-fno-strict-aliasing` and `-ffp-contract=off`.

The reference Tauri build uses its Native `native-dx7/` tree from `src-tauri/build.rs`. To create a new Native target from this SDK, start with the shared tree and replace the six files above, including the matching headers. Do not link both the shared and Native versions of a same-name `.cc` file.

**The SDK currently provides a Native CMake target for YM2612 only. DX7 Native is included as reference source; a standalone SDK Native DX7 target is not yet provided.**

## Verification scope

- The SDK's standalone DX7 WASM build succeeded and matched the reference Web `msfa.wasm` SHA-256: `f5de761e82ea303420fb3aac79a0a59dd053773b81453b955254dd13aac77d6f`.
- A fresh comparison of the actual Tauri sources with the reference Web WASM passed 114 cases and 792,576 stereo frames at 44.1 / 48 / 96 kHz, with maximum difference 0.
- That comparison used `node scripts/check_native_dx7.mjs --out <report.json>` in the reference repository. It did not build a Native SDK DX7 target. The 96 kHz result applies output-rate conversion over the same WASM exports; it does not establish public JavaScript API support for 96 kHz.

These checks did not exercise physical audio output, compilers on other operating systems or real DX7 hardware.
