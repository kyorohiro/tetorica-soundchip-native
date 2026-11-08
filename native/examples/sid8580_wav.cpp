// SPDX-License-Identifier: BSD-3-Clause
// Three seconds of original notes through the Web-matching CPU-free 8580 host.
#include <tetorica/sid8580.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
constexpr unsigned RATE = 48000, FRAMES = RATE * 3, STEP = RATE / 4;
void u16(std::vector<uint8_t>& v, unsigned n) { v.push_back(uint8_t(n)); v.push_back(uint8_t(n >> 8)); }
void u32(std::vector<uint8_t>& v, unsigned n) { u16(v, n); u16(v, n >> 16); }
void tag(std::vector<uint8_t>& v, const char* t) { v.insert(v.end(), t, t + 4); }
void frequency(tetorica::Sid8580Core& chip, unsigned channel, int midi) {
    const unsigned value = unsigned(std::lround(440.0 * std::pow(2.0, (midi - 69) / 12.0) * 16777216 / 985248));
    chip.writeRegister(channel * 7, value & 255); chip.writeRegister(channel * 7 + 1, value >> 8);
}
std::vector<uint8_t> render() {
    tetorica::Sid8580Core chip(RATE);
    for (unsigned voice = 0; voice < 3; ++voice) {
        const unsigned base = voice * 7;
        chip.writeRegister(base + 2, 0); chip.writeRegister(base + 3, 8);
        chip.writeRegister(base + 5, 0x03); chip.writeRegister(base + 6, 0xb4);
    }
    chip.writeRegister(21, 3); chip.writeRegister(22, 140); chip.writeRegister(23, 0x67); chip.writeRegister(24, 0x1f);
    std::vector<uint8_t> out; out.reserve(44 + FRAMES * 4);
    tag(out, "RIFF"); u32(out, 36 + FRAMES * 4); tag(out, "WAVE"); tag(out, "fmt ");
    u32(out, 16); u16(out, 1); u16(out, 2); u32(out, RATE); u32(out, RATE * 4); u16(out, 4); u16(out, 16);
    tag(out, "data"); u32(out, FRAMES * 4);
    const std::array<int, 4> notes{{60, 64, 67, 62}};
    std::array<float, STEP> pcm{};
    for (unsigned step = 0; step < 12; ++step) {
        for (unsigned voice = 0; voice < 3; ++voice) {
            chip.writeRegister(voice * 7 + 4, voice == 0 ? 0x10 : voice == 1 ? 0x40 : 0x20);
            frequency(chip, voice, notes[step % 4] + (voice == 0 ? 12 : voice == 1 ? 4 : -12));
            chip.writeRegister(voice * 7 + 4, voice == 0 ? 0x11 : voice == 1 ? 0x41 : 0x21);
        }
        // Original cutoff movement, not a recovered tune or software envelope.
        chip.writeRegister(22, 80 + step * 12); chip.renderInto(pcm.data(), STEP);
        for (unsigned i = 0; i < STEP; ++i) {
            const double fade = std::min(1.0, std::min(i / 240.0, (STEP - 1 - i) / 960.0));
            const double sample = 0.45 * fade * pcm[i];
            if (!std::isfinite(sample) || std::abs(sample) >= 1) throw std::runtime_error("Output headroom exceeded");
            const auto value = static_cast<uint16_t>(static_cast<int16_t>(std::lround(sample * 32767)));
            u16(out, value); u16(out, value); // One SID is mono; stereo duplication is host routing.
        }
    }
    return out;
}
}
int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "Usage: tetorica_sid8580_wav output.wav\n"; return 2; }
    try {
        const auto data = render(); std::ofstream file(argv[1], std::ios::binary);
        file.write(reinterpret_cast<const char*>(data.data()), std::streamsize(data.size()));
        if (!file) throw std::runtime_error("WAV write failed");
        std::cout << "SID 8580 Preview: 3 seconds, 48 kHz stereo PCM16; profiles Off\n"; return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
