# Native sources

This directory contains the existing chip-level C++/C ABI wrappers as bootstrap
references, without Rust, Tauri, CPAL, the application scheduler, Mixer, FX,
QuickJS, UI, or audio-device code. Existing applications still use their current
sources. Collecting them here does not yet switch those consumers to this SDK.

`reference/tauri/` preserves the existing exported functions and PCM behavior.
HuC6280 and Nuked include paths are relocated to the shared SDK source layout.
The YM2612, YM2151, YM2413, YM2203 and YM2608 adapters also carry the recorded
template-ownership amendments below.
`reference/SOURCES.json` records the original and packaged byte hashes.
The vendor cores have one canonical copy in `../vendor/`; they are not copied
again under `native/`.

[Per-chip differences](../docs/chip-differences.md) distinguish upstream
adaptations, SDK relocation, and existing Native/WASM API or rendering
differences. [MSFA details](../docs/research.md) describe all six Native
overrides, including slot-control APIs and panic behavior, not just portability.

One known prerequisite is not yet applied to the common vendor tree: the Tauri
Game Boy header adds `friend struct NativeGameboyAccess` to `GameboyApu`.
The Native reference wrapper requires this access for observation and gate-only
Stop. The common SDK header retains the Browser version. A future Native
Game Boy target must include the Native header adaptation; adding the wrapper
alone is insufficient. See the per-chip document for this and the NES/HuC6280
translation-unit constraints.

## Build support

The independently buildable Native components are **ymfm YM2612, YM2151,
YM2413, YM2203 and YM2608, plus Sega PSG and AY-3-8910**:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
```

The same targets can be configured directly with `cmake -S native -B
build/native`. Neither build downloads dependencies.

| CMake target | Static library target | Public C++ header | Existing C ABI |
| --- | --- | --- | --- |
| `tetorica::ym2612` | `tetorica_native_ym2612` | `<tetorica/ym2612.hpp>` | `native_ym2612_*`, `NativeYm2612State` |
| `tetorica::ym2151` | `tetorica_native_ym2151` | `<tetorica/ym2151.hpp>` | `native_ym2151_*`, `NativeYm2151State` |
| `tetorica::ym2413` | `tetorica_native_ym2413` | `<tetorica/ym2413.hpp>` | `native_ym2413_*`, `NativeYm2413State` |
| `tetorica::segapsg` | `tetorica_native_segapsg` | `<tetorica/segapsg.hpp>` | `native_game_gear_*`, `NativeGameGearState` |
| `tetorica::ay8910` | `tetorica_native_ay8910` | `<tetorica/ay8910.hpp>` | `native_ay8910_*`, `NativeAy8910State` |
| `tetorica::ym2203` | `tetorica_native_ym2203` | `<tetorica/ym2203.hpp>` | `native_ym2203_*`, `NativeYm2203State` |
| `tetorica::ym2608` | `tetorica_native_ym2608` | `<tetorica/ym2608.hpp>` | `native_ym2608_*`, `NativeYm2608State`, `NativeYm2608ExtraState` |

The exported names and observational state layouts remain unchanged. These
headers expose the current reference C ABI to C++ hosts; they are not yet a new
versioned, portable C-only SDK header.

The YM2612 fixture exercises two independent instances, all six FM channels, DAC, timers,
status/IRQ, clock changes, observational snapshots, cancellation, retained Stop,
reset, mute, and deferred audition edges. It checks zero C++ allocation/free
during rendering and works in Release builds with assertions enabled. It opens
no audio device.

The YM2151 fixture covers eight FM channels, left/right pan, independent
instances, timers/status/IRQ, clock changes, non-advancing observations, separate
FM/CSM cancellation, audition, retained Stop and reset. Its rendering checks also
reject C++ allocation/free in the tested paths.

The Sega PSG fixture covers the independent three-tone/noise renderer, stereo
routing, mute, retained controls, Stop/reset, clock changes and observation.
The YM2413 fixture covers melodic channels, built-in/user instruments, rhythm
aliases, retained controls, clock conversion, Stop/reset, cancellation,
observation and deferred audition. Its five rhythm voices share physical FM
channels 6–8 rather than adding five independent melodic channels.
The AY fixture covers three independent tone/noise voices, the shared hardware
envelope, readback/observation, clock conversion, retained levels, Stop/reset
and audition. The YM2203 fixture exercises three FM plus three SSG voices,
prescalers, timers/status/IRQ, separate FM/CSM cancellation, retained Stop,
observation and primary/additional reset profiles. The YM2608 fixture covers
FM/SSG/rhythm/ADPCM-B, memory boundaries and retention, timers/status/IRQ,
cancellation, observation and its distinct primary/additional output profiles.
All seven fixtures run through CTest with assertions enabled in Release builds.
See the [verification record](../docs/verification.md)
for completed checks and platform results. Other collected wrappers still need
their own standalone targets and verification.

`src/ymfm_opn_provider.cpp` includes the unchanged shared ymfm provider and explicitly instantiates the Native OPN engine/channel/operator templates. The adapter declares those templates `extern`; optimized providers must emit their callable definitions even when the provider's own calls are inlined. This incorporates the Tauri link fix without changing DSP behavior or the exported ABI. The provider's origin and include relocation are recorded in the source inventories.

The YM2203 and YM2608 targets reuse this OPN provider and unchanged SSG/ADPCM
link dependencies. Each constructs only its selected chip. Linking YM2203 does
not allocate YM2608 rhythm/sample resources; a YM2608 handle allocates its own
fixed ROM and RAM buffers, whose contents the host supplies.

`src/ymfm_opm_provider.cpp` does the same for the OPM templates used by YM2151.
Both linkage changes come from Tauri commit
`83bfba8cbbc272a02279aba250b13e4c0f6ca57b`. The shared ymfm vendor files and WASM
recipes are unchanged. The YM2151 target is an independent OPM implementation;
it does not allocate an OKIM6258 core or provide a complete X68000 sound system.

`src/ymfm_opl_provider.cpp` supplies the existing Native OPL/OPLL explicit
template definitions. The YM2413 target links the unchanged ADPCM/PCM support
translation units required by that provider, but constructs only YM2413.
Other OPL standalone targets are not implied by this linkage; their adapters
remain reference sources. Shared vendor bytes and WASM recipes are unchanged.

## Embed YM2151

Link the selected chip target from your application's CMake configuration:

```cmake
add_subdirectory(vendor/tetorica-soundchip-native)
target_link_libraries(your_application PRIVATE tetorica::ym2151)
```

This example configures a centered FM voice on channel 0 and renders 512 stereo
frames at the requested output rate:

```cpp
#include <tetorica/ym2151.hpp>

int main() {
    void* chip = native_ym2151_create(48000);
    if (!chip) return 1;
    const auto write = [chip](unsigned reg, unsigned value) {
        native_ym2151_write(chip, reg, value);
    };
    for (unsigned op = 0; op < 4; ++op) {
        const unsigned offset = op * 8; // Channel 0 in each operator group.
        write(0x40 + offset, 1);
        write(0x60 + offset, op == 0 ? 24 : 127);
        write(0x80 + offset, 31);
        write(0xa0 + offset, 0);
        write(0xc0 + offset, 0);
        write(0xe0 + offset, 15);
    }
    write(0x20, 0xc7); // Left + right, algorithm 7.
    write(0x28, 0x4a); // Key code.
    write(0x30, 0);    // Key fraction.
    write(0x08, 0x78); // All four operators on channel 0.

    float left[512], right[512];
    for (unsigned i = 0; i < 512; ++i) {
        native_ym2151_sample(chip, &left[i], &right[i]);
    }
    // Send these buffers to your audio output or file renderer.
    native_ym2151_stop(chip);
    native_ym2151_destroy(chip);
}
```

Keep the chip alive between audio callbacks. Create/destroy it outside the
callback, serialize register writes with rendering, and schedule events in the
host. `native_ym2151_get_state()` observes authored registers, key gates and
status without advancing audio; it is not a transferable WASM save state.

## Embed Sega PSG

Link `tetorica::segapsg` and include `<tetorica/segapsg.hpp>`. The public ABI keeps
its existing `native_game_gear_*` names for compatibility. Despite those names,
this target owns only one Sega PSG: three tone channels and one noise channel,
without a Genesis FM or Master System OPLL core. The core is the Tetorica
SegaPSG implementation stored under `vendor/ymfm/`; it is not a Yamaha FM chip.

`native_game_gear_create(output_rate)` defaults to a 3,579,545 Hz chip clock and
stereo mask `0xff`. Retain that mask for Genesis/Master System PSG output on
both channels. Game Gear hosts can use `native_game_gear_set_stereo()` for
per-channel routing: bits 0–3 enable right output and bits 4–7 enable left output.

For a tone, calculate the 10-bit period as `round(clock / (32 * frequency_hz))`,
then write its latch low nibble, six high bits, and attenuation byte through
`native_game_gear_write()`. Periods 0/1 have constant-output behavior, so a
musical tone should use 2–1023. Attenuation 0 is loudest and 15 is silent.
`native_game_gear_sample()` renders one stereo frame at the requested output
rate. Stop, mute, audition, reset and observational state access retain their
existing Native semantics; host scheduling and synchronization stay outside
the library.

## Embed YM2413 / OPLL

Link `tetorica::ym2413` and include `<tetorica/ym2413.hpp>` for the existing
`native_ym2413_*` ABI. The target owns one YM2413 with nine melodic channels,
or six melodic channels plus BD/SD/TOM/CYM/HH rhythm voices sharing physical
channels 6–8. It supports the built-in instruments and the chip's one shared
user patch. Output is mono, copied to both stereo channels.

The Native voice APIs use logical IDs 0–8 for melodic channels and 9–13 for
BD/SD/TOM/CYM/HH. The host must account for rhythm's physical-channel sharing
when scheduling and managing ownership. Register writes, retained Stop,
forced release, deferred audition and observational snapshots keep their
existing adapter semantics. This chip can provide the FM part of an MSX-MUSIC
configuration. The separate AY target supplies the three-voice component; the
host still supplies scheduling and system integration.

At the default 3,579,545 Hz clock, musical pitch is
`clock * FNUM * 2^BLOCK / (72 * 2^19)`, with F-NUM 1–511 and BLOCK 0–7. The
OPN formula has a different block factor; do not reuse it for OPLL. The offline
example below shows register-level melody and rhythm configuration.

## Embed AY-3-8910

Link `tetorica::ay8910` and include `<tetorica/ay8910.hpp>` for the unchanged
`native_ay8910_*` ABI. The target owns one AY core independently of OPLL.
Its three voices each combine a tone gate and the shared noise generator,
then select a fixed volume or the one shared hardware envelope. The default
clock is 1,789,773 Hz; tone periods are `round(clock / (16 * frequency_hz))`
within 1–4095. Noise uses the shared five-bit period register, and writing the
envelope shape retriggers the shared envelope.

The Native wrapper retains AY type 0 and output flags 1 from the existing MAME
adaptation: three channel tables are averaged, then clock edits use outer
averaging/hold. Output is mono on both channels. Unlike the raw WASM wrapper,
this ABI has no YM2149/type/flags selector. This output model is not a claim
about an MSX motherboard's analog mixing circuit.

Register writes/readback and `native_ay8910_get_state()` remain synchronous.
State observation does not advance rendering. Zero-volume writes silence the
host voice while retaining its configured level; audition restores that level.
Stop/forced release clear the held output, while ordinary all-notes-off and
preview release retain their existing resampler timing. Create/destroy outside
the audio callback and serialize access with `native_ay8910_sample()`.

## Embed YM2203 / OPN

Link `tetorica::ym2203` and include `<tetorica/ym2203.hpp>` for the existing
`native_ym2203_*` ABI. One handle owns three FM channels and three SSG voices,
with shared SSG noise/envelope and a combined mono signal on both output
channels. The default master clock is 4,000,000 Hz. At the standard prescaler,
FM pitch is `clock * FNUM * 2^(BLOCK-1) / (72 * 2^20)`; write the high-frequency
register immediately before its low register because the OPN latch is shared.
The effective SSG clock is **master/2**, so its tone period is
`round(master_clock / (32 * frequency_hz))`, within 1–4095. YM2608 uses a
different SSG divider. Raw prescaler changes also change these pitch relations.

`native_ym2203_create(output_rate)` retains the primary adapter's reset
boundary: chip/register state resets, while output-rate remainder and held PCM
remain. `native_ym2203_create_extra(output_rate)` selects the additional-instance
profile, whose reset also clears that output history. These constructors are
intentional profiles of the same chip. Stop silences output while retaining
authored controls; ordinary register key-off preserves the FM release envelope.
Forced voice release, FM/CSM cancellation, retained SSG levels and deferred
audition keep their existing Native behavior. Voice IDs 0–2 are FM and 3–5 are
SSG. `read`, status/IRQ and `get_state` observe without advancing rendering;
the state structure is not a transferable WASM save state.

Create/destroy outside the audio callback, serialize writes and sampling, and
schedule events in the host. The PC-98 example below supplies register-level
notes without YM2608 rhythm or ADPCM data; it does not emulate a PC-98 machine.

## Embed YM2608 / OPNA

Link `tetorica::ym2608` and include `<tetorica/ym2608.hpp>` for the existing
`native_ym2608_*` ABI. One independent handle provides six FM channels, three
SSG voices, six fixed-address ADPCM-A rhythm voices and ADPCM-B playback.
Set port 0 register `0x29` to `0x9f` to enable all six FM channels while retaining
the default IRQ enables. At the default 8 MHz master clock and standard
prescaler, FM pitch is `clock * FNUM * 2^(BLOCK-1) / (144 * 2^20)`.
SSG's effective clock is master/4, so its tone period is
`round(master_clock / (64 * frequency_hz))`. This differs from YM2203.
FM, rhythm and ADPCM-B have stereo gates; SSG contributes equally to both sides.

Creation preallocates an initially zero **8 KiB rhythm ROM** and **2 MiB
ADPCM-B RAM**. `load_rom(chip, bytes, offset, size)` and
`load_memory(chip, bytes, offset, size)` synchronously copy encoded bytes into
those fixed buffers; the caller may release its input after a successful return.
Transfers reject ranges beyond their respective capacities and null pointers
for nonempty data. `copy_memory()` copies RAM back without reading the chip's
CPU data port, and `clear_memory()` zeros RAM. These APIs copy or change memory
without implicitly stopping playback: serialize them with sampling and stop the
affected decoder before replacing active data. They do not decode PCM/WAV or
supply a hardware rhythm ROM. ROM/RAM survive both reset and Stop profiles.

For ADPCM-B, stop with port 1 register `0x00=1`, then select eight-bit DRAM
addressing through register `0x01` low bits `2`. This mode uses 32-byte units;
write the start unit to `0x02/0x03` and the **inclusive last unit** to
`0x04/0x05`. Set `0x0c/0x0d=0xff` for the full RAM address limit. The stereo
gates are register `0x01` bits 7/6, volume is `0x0b` (0–255), and Delta-N is
`0x09/0x0a`. At the standard prescaler the decoded sample rate is
`DeltaN * clock / (144 * 65536)`. `0x00=0xa0` starts external-memory playback;
`0xb0` repeats the whole selected range. The offline example supplies both
ADPCM-A and ADPCM-B encoders for its own synthetic data.

`native_ym2608_create()` selects the primary profile, whose reset clears outer
output-rate remainder and held PCM. `native_ym2608_create_extra()` selects the
additional profile, whose reset retains that output history. This is the
**opposite reset-history choice to YM2203**. Both preserve uploaded memory,
clock and source mute settings. The additional profile also keeps independent
held buses for source cancellation. Voice IDs are FM 0–5, SSG 6–8, rhythm 9–14
and ADPCM-B 15. State observations through `get_state()` / `get_extra_state()`
do not advance audio, consume ADPCM data or propagate extended flags into IRQ
state. Raw `read()` can access CPU transfer data, and `read_status_hi()` updates
ADPCM status/IRQ propagation; those reads have hardware side effects and are
not substitutes for an observational snapshot. A snapshot is not a transferable
WASM save state. Keep access serialized and allocate/destroy outside callbacks.

## Offline WAV examples

`examples/genesis_wav.cpp` links `tetorica::ym2612` and `tetorica::segapsg` in
`tetorica_genesis_wav`. `examples/master_system_wav.cpp` links
`tetorica::ym2413` and `tetorica::segapsg` in `tetorica_master_system_wav`.
`examples/msx_wav.cpp` links `tetorica::ay8910` and `tetorica::ym2413` in
`tetorica_msx_wav`. The Master System FM example uses OPLL's built-in piano,
light rhythm and PSG tones; the MSX-style example uses AY tones/noise, a roughly
200 ms plucked envelope and an OPLL flute melody.
`examples/pc98_ym2203_wav.cpp` links only `tetorica::ym2203` in
`tetorica_pc98_ym2203_wav`, rendering all three FM and three SSG voices with
noise and a roughly 200 ms shared envelope at the standard prescaler.
`examples/pc98_ym2608_wav.cpp` links `tetorica::ym2608` in
`tetorica_pc98_ym2608_wav`. It uses FM voices 0/3/5, all three SSG voices,
synthetic ADPCM-A percussion uploaded into the fixed rhythm regions and an
ADPCM-B pluck uploaded into RAM. Both encoded datasets are generated locally;
the rhythm data does not reproduce the chip's original ROM sounds.
From the SDK root:

```sh
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release --target tetorica_genesis_wav tetorica_master_system_wav tetorica_msx_wav tetorica_pc98_ym2203_wav tetorica_pc98_ym2608_wav
# Single-configuration generators:
./build/native/native/tetorica_genesis_wav "genesis demo.wav"
./build/native/native/tetorica_master_system_wav "master system demo.wav"
./build/native/native/tetorica_msx_wav "msx demo.wav"
./build/native/native/tetorica_pc98_ym2203_wav "pc98 ym2203 demo.wav"
./build/native/native/tetorica_pc98_ym2608_wav "pc98 ym2608 demo.wav"
# Visual Studio on Windows:
./build/native/native/Release/tetorica_genesis_wav.exe "genesis demo.wav"
./build/native/native/Release/tetorica_master_system_wav.exe "master system demo.wav"
./build/native/native/Release/tetorica_msx_wav.exe "msx demo.wav"
./build/native/native/Release/tetorica_pc98_ym2203_wav.exe "pc98 ym2203 demo.wav"
./build/native/native/Release/tetorica_pc98_ym2608_wav.exe "pc98 ym2608 demo.wav"
```

The one required argument selects the output WAV; the parent directory must
exist. Each example generates exactly 144,000 frames of stereo PCM16 at 48 kHz
from synthetic notes/percussion, with no audio device or external assets.
They use their chips' respective hardware pitch equations, fixed mix headroom
and short output fades. Sega PSG stereo remains `0xff`; AY, OPLL and YM2203
output is mono on both channels. Their fixed example gains are not motherboard mix
ratios or SDK-wide defaults. Rendering and file writing happen offline,
rather than inside an audio callback.

`TETORICA_NATIVE_BUILD_EXAMPLES` defaults to `ON`. Disable it with
`-DTETORICA_NATIVE_BUILD_EXAMPLES=OFF` for a library-only integration; tests are
controlled separately by `TETORICA_NATIVE_BUILD_TESTS`.

## Collected component references

| Public component | Reference wrapper or support | Native CMake build |
| --- | --- | --- |
| Sega PSG | `native_genesis_psg.h`, independent `native_genesis_game_gear.cpp` wrapper | Standalone PSG target and fixture; no OPLL core |
| YM2612 | `native_genesis_ym2612.cpp`; Nuked alternative in `native_genesis_nuked.cpp` and `.inc` | ymfm built and tested; Nuked reference only |
| YM2203 | `native_genesis_ym2203.cpp` | Standalone OPN+SSG target and fixture; both constructor profiles |
| YM2608 | `native_genesis_ym2608.cpp` | Standalone OPNA target and fixture; both constructor profiles |
| YM2610 / YM2610B | `native_genesis_ym2610b.cpp`, selected immutable variant | Not yet connected |
| YM2151 | `native_genesis_ym2151.cpp` | Standalone OPM target and fixture; X68000 OKI remains reference-only |
| YM2413 | `native_genesis_ym2413.cpp`, `native_genesis_opll.h` | Standalone OPLL target and fixture |
| AY-3-8910 | `native_genesis_ay8910.cpp` | Standalone AY target and fixture; fixed Native type/flags |
| YM3526 / YM3812 / Y8950 / YMF262 | `native_genesis_opl.cpp`, `native_genesis_extra_opl.cpp` | Not yet connected |
| RF5C164 | `native_genesis_rf5c164.cpp`, `native_genesis_extra_rf5c164.cpp` | Not yet connected |
| OKIM6258 | `native_genesis_extra_okim6258.cpp` | Not yet connected |
| Game Boy | `native_genesis_gameboy.cpp` | Not yet connected |
| NES + optional FDS | `native_genesis_nes.cpp` | Not yet connected |
| PC Engine / HuC6280 | `native_genesis_huc6280.cpp` | Not yet connected |
| DX7 | `native_genesis_dx7.cpp` | Not yet connected |
| 32X PWM | `native_genesis_pwm.cpp` | Not yet connected |
| SNES S-DSP | `native_genesis_snes.cpp` | Not yet connected |
| SPC700 file player | `native_genesis_spc.cpp` | Not yet connected |

The grouped rows cover 22 public components. Component origins and notices are
kept with the shared vendor inventory; these adapters do not replace the
per-component notices. The Native DX7 snapshot has six host portability/API
variants under `reference/overrides/msfa/`. Unchanged MSFA files are shared from
`vendor/msfa/`; the overrides are explicitly recorded rather than silently
substituted into the WASM build.

## Licensing

Original Tetorica adapters, headers, and integration code are covered by the
BSD 3-Clause License in [LICENSE](../LICENSE), matching tetorica-fm2612, unless
a file carries an explicit different declaration. This repository-wide default
also covers original files without a separate file-level declaration.

Existing declarations and third-party terms are retained. In particular,
the MSFA sources and DX7 Native overrides retain Apache-2.0, the NES/FDS port
retains its Apache-2.0 and MIT notices, and the SNES/SPC and Nuked-derived
adapters retain their LGPL notices. See [LICENSES.md](../LICENSES.md) and
[catalog/native_inventory.json](../catalog/native_inventory.json) for the
component-specific records. `LICENSE.tools` is a compatibility copy of the
same BSD 3-Clause text, not a separate restriction on the original adapters.

## Boundaries to preserve during migration

The vendor chip cores implement chip behavior. Existing reference wrappers also
contain application policies such as source-rate resampling, authored register
shadows, mute, forced release, audition, and Stop. A later shared ABI must decide
which of these policies are common before consumers are switched.

The Y8950 page table in `native_genesis_y8950_memory.h` describes memory supplied
by a host. The Rust host still owns preparation, COW pages, budget accounting,
retirement, and final reclamation. None of the Native wrappers supplies the
Playground's 16-instance/64 MiB rack, timestamp queue, owner leases, or thread
coordination by itself. Each host must keep chip access serial and satisfy the
existing pointer-lifetime contract.
