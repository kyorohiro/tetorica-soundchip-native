# Architecture and adoption

`tetorica-soundchip-native` distributes sound-chip cores and their low-level Native and WASM bridges as versioned source snapshots. It incorporates changes developed and verified in `tetorica-fm2612` and Playground Tauri, with provenance, component licenses and backend differences recorded alongside the code.

| Project | Responsibility |
| --- | --- |
| `tetorica-soundchip-native` | Source snapshots, low-level bridges, standalone build targets, provenance and license records, verification and release archives |
| `tetorica-fm2612` source repository; prospective `tetorica-fm` | Core improvements, WASM bridges, JavaScript APIs, Synth, AudioWorklet and adapter development and testing |
| Playground / Tauri | Native bridge development and testing, configuration and UI, Native IPC, playback scheduling, owner and voice management, CPAL and host effects |

Original Tetorica code is licensed under BSD-3-Clause, matching `tetorica-fm2612`. Third-party components and files with existing explicit licenses retain those terms. See [LICENSES.md](../LICENSES.md) for component exceptions and notices.

## Development sources and release snapshots

Changes developed in the application repositories enter the SDK after verification. When Native and WASM need different implementations, both versions and the reasons for their differences are retained. Each update records its source revision, file hashes and [chip-specific differences](chip-differences.md), then produces a new versioned release.

Consumers vendor a selected release and update on their own schedule. Record downstream patches separately so a later import preserves them and distinguishes them from SDK changes. Development repositories and consuming applications do not need to update together.

The SDK is the distribution source for these snapshots. Moving shared-core development into this repository is possible later; the current workflow also supports development and verification in the application repositories.

## Adoption stages

1. Collect the chip sources, component licenses and existing bridges while preserving the dependency paths used by current applications.
2. Build representative YM2612 Native and WASM targets using only a source ZIP extracted outside the original repositories, then verify PCM and state operations.
3. Switch one application's YM2612 dependency to a release pinned by version and archive hash, and compare its build and output with the existing implementation.
4. Add standalone targets for other cores incrementally. Document Native/WASM differences and integration requirements before adopting each target.

`native/reference/tauri/` contains captured Native provider implementations. These sources retain backend-specific resampling, mute, audition and cancellation behavior. Their presence does not establish a stable SDK API or a completed standalone build for every chip. DX7's Native-specific changes are also retained separately. The current standalone Native CMake target is YM2612/ymfm; see the [verification record](verification.md) for the tested scope.

`reference/javascript/` preserves the Analyzer's MSM5205 and OKIM6295 engines as synchronous JavaScript references, with their own provenance, component notices and offline example. These engines have not yet been ported to Native C++ or WASM and are cataloged separately from compiled targets.

Synchronous WASM primitives used to implement `read()` and `generateStereo()` remain part of the low-level interface. The asynchronous Native IPC path does not replace the synchronous calls needed by AudioWorklet consumers. JavaScript APIs and host transport selection remain responsibilities of the consuming projects.
