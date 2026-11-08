// SPDX-License-Identifier: BSD-3-Clause
// Actual Rust batch ABI + optional browser-policy host, without a C64/device.
#include <tetorica/sid8580.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
namespace {
unsigned checks = 0;
void check(bool condition, const char* text) { ++checks; if (!condition) throw std::runtime_error(text); }
uint64_t cycles(uint32_t h) { return uint64_t(sid8p_cycles_hi(h)) << 32 | sid8p_cycles_lo(h); }
uint64_t frames(uint32_t h) { return uint64_t(sid8p_frames_hi(h)) << 32 | sid8p_frames_lo(h); }
void configure(uint32_t h, unsigned seed = 0) {
    for (unsigned v = 0; v < 3; ++v) {
        const unsigned base = v * 7, frequency = 1700 + v * 2300 + seed * 73;
        check(sid8p_write(h, base, frequency & 255) && sid8p_write(h, base + 1, frequency >> 8), "frequency write");
        sid8p_write(h, base + 2, 0x34); sid8p_write(h, base + 3, 8);
        sid8p_write(h, base + 5, 0x03); sid8p_write(h, base + 6, 0xb4);
        sid8p_write(h, base + 4, v == 0 ? 0x11 : v == 1 ? 0x41 : 0x21);
    }
    sid8p_write(h, 21, 3); sid8p_write(h, 22, 170); sid8p_write(h, 23, 0x97); sid8p_write(h, 24, 0x1f);
}
std::vector<int16_t> run(uint32_t h, unsigned count, const std::vector<unsigned>& blocks = {30000}) {
    std::vector<int16_t> output;
    for (unsigned at = 0, part = 0; at < count;) {
        const unsigned n = std::min(blocks[part++ % blocks.size()], count - at);
        const uint32_t produced = sid8p_run(h, n);
        check(produced <= 4096 && produced == sid8p_output_frames(h), "bounded actual batch output");
        const int16_t* data = sid8p_output(h); check(data != nullptr, "Native output is a valid pointer");
        output.insert(output.end(), data, data + produced); at += n;
    }
    return output;
}
bool audible(const std::vector<int16_t>& pcm) {
    const auto bounds = std::minmax_element(pcm.begin(), pcm.end());
    return bounds.first != pcm.end() && *bounds.second - *bounds.first > 100;
}
void basic() {
    check(!sid8p_create(7999, 1) && !sid8p_create(96001, 1) && !sid8p_create(48000, 2), "invalid creation arguments");
    check(!sid8p_output(0) && sid8p_read(0, 0) == 256 && sid8p_run(0, 1) == UINT32_MAX, "invalid handles");
    check(sid8p_error(0) == 1 && !sid8p_destroy(0), "invalid handle errors");
    const auto h = sid8p_create(48000, 1); check(h != 0, "create PAL 8580");
    check(sid8p_model(h) == 1 && sid8p_rate(h) == 48000, "configuration observations");
    check(!sid8p_calibration(h) && !sid8p_cutoff_calibration(h), "research profiles default Off");
    check(sid8p_write(h, 0, 0x9a) && sid8p_read(h, 0) == 0x9a && cycles(h) == 0, "raw bus accesses do not clock");
    check(!sid8p_write(h, 32, 1) && sid8p_error(h) == 2 && cycles(h) == 0, "invalid register is atomic");
    check(sid8p_read(h, 25) == 256 && sid8p_error(h) == 5 && cycles(h) == 0, "unsupported POT is explicit");
    check(!sid8p_set_8580_calibration(h, 2) && !sid8p_calibration(h), "profile argument validation");
    configure(h); check(audible(run(h, 200000)), "real three-voice/filter audio");
    const auto before = cycles(h), beforeFrames = frames(h);
    check(sid8p_run(h, UINT32_MAX) == UINT32_MAX && sid8p_error(h) == 3, "oversized batch rejected");
    check(cycles(h) == before && frames(h) == beforeFrames && !sid8p_output_frames(h), "failed run clocks nothing and clears valid output length");
    check(sid8p_set_8580_calibration(h, 1) && sid8p_set_8580_cutoff_calibration(h, 1), "explicit profile opt in");
    check(sid8p_stop(h) && sid8p_stopped(h) && sid8p_run(h, 1000) == 0, "Stop latches stopped");
    check(cycles(h) == before && frames(h) == beforeFrames, "Stop preserves counters and prevents clocks");
    check(sid8p_written(h, 4) == 0 && sid8p_bus_value(h) == 0 && sid8p_output_frames(h) == 0, "Stop clears bus registers and output");
    check(sid8p_reset(h) && !sid8p_stopped(h) && !cycles(h) && !frames(h), "Reset clears epoch and resumes");
    check(sid8p_calibration(h) && sid8p_cutoff_calibration(h), "Stop/Reset retain explicit profiles");
    check(sid8p_destroy(h) && sid8p_error(h) == 1, "destroy invalidates generation");
    const auto fresh = sid8p_create(48000, 1); check(fresh && fresh != h, "reused slot gets new generation");
    check(!sid8p_write(h, 24, 15) && sid8p_written(fresh, 24) == 0, "stale handle cannot affect replacement");
    sid8p_destroy(fresh);
    std::array<uint32_t, 16> handles{};
    for (auto& handle : handles) { handle = sid8p_create(48000, 1); check(handle != 0, "sixteen live handles"); }
    check(!sid8p_create(48000, 1), "bounded registry capacity");
    for (auto handle : handles) sid8p_destroy(handle);
}
void partitionsAndIsolation() {
    for (unsigned rate : {8000u, 44100u, 48000u, 96000u}) {
        const auto a = sid8p_create(rate, 1), b = sid8p_create(rate, 1);
        configure(a); configure(b);
        const auto whole = run(a, 200003), split = run(b, 200003, {1, 7, 193, 509, 30000});
        check(whole == split && audible(whole), "exact integer-phase partition continuation");
        check(cycles(a) == cycles(b) && frames(a) == frames(b), "partitioned counters match");
        sid8p_reset(a); configure(a); check(run(a, 200003) == whole, "Reset replays exact PCM");
        sid8p_destroy(a); sid8p_destroy(b);
    }
    const auto a = sid8p_create(48000, 1), b = sid8p_create(48000, 1), reference = sid8p_create(48000, 1);
    configure(a, 2); configure(b, 4); configure(reference, 4);
    for (unsigned step = 0; step < 16; ++step) {
        run(a, 901 + step); sid8p_write(a, 0, step * 7);
        check(run(b, 3011 + step) == run(reference, 3011 + step), "interleaved independent chips");
        if (step == 7) sid8p_reset(a);
    }
    sid8p_destroy(a); check(run(b, 30001) == run(reference, 30001), "destroy A preserves B");
    sid8p_destroy(b); sid8p_destroy(reference);
}
void host() {
    for (unsigned rate : {44100u, 48000u, 96000u}) {
        tetorica::Sid8580Core a(rate), b(rate);
        for (auto* chip : {&a, &b}) {
            chip->writeRegister(24, 15); chip->writeRegister(0, 0x42); chip->writeRegister(1, 0x1d);
            chip->writeRegister(5, 3); chip->writeRegister(6, 0xb4); chip->writeRegister(4, 0x21);
        }
        check(a.cycles() == 6 && a.registers()[4] == 0x21, "host ticks once before each access");
        std::vector<float> whole(8193), split(8193); a.renderInto(whole.data(), unsigned(whole.size()));
        for (unsigned at = 0; at < split.size();) {
            const unsigned n = std::min<unsigned>(193, unsigned(split.size()) - at); b.renderInto(split.data() + at, n); at += n;
        }
        check(whole == split, "host queue and float/DC partition invariance");
        check(std::any_of(whole.begin(), whole.end(), [](float f) { return std::abs(f) > .001f; }), "host audible float output");
        const auto before = a.cycles(); bool rejected = false;
        try { a.writeRegister(32, 0); } catch (const std::invalid_argument&) { rejected = true; }
        check(rejected && a.cycles() == before, "invalid host arguments do not clock");
        a.reset(); check(a.cycles() == 0 && a.registers()[4] == 0, "host reset clears metadata/queue/DC");
        bool full = false;
        for (unsigned i = 0; i < 600000 && !full; ++i) {
            try { a.writeRegister(0, i & 255); } catch (const std::runtime_error&) { full = true; }
        }
        check(full, "bounded host access queue");
        const auto atFull = a.cycles();
        try { a.writeRegister(1, 0); } catch (const std::runtime_error&) {}
        check(a.cycles() == atFull, "full queue rejection advances nothing");
    }
}
unsigned number(const std::string& s) {
    if (s.empty() || s.find_first_not_of("0123456789") != std::string::npos) throw std::runtime_error("Expected decimal unsigned number");
    const auto n = std::stoull(s); if (n > UINT32_MAX) throw std::runtime_error("Number exceeds uint32"); return unsigned(n);
}
void byte(unsigned n) { if (std::fputc(int(n & 255), stdout) == EOF) throw std::runtime_error("PCM write failed"); }
void pcm16(int16_t sample) { byte(uint16_t(sample)); byte(uint16_t(sample) >> 8); }
void pcm32(float sample) { uint32_t bits; std::memcpy(&bits, &sample, 4); for (unsigned i = 0; i < 32; i += 8) byte(bits >> i); }
int protocol(int argc, char** argv) {
    if (argc != 3 || (std::string(argv[1]) != "--raw" && std::string(argv[1]) != "--host"))
        throw std::runtime_error("Usage: tetorica_sid8580_fixture --self-test | --raw RATE | --host RATE");
    const bool raw = std::string(argv[1]) == "--raw"; const unsigned rate = number(argv[2]);
    if (rate < 8000 || rate > 96000) throw std::runtime_error("Rate outside 8000..96000");
    const uint32_t h = raw ? sid8p_create(rate, 1) : 0; if (raw && !h) throw std::runtime_error("Allocation failed");
    tetorica::Sid8580Core hostChip(rate); std::vector<unsigned> reads;
    std::array<float, 4096> scratch{}; std::string line; uint64_t total = 0; unsigned commands = 0;
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    while (std::getline(std::cin, line)) {
        if (line.size() > 256 || ++commands > 1000000) throw std::runtime_error("Protocol limit");
        std::istringstream in(line); std::string op, a, b, extra; if (!(in >> op) || op[0] == '#') continue;
        if (op == "w") {
            if (!(in >> a >> b) || in >> extra) throw std::runtime_error("Expected w register value");
            const unsigned reg = number(a), value = number(b);
            if (reg > 31 || value > 255) throw std::runtime_error("Invalid register/value");
            if (raw) check(sid8p_write(h, reg, value), "protocol write"); else hostChip.writeRegister(reg, value);
        } else if (op == "r") {
            if (!(in >> a) || in >> extra) throw std::runtime_error("Expected r register");
            reads.push_back(raw ? sid8p_read(h, number(a)) : hostChip.readRegister(number(a)));
        } else if (op == "c" || op == "g") {
            if (!(in >> a) || in >> extra || (raw ? op != "c" : op != "g")) throw std::runtime_error("Use c cycles for raw, g frames for host");
            unsigned remaining = number(a); total += remaining;
            if (total > (raw ? 60ull * 985248 : 60ull * rate)) throw std::runtime_error("Protocol duration limit");
            while (remaining) {
                const unsigned n = std::min(remaining, raw ? 30000u : 4096u);
                if (raw) { const auto pcm = run(h, n); for (auto sample : pcm) pcm16(sample); }
                else { hostChip.renderInto(scratch.data(), n); for (unsigned i = 0; i < n; ++i) pcm32(scratch[i]); }
                remaining -= n;
            }
        } else if (op == "reset" || op == "stop") {
            if (in >> extra || (!raw && op == "stop")) throw std::runtime_error("Invalid reset/stop operands");
            if (raw) { if (op == "reset") sid8p_reset(h); else sid8p_stop(h); } else hostChip.reset();
        } else throw std::runtime_error("Unknown protocol command");
    }
    std::cerr << "{\"cycles\":" << (raw ? cycles(h) : hostChip.cycles()) << ",\"frames\":" << (raw ? frames(h) : hostChip.frames()) << ",\"reads\":[";
    for (unsigned i = 0; i < reads.size(); ++i) std::cerr << (i ? "," : "") << reads[i];
    std::cerr << "]}\n"; if (raw) sid8p_destroy(h); return std::fflush(stdout) ? 1 : 0;
}
}
int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--self-test") {
            basic(); partitionsAndIsolation(); host();
            std::printf("{\"status\":\"pass\",\"checks\":%u,\"cpuFree\":true,\"profilesDefaultOff\":true}\n", checks); return 0;
        }
        return protocol(argc, argv);
    } catch (const std::exception& error) { std::fprintf(stderr, "SID 8580 fixture failed: %s\n", error.what()); return 1; }
}
