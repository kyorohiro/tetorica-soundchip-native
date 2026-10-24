# tetorica-soundchip-native

**Sound-chip emulation library for commercial use, with GPL-only cores excluded.**

Self-contained C/C++ sound-chip sources, native adapters, and WebAssembly build recipes for music players, synthesizers, games, and audio tools.

The collection includes the required core sources, component licenses, local modifications, and verification tools. Source archives build from their own contents: no submodules, sibling checkouts, or sound-core downloads are required.

Commercial projects can select cores under **BSD-3-Clause, MIT, and Apache-2.0**. The default YM2612 backend uses BSD-3-Clause **ymfm**. Optional **Nuked-OPN2 and SNES/SPC** components retain their **LGPL** terms, including the applicable distribution and relinking requirements. Select the components you need and follow their licenses; [LICENSES.md](LICENSES.md) maps the sources and terms.

## Supported sources and build status

The source catalog covers 22 chip API identifiers:

- **Yamaha FM:** YM2612, YM2203, YM2608, YM2610, YM2610B, YM2151, YM2413, YM3526, YM3812, Y8950, and YMF262.
- **PSG:** Sega PSG and AY-3-8910.
- **Console audio:** Game Boy, NES with optional FDS, SNES S-DSP, SPC700/S-DSP playback, and PC Engine HuC6280.
- **PCM and ADPCM:** RF5C164, OKIM6258, and Sega 32X PWM.
- **FM synthesizer:** MSFA-based DX7.

Additional WASM recipes cover YM3438, YMF276, YMF288, YMF278B, Sega PCM, and K051649. YM2612 also includes the optional Nuked-OPN2 engine.

The collection also includes the VGM Analyzer's **MSM5205 and OKIM6295 JavaScript reference implementations**, plus separately pinned upstream C/C++ source references under [libvgm-msm5205](vendor/libvgm-msm5205/) and [mame-okim6295](vendor/mame-okim6295/). SDK Native/WASM integrations for these two engines are not yet provided.

The upstream references include files explicitly marked BSD-3-Clause. libvgm support files without an explicit license declaration are omitted, following the [upstream licensing status](https://github.com/ValleyBell/libvgm/issues/129). The component READMEs and snapshot manifests describe the omissions and framework dependencies. These reference-only files are separate from the self-contained build targets and runnable JavaScript engines.

| Deliverable | Current status |
| --- | --- |
| Standalone native CMake targets | **YM2612, YM2151, YM2413, YM2203 and YM2608 using ymfm, plus Sega PSG and AY-3-8910**, with offline test fixtures |
| Other native adapters | Reference sources included; standalone targets are being added |
| WASM build recipes | 27 artifacts; independent builds verified for YM2612 and DX7 |
| Initial compiled WASM archive | YM2612, with its matching source archive embedded |
| JavaScript references | MSM5205 and OKIM6295; runnable ES modules, with no Native/WASM port yet |

Source availability does not imply that every adapter is ready to link unchanged. The [chip differences](docs/chip-differences.md) document records required combinations and known prerequisites, including the Game Boy native header adjustment. See the [machine-readable catalog](catalog/chips.json) and [verification record](docs/verification.md) for details.

[Verify SDK](.github/workflows/verify-sdk.yml) runs on pushes, pull requests, and manual dispatch. Its Native matrix is configured for Windows x64, Linux x64/ARM64, and macOS Intel/Apple Silicon. Each job builds YM2612, YM2151, YM2413, YM2203, YM2608, Sega PSG and AY-3-8910 in Release mode from an independently extracted source ZIP, runs seven CTest fixtures, renders five offline WAV examples, and checks the JavaScript references. A separate Ubuntu job compiles YM2612 WASM, verifies the matching source archive and synchronous ABI, and rebuilds from the extracted archive. See the [verification record](docs/verification.md) for completed runs; the earlier YM2612-only matrix does not establish coverage for subsequently added targets.

## Build the native libraries

Requirements: CMake 3.20 or newer and a C++14 compiler.

```sh
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native -C Release --output-on-failure
```

To embed a source distribution in your project:

```cmake
add_subdirectory(vendor/tetorica-soundchip-native)
target_link_libraries(your_application PRIVATE tetorica::ym2612)
# For the eight-channel OPM chip, select tetorica::ym2151 instead.
# For the independent Sega PSG, select tetorica::segapsg.
# For OPLL melody/rhythm, select tetorica::ym2413.
# For AY tones/noise/envelope, select tetorica::ay8910.
# For OPN's three FM plus three SSG voices, select tetorica::ym2203.
# For OPNA FM/SSG/rhythm/ADPCM-B, select tetorica::ym2608.
```

The public headers are `<tetorica/ym2612.hpp>`, `<tetorica/ym2151.hpp>`, `<tetorica/ym2413.hpp>`, `<tetorica/ym2203.hpp>`, `<tetorica/ym2608.hpp>`, `<tetorica/segapsg.hpp>` and `<tetorica/ay8910.hpp>`. They expose the existing `native_ym2612_*`, `native_ym2151_*`, `native_ym2413_*`, `native_ym2203_*`, `native_ym2608_*`, compatibility-named `native_game_gear_*` and `native_ay8910_*` C ABIs to C++ hosts. YM2413 supports nine melodic FM channels or six FM channels plus five rhythm voices sharing physical channels 6–8. YM2203 combines three FM channels and three SSG voices in one mono output, copied to both stereo channels. YM2608 supplies six FM channels, three SSG voices, six fixed-ROM rhythm voices and ADPCM-B RAM playback; the host supplies the encoded sample data. Sega PSG supplies three tone channels, noise and optional Game Gear stereo; AY supplies three tone/noise voices and a shared envelope with mono output on both channels. These targets own their respective chips independently. X68000's OKIM6258 integration remains reference-only. See the [native guide](native/README.md) for integration examples.

This YM2612 example configures a simple voice and generates a stereo buffer:

```cpp
#include <tetorica/ym2612.hpp>

int main() {
    void* chip = native_ym2612_create(48000);
    if (!chip) return 1;
    const auto write = [chip](unsigned reg, unsigned value) {
        native_ym2612_write(chip, 0, reg, value);
    };
    for (unsigned slot = 0; slot < 4; ++slot) {
        const unsigned offset = slot * 4;
        write(0x30 + offset, 1);
        write(0x40 + offset, slot == 0 ? 20 : 127);
        write(0x50 + offset, 31);
        write(0x60 + offset, 0);
        write(0x70 + offset, 0);
        write(0x80 + offset, 15);
    }
    write(0xb0, 7);    // Algorithm 7: independent carriers
    write(0xb4, 0xc0); // CH1: left + right
    write(0xa4, 0x22);
    write(0xa0, 0x69);
    write(0x28, 0xf0); // CH1 key on

    float left[512], right[512];
    for (unsigned i = 0; i < 512; ++i) {
        native_ym2612_sample(chip, &left[i], &right[i]);
    }
    // Send these buffers to your audio output or file renderer.
    native_ym2612_destroy(chip);
}
```

In a real-time application, create and configure the chip before the audio callback, retain it between callbacks, and destroy it after playback has stopped. Your host supplies audio output, scheduling, and synchronization. The [native API notes](native/README.md) describe state access, lifetime requirements, and the current ABI.

## Render sound-chip WAV examples

The default build produces five offline examples using the actual SDK libraries. `tetorica_genesis_wav` combines a YM2612 melody with PSG tones and short noise percussion. `tetorica_master_system_wav` combines YM2413's built-in piano and rhythm voices with Sega PSG tones. `tetorica_msx_wav` combines AY tones, noise and a hardware envelope with an OPLL flute melody. `tetorica_pc98_ym2203_wav` uses all three FM channels and three SSG voices, including noise and envelope, within one YM2203. `tetorica_pc98_ym2608_wav` combines OPNA FM/SSG with original synthetic ADPCM-A percussion and an ADPCM-B pluck, uploading both ROM and RAM data. They demonstrate Genesis, FM-enabled Master System, MSX+MSX-MUSIC and two PC-98 sound configurations. Each writes three seconds of 48 kHz stereo PCM16. No audio device, external ROM, asset or npm dependency is needed. The OPNA example's generated rhythm data is not a copy of a hardware rhythm ROM.

```sh
# After the root CMake build above, with a single-configuration generator:
./build/native/native/tetorica_genesis_wav "genesis demo.wav"
./build/native/native/tetorica_master_system_wav "master system demo.wav"
./build/native/native/tetorica_msx_wav "msx demo.wav"
./build/native/native/tetorica_pc98_ym2203_wav "pc98 ym2203 demo.wav"
./build/native/native/tetorica_pc98_ym2608_wav "pc98 ym2608 demo.wav"
# With Visual Studio on Windows:
./build/native/native/Release/tetorica_genesis_wav.exe "genesis demo.wav"
./build/native/native/Release/tetorica_master_system_wav.exe "master system demo.wav"
./build/native/native/Release/tetorica_msx_wav.exe "msx demo.wav"
./build/native/native/Release/tetorica_pc98_ym2203_wav.exe "pc98 ym2203 demo.wav"
./build/native/native/Release/tetorica_pc98_ym2608_wav.exe "pc98 ym2608 demo.wav"
```

Each executable's single required argument selects the output file; its parent directory must exist. All use fixed example gains and chip-clock pitch conversion. Sega PSG stereo `0xff` retains Genesis/Master System mono output on both channels; AY, OPLL and YM2203 output is also mono on both channels. These are sound configurations, not whole-console emulators or measurements of a motherboard's analog mix. Set `-DTETORICA_NATIVE_BUILD_EXAMPLES=OFF` to omit them when embedding the libraries.

## Build WebAssembly

Requirements: an installed Emscripten toolchain, Node.js, and a POSIX shell.

```sh
sh scripts/build-wasm.sh --list
sh scripts/build-wasm.sh ym2612 build/verified-wasm
```

Most artifacts produce an Emscripten ES module (`*_wasm.js`) and its matching `.wasm` file. Ship both files together. DX7 produces the standalone `msfa.wasm` artifact. Synchronous register reads and PCM generation remain available through the corresponding low-level exports; the native and WASM entry points are documented separately.

Each build records its compiler, input hashes, and output hashes in `build-info.json`. A separate output directory keeps rebuilt artifacts apart from any imported reference binaries.

## Run the JavaScript ADPCM references

Requirements: Node.js 22 or newer. No npm installation, audio device, or external sample ROM is required for the example.

```sh
node reference/javascript/examples/render-adpcm.mjs build/adpcm-reference
```

The example generates MSM5205 and OKIM6295 WAV files from synthetic data. The two reference engines are unchanged copies of the Tetorica Analyzer implementations and can also be imported as ES modules. They provide a behavioral reference for future native ports. See [the JavaScript reference guide](reference/javascript/README.md) for their APIs and limitations.

## Use a release archive

Keep a versioned source archive in your own project and record its SHA-256. Updates are explicit; an application can keep using its pinned version independently of this repository.

To create and verify archives locally:

```sh
python3 scripts/check_sdk.py
python3 scripts/package_release.py --out-dir releases --wasm-dir build/verified-wasm
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip
```

The source ZIP includes sources, build recipes, licenses, provenance, and tests. The WASM ZIP includes compiled artifacts and the exact matching source ZIP. Both carry per-file SHA-256 manifests. Omit `--wasm-dir` to create only the source archive. See [release packaging and integration](docs/releases.md).

For JavaScript Synth helpers, AudioWorklet integration, and higher-level APIs, see [tetorica-fm2612](https://www.npmjs.com/package/tetorica-fm2612).

## Documentation

- [Native API and build notes](native/README.md)
- [Per-chip source and backend differences](docs/chip-differences.md)
- [MSFA/DX7 modifications](docs/research.md)
- [MSM5205 and OKIM6295 JavaScript references](reference/javascript/README.md)
- [Release packaging and integration](docs/releases.md)
- [Architecture and source maintenance](docs/architecture.md)
- [Verification results](docs/verification.md)

## License

Original Tetorica code, adapters, tooling, tests, and documentation use the **BSD 3-Clause License**, matching tetorica-fm2612, unless a file explicitly specifies otherwise. See [LICENSE](LICENSE).

Third-party cores and explicitly licensed adaptations retain their existing licenses and copyright notices, including BSD, Apache-2.0, MIT, and LGPL components. [LICENSES.md](LICENSES.md) and the source catalogs identify the applicable files and license texts.
