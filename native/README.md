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

The independently buildable Native components are **ymfm YM2612 and YM2151**:

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
reject C++ allocation/free in the tested paths. Both fixtures run through CTest
with assertions enabled in Release builds. See the [verification record](../docs/verification.md)
for completed checks and platform results. Other collected wrappers still need
their own standalone targets and verification.

`src/ymfm_opn_provider.cpp` includes the unchanged shared ymfm provider and explicitly instantiates the Native OPN engine/channel/operator templates. The adapter declares those templates `extern`; optimized providers must emit their callable definitions even when the provider's own calls are inlined. This incorporates the Tauri link fix without changing DSP behavior or the exported ABI. The provider's origin and include relocation are recorded in the source inventories.

`src/ymfm_opm_provider.cpp` does the same for the OPM templates used by YM2151.
Both linkage changes come from Tauri commit
`83bfba8cbbc272a02279aba250b13e4c0f6ca57b`. The shared ymfm vendor files and WASM
recipes are unchanged. The YM2151 target is an independent OPM implementation;
it does not allocate an OKIM6258 core or provide a complete X68000 sound system.

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

## Collected component references

| Public component | Reference wrapper or support | Native CMake build |
| --- | --- | --- |
| Sega PSG | `native_genesis_psg.h`, Game Gear/Master System wrappers | Not yet connected |
| YM2612 | `native_genesis_ym2612.cpp`; Nuked alternative in `native_genesis_nuked.cpp` and `.inc` | ymfm built and tested; Nuked reference only |
| YM2203 | `native_genesis_ym2203.cpp` | Not yet connected |
| YM2608 | `native_genesis_ym2608.cpp` | Not yet connected |
| YM2610 / YM2610B | `native_genesis_ym2610b.cpp`, selected immutable variant | Not yet connected |
| YM2151 | `native_genesis_ym2151.cpp` | Standalone OPM target and fixture; X68000 OKI remains reference-only |
| YM2413 | `native_genesis_ym2413.cpp`, `native_genesis_opll.h` | Not yet connected |
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
