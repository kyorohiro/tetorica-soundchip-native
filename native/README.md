# Native sources

This directory contains the existing chip-level C++/C ABI wrappers as bootstrap
references, without Rust, Tauri, CPAL, the application scheduler, Mixer, FX,
QuickJS, UI, or audio-device code. Existing applications still use their current
sources. Collecting them here does not yet switch those consumers to this SDK.

`reference/tauri/` preserves the existing exported functions and PCM behavior.
HuC6280 and Nuked include paths are relocated to the shared SDK source layout.
The YM2612 and YM2151 adapters also carry the recorded template-ownership
amendments below.
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

The independently buildable Native components are **ymfm YM2612, YM2151 and
YM2413, plus Sega PSG**:

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
All four fixtures run through CTest with assertions enabled in Release builds.
See the [verification record](../docs/verification.md)
for completed checks and platform results. Other collected wrappers still need
their own standalone targets and verification.

`src/ymfm_opn_provider.cpp` includes the unchanged shared ymfm provider and explicitly instantiates the Native OPN engine/channel/operator templates. The adapter declares those templates `extern`; optimized providers must emit their callable definitions even when the provider's own calls are inlined. This incorporates the Tauri link fix without changing DSP behavior or the exported ABI. The provider's origin and include relocation are recorded in the source inventories.

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
configuration; it does not add a standalone AY-3-8910 or complete MSX target.

At the default 3,579,545 Hz clock, musical pitch is
`clock * FNUM * 2^BLOCK / (72 * 2^19)`, with F-NUM 1–511 and BLOCK 0–7. The
OPN formula has a different block factor; do not reuse it for OPLL. The offline
example below shows register-level melody and rhythm configuration.

## Offline WAV examples

`examples/genesis_wav.cpp` links `tetorica::ym2612` and `tetorica::segapsg` in
`tetorica_genesis_wav`. `examples/master_system_wav.cpp` links
`tetorica::ym2413` and `tetorica::segapsg` in `tetorica_master_system_wav`.
The second example uses OPLL's built-in piano, light rhythm and PSG tones.
From the SDK root:

```sh
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release --target tetorica_genesis_wav tetorica_master_system_wav
# Single-configuration generators:
./build/native/native/tetorica_genesis_wav "genesis demo.wav"
./build/native/native/tetorica_master_system_wav "master system demo.wav"
# Visual Studio on Windows:
./build/native/native/Release/tetorica_genesis_wav.exe "genesis demo.wav"
./build/native/native/Release/tetorica_master_system_wav.exe "master system demo.wav"
```

The one required argument selects the output WAV; the parent directory must
exist. Each example generates exactly 144,000 frames of stereo PCM16 at 48 kHz
from synthetic notes/percussion, with no audio device or external assets.
They use their chips' respective hardware pitch equations, fixed mix headroom
and short output fades. PSG stereo remains `0xff`; the OPLL output is mono on
both channels. Rendering and file writing happen offline, rather than inside
an audio callback.

`TETORICA_NATIVE_BUILD_EXAMPLES` defaults to `ON`. Disable it with
`-DTETORICA_NATIVE_BUILD_EXAMPLES=OFF` for a library-only integration; tests are
controlled separately by `TETORICA_NATIVE_BUILD_TESTS`.

## Collected component references

| Public component | Reference wrapper or support | Native CMake build |
| --- | --- | --- |
| Sega PSG | `native_genesis_psg.h`, independent `native_genesis_game_gear.cpp` wrapper | Standalone PSG target and fixture; no OPLL core |
| YM2612 | `native_genesis_ym2612.cpp`; Nuked alternative in `native_genesis_nuked.cpp` and `.inc` | ymfm built and tested; Nuked reference only |
| YM2203 | `native_genesis_ym2203.cpp` | Not yet connected |
| YM2608 | `native_genesis_ym2608.cpp` | Not yet connected |
| YM2610 / YM2610B | `native_genesis_ym2610b.cpp`, selected immutable variant | Not yet connected |
| YM2151 | `native_genesis_ym2151.cpp` | Standalone OPM target and fixture; X68000 OKI remains reference-only |
| YM2413 | `native_genesis_ym2413.cpp`, `native_genesis_opll.h` | Standalone OPLL target and fixture; MSX AY remains reference-only |
| AY-3-8910 | `native_genesis_ay8910.cpp` | Not yet connected |
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
