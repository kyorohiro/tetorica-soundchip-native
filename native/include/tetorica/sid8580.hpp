// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include "sid8580.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace tetorica {
// Optional host policy matching the browser Sid8580Core. This is separate from
// the raw C ABI: tick once BEFORE each bus access, retain generated samples in
// a preallocated 4096-frame queue, normalize int16 /32768, then apply 12 Hz DC
// removal. No C64 CPU, scheduler, hidden gain, envelope reset or device exists.
// Allocation/destruction and all calls must be serialized by the owner.
class Sid8580Core {
public:
    static constexpr uint32_t clockHz = TETORICA_SID8580_CLOCK;
    static constexpr uint32_t capacity = TETORICA_SID8580_OUTPUT_CAPACITY;
    explicit Sid8580Core(uint32_t rate = 48000) : rate_(rate) {
        if (rate < 8000 || rate > 96000) throw std::invalid_argument("SID rate must be 8000..96000");
        handle_ = sid8p_create(rate, 1);
        if (!handle_) throw std::runtime_error("SID 8580 allocation failed");
        dcPole_ = std::exp(-2.0 * 3.14159265358979323846 * 12.0 / rate);
    }
    ~Sid8580Core() { if (handle_) sid8p_destroy(handle_); }
    Sid8580Core(const Sid8580Core&) = delete;
    Sid8580Core& operator=(const Sid8580Core&) = delete;
    Sid8580Core(Sid8580Core&&) = delete;
    Sid8580Core& operator=(Sid8580Core&&) = delete;
    void reset() {
        if (!sid8p_reset(handle_)) throw std::runtime_error("SID 8580 reset failed");
        queue_.fill(0); registers_.fill(0); read_ = count_ = phase_ = 0;
        previousInput_ = previousOutput_ = 0;
    }
    void writeRegister(uint32_t reg, uint32_t value) {
        if (reg > 31 || value > 255) throw std::invalid_argument("SID register/value out of range");
        accessTick();
        if (!sid8p_write(handle_, reg, value)) throw std::runtime_error("SID 8580 write failed");
        registers_[reg] = static_cast<uint8_t>(value);
    }
    uint32_t readRegister(uint32_t reg) {
        if (reg > 31) throw std::invalid_argument("SID register out of range");
        accessTick();
        const uint32_t value = sid8p_read(handle_, reg);
        if (value > 255) throw std::runtime_error("SID 8580 read unsupported or failed");
        return value;
    }
    void renderInto(float* output, uint32_t frames) {
        if (frames && !output) throw std::invalid_argument("Expected SID output buffer");
        for (uint32_t at = 0; at < frames;) {
            if (!count_) {
                const uint32_t wanted = frames - at < capacity ? frames - at : capacity;
                const uint32_t cycles = static_cast<uint32_t>((uint64_t(wanted) * clockHz - phase_ + rate_ - 1) / rate_);
                run(cycles);
            }
            const uint32_t n = count_ < frames - at ? count_ : frames - at;
            for (uint32_t i = 0; i < n; ++i) output[at + i] = queue_[(read_ + i) % capacity];
            read_ = (read_ + n) % capacity; count_ -= n; at += n;
        }
    }
    const std::array<uint8_t, 32>& registers() const { return registers_; }
    uint32_t sampleRate() const { return rate_; }
    uint64_t cycles() const { return uint64_t(sid8p_cycles_hi(handle_)) << 32 | sid8p_cycles_lo(handle_); }
    uint64_t frames() const { return uint64_t(sid8p_frames_hi(handle_)) << 32 | sid8p_frames_lo(handle_); }
private:
    void accessTick() {
        if (count_ == capacity) throw std::runtime_error("SID access queue is full; render before accessing");
        run(1);
    }
    void run(uint32_t cycles) {
        const uint32_t predicted = static_cast<uint32_t>((uint64_t(phase_) + uint64_t(cycles) * rate_) / clockHz);
        if (predicted > capacity - count_) throw std::runtime_error("SID access queue is full; render before accessing");
        const uint32_t produced = sid8p_run(handle_, cycles);
        if (produced != predicted || produced != sid8p_output_frames(handle_)) throw std::runtime_error("SID 8580 render failed");
        phase_ = static_cast<uint32_t>((uint64_t(phase_) + uint64_t(cycles) * rate_) % clockHz);
        const int16_t* samples = sid8p_output(handle_);
        for (uint32_t i = 0; i < produced; ++i) {
            const double input = double(samples[i]) / 32768.0;
            const double output = input - previousInput_ + dcPole_ * previousOutput_;
            previousInput_ = input; previousOutput_ = output;
            queue_[(read_ + count_) % capacity] = static_cast<float>(output); ++count_;
        }
    }
    uint32_t handle_ = 0, rate_, read_ = 0, count_ = 0, phase_ = 0;
    std::array<float, capacity> queue_{};
    std::array<uint8_t, 32> registers_{};
    double previousInput_ = 0, previousOutput_ = 0, dcPole_ = 0;
};
}
