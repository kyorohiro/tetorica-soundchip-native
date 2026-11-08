/* SPDX-License-Identifier: BSD-3-Clause
 * Copyright (c) 2026, kyorohiro
 * Compile as C, then link with the C++ implementation. No device or assets. */
#include <tetorica/sid.h>
#include <assert.h>
#include <stdio.h>
#ifdef TETORICA_TEST_SID8580
#include <tetorica/sid8580.h>
#endif

/* Checks must run in Release builds too. */
#undef assert
#define assert(expression) do { if (!(expression)) { \
    fprintf(stderr, "C ABI check failed: %s\n", #expression); return 1; } } while (0)

int main(void) {
    tetorica_sid_instance *sid = sid_create(48000, 985248);
    unsigned nonzero = 0, i;
    const float *pcm;
    assert(sid != NULL);
    assert(sid_write(sid, 24, 15));
    assert(sid_write(sid, 4, 0x18));
    assert(sid_write(sid, 0, 0x44));
    assert(sid_write(sid, 1, 0x1d));
    assert(sid_write(sid, 5, 0x20));
    assert(sid_write(sid, 6, 0xa3));
    assert(sid_write(sid, 4, 0x11));
    assert(sid_cycles(sid) == 7);
    assert(sid_render(sid, 2048));
    pcm = sid_output(sid);
    assert(pcm != NULL);
    for (i = 0; i < 2048; ++i) if (pcm[i] != 0) ++nonzero;
    assert(nonzero > 50 && sid_envelope(sid, 0) > 0);
    sid_reset(sid);
    assert(sid_cycles(sid) == 0 && sid_render(sid, 128));
    for (i = 0; i < 128; ++i) assert(sid_output(sid)[i] == 0);
    sid_destroy(sid);
    sid_destroy(NULL);
#ifdef TETORICA_TEST_SID8580
    {
        uint32_t handle = sid8p_create(48000, 1);
        const int16_t *output;
        uint32_t frames;
        nonzero = 0;
        assert(handle != 0);
        assert(sid8p_write(handle, 24, 15));
        assert(sid8p_write(handle, 4, 0x18));
        assert(sid8p_write(handle, 0, 0x44));
        assert(sid8p_write(handle, 1, 0x1d));
        assert(sid8p_write(handle, 5, 0x20));
        assert(sid8p_write(handle, 6, 0xa3));
        assert(sid8p_write(handle, 4, 0x11));
        frames = sid8p_run(handle, 42000);
        assert(frames > 0 && frames <= TETORICA_SID8580_OUTPUT_CAPACITY);
        output = sid8p_output(handle);
        assert(output != NULL);
        for (i = 0; i < frames; ++i) if (output[i] != 0) ++nonzero;
        assert(nonzero > 50 && sid8p_cycles_lo(handle) == 42000);
        assert(sid8p_reset(handle));
        assert(sid8p_cycles_lo(handle) == 0 && sid8p_output_frames(handle) == 0);
        assert(sid8p_destroy(handle));
    }
#endif
    puts("SID public C header, lifecycle and nonzero PCM passed.");
    return 0;
}
