# Native sources

This directory contains the existing chip-level C++/C ABI wrappers as bootstrap
references, without Rust, Tauri, CPAL, the application scheduler, Mixer, FX,
QuickJS, UI, or audio-device code. Existing applications still use their current
sources. Collecting them here does not yet switch those consumers to this SDK.

`reference/tauri/` preserves the existing exported functions and PCM behavior.
HuC6280 and Nuked include paths are relocated to the shared SDK source layout.
The YM2612, YM2151, YM2413, YM2203, YM2608 and YM2610/YM2610B adapters also
carry the recorded template-ownership amendments below.
`reference/SOURCES.json` records the original and packaged byte hashes.
The vendor cores have one canonical copy in `../vendor/`; they are not copied
again under `native/`.

[Per-chip differences](../docs/chip-differences.md) distinguish upstream
adaptations, SDK relocation, and existing Native/WASM API or rendering
differences. [MSFA details](../docs/research.md) describe all six Native
overrides, including slot-control APIs and panic behavior, not just portability.

The shared Game Boy header includes Tauri's
`friend struct NativeGameboyAccess` declaration for state observation and
gate-only Stop. This recorded SDK amendment changes access only; the shared
implementation, Native wrapper and WASM bridge remain unchanged. See the
per-chip document for the original/amended hashes and the NES/HuC6280
translation-unit constraints.

## Build support

The independently buildable Native components are **ymfm YM2612, YM2151,
YM2413, YM2203, YM2608 and YM2610/YM2610B, plus Sega PSG, AY-3-8910, OKIM6258, RF5C164, Game Boy, HuC6280, NES with optional FDS and YM3526/YM3812/YMF262/Y8950**.
These eighteen chip IDs use fourteen static libraries; YM2610/YM2610B share one
library, and four OPL-family chips share another. Constructors explicitly select
the per-handle variant/kind. Nineteen aliases/headers include the generic OPL entry:

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
| `tetorica::ym2610`, `tetorica::ym2610b` | `tetorica_native_ym2610` | `<tetorica/ym2610.hpp>`, `<tetorica/ym2610b.hpp>` | `native_ym2610b_*`, `NativeYm2610BState`, `NativeYm2610BExtraState` |
| `tetorica::okim6258` | `tetorica_native_okim6258` | `<tetorica/okim6258.hpp>` | `native_extra_okim6258_*`, `NativeExtraOkim6258State` |
| `tetorica::rf5c164` | `tetorica_native_rf5c164` | `<tetorica/rf5c164.hpp>` | `native_rf5c164_*`, `native_extra_rf5c164_*`, `NativeExtraRf5c164State` |
| `tetorica::opl`, `tetorica::ym3526`, `tetorica::ym3812`, `tetorica::ymf262`, `tetorica::y8950` | `tetorica_native_opl` | `<tetorica/opl.hpp>` and matching chip forwarders | `native_opl_*`, `native_extra_opl_*`, `NativeOplState`, `NativeExtraOplState` |
| `tetorica::gameboy` | `tetorica_native_gameboy` | `<tetorica/gameboy.hpp>` | `native_gameboy_*`, `NativeGameboyState` |
| `tetorica::huc6280` | `tetorica_native_huc6280` | `<tetorica/huc6280.hpp>` | `native_huc6280_*`, `NativeHuc6280State` |
| `tetorica::nes` | `tetorica_native_nes` | `<tetorica/nes.hpp>` | `native_nes_*`, `NativeNesState` |

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
The YM2610 fixture covers both immutable FM variants and both constructor
profiles, FM/SSG/ADPCM-A/B, dense ROM boundaries/copies, sparse-page ownership,
retained controls, Stop/reset, cancellation, timers/status/IRQ and observation.
The OKIM6258 fixture covers sample borrowing/replacement, nibble/FIFO timing,
clock/divider guards, pan, repeat, retained Stop/reset and observation.
The RF5C164 fixture covers both profiles, eight voices, sign-magnitude PCM,
loop markers, RAM/bank access, clock conversion, reset retention and the
additional profile's immediate source cancellation and observation.
All sixteen fixtures run through CTest with assertions enabled in Release builds.
The three OPL-family fixtures exercise primary controls/PCM, additional source
ownership/held output, and Y8950 writable-page memory separately. The shared OPL
library covers four selected chip kinds; each handle constructs only one kind.
The Game Boy fixture covers both pulses, wave RAM and noise, asymmetric stereo
gains/routing, clock conversion, mute progression, retained Stop, per-channel
Stop, reset and repeated non-advancing state observations. It checks every
channel's Stop against foreign-voice reference PCM at 44.1/48/96 kHz and
100 kHz/base/100 MHz clocks, including retained outer samples below the base
clock, along with invalid controls, ABI layout and allocation-free rendering.
The HuC6280 fixture covers six audible sources, owned 5-bit wave RAM, selected
and explicit-channel writes, waveform-helper control/DDA restoration and phase
effects, stereo, noise/LFO, mute progression, Stop/reset, clock conversion,
non-advancing observation and rendering without allocation/free.
The NES fixture checks all six source gates/mutes, copied RAM boundaries and
DMC wrap/loop/IRQ/final-byte lifetime, protected host gates, FDS wave/modulation
and I/O gates, the 400-byte state ABI, independent instances, regional tables,
creation/clock guards, retained Stop/full reset and non-advancing observation.
It compares exact DMC PCM/lifetime during unrelated protected gate edits and
rejects allocation/free while rendering and applying tested controls.
See the [verification record](../docs/verification.md)
for completed checks and platform results. Other collected wrappers still need
their own standalone targets and verification.

`src/ymfm_opn_provider.cpp` includes the unchanged shared ymfm provider and explicitly instantiates the Native OPN engine/channel/operator templates. The adapter declares those templates `extern`; optimized providers must emit their callable definitions even when the provider's own calls are inlined. This incorporates the Tauri link fix without changing DSP behavior or the exported ABI. The provider's origin and include relocation are recorded in the source inventories.

The YM2203, YM2608 and YM2610/YM2610B targets reuse this OPN provider and unchanged
SSG/ADPCM link dependencies. Each constructs only its selected chip. Linking YM2203 does
not allocate YM2608 rhythm/sample resources; a YM2608 handle allocates its own
fixed ROM and RAM buffers, whose contents the host supplies.

`src/ymfm_opm_provider.cpp` does the same for the OPM templates used by YM2151.
Both linkage changes come from Tauri commit
`83bfba8cbbc272a02279aba250b13e4c0f6ca57b`. The shared ymfm vendor files and WASM
recipes are unchanged. The YM2151 target is an independent OPM implementation;
it does not allocate an OKIM6258 core or provide a complete X68000 sound system.

`src/ymfm_opl_provider.cpp` supplies the existing Native OPL/OPLL explicit
template definitions. YM2413 and the shared OPL-family target link the unchanged
ADPCM/PCM support translation units required by that provider. YM2413 constructs
only OPLL; the separate OPL-family constructors select YM3526, YM3812, YMF262 or
Y8950. Shared vendor bytes and WASM recipes are unchanged.

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

## Embed YM2610 / YM2610B / OPNB

Link either `tetorica::ym2610` or `tetorica::ym2610b` and include
`<tetorica/ym2610.hpp>` or `<tetorica/ym2610b.hpp>`. Both aliases link the same
`tetorica_native_ym2610` library and both headers forward the unchanged
`native_ym2610b_*` ABI. The alias/header does not select the variant for you:
`native_ym2610b_create(output_rate, variant)` selects immutable variant **0** for
YM2610's four physical FM slots **1, 2, 4, 5**, or **1** for all six YM2610B FM
slots. A four-channel host must not use physical slots 0–3 as a compact mapping.
`native_ym2610b_create_extra_variant(output_rate, variant)` makes the same choice
for an additional-instance profile; the convenience `create_extra(output_rate)`
defaults to variant 0, unlike the raw WASM `ym2610b_create()` six-FM default.

Both variants include three SSG voices, six programmable ADPCM-A voices and one
ADPCM-B voice. The default master clock is 8 MHz. FM pitch uses
`clock * FNUM * 2^(BLOCK-1) / (144 * 2^20)`; SSG uses master/4, so its tone
period is `round(clock / (64 * frequency_hz))`. ADPCM-A decodes at clock/432;
ADPCM-B rate is `DeltaN * clock / (144 * 65536)`. FM and ADPCM have stereo
gates; SSG contributes equally to both sides.

The **primary constructor** owns two initially zero, dense **16 MiB ROM banks**:
type 0 is ADPCM-A and type 1 is ADPCM-B. `load_rom(chip, type, bytes, offset,
size)` validates the bank/range and synchronously copies data. The input buffer
may be released after success. `copy_rom()` copies bytes back; `clear_rom()`
zeros the selected bank without releasing its allocation. These memory APIs do
not stop a decoder: serialize access with sampling and stop affected playback
before replacing active bytes. No hardware or game ROM is supplied by the SDK.

The **additional constructor** instead exposes two 16 MiB address spaces through
externally owned, immutable **64 KiB pages**, with 256 page slots per bank.
`alloc_rom_page()` returns a zeroed page for control-side preparation. Fill it
before publication, then `install_rom_page(chip, bank, index, page)` publishes
the pointer without copying or freeing any page. Never mutate a published page.
The host must keep both current and replaced pages alive until rendering can no
longer reference them, then reclaim them with `free_rom_page()` on the control
side. Serialize publication/clearing/destruction with the renderer; the SDK
provides no thread synchronization, callback fence, retirement queue or budgets.
Destroying the chip does not free external pages. For additional instances,
nonempty `load_rom()` calls are rejected, `copy_rom()` reads mapped bytes (zero
for unmapped pages), and `clear_rom()` detaches the selected bank's pointers
without freeing them. A zero-length transfer is only a validated no-op.

Both A and B sample ranges use **256-byte units** with inclusive hardware end
units, unlike YM2608's 32-byte ADPCM-B RAM mode. ADPCM-A registers are on port 1:
start low/high `0x10+voice` / `0x18+voice`, end low/high `0x20+voice` /
`0x28+voice`, individual pan/level `0x08+voice`, total level `0x01` and trigger
mask `0x00`. Keep each A range shorter than 1 MiB because its end comparison
uses the low 20 address bits. ADPCM-B registers occupy port 0 `0x10–0x1b`:
start `0x12/0x13`, end `0x14/0x15`, stereo `0x11`, Delta-N `0x19/0x1a`, volume
`0x1b`, and control `0x10` (`1` stops, `0xa0` starts, `0xb0` repeats). B uses
fixed ROM addressing; OPNA's DRAM-mode/limit programming does not apply.

Both constructor profiles clear outer held PCM and output-rate remainder on
reset, while retaining ROM contents/page mappings, clock and source mute
settings. Stop retains authored controls and memory; the additional profile
preserves independent held buses for cancellation. Voice IDs remain physical
FM 0–5, SSG 6–8, ADPCM-A 9–14 and ADPCM-B 15; unsupported FM slots stay absent
in variant 0. Both status reads and state snapshots are observational, unlike
YM2608's extended-status IRQ propagation. They do not advance audio or expose
a transferable WASM save state. The host supplies all scheduling and output.

## Embed OKIM6258

Link `tetorica::okim6258` and include `<tetorica/okim6258.hpp>` for the unchanged
`native_extra_okim6258_*` ABI and `NativeExtraOkim6258State`. The target owns one
OKI decoder, independently of YM2151. It uses the existing additional-instance
adapter rather than the X68000 primary path's two sample staging banks. The
fixed format is **4-bit OKI ADPCM with 12-bit decoder output** (flags 12), packed
**low nibble first**, unlike Yamaha ADPCM-A/B. The default clock is 8 MHz,
divider 512, and pan 0 enables both outputs. Three-bit ADPCM, recording and a
Native 10/12-bit format selector are not provided.

`load_sample(chip, bytes, size)` accepts 1 byte through 16 MiB, stops playback
and **borrows the input without copying or taking ownership**. Keep the bytes
immutable and alive until a successful replacement or destruction of the core.
Stop and reset retain this pointer; neither ends the lifetime requirement.
Serialize binding, playback and rendering, and retire replaced buffers only
after no rendering call can still use them. The SDK supplies no callback
fence, ownership queue or reclamation. A C++ owner should declare the sample
buffer before the core's RAII handle so reverse destruction releases the core
first, including during exceptions. The X68000 example demonstrates this order.

`play(chip, repeat)` requires a bound sample and repeat 0/1. It resets the
decoder/FIFO and feed position, then streams the borrowed bytes at
`clock / divider` decoded samples per second, with two samples per byte.
Repetition restarts the complete sample. Register `12` low bits select
1024/768/512/512; there is no musical pitch register. Changing the rate changes
sample pitch and duration. Register `2` holds mute bits: bit 0 disables right,
bit 1 disables left. `set_clock()` validates 100 kHz–100 MHz and limits the
VCLK/output-rate ratio to at most 14, both at the selected divider and at the
reset divider 512. Check failure returns; creation accepts output rates
8–384 kHz. Raw clock bytes use registers 8–11, applying the assembled clock on
the final byte.

For a raw FIFO host, control register `0` selects play/stop and data register
`1` feeds encoded bytes. Writing register `0` leaves the convenience sample
streaming path, so the host then owns feed timing. The core has a bounded
eight-byte FIFO; this is not an unbounded PCM stream or a file loader. With no
new nibble, the raw decoder retains its last generated sample. Stop clears the
held output immediately and ends playback/streaming while retaining the sample,
clock, divider, pan and repeat setting. Reset also clears decoder/FIFO phase,
restores divider 512 and pan 0, and retains the edited clock and bound sample.
The next `play()` resets wrapper feed counters. `get_state()` is observational;
its progress fields are not a transferable WASM save state. Allocate/free
outside the callback and keep all chip access serialized.

## Embed RF5C164

Link `tetorica::rf5c164` and include `<tetorica/rf5c164.hpp>`. One static library
exposes both existing ABIs: `native_rf5c164_*` for the primary profile and
`native_extra_rf5c164_*` for independent additional instances. Each handle owns
one eight-voice PCM chip and **64 KiB of RAM**. Neither profile allocates FM or
PSG siblings. Common-operation PCM is checked between the two profiles;
direct Worklet/WASM comparisons exercise the additional API. Their
implementation, validation and control APIs remain distinct.

PCM bytes are sign-magnitude: bit 7 means positive, `0x80` is positive zero,
and bit-clear values are negative magnitudes. **`0xff` is a loop marker**, so
positive magnitude 127 cannot be ordinary sample data. A marker jumps to the
voice's byte-addressed loop start; a second marker there produces silence for
that tick. When large steps can skip bytes, pad the end with enough marker
bytes to catch them. Voice start register `6` uses **256-byte units**, while
loop registers `4/5` use byte units. Step registers `2/3` form a 16-bit value
with 11 fractional bits. At the reference **12.5 MHz** clock, source ticks run
at `clock/384`; for an N-sample waveform use approximately
`step = round(frequency_hz * N * 384 * 2048 / clock)`. Marker-loop quantization
and the chip's stepping still determine the actual period.

Register `7` bit 7 globally enables output; with bit 6 set, bits 0–2 select a
voice, otherwise bits 0–3 select a 4 KiB CPU RAM bank. Register `0` is envelope
level 0–255, and register `1` has left/right pan levels in its low/high nibbles.
Register `8` is an inverted gate mask: a set bit disables that voice and resets
its address to the configured start. `write_memory(offset, value)` follows the
original CPU window behavior **`bank | offset`**, not addition or an absolute
upload. Use offsets 0–4095 for the selected bank window. In contrast,
`load(chip, bytes, offset, size)` uses a bounded absolute RAM range and copies
the caller's bytes synchronously; the input may be released after success.

Both profiles preserve RAM on reset, while resetting voice/control/output
history. `clear_memory()` zeros RAM separately, without implicitly gating
voices or discarding a held output sample. Serialize memory edits with
rendering and disable affected voices before replacing active waveforms.
Creation/destruction and host synchronization remain outside the audio callback.

The primary profile constructs the shared vendor `RF5C164` core at 12.5 MHz.
Clock edits add outer averaging/hold of its canonical output. Its legacy
constructor rejects only an output rate of zero, and its clock setter is
**void and unbounded**; the host must validate suitable rates/clocks. Its
`load()` checks numeric bounds but does not explicitly reject a nonempty null
pointer: callers must provide valid source storage. Do not infer additional
validation from the other profile. The primary API does not expose the extra
profile's observational state/readback or immediate cancellation functions.

The additional profile uses an independent per-voice implementation, retaining
held contributions and outer resampling history to preserve reference PCM while
supporting source cancellation. It accepts output rates 8–384 kHz and clock
values 100 kHz–100 MHz, reports clock rejection, and rejects null pointers for
nonempty uploads. Ordinary register-8 gate writes retain the reference held
output until its normal update. `native_extra_rf5c164_key_off()` and `stop()`
instead clear only the relevant cached contributions and remix immediately,
without advancing foreign voices or sample addresses. Extra state and register
reads are observational; extra `read_memory()` / `read_memory_range()` inspect
absolute RAM, independent of the CPU bank. These views are not WASM save states.

## Embed the OPL family

`tetorica::opl`, `tetorica::ym3526`, `tetorica::ym3812`, `tetorica::ymf262` and
`tetorica::y8950` all link **one** `tetorica_native_opl` library. Include
`<tetorica/opl.hpp>` or a matching chip forwarder. Every header exposes the same
existing primary/additional ABIs. **Neither alias nor header selects the chip.**
Pass a kind to `native_opl_create(rate, kind)` or
`native_extra_opl_create(rate, kind)`; one chosen core/profile is constructed:

| Kind | Chip | Default clock | FM channels | Source sample rate |
| --- | --- | --- | --- | --- |
| 0 | YM3526 / OPL | 3,579,545 Hz | 9 | clock/72 |
| 1 | YM3812 / OPL2 | 3,579,545 Hz | 9 | clock/72 |
| 2 | YMF262 / OPL3 | 14,318,180 Hz | 18 | clock/288 |
| 3 | Y8950 / MSX-AUDIO | 3,579,545 Hz | 9 plus ADPCM-B | clock/72 |

At operator multiplier 1, pitch is `clock * FNUM * 2^BLOCK / (divider * 2^20)`,
with divider 72 or 288 above, F-NUM 1–1023 and BLOCK 0–7. OPL2 has four waveforms;
OPL3 has eight when NEW mode is enabled. OPL3 four-operator pairs share two
physical channels, and rhythm's five logical voices share channels 6–8. OPL3
NEW=0 folds upper bus writes according to the existing core; the additional
profile exposes authored/effective register views for this distinction. Its four
output buses fold A+C to left and B+D to right. Other kinds produce mono on both
channels. Voice IDs are FM 0–8 (OPL3 0–17), BD/SD/TOM/CYM/HH 18–22, and Y8950
ADPCM 23. Constructors accept 8–384 kHz; clock edits accept 100 kHz–100 MHz.

Primary Stop clears active voices/pending previews and silences output while
retaining controls. Additional `all_notes_off()` uses ordinary gate writes and
keeps release timing; `host_all_notes_off()` silences the host presentation,
while strong `stop()` also cancels CSM. The additional profile separates normal
FM cancellation from CSM and tracks held voice/drum contributions so runtime
cancellation does not advance foreign sources. Preview release/audition retains
its distinct held-output timing, with retrigger after an ordinary chip interval;
OPL3 source-preview functions also respect physical/effective state when NEW
mode has changed. These functions are not interchangeable generic key-offs.
Primary reset calls the core reset; additional reset restores its captured
power-on state and clears held caches. Both clear outer output history and
register controls, retaining the selected kind, edited clock and Y8950 page
bindings. See the existing headers for profile-specific functions.

### Y8950 writable ADPCM memory

Both profiles borrow **up to 2 MiB of writable RAM** as 512 caller-owned
**4 KiB pages**. `memory_page(chip, index, page)` publishes a pointer (or null)
without copying/owning/freeing it; `memory_length(chip, bytes)` publishes the
logical byte length, up to 2 MiB. A mapped page beyond that length still reads
as zero. Unmapped reads return zero and unmapped writes are ignored. Index/length
values outside capacity are ignored. These operations are inert for other kinds.
The raw ABI does not atomically stop playback on page/length edits: cancel ADPCM
first and serialize publication with the renderer. CPU transfer writes can
modify mapped pages, so immutable sample storage is not valid here.

Keep page storage stable and writable across reset and until replacement or
destruction has been synchronized with all rendering users. Stop/reset retain
page pointers, length and revision counters; destruction does not free pages.
The host owns preparation, synchronization, replacement and retirement; the SDK
does not include the Rust queue, copy-on-write manager, budgets or callback
fences. Declare the page owner before the chip's RAII handle so it is destroyed
after the chip. The MSX-AUDIO example maps one full page with a 2048-byte logical
sample, without an external allocator or application runtime.

Each accepted `memory_length()` sets
`upload_revision = ++memory_revision`; actual mapped CPU RAM writes increment
only `memory_revision`. Installing a page alone does not change either counter.
These are revision markers, not independent upload/write counts. To clear,
cancel ADPCM, zero or replace pages and publish the desired length; there is no
copy-owning bulk-memory API in this C ABI.

Y8950 ADPCM-B uses register `7` for control (`1` stop, `0xa0` start, `0xb0`
repeat), register `8` low bits `2` for eight-bit DRAM/32-byte units, start
`9/10`, inclusive end `11/12`, Delta-N `16/17` and volume `18`. Preserve the
FM CSM/note-select bits in register `8` when changing memory mode. Decoded rate
is `DeltaN * clock / (72 * 65536)`. Output is mono, with no ADPCM pan API.
Raw CPU-data reads/writes have transfer side effects. State snapshots do not
consume ADPCM data or advance audio, but their Y8950 status read can propagate
ADPCM flags into IRQ state; they are not universally IRQ-neutral observations.
No Native snapshot is a transferable WASM save state.

## Embed Game Boy DMG audio

Link `tetorica::gameboy` and include `<tetorica/gameboy.hpp>`. The header forwards
the unchanged `native_genesis_gameboy.h` ABI, including `NativeGameboyState`.
Each handle owns one DMG APU: pulse channels 0/1 (sweep on channel 0), wave
channel 2 with 16 bytes of owned RAM, and noise channel 3. There is no borrowed
sample storage or external ROM dependency. This is the existing MAME-derived
DMG adaptation; CGB/AGB variants, CPU execution, hardware register reads and
the wave-RAM corruption glitch are outside its scope.

```cmake
add_subdirectory(vendor/tetorica-soundchip-native)
target_link_libraries(your_application PRIVATE tetorica::gameboy)
```

```cpp
#include <tetorica/gameboy.hpp>

int main() {
    void* chip = native_gameboy_create(48000);
    if (!chip) return 1;
    native_gameboy_write(chip, 0x16, 0x80); // NR52: power on.
    native_gameboy_write(chip, 0x14, 0x77); // NR50: equal output gains.
    native_gameboy_write(chip, 0x15, 0x11); // NR51: pulse 1 to both sides.
    native_gameboy_write(chip, 0x01, 0x80); // NR11: 50% duty.
    native_gameboy_write(chip, 0x02, 0xf0); // NR12: constant envelope, DAC on.
    native_gameboy_write(chip, 0x03, 0xd6); // NR13/14: approximately 440 Hz.
    native_gameboy_write(chip, 0x04, 0x86); // Trigger, length disabled.
    float left[512], right[512];
    for (unsigned i = 0; i < 512; ++i)
        native_gameboy_sample(chip, &left[i], &right[i]);
    // Send these buffers to your audio output or file renderer.
    native_gameboy_stop(chip);
    native_gameboy_destroy(chip);
}
```

Creation accepts output rates **1–384,000 Hz**, rejecting zero and higher rates.
The reference input clock is **4,194,304 Hz**. `set_clock()` accepts
100 kHz–100 MHz and reports rejection without changing the clock. The shared
core remains at its reference clock; the Native wrapper adds fractional
averaging/hold for edits. The first accepted edit initializes outer held PCM
and phase; later edits preserve them. Pulse frequency is
`clock / (32 * (2048-N))`; the 32-nibble wave frequency is
`clock / (64 * (2048-N))`, with eleven-bit N. Noise uses a 15-bit or short
7-bit LFSR with period `{8,16,32,48,64,80,96,112}[divisor] << shift` CPU cycles.

`write()` takes offsets **0x00–0x2f from CPU I/O 0xFF10**. For example, NR52 is
offset `0x16`, and wave RAM is `0x20–0x2f`; absolute CPU addresses are not this
ABI's address format. Unused offsets are inert. NR51 low bits route channels
0–3 right and high bits route them left. Preserve the existing NR50 convention:
**low three bits control left, bits 4–6 control right**; each scale is
`(1 + volume) / 480`, so volume zero is the minimum gain rather than silence.
VIN bits are unused. The core adds the centered DAC values and integrates
native ticks without a motherboard filter or automatic peak normalization.

Power NR52 on before normal configuration writes. While powered off, only
NR52 and length registers NR11/NR21/NR31/NR41 accept sound-register writes.
Wave RAM remains writable while the wave channel is off, including with APU
power off. During active wave playback, writes follow the existing narrow
sample-read access window and target the currently read byte. Disable the wave
DAC or Stop its channel before replacing a complete waveform.

`set_mute_mask()` bits 0–3 suppress presentation while synthesis, envelopes,
length/sweep and the noise LFSR keep progressing. `stop_channel()` clears only
that channel's gate and core contribution, retaining its registers and foreign
voices. At clocks below the reference, an already held outer mixed frame can
remain until the next source frame. `stop()` gates all four channels and clears
both core and outer held output immediately. Both retain wave RAM, registers,
power, routing, output gains, clock and mute. Reset instead powers off the APU,
clears gates/register controls and output phase, and restores the documented
16-byte DMG wave-RAM startup pattern; the edited clock and source mute survive.

`get_state()` copies the 48-byte register/wave view, active gate mask, clock and
source mute mask without ticking audio or triggering voices. Trigger bits are
stripped from NRx4 views; NR52 reconstructs power and active gates. Active gates
do not imply audible output when routing, DAC or mute suppresses a source.
This is an observational snapshot, not hardware readback or a transferable
WASM save state. The access-only friend declaration is recorded in the vendor
inventory; no synthesis algorithm is amended. Create/destroy outside the audio
callback, keep valid handles/output pointers, and serialize all chip access.

## Embed PC Engine HuC6280 audio

Link `tetorica::huc6280` and include `<tetorica/huc6280.hpp>`. This forwards the
existing `native_genesis_huc6280.h` ABI and `NativeHuc6280State` without renaming
exports. Each handle owns six audible channels 0–5, each with 32 unsigned 5-bit
wave samples and a DDA latch. Channels 4/5 also support noise; LFO modulates
channel 0 using channel 1. The eight-channel register/state storage retains
selection slots 6/7 for compatibility; those slots are not audible sources.
No external ROM or borrowed sample storage is needed. The existing MAME
adaptation retains its documented imperfect/unverified noise and LFO model.

```cmake
add_subdirectory(vendor/tetorica-soundchip-native)
target_link_libraries(your_application PRIVATE tetorica::huc6280)
```

```cpp
#include <tetorica/huc6280.hpp>
#include <cstdint>

int main() {
    void* chip = native_huc6280_create(48000);
    if (!chip) return 1;
    uint8_t wave[32];
    for (unsigned i = 0; i < 32; ++i)
        wave[i] = uint8_t(i < 16 ? 1 + 2 * i : 63 - 2 * i);
    native_huc6280_waveform(chip, 0, wave); // Synchronous copy; wave may now expire.
    native_huc6280_write(chip, 1, 0xff, -1); // Global left/right balance.
    native_huc6280_write(chip, 5, 0xff, 0);  // Channel 0 left/right balance.
    native_huc6280_write(chip, 2, 254, 0);   // round(3579545 / (32 * 440)).
    native_huc6280_write(chip, 3, 0, 0);
    native_huc6280_write(chip, 4, 0x9f, 0);  // Wave enabled, maximum level.
    float left[512], right[512];
    for (unsigned i = 0; i < 512; ++i)
        native_huc6280_sample(chip, &left[i], &right[i]);
    // Send these buffers to your audio output or file renderer.
    native_huc6280_stop(chip);
    native_huc6280_destroy(chip);
}
```

Creation accepts **8,000–384,000 Hz** inclusive. The reference chip clock is
**3,579,545 Hz**. `set_clock()` accepts **100,000–100,000,000 Hz** inclusive,
returning 1 on success or 0 without changing the clock on rejection. Clock
edits keep the shared core at its reference clock and apply outer fractional
averaging/hold; accepted edits preserve that outer phase/held PCM. At the
reference clock no outer conversion is enabled until `set_clock()` is called.
With LFO disabled, wave pitch is `clock / (32 * period)`, where the 12-bit
frequency in registers 2/3 encodes periods 1–4095 and zero means 4096. DDA
instead holds an unsigned 5-bit value until the host supplies another timed
register-6 write. Both wave samples and DDA use **16 as neutral**; zero is a
negative DAC extreme, not silence.

`write(handle, reg, value, channel)` accepts register offsets **0–9**, not CPU
addresses. Register 0 selects `value & 7`; register 1 is global balance;
registers 8/9 are global LFO frequency/control. Their channel argument is
ignored. For registers 2–7, an explicit channel 0–7 temporarily selects that
slot and restores the previous selection afterward. Any other channel value,
including the conventional `-1`, writes the currently selected slot. Offsets
above 9 are ignored. Register 4 uses bit 7 as enable, bit 6 as DDA mode and bits
0–4 as level. Register 5 and global balance use the high nibble for left and
low nibble for right. The retained logarithmic attenuation table is summed
without automatic peak normalization or an analog output filter. Register 7's
noise-enable bit 7 affects only channels 4/5; bits 0–4 select the noise rate.
LFO mode uses register 9's low two bits, with bit 7 resetting its source phase.
The retained model can also output channel 1 while it supplies LFO modulation.

`waveform(handle, channel, samples)` copies exactly 32 bytes immediately for
channels 0–5; each byte is masked to five bits. A null source or any other
channel is ignored. The caller may release or modify the source array after
the call. The helper preserves current channel selection, restores the
channel's control byte and, if DDA was selected, restores its prior DDA latch.
It temporarily disables playback and toggles DDA to reset the wave-write
index, then writes the complete wave. **It changes index/phase**: the final
index is zero and restoring an enabled control can retrigger its period
counter. It does not promise uninterrupted active playback. Raw register-6
wave writes use the current index, advancing it only while playback is off;
raw DDA writes update the latch instead. Serialize either operation with
rendering. There is no sample-buffer publication or retirement obligation.

`set_mute_mask()` bits 0–5 suppress output while enabled oscillators, noise and
LFO continue advancing. `key_off(channel)` accepts slots 0–7 and only clears
control bit 7; `stop()` does the same for all eight slots. They preserve waves,
frequency, levels, balance, noise/LFO, DDA mode/latch, clock and mute. **Stop
does not write neutral DDA**: re-enabling a DDA channel resumes its retained
value. Neither operation clears outer held PCM, so below the reference clock
an old mixed frame can remain until the next core frame. They do not provide
immediate source cancellation or advance other channels at the call itself.
Reset instead clears registers, wave RAM, DDA, selection, LFO/noise controls
and core/outer output phase, restoring the noise seeds; edited clock and mute
survive. Applications can fade output or explicitly supply neutral DDA when
that is their intended playback policy.

`get_state()` copies selection, authored register shadows, all eight wave,
index and DDA slots, and the edited clock without advancing audio. Shadows
record authored bytes, including helper writes; this is an observational
snapshot, not hardware readback or a portable save/load format. Keep valid
handles and output pointers, create/destroy outside the audio callback, and
serialize register writes, waveform copies, reset, observation and rendering.
The CMake target compiles only `native_genesis_huc6280.cpp`, which already
includes `huc6280.cpp`; do not compile the vendor implementation again as a
separate translation unit. No scheduler, audio device or machine runtime is
imported.

## Embed NES with optional FDS

Link `tetorica::nes` and include `<tetorica/nes.hpp>` for the unchanged
`native_nes_*` ABI and `NativeNesState`. FDS is a constructor flag in this one
library/header. The target compiles only `native_genesis_nes.cpp`: it is a
self-contained renderer. Do not add `vendor/tetorica-nes/nes_core.cpp`, whose
`native_nes_*` exports would collide. The two core sources differ only in their local header include; WASM adds
block generation and compiled state-layout descriptors. Neither core is
changed by this target.
The NES target selects C++17 and applies the original Tauri integer/aliasing/
floating-point flags when the compiler supports them; those private flags do
not affect other chip libraries or consumers.

```cmake
add_subdirectory(vendor/tetorica-soundchip-native)
target_link_libraries(your_application PRIVATE tetorica::nes)
```

```cpp
#include <tetorica/nes.hpp>

int main() {
    void* chip = native_nes_create(48000, 1789773.0, true); // NTSC, FDS enabled.
    if (!chip) return 1;
    native_nes_write(chip, 0x4017, 0x40); // Four-step frame clock, no frame IRQ.
    native_nes_write(chip, 0x4015, 0x01); // Pulse 1 gate.
    native_nes_write(chip, 0x4000, 0xbf); // 50%, held length, constant level 15.
    native_nes_write(chip, 0x4001, 0x08); // No sweep; negate mode.
    native_nes_write(chip, 0x4002, 253);  // round(1789773/(16*440)) - 1.
    native_nes_write(chip, 0x4003, 0xf8); // Timer high bits + length reload.
    float left[512], right[512];
    for (unsigned i = 0; i < 512; ++i)
        native_nes_sample(chip, &left[i], &right[i]);
    native_nes_stop(chip);
    native_nes_destroy(chip);
}
```

Creation accepts 8,000–384,000 Hz output and a finite base clock from
1,600,000–1,900,000 Hz. Choose, for example, 1,789,773 Hz NTSC or 1,662,607 Hz
PAL; base clocks below 1,700,000 select PAL noise/DMC/frame tables. The base
clock and FDS flag are immutable. `native_nes_set_clock` accepts integer
100,000–100,000,000 Hz and returns success/failure. It changes outer
averaging/hold relative to the base clock, preserving phase/remainder and the
original regional tables; it does not rebuild the APU for a new region.
At the base clock, pulse pitch is `base_clock / (16 * (period + 1))` and
triangle pitch is `base_clock / (32 * (period + 1))`; periods above 7 are the
usable range in this renderer. With zero FDS sweep gain, wave pitch is
`base_clock * frequency / 4194304`. Clock edits scale these pitches by
`clock / base_clock`.

Writes use absolute CPU addresses: pulses `$4000–$4007`, triangle
`$4008/$400A/$400B`, noise `$400C/$400E/$400F`, DMC `$4010–$4013`, gates
`$4015` and frame control `$4017`. DMC starts at `$C000 + 64*$4012`, plays
`16*$4013 + 1` bytes, consumes bits least significant first and wraps from
`$FFFF` to `$8000`. The copied memory API addresses the entire 64 KiB CPU
space: `native_nes_load(chip, bytes, offset, size)` returns 1 on success and
0 when `offset > 65536`, `size > 65536-offset`, or nonempty data has a null
pointer. A zero-byte upload may use null and offset 65536. Successful uploads
copy immediately; the input can expire on return. `native_nes_read_memory`
reads this RAM, not registers or hardware status. The host supplies encoded
DMC data and serializes uploads with rendering; no ROM parser, memory bus or
asynchronous loader is included.

FDS I/O must be enabled through `$4023` bit 1. The owned 64-byte wave table at
`$4040–$407F` accepts writes only when `$4089` bit 7 opens its write window;
audio uses each byte's low six bits. Close the window for playback. `$4080`
controls volume envelope/fixed gain, `$4082/$4083` hold the 12-bit frequency,
`$4083` bit 7 halts/restarts wave phase and bit 6 gates envelopes. `$4084`
controls sweep envelope/fixed gain, `$4085` writes a signed 7-bit modulation
counter, and `$4086/$4087` set modulation frequency/control. `$4088` writes
3-bit modulation entries only while `$4087` bit 7 disables modulation; each
write advances the doubled index by two through 32 owned entries. `$4089`
also selects master attenuation, and `$408A` sets envelope speed. Disabling
I/O blocks subsequent wave/control writes but does not stop a running FDS
oscillator. The state register mirror records submitted writes even when an
FDS gate rejects their hardware effect; inspect applied FDS fields/tables too.

Source IDs and mute bits are pulse 1/2 = 0/1, triangle = 2, noise = 3,
DMC = 4 and FDS = 5. `native_nes_enable` is the legacy APU `$4015` helper;
ordinary enable writes can refill an exhausted DMC sample. For independent
host gates, `native_nes_enable_channel` accepts APU IDs 0–4 and preserves
DMC decoder state when editing IDs 0–3. `native_nes_write_enable` merges
protected gate bits from the current mask; protecting bit 4 also preserves
the complete DMC state rather than refilling its final shifting byte.
`native_nes_active_mask` observes gates/lengths/DMC data-in-flight and FDS
oscillator enable without advancing synthesis; it is not an amplitude meter.
`native_nes_core_size` reports the retained C++ allocation including RAM.

The APU mixes pulses and triangle/noise/DMC through the retained nonlinear
lookup model and integer high-pass history. FDS has a 2 kHz low-pass and
20 Hz DC-removal filter before addition; the Native mix then passes through
its 10 Hz DC remover. Output is mono duplicated to left/right. Mute bits 0–5
preserve progression: APU mutes act before nonlinear mixing, FDS mute after
its own filters. `get_state`, `active_mask` and memory reads neither advance
audio nor acknowledge IRQ. State reports raw timer/rate quantities, not
hertz; DMC frequency is eight times its CPU-cycle bit period. It includes
frame/DMC IRQ flags, applied FDS fields, wave/modulation bytes and clock data.
The 400-byte snapshot omits RAM and internal filter/resampler history; it is
not a resumable save-state.

Global Stop gates off the APU and submits FDS halt/zero-gain writes through
the I/O gate; if FDS I/O is disabled, that FDS oscillator can remain active.
`stop_channel(5)` deliberately halts it even with I/O disabled while restoring
the authored I/O setting and retaining wave/envelope data. APU source Stop
preserves foreign DMC state; DMC Stop also clears its current DAC sample while
retaining the authored `$4011` and decoder level. Stop is not a PCM-buffer
clear: DAC latches, filter tails and sub-base-clock held output can persist.
Both Stop forms retain RAM, waves, clock and mute. Full reset clears the
64 KiB DMC RAM, FDS wave/modulation tables, registers, gates, phases and
filter/outer output history, retaining current/base clocks, mute and FDS flag.
Serialize every handle operation on its owning audio thread; state snapshots
are copied, with no imported host scheduler, lock or ownership queue.

The public forwarder and SDK integration use the default BSD-3-Clause terms.
The existing Native NES/FDS renderer explicitly retains **Apache-2.0 AND MIT**,
including the JSNES and fixNES notices; see [LICENSES.md](../LICENSES.md).

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
`examples/neogeo_wav.cpp` links `tetorica::ym2610` in `tetorica_neogeo_wav`.
It creates the four-FM primary variant, uses all four physical FM slots and
three SSG voices, and uploads original synthetic ADPCM-A percussion and an
ADPCM-B pluck into the two dense ROM banks. These are programmable sample
ranges rather than OPNA's fixed rhythm layout.
`examples/x68000_wav.cpp` links `tetorica::ym2151` and `tetorica::okim6258` in
`tetorica_x68000_wav`. It compensates OPM KC/KF pitch for the selected 4 MHz
clock and plays a locally encoded percussion sample through OKI at
8 MHz/divider 512 (15,625 decoded samples/s). Its immutable sample vector
outlives both core handles, including on errors. This is an offline sound
configuration, without device drivers or a complete X68000 emulation.
`examples/megacd_wav.cpp` links `tetorica::ym2612`, `tetorica::segapsg` and
`tetorica::rf5c164` in `tetorica_megacd_wav`. It uses the primary RF profile,
uploads an original sign-magnitude looping waveform and plays three PCM voices
alongside FM/PSG. A marker-filled tail handles skipped bytes safely; positive
sample magnitudes avoid the reserved `0xff` encoding.
`examples/dos_opl_wav.cpp` renders YM3526, YM3812 and YMF262 in three one-second
sections, exercising sine/half-sine waveforms, rhythm, an OPL3 four-operator pair
and left/right routing. `examples/msx_audio_wav.cpp` combines one Y8950's FM and
original ADPCM-B with AY8910 and YM2413. The writable sample page is declared
before the Y8950 handle so the decoder never outlives its RAM.
`examples/gameboy_wav.cpp` links only `tetorica::gameboy` in
`tetorica_gameboy_wav`. The first second isolates pulse 1 left and pulse 2
right; the second isolates an original triangle in wave RAM left and short
noise hits right; the last combines all four with pulse sides reversed.
It derives musical pitches from the 4,194,304 Hz clock and uses equal NR50
gains, fixed output headroom and short per-note fades.
`examples/pcengine_wav.cpp` links only `tetorica::huc6280` in
`tetorica_pcengine_wav`. Its first second separates original triangle/sine
waves left/right; the next uses a pulse bass, host-fed 5-bit DDA melody and
both noise channels; the last combines all six audible sources and reverses
the first two voices' sides. It uses the 3,579,545 Hz clock, unsigned DAC
neutral 16, fixed gain and short per-note fades without external sample data.
`examples/nes_fds_wav.cpp` links only `tetorica::nes` in
`tetorica_nes_fds_wav`. At the 1,789,773 Hz NTSC base clock, its first second
uses both pulses, triangle, noise and 65 original DMC bytes copied into RAM;
the next uses an original 64-sample FDS triangle; the last mixes all six.
It disables modulation for musical pitch conversion and checks timer
quantization within one percent. The retained mono output is duplicated
into stereo, using fixed gain and per-note fades.
From the SDK root:

```sh
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release --target tetorica_genesis_wav tetorica_master_system_wav tetorica_msx_wav tetorica_pc98_ym2203_wav tetorica_pc98_ym2608_wav tetorica_neogeo_wav tetorica_x68000_wav tetorica_megacd_wav tetorica_dos_opl_wav tetorica_msx_audio_wav tetorica_gameboy_wav tetorica_pcengine_wav tetorica_nes_fds_wav
# Single-configuration generators:
./build/native/native/tetorica_genesis_wav "genesis demo.wav"
./build/native/native/tetorica_master_system_wav "master system demo.wav"
./build/native/native/tetorica_msx_wav "msx demo.wav"
./build/native/native/tetorica_pc98_ym2203_wav "pc98 ym2203 demo.wav"
./build/native/native/tetorica_pc98_ym2608_wav "pc98 ym2608 demo.wav"
./build/native/native/tetorica_neogeo_wav "neogeo demo.wav"
./build/native/native/tetorica_x68000_wav "x68000 demo.wav"
./build/native/native/tetorica_megacd_wav "megacd demo.wav"
./build/native/native/tetorica_dos_opl_wav "dos opl demo.wav"
./build/native/native/tetorica_msx_audio_wav "msx audio demo.wav"
./build/native/native/tetorica_gameboy_wav "gameboy demo.wav"
./build/native/native/tetorica_pcengine_wav "pcengine demo.wav"
./build/native/native/tetorica_nes_fds_wav "nes fds demo.wav"
# Visual Studio on Windows:
./build/native/native/Release/tetorica_genesis_wav.exe "genesis demo.wav"
./build/native/native/Release/tetorica_master_system_wav.exe "master system demo.wav"
./build/native/native/Release/tetorica_msx_wav.exe "msx demo.wav"
./build/native/native/Release/tetorica_pc98_ym2203_wav.exe "pc98 ym2203 demo.wav"
./build/native/native/Release/tetorica_pc98_ym2608_wav.exe "pc98 ym2608 demo.wav"
./build/native/native/Release/tetorica_neogeo_wav.exe "neogeo demo.wav"
./build/native/native/Release/tetorica_x68000_wav.exe "x68000 demo.wav"
./build/native/native/Release/tetorica_megacd_wav.exe "megacd demo.wav"
./build/native/native/Release/tetorica_dos_opl_wav.exe "dos opl demo.wav"
./build/native/native/Release/tetorica_msx_audio_wav.exe "msx audio demo.wav"
./build/native/native/Release/tetorica_gameboy_wav.exe "gameboy demo.wav"
./build/native/native/Release/tetorica_pcengine_wav.exe "pcengine demo.wav"
./build/native/native/Release/tetorica_nes_fds_wav.exe "nes fds demo.wav"
```

The one required argument selects the output WAV; the parent directory must
exist. Each example generates exactly 144,000 frames of stereo PCM16 at 48 kHz
from synthetic notes/percussion, with no audio device or external assets.
They use their chips' respective hardware pitch equations, fixed mix headroom
and short output fades. Sega PSG stereo remains `0xff`; AY, OPLL, YM2203 and NES/FDS
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
| YM2610 / YM2610B | `native_genesis_ym2610b.cpp`, selected immutable variant | One standalone OPNB library and fixture; both constructor profiles |
| YM2151 | `native_genesis_ym2151.cpp` | Standalone OPM target and fixture; separate from the OKI handle |
| YM2413 | `native_genesis_ym2413.cpp`, `native_genesis_opll.h` | Standalone OPLL target and fixture |
| AY-3-8910 | `native_genesis_ay8910.cpp` | Standalone AY target and fixture; fixed Native type/flags |
| YM3526 / YM3812 / Y8950 / YMF262 | `native_genesis_opl.cpp`, `native_genesis_extra_opl.cpp` | One kind-selected library; primary, additional and Y8950 memory fixtures |
| RF5C164 | `native_genesis_rf5c164.cpp`, `native_genesis_extra_rf5c164.cpp` | One standalone library and fixture; distinct primary/additional profiles |
| OKIM6258 | `native_genesis_extra_okim6258.cpp` | Standalone ADPCM target and fixture; borrowed immutable sample |
| Game Boy | `native_genesis_gameboy.cpp` | Standalone DMG APU target and fixture; owned wave RAM, gate-only Stop and observation |
| NES + optional FDS | `native_genesis_nes.cpp` | Standalone APU/FDS target and fixture; copied DMC RAM, wave/modulation tables and observation |
| PC Engine / HuC6280 | `native_genesis_huc6280.cpp` | Standalone six-source target and fixture; copied wave RAM, DDA/noise/LFO and observation |
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
by a host. In the reference Tauri application, Rust owns preparation, COW pages,
budget accounting, retirement and final reclamation; standalone consumers must
supply their own lifetime and synchronization policy. None of the Native wrappers supplies the
Playground's 16-instance/64 MiB rack, timestamp queue, owner leases, or thread
coordination by itself. Each host must keep chip access serial and satisfy the
existing pointer-lifetime contract.
