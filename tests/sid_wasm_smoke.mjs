// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2026, kyorohiro
// Raw standalone SID WASM, optional byte-exact Native/parent comparisons.
import assert from 'node:assert/strict';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import path from 'node:path';

const options = {'--wasm-dir': 'dist/wasm'};
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index], value = process.argv[index + 1];
  assert(['--wasm-dir', '--native-fixture', '--reference-wasm', '--out'].includes(key) && value,
    'Usage: node tests/sid_wasm_smoke.mjs --wasm-dir DIR [--native-fixture EXE] [--reference-wasm FILE] [--out JSON]');
  options[key] = value;
}
const capacity = 4096, frames = 8191, scenes = ['triangle', 'pulse', 'combined', 'sync-ring', 'filter', 'release'];
const checks = [], handles = new Set();
let renderedFrames = 0, nativeComparisons = 0, referenceComparisons = 0;
async function load(filename) {
  const bytes = await readFile(filename), module = new WebAssembly.Module(bytes);
  const accepted = new Set(['env.emscripten_notify_memory_growth', 'wasi_snapshot_preview1.proc_exit']);
  for (const entry of WebAssembly.Module.imports(module))
    assert(accepted.has(entry.module + '.' + entry.name) && entry.kind === 'function', 'Small standalone runtime imports only');
  const instance = new WebAssembly.Instance(module, {
    env: {emscripten_notify_memory_growth() {}},
    wasi_snapshot_preview1: {proc_exit(code) {throw new Error('Unexpected WASI exit: ' + code);}},
  });
  const api = instance.exports;
  if (api._initialize) api._initialize();
  for (const suffix of ['create', 'destroy', 'reset', 'write', 'read', 'output', 'render', 'cycles', 'envelope', 'phase'])
    assert.equal(typeof api['sid_' + suffix], 'function', 'Original sid_' + suffix + ' export');
  assert(api.memory instanceof WebAssembly.Memory, 'Raw WASM linear memory');
  return {api, sha256: createHash('sha256').update(bytes).digest('hex')};
}
const {api, sha256} = await load(path.join(path.resolve(options['--wasm-dir']), 'sid_wasm.wasm'));
const reference = options['--reference-wasm'] ? (await load(path.resolve(options['--reference-wasm']))).api : null;
function create(rate = 48000, clock = 985248) {
  const handle = api.sid_create(rate, clock); assert(handle > 0, 'Valid handle'); handles.add(handle); return handle;
}
function destroy(handle) { api.sid_destroy(handle); handles.delete(handle); }
function write(target, handle, reg, value) { assert.equal(target.sid_write(handle, reg, value), 1, 'Successful register write'); }
function configure(target, handle, scene) {
  write(target, handle, 24, 15);
  const frequencies = [0x1d44, 0x24e2, 0x2bf4], widths = [0x800, 0x400, 0xc00];
  for (let voice = 0; voice < 3; ++voice) {
    const base = voice * 7;
    for (const [reg, value] of [[4, 8], [0, frequencies[voice] & 255], [1, frequencies[voice] >> 8],
      [2, widths[voice] & 255], [3, widths[voice] >> 8], [5, 0x20 + voice * 0x11], [6, 0xa3 - voice * 0x0f]])
      write(target, handle, base + reg, value);
  }
  if (scene === 'filter') for (const [reg, value] of [[21, 5], [22, 90], [23, 0xa7], [24, 0x3f]])
    write(target, handle, reg, value);
  for (let voice = 0; voice < 3; ++voice) {
    let control = 0x11;
    if (scene === 'pulse') control = 0x41;
    if (scene === 'combined') control = [0x31, 0x51, 0x71][voice];
    if (scene === 'filter') control = [0x21, 0x41, 0x11][voice];
    if (scene === 'sync-ring') control = [0x17, 0, 0x10][voice];
    if (scene === 'release' && voice !== 0) control = 0;
    write(target, handle, voice * 7 + 4, control);
  }
}
function generate(target, handle, count) {
  assert(Number.isInteger(count) && count >= 0 && count <= capacity);
  assert.equal(target.sid_render(handle, count), 1);
  // Construct a fresh view: allocation may have grown/detached linear memory.
  const bytes = Buffer.from(new Uint8Array(target.memory.buffer, target.sid_output(handle), count * 4));
  for (let offset = 0; offset < bytes.length; offset += 4) assert(Number.isFinite(bytes.readFloatLE(offset)), 'Finite float32 PCM');
  renderedFrames += count;
  return bytes;
}
function state(target, handle) {
  return {cycles: target.sid_cycles(handle),
    envelope: Array.from({length: 3}, (_, voice) => target.sid_envelope(handle, voice)),
    phase: Array.from({length: 3}, (_, voice) => target.sid_phase(handle, voice))};
}
function renderScene(target, scene, rate, clock, chunk) {
  const handle = target.sid_create(rate, clock); assert(handle > 0);
  try {
    configure(target, handle, scene);
    const blocks = [];
    for (let at = 0; at < frames;) {
      if (scene === 'release' && at === 2048) write(target, handle, 4, 0x10);
      let count = Math.min(chunk, frames - at);
      if (scene === 'release' && at < 2048) count = Math.min(count, 2048 - at);
      blocks.push(generate(target, handle, count)); at += count;
    }
    return {pcm: Buffer.concat(blocks), ...state(target, handle)};
  } finally { target.sid_destroy(handle); }
}
function samePCM(actual, expected, label) {
  assert.equal(actual.length, expected.length, label + ' length');
  if (!actual.equals(expected)) {
    let offset = 0;
    while (offset < actual.length && actual[offset] === expected[offset]) ++offset;
    assert.fail(label + ': first differing float32 frame ' + Math.floor(offset / 4));
  }
}
function varying(pcm) {
  let low = Infinity, high = -Infinity;
  for (let at = 0; at < pcm.length; at += 4) { const value = pcm.readFloatLE(at); low = Math.min(low, value); high = Math.max(high, value); }
  return high - low > 0.001;
}
try {
  for (const rate of [0, 7999, 96001]) assert.equal(api.sid_create(rate, 985248), 0);
  for (const clock of [0, 899999, 1100001]) assert.equal(api.sid_create(48000, clock), 0);
  for (const [rate, clock] of [[8000, 900000], [96000, 1100000]]) destroy(create(rate, clock));
  api.sid_destroy(0); api.sid_reset(0);
  assert.equal(api.sid_write(0, 0, 0), 0); assert.equal(api.sid_read(0, 0), -1);
  assert.equal(api.sid_render(0, 1), 0); assert.equal(api.sid_output(0), 0);
  assert.equal(api.sid_cycles(0), 0); assert.equal(api.sid_phase(0, 0), 0); assert.equal(api.sid_envelope(0, 0), 0);
  const basic = create();
  assert.equal(api.sid_render(basic, 0), 1); assert.equal(api.sid_cycles(basic), 0);
  assert(generate(api, basic, 257).every(byte => byte === 0), 'Cold silence');
  api.sid_reset(basic); configure(api, basic, 'triangle');
  const beforePCM = generate(api, basic, capacity), beforeState = state(api, basic);
  assert(varying(beforePCM), 'Three physical oscillators audible');
  assert.equal(api.sid_write(basic, 32, 0), 0); assert.equal(api.sid_write(basic, 0, 256), 0);
  assert.equal(api.sid_read(basic, 32), -1); assert.equal(api.sid_render(basic, capacity + 1), 0);
  assert.deepEqual(state(api, basic), beforeState, 'Invalid operations do not clock');
  samePCM(Buffer.from(new Uint8Array(api.memory.buffer, api.sid_output(basic), capacity * 4)), beforePCM, 'Invalid render preserves buffer');
  assert.equal(api.sid_phase(basic, 3), 0); assert.equal(api.sid_envelope(basic, 3), 0);
  const time = api.sid_cycles(basic);
  assert(api.sid_read(basic, 28) >= 0); assert.equal(api.sid_cycles(basic), time + 1);
  write(api, basic, 24, 15); assert.equal(api.sid_cycles(basic), time + 2);
  api.sid_reset(basic); assert.equal(api.sid_cycles(basic), 0);
  assert(generate(api, basic, 257).every(byte => byte === 0), 'Reset clears chip/queue/DC history');
  destroy(basic);
  checks.push('standalone-exports-C-ABI-guards-and-clocked-register-accesses');

  for (let voice = 0; voice < 3; ++voice) {
    const handle = create();
    for (const [reg, value] of [[24, 15], [voice * 7 + 4, 0x18], [voice * 7, 0x44], [voice * 7 + 1, 0x1d],
      [voice * 7 + 5, 0x20], [voice * 7 + 6, 0xa3], [voice * 7 + 4, 0x11]]) write(api, handle, reg, value);
    assert(varying(generate(api, handle, 4096)), 'Physical CH' + (voice + 1) + ' audible'); destroy(handle);
  }
  const selectors = create();
  for (let mask = 1; mask < 16; ++mask) {
    api.sid_reset(selectors); configure(api, selectors, 'triangle'); write(api, selectors, 4, (mask << 4) | 1);
    generate(api, selectors, 129); // Noise combinations may physically lock; only finiteness is required.
  }
  api.sid_reset(selectors); write(api, selectors, 0, 0x44); write(api, selectors, 1, 0x1d);
  generate(api, selectors, 128); assert.notEqual(api.sid_phase(selectors, 0), 0, 'Waveform off leaves phase running');
  write(api, selectors, 4, 8); generate(api, selectors, 128); assert.equal(api.sid_phase(selectors, 0), 0, 'TEST holds phase');
  destroy(selectors); checks.push('three-voices-all-wave-selectors-wave-off-and-TEST');

  for (const scene of scenes) for (const rate of [8000, 44100, 48000, 96000]) for (const clock of [985248, 1022727]) {
    const whole = renderScene(api, scene, rate, clock, 4096), split = renderScene(api, scene, rate, clock, 113);
    const label = scene + '/' + rate + '/' + clock;
    samePCM(whole.pcm, split.pcm, 'Partition ' + label);
    assert.deepEqual({...whole, pcm: null}, {...split, pcm: null}, 'Partition observation continuity');
    if (options['--native-fixture']) {
      const result = spawnSync(path.resolve(options['--native-fixture']), ['--render', scene, String(rate), String(clock), '193'],
        {encoding: null, maxBuffer: 1024 * 1024});
      assert.ifError(result.error); assert.equal(result.status, 0, 'Native fixture: ' + (result.stderr?.toString() ?? ''));
      samePCM(whole.pcm, result.stdout, 'Native ' + label); ++nativeComparisons;
    }
    if (reference) {
      const parent = renderScene(reference, scene, rate, clock, 193);
      samePCM(whole.pcm, parent.pcm, 'Parent WASM ' + label);
      assert.deepEqual({...whole, pcm: null}, {...parent, pcm: null}, 'Parent observation continuity'); ++referenceComparisons;
    }
  }
  checks.push('exact-PCM-and-state-partition-invariance-six-original-scenes-four-rates-two-clocks');
  if (nativeComparisons) checks.push('byte-exact-Native-WASM-PCM');
  if (referenceComparisons) checks.push('byte-exact-original-parent-WASM-PCM-and-state');

  let a = create(); const ar = create(), b = create(44100, 1022727), br = create(44100, 1022727);
  for (const handle of [a, ar]) configure(api, handle, 'filter');
  for (const handle of [b, br]) configure(api, handle, 'sync-ring');
  for (let block = 0; block < 23; ++block) {
    const count = 17 + block * 13;
    for (const handle of [a, ar]) write(api, handle, 0, block * 7);
    samePCM(generate(api, a, count), generate(api, ar, count), 'Interleaved handle A');
    samePCM(generate(api, b, count + 3), generate(api, br, count + 3), 'Interleaved handle B');
  }
  api.sid_reset(a); destroy(a); a = create(96000, 1000000); configure(api, a, 'combined'); generate(api, a, 777);
  samePCM(generate(api, b, 4096), generate(api, br, 4096), 'Independent other-handle reset/destroy/recreate');
  for (const handle of [a, ar, b, br]) destroy(handle);
  checks.push('independent-interleaved-handles-and-lifetimes');

  const queue = create(); let writes = 0;
  while (api.sid_write(queue, 24, 15)) assert(++writes < 500000, 'Bounded queue fills');
  const fullTime = api.sid_cycles(queue);
  assert(writes > 4096); assert.equal(api.sid_write(queue, 0, 1), 0); assert.equal(api.sid_read(queue, 28), -1);
  assert.equal(api.sid_cycles(queue), fullTime, 'Full queue rejects without clocking');
  generate(api, queue, 4096); assert.equal(api.sid_cycles(queue), fullTime, 'Drain uses queued bus samples');
  assert.equal(api.sid_write(queue, 24, 0), 1, 'Retry after draining'); destroy(queue);
  checks.push('bounded-lossless-register-sample-queue-and-retry');

  const report = {passed: true, artifact: 'sid', format: 'standalone-wasm', sha256, renderedFrames,
    nativeComparisons, referenceComparisons, checks,
    outputPolicy: 'Original 6581 mono + 12 Hz host DC blocker; no normalization, device or machine'};
  if (options['--out']) {
    const filename = path.resolve(options['--out']); await mkdir(path.dirname(filename), {recursive: true});
    await writeFile(filename, JSON.stringify(report, null, 2) + '\n');
  }
  console.log(JSON.stringify(report));
} finally { for (const handle of handles) api.sid_destroy(handle); }
