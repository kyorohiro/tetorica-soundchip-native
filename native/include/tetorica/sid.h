// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2026, kyorohiro
#ifndef TETORICA_PUBLIC_SID_H
#define TETORICA_PUBLIC_SID_H

/* CPU-free 6581 approximation. One handle owns one mono SID, its 12 Hz host
 * DC blocker and a 4096-frame PCM queue. No player, device, CPU or ROM is used.
 * Serialize calls to a handle; independent handles can run on separate threads.
 * The implementation is C++17, but this header and ABI are usable from C.
 */
#ifdef __cplusplus
extern "C" {
#endif

typedef struct tetorica_sid_instance tetorica_sid_instance;

/* Rate 8000..96000 Hz, chip clock 900000..1100000 Hz. Invalid configuration or
 * allocation failure returns NULL. PAL commonly uses 985248 Hz. */
tetorica_sid_instance* sid_create(int sample_rate, int clock_hz);
void sid_destroy(tetorica_sid_instance* instance);
void sid_reset(tetorica_sid_instance* instance);

/* Register 0..31, byte 0..255. Every successful bus access advances one clock
 * and queues any generated sample. Write returns 1/0; read returns byte/-1.
 * A full PCM queue rejects an access without advancing time; render to drain.
 * Reads are hardware reads, not a mirror of write-only registers. */
int sid_write(tetorica_sid_instance* instance, unsigned reg, unsigned value);
int sid_read(tetorica_sid_instance* instance, unsigned reg);

/* Borrowed 4096-float mono output buffer, valid until destroy. Render accepts
 * 0..4096 frames and returns 1/0. Read only the requested frames on success.
 * Rejected requests preserve state and buffer. Reset clears chip/queue/time/DC
 * history, but does not clear this scratch buffer. No normalization is added. */
float* sid_output(tetorica_sid_instance* instance);
int sid_render(tetorica_sid_instance* instance, unsigned frames);

/* Observations do not advance time. Voice indices are 0..2. Cycles is double
 * for compatibility with the original WASM ABI (integer exact through 2^53). */
double sid_cycles(tetorica_sid_instance* instance);
unsigned sid_envelope(tetorica_sid_instance* instance, unsigned voice);
unsigned sid_phase(tetorica_sid_instance* instance, unsigned voice);

/* NULL: destroy/reset are no-ops; write/render return 0; read returns -1;
 * output returns NULL; observations return 0. Invalid voice returns 0.
 * Other invalid, freed, or foreign pointers are not valid handles. */
#ifdef __cplusplus
}
#endif
#endif
