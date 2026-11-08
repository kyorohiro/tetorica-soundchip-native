// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2026, kyorohiro
// Original register fixtures, with no C64 CPU, music, firmware or audio device.
#include <tetorica/sid.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

namespace {
constexpr unsigned frames = 8191;
using Handle = std::unique_ptr<tetorica_sid_instance, decltype(&sid_destroy)>;
void require(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
Handle create(int rate = 48000, int clock = 985248) {
    Handle handle(sid_create(rate, clock), sid_destroy);
    require(bool(handle), "create valid handle");
    return handle;
}
void write(tetorica_sid_instance* sid, unsigned reg, unsigned value) {
    require(sid_write(sid, reg, value) == 1, "register write");
}
bool validScene(const std::string& scene) {
    return scene == "triangle" || scene == "pulse" || scene == "combined" ||
           scene == "sync-ring" || scene == "filter" || scene == "release";
}
void configure(tetorica_sid_instance* sid, const std::string& scene) {
    require(validScene(scene), "unknown fixture scene");
    write(sid, 24, 15);
    const unsigned frequencies[] = {0x1d44, 0x24e2, 0x2bf4};
    const unsigned widths[] = {0x800, 0x400, 0xc00};
    for (unsigned voice = 0; voice < 3; ++voice) {
        const unsigned base = voice * 7;
        write(sid, base + 4, 8); // TEST holds phase during setup.
        write(sid, base, frequencies[voice] & 255);
        write(sid, base + 1, frequencies[voice] >> 8);
        write(sid, base + 2, widths[voice] & 255);
        write(sid, base + 3, widths[voice] >> 8);
        write(sid, base + 5, 0x20 + voice * 0x11);
        write(sid, base + 6, 0xa3 - voice * 0x0f);
    }
    if (scene == "filter") {
        write(sid, 21, 5); write(sid, 22, 90); write(sid, 23, 0xa7); write(sid, 24, 0x3f);
    }
    for (unsigned voice = 0; voice < 3; ++voice) {
        unsigned control = 0x11;
        if (scene == "pulse") control = 0x41;
        if (scene == "combined") control = std::array<unsigned, 3>{{0x31, 0x51, 0x71}}[voice];
        if (scene == "filter") control = std::array<unsigned, 3>{{0x21, 0x41, 0x11}}[voice];
        if (scene == "sync-ring") control = std::array<unsigned, 3>{{0x17, 0, 0x10}}[voice];
        if (scene == "release" && voice != 0) control = 0;
        write(sid, voice * 7 + 4, control);
    }
}
std::vector<float> generate(tetorica_sid_instance* sid, unsigned count) {
    require(sid_render(sid, count) == 1, "render bounded frames");
    const float* output = sid_output(sid);
    require(output != nullptr, "borrow output");
    std::vector<float> result(output, output + count);
    for (float value : result) require(std::isfinite(value), "finite mono output");
    return result;
}
struct Result {
    std::vector<float> pcm;
    double cycles;
    std::array<unsigned, 3> envelope, phase;
};
Result renderScene(const std::string& scene, int rate, int clock, unsigned chunk) {
    require(chunk >= 1 && chunk <= 4096, "chunk must be 1..4096");
    auto sid = create(rate, clock); configure(sid.get(), scene);
    Result result; result.pcm.reserve(frames);
    for (unsigned at = 0; at < frames;) {
        if (scene == "release" && at == 2048) write(sid.get(), 4, 0x10);
        unsigned count = std::min(chunk, frames - at);
        if (scene == "release" && at < 2048) count = std::min(count, 2048 - at);
        const auto part = generate(sid.get(), count);
        result.pcm.insert(result.pcm.end(), part.begin(), part.end());
        at += count;
    }
    result.cycles = sid_cycles(sid.get());
    for (unsigned voice = 0; voice < 3; ++voice) {
        result.envelope[voice] = sid_envelope(sid.get(), voice);
        result.phase[voice] = sid_phase(sid.get(), voice);
    }
    return result;
}
bool equalPCM(const std::vector<float>& a, const std::vector<float>& b) {
    return a.size() == b.size() && std::memcmp(a.data(), b.data(), a.size() * sizeof(float)) == 0;
}
bool varying(const std::vector<float>& pcm) {
    const auto limits = std::minmax_element(pcm.begin(), pcm.end());
    return *limits.second - *limits.first > 0.001f;
}
void selfTest() {
    for (int rate : {0, 7999, 96001}) require(sid_create(rate, 985248) == nullptr, "invalid rate");
    for (int clock : {0, 899999, 1100001}) require(sid_create(48000, clock) == nullptr, "invalid clock");
    sid_destroy(nullptr); sid_reset(nullptr);
    require(!sid_write(nullptr, 0, 0) && sid_read(nullptr, 0) == -1 && !sid_render(nullptr, 1), "null commands");
    require(sid_output(nullptr) == nullptr && sid_cycles(nullptr) == 0 &&
            sid_phase(nullptr, 0) == 0 && sid_envelope(nullptr, 0) == 0, "null observations");
    auto sid = create();
    require(sid_render(sid.get(), 0) == 1 && sid_cycles(sid.get()) == 0, "zero render");
    const auto cold = generate(sid.get(), 257);
    require(std::all_of(cold.begin(), cold.end(), [](float value) { return value == 0; }), "cold silence");
    sid_reset(sid.get()); configure(sid.get(), "triangle");
    require(varying(generate(sid.get(), 4096)), "three voice sound");
    const auto time = sid_cycles(sid.get());
    const auto before = std::vector<float>(sid_output(sid.get()), sid_output(sid.get()) + 4096);
    require(!sid_write(sid.get(), 32, 0) && !sid_write(sid.get(), 0, 256) &&
            sid_read(sid.get(), 32) == -1 && !sid_render(sid.get(), 4097), "invalid operation rejected");
    require(sid_cycles(sid.get()) == time && equalPCM(before,
            std::vector<float>(sid_output(sid.get()), sid_output(sid.get()) + 4096)), "invalid operation preserves state/buffer");
    require(sid_phase(sid.get(), 3) == 0 && sid_envelope(sid.get(), 3) == 0 && sid_cycles(sid.get()) == time,
            "invalid voice and observation timing");
    require(sid_read(sid.get(), 28) >= 0 && sid_cycles(sid.get()) == time + 1, "hardware read clocks once");
    require(sid_write(sid.get(), 24, 15) && sid_cycles(sid.get()) == time + 2, "hardware write clocks once");
    sid_reset(sid.get());
    require(sid_cycles(sid.get()) == 0 && sid_phase(sid.get(), 0) == 0, "reset clocks/phase");
    const auto resetPCM = generate(sid.get(), 257);
    require(std::all_of(resetPCM.begin(), resetPCM.end(), [](float value) { return value == 0; }), "reset clears output history");
    for (unsigned voice = 0; voice < 3; ++voice) {
        sid_reset(sid.get());
        write(sid.get(), 24, 15); write(sid.get(), voice * 7 + 4, 0x18);
        write(sid.get(), voice * 7, 0x44); write(sid.get(), voice * 7 + 1, 0x1d);
        write(sid.get(), voice * 7 + 5, 0x20); write(sid.get(), voice * 7 + 6, 0xa3);
        write(sid.get(), voice * 7 + 4, 0x11);
        require(varying(generate(sid.get(), 4096)), "each physical voice audible");
    }
    // Waveform off must not stop the accumulator; TEST must still reset it.
    sid_reset(sid.get()); write(sid.get(), 0, 0x44); write(sid.get(), 1, 0x1d);
    generate(sid.get(), 128); require(sid_phase(sid.get(), 0) != 0, "waveform off advances phase");
    write(sid.get(), 4, 8); generate(sid.get(), 128); require(sid_phase(sid.get(), 0) == 0, "TEST holds phase");
    // Exercise every nonzero selector without claiming all Noise combinations audible.
    for (unsigned mask = 1; mask < 16; ++mask) {
        sid_reset(sid.get()); configure(sid.get(), "triangle");
        write(sid.get(), 4, (mask << 4) | 1); generate(sid.get(), 129);
    }
    for (const std::string scene : {"triangle", "pulse", "combined", "sync-ring", "filter", "release"}) {
        for (int rate : {8000, 44100, 48000, 96000}) for (int clock : {985248, 1022727}) {
            const auto a = renderScene(scene, rate, clock, 4096), b = renderScene(scene, rate, clock, 113);
            require(equalPCM(a.pcm, b.pcm), "exact partition PCM");
            require(a.cycles == b.cycles && a.envelope == b.envelope && a.phase == b.phase, "partition observation continuity");
        }
    }
    auto a = create(), ar = create(), b = create(44100, 1022727), br = create(44100, 1022727);
    configure(a.get(), "filter"); configure(ar.get(), "filter");
    configure(b.get(), "sync-ring"); configure(br.get(), "sync-ring");
    for (unsigned block = 0; block < 23; ++block) {
        const unsigned count = 17 + block * 13;
        write(a.get(), 0, block * 7); write(ar.get(), 0, block * 7);
        require(equalPCM(generate(a.get(), count), generate(ar.get(), count)), "interleaved handle A");
        require(equalPCM(generate(b.get(), count + 3), generate(br.get(), count + 3)), "interleaved handle B");
    }
    sid_reset(a.get()); a.reset(); a = create(96000, 1000000); configure(a.get(), "combined"); generate(a.get(), 777);
    require(equalPCM(generate(b.get(), 4096), generate(br.get(), 4096)), "other lifetime does not alter B");
    // Backpressure is deliberate: bus traffic never discards pending PCM.
    sid_reset(sid.get());
    unsigned writes = 0;
    while (sid_write(sid.get(), 24, 15)) require(++writes < 500000, "queue eventually fills");
    const auto fullTime = sid_cycles(sid.get());
    require(writes > 4096 && !sid_write(sid.get(), 0, 1) && sid_read(sid.get(), 28) == -1 &&
            sid_cycles(sid.get()) == fullTime, "full queue preserves time on rejected bus accesses");
    generate(sid.get(), 4096);
    require(sid_cycles(sid.get()) == fullTime && sid_write(sid.get(), 24, 0), "render drains queued bus PCM without extra cycles");
    std::cout << "{\"passed\":true,\"artifact\":\"sid\",\"checks\":[\"C-ABI-guards\",\"three-physical-voices\","
                 "\"wave-off-and-TEST\",\"all-wave-selectors-finite\",\"exact-partition-continuity\","
                 "\"independent-handles\",\"bounded-lossless-bus-sample-queue\"]}\n";
}
void rawPCM(const std::vector<float>& pcm) {
    static_assert(sizeof(float) == 4, "fixture requires IEEE float32");
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    for (float value : pcm) {
        std::uint32_t bits; std::memcpy(&bits, &value, 4);
        const unsigned char bytes[] = {static_cast<unsigned char>(bits), static_cast<unsigned char>(bits >> 8),
                                      static_cast<unsigned char>(bits >> 16), static_cast<unsigned char>(bits >> 24)};
        require(std::fwrite(bytes, 1, 4, stdout) == 4, "write raw float32 output");
    }
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 1 || (argc == 2 && std::string(argv[1]) == "--self-test")) { selfTest(); return 0; }
        if (argc == 6 && std::string(argv[1]) == "--render") {
            const int rate = std::stoi(argv[3]), clock = std::stoi(argv[4]), chunk = std::stoi(argv[5]);
            require(chunk >= 1 && chunk <= 4096, "chunk must be 1..4096");
            rawPCM(renderScene(argv[2], rate, clock, static_cast<unsigned>(chunk)).pcm); return 0;
        }
        throw std::runtime_error("Usage: tetorica_sid_fixture [--self-test | --render SCENE RATE CLOCK CHUNK]");
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
