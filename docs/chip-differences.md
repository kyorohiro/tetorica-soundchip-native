# Chip origins and differences between WASM and Native backends

This document describes the initial source snapshot inspected on 2026-10-24. The **reference Web implementation** is the Browser / WASM side of `hello_ymfm`; the **reference Native implementation** is the Tauri project `tetorica-fm2612-playground-tauri`. Upstream chip projects, those applications and this distributable SDK are separate layers.

## Comparison layers

1. **Upstream → Tetorica:** existing standalone adaptations, observation, muting, live edits and other changes. A core may already differ from its upstream source.
2. **Reference applications → SDK:** changes made while importing sources for distribution. Origins, versions and original / packaged hashes identify each snapshot.
3. **WASM ↔ Native:** shared cores can still have different rate conversion, Stop behavior, sample memory, output settings and APIs.

This SDK collects implementations already developed and checked in the reference applications, retaining their differences. Maintaining the collection does not require replacing every variant with one common version.

## Changes made while importing the SDK

The original C/C++ and WASM import commit is `0fff93d46ab3e9227ecffcacdf96f3ca115e6f72`. The JavaScript ADPCM references were imported separately from `a9f9a8a86ec4bd182224b1bc3979cfde6cf95b48`. [source_inventory.json](../catalog/source_inventory.json) records each component's source version; it and [Native SOURCES.json](../native/reference/SOURCES.json) identify the exact included bytes by hash.

| Area | Inspection result |
| --- | --- |
| Original shared cores, WASM wrappers and accompanying documents | All 170 files across the original 15 components match their `originPath` sources byte for byte. MSFA's actual source comes from the standalone package checkout |
| JavaScript ADPCM references | Both engines and their license texts remain byte-identical to the imported Tetorica files. Component READMEs now describe independently collected upstream references and license omissions. These references are separate from the 22 Playground IDs and 27 WASM artifacts |
| Native reference sources | Original and packaged hashes record include relocations and the YM2612/YM2151/YM2203/YM2608 template-ownership amendments; the exported ABI and DSP behavior are preserved |
| HuC6280 Native | `native_genesis_huc6280.cpp`: changes `../native-huc6280/snapshot/third_party/mame-huc6280/huc6280.{h,cpp}` to `huc6280.{h,cpp}` |
| Nuked Native | `native_genesis_nuked.cpp`: changes `../native-nuked/snapshot/wasm/nuked_opn2_wasm.c` to `nuked_opn2_wasm.c` |
| YM2612 fixture | `native/tests/ym2612_fixture.cpp`: includes the public forwarder `<tetorica/ym2612.hpp>` instead of the existing wrapper header directly |
| YM2612 Native linkage | Incorporates Tauri commit `83bfba8cbbc272a02279aba250b13e4c0f6ca57b`: removes the adapter's redundant local helper instantiation and adds `native/src/ymfm_opn_provider.cpp` with explicit OPN template definitions. The provider's include points to the SDK's unchanged `vendor/ymfm/ymfm_opn.cpp` |
| YM2151 Native linkage and build | Incorporates the OPM fix from the same Tauri commit: the adapter uses `extern` declarations and `native/src/ymfm_opm_provider.cpp` explicitly instantiates OPM engine/channel/operator templates from the unchanged `vendor/ymfm/ymfm_opm.cpp`. Adds the standalone target, public `<tetorica/ym2151.hpp>` forwarder and offline fixture. This OPM target does not include X68000's OKIM6258 path |
| Sega PSG standalone build | Adds `tetorica::segapsg` using the unchanged independent Game Gear wrapper, shared `native_genesis_psg.h` and Tetorica `vendor/ymfm/segapsg.cpp`. The public `<tetorica/segapsg.hpp>` forwarder preserves the `native_game_gear_*` ABI. The target includes no Genesis FM or Master System OPLL core; a separate offline example links it with YM2612 |
| YM2413 standalone build | Adds `tetorica::ym2413`, the public `<tetorica/ym2413.hpp>` forwarder and existing `native_ym2413_*` ABI using the cached Native OPLL adapter. The relocated full Native OPL explicit-template provider links unchanged ADPCM/PCM support; this target constructs only YM2413, without completing the other OPL standalone targets. The offline Master System FM example combines it with Sega PSG |
| AY-3-8910 standalone build | Adds `tetorica::ay8910` and the public `<tetorica/ay8910.hpp>` forwarder using the unchanged Native adapter and existing `native_ay8910_*` ABI. It keeps AY type 0 / flags 1, three-channel averaging and outer clock conversion; it does not add Native YM2149/type/flags selection. The offline MSX example combines this independent AY handle with YM2413 |
| YM2203 standalone build | Adds `tetorica::ym2203` and the public `<tetorica/ym2203.hpp>` forwarder, retaining `native_ym2203_*` and both constructor profiles. OPN helper template ownership moves to the common Native provider; SSG/ADPCM link dependencies and vendor DSP bytes remain unchanged. The offline PC-98 example uses one YM2203 with three FM and three SSG voices, without YM2608 resources |
| YM2608 standalone build | Adds `tetorica::ym2608` and the public `<tetorica/ym2608.hpp>` forwarder, retaining `native_ym2608_*`, its two state layouts and both constructor profiles. The common Native OPN provider owns the required OPNA helper definitions, with unchanged SSG/ADPCM dependencies and vendor DSP. The offline example uploads original synthetic ADPCM-A ROM and ADPCM-B RAM data alongside FM/SSG playback |
| Build procedures | Relocates `src/`, `third_party/` and related references into the SDK's `vendor/` / `wasm/` layout; adds standalone build entry points and source / output hash records |

An unchanged import can still contain earlier upstream adaptations. It also does not imply identical Native and WASM APIs or output settings.

## Shared integration considerations

- WASM `*_generate` functions provide low-level block generation. Many Native wrappers convert to the device output rate, return a stereo frame through `*_sample`, and retain state for Stop, manual audition and individual source cancellation.
- Native `get_state` / snapshots are observational. A chip's opaque WASM save / load format is not necessarily interchangeable with a Native snapshot. Follow each header's contract.
- Native source cancellation is called by host ownership management. The SDK does not include the Tauri Rust queue, voice leases, copy-on-write memory lifetimes, 16-device / 64 MiB budgets, retirement or CPAL integration.
- The reference JavaScript Synth, AudioWorklet, Keyboard, sample editor, Mixer defaults, master volume and FX are outside this SDK. Applications must configure their own mixing and output levels.
- The standalone Native CMake targets cover **YM2612/YM2151/YM2413/YM2203/YM2608 using ymfm, Sega PSG and AY-3-8910**. Other Native entries below describe included reference sources. Included WASM recipes, completed SDK builds and platform results are recorded separately in [verification.md](verification.md).

## Native / WASM differences for the 22 public chip IDs

These differences mainly originate in the reference applications. Importing the sources into this SDK did not create them. Native links point to the included reference code.

| Public ID | Core and WASM interface | Native differences and integration requirements |
| --- | --- | --- |
| `ym2612` | [ymfm](../vendor/ymfm/ymfm_opn.cpp) / [WASM](../wasm/ym2612_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ym2612.cpp) adds output-rate averaging / hold, an authored-register shadow, separate FM / CSM cancellation, DAC retention and deferred audition. A standalone Native target is provided. See Nuked below |
| `ym2203` | [ymfm](../vendor/ymfm/ymfm_opn.cpp) / [WASM](../wasm/ym2203_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ym2203.cpp) handles the prescaler, retained SSG levels, Stop / CSM, audition at FM clock boundaries and output-rate conversion. The standalone `tetorica::ym2203` target exposes three FM and three SSG voices, including shared noise/envelope and synchronous read/status/IRQ/state observations. Both paths send combined mono FM+SSG to left and right. `native_ym2203_create()` retains output-rate remainder/held PCM across reset; `create_extra()` clears both, matching the additional Worklet profile. At the standard prescaler the SSG effective clock is master/2; unlike YM2608, tone frequency is master/(32*period). This target provides no YM2608 rhythm or ADPCM resources |
| `ym2608` | [ymfm](../vendor/ymfm/ymfm_opn.cpp) / [WASM](../wasm/ym2608_wasm.cpp) | The standalone `tetorica::ym2608` target retains the [Native adapter](../native/reference/tauri/native_genesis_ym2608.cpp): six FM, three SSG, six fixed-address rhythm voices and ADPCM-B, with preallocated 8 KiB ROM / 2 MiB RAM and synchronous bounded copies. The WASM ROM vector grows on load; its RAM is 2 MiB. Both Native profiles retain memory on Stop/reset. Primary reset clears outer held PCM/remainder; `create_extra()` retains it, opposite to YM2203. Additional cancellation retains separate held buses. `get_state()` / `get_extra_state()` are observational, whereas raw ADPCM CPU-data reads and extended-status IRQ propagation have side effects. Hosts supply encoded data, serialized access and event timing. The example's generated rhythm bytes are not a hardware ROM |
| `ym2610` | [ymfm](../vendor/ymfm/ymfm_opn.cpp) / [WASM](../wasm/ym2610b_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ym2610b.cpp) also selects the four-FM variant, mask `0x36`. Additional-instance ADPCM-A / B ROM uses replaceable sparse 64 KiB pages. WASM uses ROM vectors |
| `ym2610b` | [ymfm](../vendor/ymfm/ymfm_opn.cpp) / [WASM](../wasm/ym2610b_wasm.cpp) | The same [Native wrapper](../native/reference/tauri/native_genesis_ym2610b.cpp) selects the six-FM variant, mask `0x3f`. WASM `ym2610b_create()` defaults to six FM channels, while the older Native `create_extra()` convenience function defaults to four. Public adapters pass the variant explicitly; raw ABI constructors are not interchangeable by name alone |
| `ym2151` | [ymfm](../vendor/ymfm/ymfm_opm.cpp) / [WASM](../wasm/ym2151_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ym2151.cpp) adds per-source cached output / mute / CSM release, averaging / hold, audition and Stop. The standalone `tetorica::ym2151` target exposes eight FM channels, pan, timers/status/IRQ and observational state through the existing C ABI. It is OPM only; X68000's OKIM6258 integration remains reference-only |
| `ym2413` | [ymfm](../vendor/ymfm/ymfm_opl.cpp) / [WASM](../wasm/ym2413_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ym2413.cpp) retains separate cached output and cancellation for nine FM channels and rhythm aliases, power-on snapshot reset and held output during manual release. These operations have more specific semantics than a global key-off. The standalone `tetorica::ym2413` target provides nine melodic channels or six FM plus five logical drum voices sharing physical channels 6–8, with mono output on both stereo channels. Hosts can combine this FM component with the separate AY target for an MSX sound configuration; machine integration remains with the host |
| `ay8910` | [MAME adaptation](../vendor/mame-ay8910/README.md) / [WASM](../wasm/ay8910_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_ay8910.cpp) uses a 1,789,773 Hz reference with outer clock averaging/hold, per-channel held output, retained levels, audition and remixing on forced off. The standalone `tetorica::ay8910` target preserves this adapter and its synchronous observation API. It fixes AY type 0 / flags 1 and averages three channel outputs, copying mono to both stereo channels. Its ABI does not expose raw WASM's YM2149/type/flags selection or a motherboard analog mixer |
| `ym3526` | [ymfm](../vendor/ymfm/ymfm_opl.cpp) / [WASM](../wasm/ym3526_wasm.cpp) | Profile 0 of [Native OPL](../native/reference/tauri/native_genesis_opl.cpp) / [additional-instance OPL](../native/reference/tauri/native_genesis_extra_opl.cpp): nine mono FM channels, with mute, Stop, audition, CSM, per-source cancellation and output-rate conversion |
| `ym3812` | [ymfm](../vendor/ymfm/ymfm_opl.cpp) / [WASM](../wasm/ym3812_wasm.cpp) | Profile 1 of the same [Native OPL wrapper](../native/reference/tauri/native_genesis_opl.cpp). OPL2 waveform differences belong to the existing core; the wrapper handles Native stopping, cancellation and rate conversion |
| `y8950` | [ymfm](../vendor/ymfm/ymfm_opl.cpp) / [WASM](../wasm/y8950_wasm.cpp) | WASM uses a vector of up to 2 MiB. Native uses [host-owned pages / revisions](../native/reference/tauri/native_genesis_y8950_memory.h) and [ADPCM manual gates / repeat](../native/reference/tauri/native_genesis_opl.cpp). The Rust host responsible for copy-on-write storage, budgets and reclamation is outside this SDK |
| `ymf262` | [ymfm](../vendor/ymfm/ymfm_opl.cpp) / [WASM](../wasm/ymf262_wasm.cpp) | Both paths fold A+C / B+D into stereo. The [additional-instance Native wrapper](../native/reference/tauri/native_genesis_extra_opl.cpp) manages NEW mode authored / effective registers, four-operator pairs and per-source cancellation |
| `segapsg` | [Tetorica SegaPSG](../vendor/ymfm/segapsg.cpp) / [WASM](../wasm/segapsg_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_psg.h) adds outer averaging / hold at a retained reference clock, level retention and Stop; mute / stereo connect to the shared core. The standalone `tetorica::segapsg` target uses the independent Game Gear wrapper and keeps its `native_game_gear_*` ABI. Stereo `0xff` retains Genesis/Master System mono output on both channels; optional masks provide Game Gear routing. No OPLL core is included. Its location under `vendor/ymfm/` reflects the source layout: SegaPSG is a Tetorica addition absent from the historical ymfm comparison below |
| `gameboy` | [MAME adaptation](../vendor/mame-gameboy/README.md) / [WASM](../wasm/gameboy_apu_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_gameboy.cpp) keeps an internal 4,194,304 Hz reference with outer clock conversion, gate-only Stop and observation. **One Tauri-specific friend declaration is not applied to the shared header.** See the header requirement below |
| `nes` | [Tetorica C++ port](../vendor/tetorica-nes/README.md) / [WASM](../wasm/nesapu_wasm.cpp) | The [Native core](../native/reference/tauri/native_genesis_nes.cpp) and vendor core differ only in an include name. WASM adds block generation and state-field descriptors. The 400-byte state is observational. Full reset differs from gate-only Stop that retains RAM / wave data. Do not link both core implementations |
| `snes` | [SNES-SPC](../vendor/snes-spc/README.md) / [shared WASM wrapper](../wasm/spc_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_snes.cpp) runs S-DSP only, with 32 kHz interpolation, KON / KOFF protection and a timeline; it does not execute SPC700. [Timeline RAM / DSP / event data](../native/reference/tauri/native_genesis_snes.h) is borrowed immutably and needs host-managed lifetimes |
| `spc` | [SNES-SPC](../vendor/snes-spc/README.md) / [shared WASM wrapper](../wasm/spc_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_spc.cpp) is an SPC700 + S-DSP player, using 128-native-frame blocks and 32 kHz interpolation. Load / seek belong on the control side. It does not expose every WASM analysis API, such as trace / RAM discovery. The host retains the original file and synchronizes seek reconstruction / event draining |
| `huc6280` | [MAME adaptation](../vendor/mame-huc6280/README.md) / [WASM](../wasm/huc6280_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_huc6280.cpp) uses an internal 3,579,545 Hz reference with outer clock conversion, preserves selection during wave writes and adds per-channel off / observation. It uses private access and includes the vendor `.cpp` directly; avoid compiling that implementation twice |
| `rf5c164` | [MAME adaptation](../vendor/mame-rf5c164/README.md) / [WASM](../wasm/rf5c164_wasm.cpp) | [Native primary](../native/reference/tauri/native_genesis_rf5c164.cpp) uses the vendor core with outer averaging / hold around a 12.5 MHz reference. [Native additional instances](../native/reference/tauri/native_genesis_extra_rf5c164.cpp) use a separate implementation for per-voice held sums and cancellation. The difference extends beyond two thin wrappers |
| `okim6258` | [MAME adaptation](../vendor/mame-okim6258/README.md) / [WASM](../wasm/okim6258_wasm.cpp) | [Native additional instances](../native/reference/tauri/native_genesis_extra_okim6258.cpp) use 8 MHz / divider 512 / flags 12, with a sample feeder and repeat. They borrow up to 16 MiB of immutable ADPCM bytes, unlike the X68000 primary path's two sample-bank staging buffers |
| `pwm` | [32X extraction](../vendor/mame-32x-pwm/README.md) / [WASM](../wasm/pwm32x_wasm.cpp) | [Native](../native/reference/tauri/native_genesis_pwm.cpp) uses 23,011,361 Hz / gain 1 / duty mode, adding owner tags to FIFO / DAC latches, cancellation and Stop. The reference standalone JavaScript defaults to dac mode / gain 0.4; the VGM comparison path uses duty / 1 |
| `dx7` | [Shared MSFA core](../vendor/msfa/UPSTREAM.md) / [WASM](../wasm/dx7/dx7.cc) | [Native](../native/reference/tauri/native_genesis_dx7.cpp) uses six shared-core overrides, slot lease APIs, panic without reallocation and output conversion from a fixed internal 44.1 kHz rate. [MSFA details](research.md) describe each file |

### Game Boy Native header requirement

The reference Web / SDK [gameboy_apu.h](../vendor/mame-gameboy/gameboy_apu.h) differs from Tauri's `src-tauri/native-gameboy/snapshot/third_party/mame-gameboy/gameboy_apu.h` by this declaration inside `class GameboyApu`:

```cpp
friend struct NativeGameboyAccess; // Native state observation / gate-only Stop; DSP unchanged.
```

The Native wrapper uses it to observe and stop private counters / gates. The shared `.cpp` files match byte for byte. This friend declaration is currently absent from the SDK's shared vendor header. Apply the Native header difference when creating a Native Game Boy target; adding the reference wrapper alone is insufficient to build it.

### NES / HuC6280 translation units

- NES: `vendor/tetorica-nes/nes_core.cpp` and `native/reference/tauri/native_genesis_nes.cpp` define the same `native_nes_*` symbols. Compile the implementation appropriate to the WASM or Native target.
- HuC6280: the Native wrapper directly includes `huc6280.cpp`. Do not also add the vendor `.cpp` as another translation unit in that target. WASM uses the combination in its existing recipe.

## Existing upstream adaptations and inspection scope

This summary is based on the included README / UPSTREAM documents and current sources. Except where a MAME `upstream/` directory is retained, the SDK may not contain a complete unmodified upstream source tree. No project was fetched from the network for a full comparison against its latest version during this inspection.

| Chip or family | Existing Tetorica adaptations and limitations | Included evidence |
| --- | --- | --- |
| ymfm chips | Observation, advancing feedback while muted, shared OPN frequency latches, dynamic OPL3 four-operator allocation, save / restore corrections and signed-shift fixes | [ymfm sources](../vendor/ymfm/), [source inventory](../catalog/source_inventory.json); see the historical comparison below |
| Sega PSG | Tetorica implementation covering tone / noise / stereo and host behavior | [segapsg.cpp](../vendor/ymfm/segapsg.cpp), [.h](../vendor/ymfm/segapsg.h) |
| Nuked-OPN2 | Uses kyorohiro fork `335747d78cb0abbc3b55b004e62dad9763140115`. The complete changes from nukeykt's original to this fork were not compared here | [README](../vendor/nuked-opn2/README.md); the included core matches both reference applications byte for byte |
| AY-3-8910 | Removes MAME device / CPU / stream infrastructure; retains an AY / YM2149 subset, averages three independent output tables and uses an integer-phase resampler. MAME's nonlinear single-pin mix and all chip variants are not implemented | [README](../vendor/mame-ay8910/README.md), [upstream originals](../vendor/mame-ay8910/upstream/) |
| Game Boy | Ports the MAME DMG model to per-cycle ticks and an integrating resampler. Omits CGB / AGB, readback and the DMG wave-RAM corruption glitch | [README](../vendor/mame-gameboy/README.md), [upstream originals](../vendor/mame-gameboy/upstream/) |
| HuC6280 | Makes six-channel wave / DDA / noise / LFO standalone; adds reset / mute / integer-phase averaging. Retains the original model's imperfect noise / LFO behavior | [README](../vendor/mame-huc6280/README.md), [upstream originals](../vendor/mame-huc6280/upstream/) |
| RF5C164 | Exposes the 16-bit RF5C164 output with local 64 KiB RAM. Removes MAME CPU / device / sample-end callbacks; reset retains RAM | [README](../vendor/mame-rf5c164/README.md), [upstream originals](../vendor/mame-rf5c164/upstream/) |
| OKIM6258 | Extracts the MAME decoder. Supports 4-bit ADPCM; 3-bit operation and recording are unavailable. Adds VGM pan / clock / divider and fractional hold | [README](../vendor/mame-okim6258/README.md), [upstream originals](../vendor/mame-okim6258/upstream/) |
| 32X PWM | Extracts FIFO / timer / routing. Omits SH2 / DMA / video / analog PWM filtering; exposes interrupts as counts | [README](../vendor/mame-32x-pwm/README.md), [upstream originals](../vendor/mame-32x-pwm/upstream/), [core](../wasm/pwm32x_core.h) |
| NES + FDS | C++ port of the existing JSNES / fixNES adaptations, retaining the JavaScript int32 / rounding / nonlinear mix / filter / FDS behavior model | [README](../vendor/tetorica-nes/README.md), [JSNES origin](../vendor/tetorica-nes/UPSTREAM-JSNES.md), [FDS origin](../vendor/tetorica-nes/UPSTREAM-FDS.md); the complete original JavaScript sources are outside this SDK |
| SNES / SPC | Uses the accurate DSP with output mute, undefined-behavior fixes, 16-bit RAM wrap and trace / read-mask hooks. Does not use the fast DSP, optional filter, tempo control or surround-disable feature | [README](../vendor/snes-spc/README.md); the complete unmodified library and full Nintendo IPL ROM are not bundled |
| MSFA / DX7 | Standalone adaptation, initialized state, scalar selection, live controls and extreme-frequency arithmetic fixes, plus six Native overrides | [Details](research.md), [UPSTREAM](../vendor/msfa/UPSTREAM.md) |

The included ymfm sources were compared with Aaron Giles's commit `16e1d4281a59a60e589cf21f6b93329a8be5ff7a` (2024-09-06), retained in the reference repository's Git history. Its subject is `Use snprintf instead of sprintf to fix #59. Use std::array for operators to remove the need for array_size.` This establishes differences against that historical revision; it does not establish the current upstream version or its branch name at the time.

### YM2612 Nuked Native differences

The shared [nuked_opn2_wasm.c](../wasm/nuked_opn2_wasm.c) uses the existing adapter that advances 24 internal clocks × 11. The [Native wrapper](../native/reference/tauri/native_genesis_nuked.cpp) adds symbol prefixes and initial process-global chip-type configuration. [Additional YM2612 controls](../native/reference/tauri/native_genesis_nuked_ym2612.inc) provide source cancellation, Stop and output-rate averaging / hold. Only the include location changed during SDK import. A standalone Native SDK target for Nuked is not yet provided.

## Additional WASM artifacts outside the 22 public IDs

| Artifact | Changes from the reference Web implementation and Native availability |
| --- | --- |
| `ym3438` | ymfm variant using the [shared wrapper](../wasm/opn_variant_wasm.cpp); matches the reference bytes. No standalone Native SDK adapter |
| `ymf276` | Same shared wrapper, retaining its ymfm variant behavior |
| `ymf288` | Same shared wrapper, retaining its ymfm variant behavior |
| `ymf278b` | [ymfm OPL4 wrapper](../wasm/ymf278b_wasm.cpp), matching the reference bytes. No standalone Native SDK adapter; the host prepares sample ROM |
| `segapcm` | [README](../vendor/mame-segapcm/README.md). Matches the reference bytes; adapts the 16-voice 315-5218 to VGM flat offsets, a ROM vector and bank settings. Reset retains ROM. No Native SDK adapter |
| `k051649` | [README](../vendor/mame-k051649/README.md). Matches the reference bytes; adapts five-channel SCC / SCC+ to VGM ports / registers. SCC channels 4 / 5 share a waveform; SCC+ keeps them independent. Reset additionally clears wave RAM. No Native SDK adapter |

## JavaScript-only Analyzer reference engines

| Reference | Origin and behavior | Native / WASM status |
| --- | --- | --- |
| `msm5205` | [Engine](../reference/javascript/msm5205audioengine.js), imported unchanged from `web/msm5205audioengine.js`. The libvgm-derived model includes ADPCM decoding, a leaky accumulator, FIFO, reset, prescaler, 3/4-bit data, external VCLK, and fractional output timing. Mute masks output while decoder timing continues. [Original notices](../vendor/libvgm-msm5205/README.md) and [BSD license](../vendor/libvgm-msm5205/LICENSE) are retained | Not ported. The runnable JavaScript source is a behavioral reference; no CMake target or WASM recipe is claimed |
| `okim6295` | [Engine](../reference/javascript/okim6295audioengine.js), imported unchanged from `web/okim6295audioengine.js`. The MAME/libvgm-derived model has four ADPCM voices, sample-ROM command handling, clock/pin7 changes, standard and NMK112 banks, and held-sample output timing. Mute retains voice progression. [Original notices](../vendor/mame-okim6295/README.md) and [BSD license](../vendor/mame-okim6295/LICENSE) are retained | Not ported. The host supplies ROM data and event timing; the example generates synthetic data |

Both engines render stereo Float32 blocks synchronously and need no AudioContext. Their source comments retain the original repository paths for provenance; this SDK's relocated notices are linked above. The existing port notices did not pin their historical upstream revisions, so that limitation remains recorded with the exact Tetorica revision and hashes.

Separately collected source references now include libvgm's BSD-declared `msm5205.c`, `okim6295.c`, `okiadpcm.c` and `okiadpcm.h`, plus MAME's BSD-declared OKIM6295/ADPCM C++ files and headers. Each vendor snapshot records a full official commit and SHA-256 hashes. A newly collected revision does not establish the older JavaScript port's baseline.

These upstream C/C++ files are reference-only. MAME's framework is not bundled; libvgm integration headers and support/player code without explicit license declarations are omitted, with [the upstream licensing explanation](https://github.com/ValleyBell/libvgm/issues/129) linked in each component guide. The JavaScript engines and existing build targets do not depend on these omitted files. No game ROM is included.

See [reference/javascript/README.md](../reference/javascript/README.md) for the standalone example and APIs. These two references do not add Playground modes or `createSoundChip()` IDs.

## Licensing and future updates

Tetorica-authored SDK integration code and documentation use [BSD-3-Clause](../LICENSE), consistent with `tetorica-fm2612`, except where an existing explicit license applies. Third-party cores, adaptations with their own license and all existing copyright / license notices retain their terms. In particular, the six MSFA Native overrides retain Apache-2.0; Tetorica-authored wrapper headers without an individual declaration use the SDK's BSD-3-Clause default. [LICENSES.md](../LICENSES.md) maps the component terms.

When updating a chip, record the import version and hashes, upstream adaptations, import changes, Native-specific changes, required build combinations, API / Stop / sample-memory / output differences and verification scope. If variants are unified, record the revision and comparison results that established their equivalence.
