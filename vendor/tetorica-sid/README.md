# CPU-free SID 6581 host

This SDK component uses the same adapted chips/m6581 core, cycle-to-sample queue,
and mono output as Tetorica's browser SID instrument. It supplies a **6581
approximation**, not an 8580 engine, C64 machine, CPU, `.sid` song player or ROM.
It is independent of the SDK's generic sound-chip factory and device output.

The exact parent `sid_core.h` and WASM bridge are retained under `upstream/`,
with SHA-256 hashes in [PROVENANCE.json](PROVENANCE.json). The compiled
`sid_core.h` changes only the relative include path. `sid.cpp` retains all ten
original `sid_*` ABI names and valid-input behavior, adds a public opaque handle,
and guards null/invalid arguments. Parent sources use BSD-3-Clause; the included
chip retains its separate [zlib license](../chips-m6581/LICENSE). Retain both
licenses with redistributed source or binaries.

## Native

Link `tetorica::sid` (`tetorica_native_sid`) and include `<tetorica/sid.h>` from
C or C++. The implementation requires C++17. For matching floating-point
behavior, build it with `-ffp-contract=off` on GCC/Clang (no fast math), or the
SDK's strict floating-point setting on MSVC. No Emscripten or external package
is needed for a Native build.

```c
#include <tetorica/sid.h>

void render_example(void) {
    tetorica_sid_instance *sid = sid_create(48000, 985248);
    if (!sid) return;
    sid_write(sid, 24, 15); /* Master volume, dry routing. */
    sid_write(sid, 4, 0x18); /* Triangle + TEST while configuring. */
    sid_write(sid, 0, 0x44);
    sid_write(sid, 1, 0x1d);
    sid_write(sid, 5, 0x20); /* Attack / decay. */
    sid_write(sid, 6, 0xa3); /* Sustain / release. */
    sid_write(sid, 4, 0x11); /* Release TEST, Triangle + Gate. */
    if (sid_render(sid, 128)) {
        const float *mono = sid_output(sid);
        /* Consume/copy exactly 128 floats before the next render. */
        (void)mono;
    }
    sid_destroy(sid);
}
```

Keep the handle between callbacks. Each handle owns three physical oscillators,
one shared filter, a bounded sample queue and scratch PCM buffer. Serialize calls
on the same handle; separate handles have independent state. The constructor
accepts output rates 8000–96000 Hz and chip clocks 900000–1100000 Hz (PAL commonly
985248, NTSC commonly 1022727). There is no implicit clock/rate selection.

Every successful register read or write consumes one chip cycle. Generated
samples are queued, then consumed by `sid_render`; they are not dropped. When
the 4096-frame queue is full, writes return 0 and reads return -1 without
advancing time. Render to drain before retrying. Hardware read registers are
exposed, rather than a write-register shadow. `sid_cycles`, `sid_envelope` and
`sid_phase` are observation-only. Rendering accepts at most 4096 mono frames
per call, including zero. The output pointer is borrowed until destroy.

Null destroy/reset are no-ops; null write/render return 0; null read returns -1;
null output returns null; null observations and invalid voice indices return 0.
Invalid rate/clock, register/value or oversized render requests are rejected
without changing a valid handle or its output buffer. A freed or foreign pointer
is never a valid handle. Reset clears chip, clock, sample queue and DC history;
it retains the scratch-buffer allocation and does not promise to zero that buffer.

## Output and limitations

Core mono output passes through the original **12 Hz software DC blocker**.
It is a host stage, not another programmable SID filter. No gain, normalization,
mute, stereo, resampler or note allocator is invented by the ABI. The WAV example
duplicates mono into stereo and applies explicit example gain and fades.

The chip's filter and combined waveforms are simplified approximations, not
measured analog 6581 variation or an 8580 substitute. No-wave output uses the
documented simplified latch decay while oscillator phase continues. Gate,
TEST, Sync/Ring, physical ADSR retrigger behavior (including attack wrap at 255)
and hardware shared-filter routing retain the parent behavior. Do not assume
every possible combined waveform will remain audible, especially with Noise.

## Standalone WebAssembly

```sh
sh scripts/build_sid_wasm.sh build/sid
node tests/sid_wasm_smoke.mjs --wasm-dir build/sid
# Optional exact Native comparison:
node tests/sid_wasm_smoke.mjs --wasm-dir build/sid \
  --native-fixture build/native/native/tetorica_sid_fixture --out build/sid/check.json
```

`sid_wasm.wasm` is a standalone reactor, with no generated JavaScript loader or
npm dependency. Instantiate it with WebAssembly, call `_initialize` once if
exported, then use the same ten `sid_*` exports and `memory`. On WASM32 handles
and `sid_output` are linear-memory addresses. Recreate typed-array views after
any operation that can grow memory. See the smoke checker for the small runtime
import shim and byte-exact render examples. Memory starts at 2 MiB, grows on
demand, and uses a 64 KiB stack. Only constructor/destructor allocate.

`tetorica_sid_fixture --self-test` verifies guards, queue backpressure, physical
channels, partition invariance and independent handles without a device.
`--render SCENE RATE CLOCK CHUNK` emits 8191 little-endian mono float32 samples;
scenes are `triangle`, `pulse`, `combined`, `sync-ring`, `filter` and `release`.
The smoke checker can compare these bytes against Native and optionally the
original parent WASM (`--reference-wasm FILE`). Fixtures are original register
sequences; no music, game assets, firmware or third-party reference engine is used.
