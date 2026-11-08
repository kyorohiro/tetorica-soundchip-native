// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2026, kyorohiro
// Self-authored 3-voice SID chord. Offline only; stereo duplicates core mono.
#include <tetorica/sid.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
void le16(std::ostream& output, unsigned value) {
    output.put(static_cast<char>(value)); output.put(static_cast<char>(value >> 8));
}
void le32(std::ostream& output, unsigned value) {
    le16(output, value & 65535); le16(output, value >> 16);
}
void write(tetorica_sid_instance* sid, unsigned reg, unsigned value) {
    if (!sid_write(sid, reg, value)) throw std::runtime_error("SID register write failed");
}
}
int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("Usage: tetorica_sid_wav output.wav");
        constexpr unsigned rate = 48000, clock = 985248, frames = rate * 3;
        std::unique_ptr<tetorica_sid_instance, decltype(&sid_destroy)> sid(sid_create(rate, clock), sid_destroy);
        if (!sid) throw std::runtime_error("SID allocation failed");
        write(sid.get(), 24, 15);
        const double frequencies[] = {261.625565, 329.627557, 391.995436};
        const unsigned waves[] = {0x10, 0x20, 0x40};
        for (unsigned voice = 0; voice < 3; ++voice) {
            const unsigned base = voice * 7;
            const unsigned frequency = static_cast<unsigned>(std::lround(frequencies[voice] * 16777216.0 / clock));
            write(sid.get(), base + 4, waves[voice] | 8);
            write(sid.get(), base, frequency & 255); write(sid.get(), base + 1, frequency >> 8);
            write(sid.get(), base + 2, 0); write(sid.get(), base + 3, 8);
            write(sid.get(), base + 5, 0x42); write(sid.get(), base + 6, 0xa6);
            write(sid.get(), base + 4, waves[voice] | 1);
        }
        std::ofstream output(argv[1], std::ios::binary);
        if (!output) throw std::runtime_error("Cannot open output file");
        output.write("RIFF", 4); le32(output, 36 + frames * 4); output.write("WAVEfmt ", 8);
        le32(output, 16); le16(output, 1); le16(output, 2); le32(output, rate);
        le32(output, rate * 4); le16(output, 4); le16(output, 16);
        output.write("data", 4); le32(output, frames * 4);
        for (unsigned at = 0; at < frames;) {
            if (at == rate * 2) for (unsigned voice = 0; voice < 3; ++voice) write(sid.get(), voice * 7 + 4, waves[voice]);
            unsigned count = std::min(256u, frames - at);
            if (at < rate * 2) count = std::min(count, rate * 2 - at);
            if (!sid_render(sid.get(), count)) throw std::runtime_error("SID render failed");
            const float* pcm = sid_output(sid.get());
            for (unsigned i = 0; i < count; ++i) {
                // Explicit example gain/fades belong to the host, not the C ABI.
                const double fade = std::min({1.0, (at + i) / 480.0, (frames - 1 - at - i) / 2400.0});
                const double sample = std::max(-0.95, std::min(0.95, pcm[i] * 0.4 * fade));
                const auto value = static_cast<std::int16_t>(std::lround(sample * 32767));
                le16(output, static_cast<std::uint16_t>(value)); le16(output, static_cast<std::uint16_t>(value));
            }
            at += count;
        }
        if (!output) throw std::runtime_error("Cannot write complete WAV");
        std::cout << "Wrote 3 seconds at 48000 Hz, PCM16 stereo (duplicated SID mono).\n";
        return 0;
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
