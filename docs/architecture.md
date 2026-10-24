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
2. Build the YM2612, YM2151, YM2413, YM2203, YM2608, Sega PSG and AY-3-8910 Native targets and representative WASM recipes using only a source ZIP extracted outside the original repositories, then verify PCM, observation and state operations appropriate to each ABI. Render the offline Genesis, Master System FM, MSX and both PC-98 examples to check small hosts.
3. Switch one application's YM2612 dependency to a release pinned by version and archive hash, and compare its build and output with the existing implementation.
4. Add standalone targets for other cores incrementally. Document Native/WASM differences and integration requirements before adopting each target.

`native/reference/tauri/` contains captured Native provider implementations. These sources retain backend-specific resampling, mute, audition and cancellation behavior. Their presence does not establish a stable SDK API or a completed standalone build for every chip. DX7's Native-specific changes are also retained separately. The standalone Native CMake targets are YM2612/ymfm, YM2151/ymfm, YM2413/ymfm, YM2203/ymfm, YM2608/ymfm, Sega PSG and AY-3-8910; see the [verification record](verification.md) for completed checks and platform coverage.

The Native-owned OPN and OPM providers under `native/src/` explicitly instantiate the templates used by those adapters. They incorporate the Tauri linkage fix while preserving the shared vendor bytes and existing chip ABI. YM2151 is an independent eight-channel OPM target; the X68000 OKIM6258 path remains a reference implementation. Adding a chip target does not import the Tauri scheduler, device output or ownership system.

The YM2203 target reuses the OPN provider and unchanged SSG/ADPCM link dependencies, exposing only one YM2203 with three FM plus three SSG voices. FM and SSG combine to mono on both output channels. Its existing primary constructor preserves held PCM/output-rate remainder across reset; the additional-instance constructor clears that history on reset. The host selects the intended profile explicitly. The PC-98 example uses the default 4 MHz clock and standard prescaler; it does not require or provide YM2608 rhythm/ADPCM resources.

The separate YM2608 target uses the same provider infrastructure for six FM channels, SSG, fixed-address rhythm and ADPCM-B. Each handle preallocates zeroed 8 KiB ROM and 2 MiB RAM buffers; synchronous memory APIs copy caller bytes, so the host retains no input-buffer lifetime obligation after a successful transfer. The host must serialize transfers with rendering and supply suitable encoded data. Both reset profiles retain memory: primary reset clears outer output history, while additional reset retains it, opposite to YM2203. Observational snapshots avoid ADPCM data/status-read side effects; the raw hardware reads remain distinct APIs.

The YM2413 target uses the imported cached OPLL adapter and the full Native OPL template provider, including its unchanged ADPCM/PCM link dependencies. Only YM2413 is constructed and exposed by this target; linking the common provider does not complete standalone targets for the other OPL chips. Its nine melodic channels become six FM channels plus five logical drum voices in rhythm mode, with those drums sharing physical channels 6–8. A host can combine this MSX-MUSIC FM component with the separate AY target to build an MSX sound configuration.

Sega PSG uses the independent Game Gear wrapper and the existing Tetorica SegaPSG core. Its `native_game_gear_*` ABI is preserved rather than renamed; the target owns no FM or OPLL core. Stereo `0xff` retains Genesis/Master System PSG output on both channels, while Game Gear hosts can select per-channel stereo.

The AY-3-8910 target preserves the existing `native_ay8910_*` ABI and independent three-channel adapter, including shared noise/envelope, retained levels, Stop, audition and observation. It fixes the core configuration to AY type 0 / flags 1, averages three channel outputs and retains outer clock averaging/hold. Unlike raw WASM, this Native ABI does not select YM2149 or other type/flag combinations. Its mono signal is copied to both channels; motherboard analog mixing remains a host concern.

The small `tetorica_genesis_wav`, `tetorica_master_system_wav` and `tetorica_msx_wav` hosts mix YM2612+Sega PSG, YM2413+Sega PSG and AY-3-8910+YM2413, respectively, into synthetic WAVs. `tetorica_pc98_ym2203_wav` uses a single YM2203's FM and SSG voices. `tetorica_pc98_ym2608_wav` adds synthetic rhythm-ROM percussion and ADPCM-B RAM playback to one OPNA's FM/SSG mix; it generates the encoded bytes rather than distributing hardware ROM contents. Their fixed example gains do not define SDK-wide mixing defaults or emulate complete machines.

`reference/javascript/` preserves the Analyzer's MSM5205 and OKIM6295 engines as synchronous JavaScript references, with their own provenance, component notices and offline example. SDK Native/WASM integrations are not provided for these engines. Separately pinned, explicitly BSD-licensed upstream C/C++ references live in their vendor directories and are cataloged as `upstreamReferences`. Their manifests document omitted framework dependencies; they are not part of the existing build targets.

Synchronous WASM primitives used to implement `read()` and `generateStereo()` remain part of the low-level interface. The asynchronous Native IPC path does not replace the synchronous calls needed by AudioWorklet consumers. JavaScript APIs and host transport selection remain responsibilities of the consuming projects.
