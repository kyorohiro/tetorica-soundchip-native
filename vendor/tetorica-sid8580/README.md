# CPU-free SID 8580 Preview

`lib.rs` is the exact BSD-3-Clause `sid8p_*` adapter from Tetorica's browser
endpoint. [SOURCES.json](SOURCES.json) pins its origin and unchanged bytes.
It uses the separately pinned MIT [sidera adaptation](../sidera/README.md).
This instrument does not include a C64 CPU, a SID-file player, user ROMs,
firmware, game assets, an audio device or a scheduler.

## Two explicit API layers

Include `<tetorica/sid8580.h>` for the existing **raw C ABI**. Handles are
32-bit generation-tagged IDs, not pointers. `sid8p_create(rate, 1)` selects
8580 Preview at **985,248 Hz PAL**, with rate 8,000–96,000 Hz. The unchanged
ABI also accepts model 0 from its original probe; that is not the separate
SDK chips/m6581 implementation. Both optional research profiles default Off.

Raw writes and reads take **no cycles**. `sid8p_run(handle, cycles)` advances
exact chip cycles and samples with a retained integer phase. It returns the
valid mono **int16** sample count, at most 4096; `UINT32_MAX` indicates failure.
`sid8p_output` is a borrowed `const int16_t*` on Native and a linear-memory
offset in WASM. Copy only `output_frames` samples before another mutation or
destruction. There is no additional float normalization or host DC filter here.
Native pointers are never truncated through a wasm32 integer declaration.

Stop clears chip/bus/output, preserves cycle/frame counts and sampler phase,
and latches stopped. It does not resume on a write; Reset resumes and clears
the epoch. Both preserve explicitly selected profiles. Invalid arguments,
capacity overflow, stale IDs and unsupported POT reads are reported by the
existing return/error conventions. OSC3/ENV3 are real reads; data-bus reads
have the original bounded retention approximation. Register 25/26 POT values
and per-voice phase/envelope snapshots are not fabricated.

Include `<tetorica/sid8580.hpp>` for optional noncopyable
`tetorica::Sid8580Core`. This header-only **software host policy** matches the
browser: one tick before each bus access, a 4096-frame preallocated access
queue, int16 /32768 normalization, and the same 12 Hz DC blocker. It owns one
8580 handle with profiles Off. `renderInto(float*, frames)` consumes retained
samples; `reset()` clears queue, registers, chip phase/counters and DC history.
Unsupported POT access still performs the browser's one access tick before
reporting failure. Neither layer replaces SID's hardware envelope or retrigger
behavior. Host tone allocation, key identities, Legato and model switching are
application responsibilities.

Create/destroy outside an audio callback. All calls, output copying and lifetimes
must be serialized by the owner. The original registry has 16 slots and a Mutex;
this integration makes **no lock-free or hard-realtime guarantee**. Destroyed IDs
are invalidated with generation counters. No Rust objects cross the C boundary.

## Native build without Cargo or downloads

The SDK keeps its usual C/C++ build independent of Rust by default. Opt in:

```sh
cmake -S . -B build/sid8580 -DTETORICA_ENABLE_SID8580=ON
cmake --build build/sid8580 --target tetorica_sid8580_fixture tetorica_sid8580_wav
ctest --test-dir build/sid8580 -R tetorica.sid8580.self_test --output-on-failure
build/sid8580/native/tetorica_sid8580_wav sid8580.wav
```

Link `tetorica::sid8580` in a CMake consumer. Its imported static library is
`tetorica_native_sid8580`; building dependent targets builds its archive. To
build just that archive use `tetorica_sid8580_rust_build`, which is also part
of the default ALL build while the option is On. It is not a fake C++ anchor
library. The helper compiles `sidera` as an rlib and this adapter as a staticlib,
using the installed `rustc` directly. No Cargo resolution/network access occurs.

`TETORICA_SID8580_RUSTC` selects the compiler executable. The checked baseline
is Rust 1.91.1. `TETORICA_SID8580_RUST_TARGET` selects a target triple; install its
standard library beforehand. Windows MSVC and MinGW require their matching
`windows-msvc` / `windows-gnu` Rust target, pointer width and architecture.
Cross-compilation requires a matching target and C/C++ linker/toolchain; a Mac
build does not produce Linux/Windows libraries by itself. Build macOS arm64 and
x86_64 separately, then combine completed outputs if a universal distribution
is needed. The helper queries the selected Rust toolchain's actual native
system-link libraries with `--print native-static-libs`. No platform-specific
system library list is hard-coded. Additional semicolon-separated Rust flags
(such as an explicitly coordinated CRT policy) can be supplied through
`TETORICA_SID8580_RUST_FLAGS`. Parent source paths are not used.

## Standalone WASM and parity

```sh
sh scripts/build_sid8580_wasm.sh build/sid8580-wasm
node tests/sid8580_wasm_smoke.mjs --wasm-dir build/sid8580-wasm \
  --native-fixture build/sid8580/native/tetorica_sid8580_fixture
```

Install Rust's `wasm32-unknown-unknown` standard library before this command.
The sole product output is `sid8580_wasm.wasm`, a raw standalone WASM with no
imports and the exact `sid8p_*` exports. It needs no Emscripten JS factory or
C/C++/CPU bridge. The smoke verifies real PCM, all 16 waveform masks, filter,
Sync/Ring, bus/error/Stop/reset and independent lifetime behavior. With the
Native fixture it compares raw PCM exactly and the optional float host within
1e-7. The sample WAV contains only locally authored notes and uses the optional
Web-matching host, fixed example gain and note-edge fades; stereo duplicates
one mono chip. Those listening choices do not alter raw ABI PCM.

BSD wrapper/integration, MIT core and the complete supplied Rust standard-library
notices remain included. No GPL SID reference engine is linked or distributed.

## Integration verification, 2026-11-09

The checked local baseline was macOS, Apple Clang 17 and Rust 1.91.1. Both
`aarch64-apple-darwin` and `x86_64-apple-darwin` archives compiled and their
Native fixture executed successfully (647 checks each). Against the standalone
SDK WASM, each architecture matched **67,424 raw int16 frames exactly** and
**67,416 optional-host float frames with maximum difference 0**, at 44.1, 48
and 96 kHz. Those scenes cover all 16 waveform masks, shared filter outputs,
Sync/Ring, reads, Stop/reset, partitioning, profiles and independent instances.
The original offline example produced three seconds of 48 kHz stereo PCM16
with identical mono routes and peak 7,958, below full scale.

A separate development comparison used the actual parent
`tetorica_src/runtime/sid8580.js` / `Sid8580Core`, first with its unchanged
`sid8580-endpoint.wasm`, then with this SDK's standalone WASM. Their **60,507
float frames were exactly equal**, across all 16 masks, filter, Sync/Ring and
the three rates above. The public C++ helper produced the same frames with
maximum difference 0. This parent comparison is evidence for the host policy;
it is not a sibling-checkout dependency of the distributed SDK checker.

Explicit CMake architecture mismatch and multi-architecture macOS settings are
rejected before the Rust build. Windows/Linux support uses the selected native
toolchains and still requires their own platform checks; the macOS result
does not substitute for those runs. No physical SID accuracy claim follows.
