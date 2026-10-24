# Native sources

This directory contains the existing chip-level C++/C ABI wrappers as bootstrap
references, without Rust, Tauri, CPAL, the application scheduler, Mixer, FX,
QuickJS, UI, or audio-device code. Existing applications still use their current
sources. Collecting them here does not yet switch those consumers to this SDK.

`reference/tauri/` preserves the existing exported functions and PCM behavior.
Only the HuC6280 and Nuked include paths are relocated to the shared SDK source
layout. `reference/SOURCES.json` records the original and packaged byte hashes.
The vendor cores have one canonical copy in `../vendor/`; they are not copied
again under `native/`.

## Build support

The initial independently buildable Native component is **ymfm YM2612**:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The same component can be configured directly with `cmake -S native -B
build/native`. Neither build downloads dependencies. Target `tetorica::ym2612`
links the static library; `<tetorica/ym2612.hpp>` exposes the existing reference
C ABI from C++. The `native_ym2612_*` names and `NativeYm2612State` layout remain
unchanged. This is not yet a new versioned, portable C-only SDK header.

The test exercises two independent instances, all six FM channels, DAC, timers,
status/IRQ, clock changes, observational snapshots, cancellation, retained Stop,
reset, mute, and deferred audition edges. It checks zero C++ allocation/free
during rendering and works in Release builds with assertions enabled. It opens
no audio device. Building the target proves this component only; it does not
claim that every collected Native wrapper already has an independent SDK build.

## Collected component references

| Public component | Reference wrapper or support | Native CMake build |
| --- | --- | --- |
| Sega PSG | `native_genesis_psg.h`, Game Gear/Master System wrappers | Not yet connected |
| YM2612 | `native_genesis_ym2612.cpp`; Nuked alternative in `native_genesis_nuked.cpp` and `.inc` | ymfm built and tested; Nuked reference only |
| YM2203 | `native_genesis_ym2203.cpp` | Not yet connected |
| YM2608 | `native_genesis_ym2608.cpp` | Not yet connected |
| YM2610 / YM2610B | `native_genesis_ym2610b.cpp`, selected immutable variant | Not yet connected |
| YM2151 | `native_genesis_ym2151.cpp` | Not yet connected |
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

## Reference wrapper license status

No repository-wide `LICENSE`, `COPYING`, or `NOTICE`, and no `package.json`
license field, was found in the source Tauri checkout. Many imported wrappers
and headers have no file-level declaration. Existing explicit declarations are
preserved, but a vendor core's license does not establish the license of a
separately authored Native wrapper. `catalog/native_inventory.json` records the
located declarations and unresolved files for each component.

The imported code has not been relicensed, and `LICENSE.tools` does not apply to
it. The applicable source terms need to be confirmed with the source owners
before public distribution. Build verification does not resolve that provenance
question.

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
