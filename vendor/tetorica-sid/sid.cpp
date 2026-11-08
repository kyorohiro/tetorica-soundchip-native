// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2026, kyorohiro
// Original CPU-free browser ABI, with portable declarations and null guards.
#include <tetorica/sid.h>
#include "sid_core.h"
#include <new>

#if defined(__EMSCRIPTEN__)
#include <emscripten/emscripten.h>
#define TETORICA_SID_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define TETORICA_SID_EXPORT
#endif

struct tetorica_sid_instance {
    tetorica::SidCore core;
    std::array<float, 4096> output{};
    tetorica_sid_instance(int sample_rate, int clock_hz) : core(sample_rate, clock_hz) {}
};

extern "C" {
TETORICA_SID_EXPORT tetorica_sid_instance* sid_create(int sample_rate, int clock_hz) {
    if (sample_rate < 8000 || sample_rate > 96000 || clock_hz < 900000 || clock_hz > 1100000) return nullptr;
    return new (std::nothrow) tetorica_sid_instance(sample_rate, clock_hz);
}
TETORICA_SID_EXPORT void sid_destroy(tetorica_sid_instance* instance) { delete instance; }
TETORICA_SID_EXPORT void sid_reset(tetorica_sid_instance* instance) { if (instance) instance->core.reset(); }
TETORICA_SID_EXPORT int sid_write(tetorica_sid_instance* instance, unsigned reg, unsigned value) {
    return instance ? instance->core.write(reg, value) : 0;
}
TETORICA_SID_EXPORT int sid_read(tetorica_sid_instance* instance, unsigned reg) {
    return instance ? instance->core.read(reg) : -1;
}
TETORICA_SID_EXPORT float* sid_output(tetorica_sid_instance* instance) {
    return instance ? instance->output.data() : nullptr;
}
TETORICA_SID_EXPORT int sid_render(tetorica_sid_instance* instance, unsigned frames) {
    if (!instance || frames > instance->output.size()) return 0;
    instance->core.render(instance->output.data(), frames);
    return 1;
}
TETORICA_SID_EXPORT double sid_cycles(tetorica_sid_instance* instance) {
    return instance ? static_cast<double>(instance->core.cycles()) : 0;
}
TETORICA_SID_EXPORT unsigned sid_envelope(tetorica_sid_instance* instance, unsigned voice) {
    return instance && voice < 3 ? instance->core.envelope(voice) : 0;
}
TETORICA_SID_EXPORT unsigned sid_phase(tetorica_sid_instance* instance, unsigned voice) {
    return instance && voice < 3 ? instance->core.phase(voice) : 0;
}
}
