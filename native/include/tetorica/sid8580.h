/* SPDX-License-Identifier: BSD-3-Clause */
#ifndef TETORICA_SID8580_H
#define TETORICA_SID8580_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Existing CPU-free Rust batch ABI, unchanged from the browser endpoint.
 * Handles are generation-tagged integers, never pointers. At most 16 live
 * instances share a module/library registry. Creation/destruction allocate;
 * serialize all operations and copy output before mutation/destruction.
 * The registry uses a Mutex: this API is not a lock-free callback contract.
 * sid8p_create accepts rate 8000..96000 and model 0 (upstream 6581) / 1 (8580).
 * Use model 1 for this Preview instrument. Clock is fixed at PAL 985248 Hz.
 * Calibration profiles default Off. Reset/Stop retain explicit profile choices.
 * Writes/reads do NOT clock. run completes exact cycles, returning 0..4096
 * mono int16 samples or UINT32_MAX. No gain or extra host DC blocker is added.
 * Native output is a real const int16_t pointer; WASM uses a linear-memory
 * offset. It remains valid only while this handle exists and until the next
 * mutation. Copy output_frames samples, never the entire stale scratch area.
 * Stop clears chip/output/bus, preserves counters/phase and latches stopped;
 * further run returns zero and clocks nothing until Reset. Reset clears the
 * epoch/counters/phase. Invalid operations report errors without advancing time.
 * POTX/POTY reads are unsupported (256); OSC3/ENV3 are real hardware reads.
 */
enum {
    TETORICA_SID8580_CLOCK = 985248,
    TETORICA_SID8580_OUTPUT_CAPACITY = 4096,
    TETORICA_SID8580_MAX_INSTANCES = 16,
    TETORICA_SID8580_ERROR_NONE = 0,
    TETORICA_SID8580_ERROR_HANDLE = 1,
    TETORICA_SID8580_ERROR_ARGUMENT = 2,
    TETORICA_SID8580_ERROR_CAPACITY = 3,
    TETORICA_SID8580_ERROR_COUNTER = 4,
    TETORICA_SID8580_ERROR_UNSUPPORTED_READ = 5
};
uint32_t sid8p_create(uint32_t rate, uint32_t model);
uint32_t sid8p_destroy(uint32_t handle);
uint32_t sid8p_reset(uint32_t handle);
uint32_t sid8p_stop(uint32_t handle);
uint32_t sid8p_write(uint32_t handle, uint32_t reg, uint32_t value);
uint32_t sid8p_read(uint32_t handle, uint32_t reg);
uint32_t sid8p_run(uint32_t handle, uint32_t cycles);
const int16_t* sid8p_output(uint32_t handle);
uint32_t sid8p_output_frames(uint32_t handle);
uint32_t sid8p_error(uint32_t handle);
uint32_t sid8p_bus_value(uint32_t handle);
uint32_t sid8p_bus_remaining(uint32_t handle);
uint32_t sid8p_rate(uint32_t handle);
uint32_t sid8p_model(uint32_t handle);
uint32_t sid8p_stopped(uint32_t handle);
uint32_t sid8p_set_8580_calibration(uint32_t handle, uint32_t enabled);
uint32_t sid8p_calibration(uint32_t handle);
uint32_t sid8p_set_8580_cutoff_calibration(uint32_t handle, uint32_t enabled);
uint32_t sid8p_cutoff_calibration(uint32_t handle);
uint32_t sid8p_written(uint32_t handle, uint32_t reg);
uint32_t sid8p_cycles_lo(uint32_t handle);
uint32_t sid8p_cycles_hi(uint32_t handle);
uint32_t sid8p_frames_lo(uint32_t handle);
uint32_t sid8p_frames_hi(uint32_t handle);

#ifdef __cplusplus
}
#endif
#endif
