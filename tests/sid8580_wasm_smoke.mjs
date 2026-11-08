// SPDX-License-Identifier: BSD-3-Clause
// Real standalone Rust ABI; optional Native parity uses only this SDK's fixture.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {createHash} from 'node:crypto';

const options={};
for(let i=2;i<process.argv.length;i++){
  const name=process.argv[i];assert(['--wasm-dir','--native-fixture','--out'].includes(name),'Unknown argument '+name);
  assert(!options[name]&&process.argv[i+1]&&!process.argv[i+1].startsWith('--'),'Expected one value for '+name);
  options[name]=path.resolve(process.argv[++i]);
}
const wasm=await readFile(path.join(options['--wasm-dir']??'dist/wasm','sid8580_wasm.wasm'));
const compiled=await WebAssembly.compile(wasm);assert.deepEqual(WebAssembly.Module.imports(compiled),[],'No CPU or host imports');
const {exports:a}=await WebAssembly.instantiate(compiled,{}),CLOCK=985248,CAPACITY=4096;
const functions=['create','destroy','reset','stop','write','read','run','output','output_frames','error','bus_value','bus_remaining',
  'rate','model','stopped','set_8580_calibration','calibration','set_8580_cutoff_calibration','cutoff_calibration','written',
  'cycles_lo','cycles_hi','frames_lo','frames_hi'];
for(const name of functions)assert.equal(typeof a['sid8p_'+name],'function','Export '+name);
assert(a.memory instanceof WebAssembly.Memory);
const checks=[],handles=new Set();let comparedRawFrames=0,comparedHostFrames=0,maxHostDifference=0;
const cycles=h=>(a.sid8p_cycles_hi(h)>>>0)*2**32+(a.sid8p_cycles_lo(h)>>>0);
const frames=h=>(a.sid8p_frames_hi(h)>>>0)*2**32+(a.sid8p_frames_lo(h)>>>0);
const create=(rate=48000)=>{const h=a.sid8p_create(rate,1)>>>0;assert(h);handles.add(h);return h;};
const destroy=h=>{assert.equal(a.sid8p_destroy(h),1);handles.delete(h);};
const batch=(h,count)=>{const n=a.sid8p_run(h,count)>>>0;assert(n<=CAPACITY);assert.equal(n,a.sid8p_output_frames(h));return Int16Array.from(new Int16Array(a.memory.buffer,a.sid8p_output(h)>>>0,n));};
const run=(h,count,parts=[30000])=>{const pcm=[];for(let at=0,i=0;at<count;){const n=Math.min(parts[i++%parts.length],count-at);pcm.push(...batch(h,n));at+=n;}return Int16Array.from(pcm);};
const configure=(h,seed=0)=>{
  for(let voice=0;voice<3;voice++){
    const base=voice*7,f=1700+voice*2300+seed*73;
    for(const [reg,value]of [[base,f&255],[base+1,f>>8],[base+2,0x34],[base+3,8],[base+5,3],[base+6,0xb4],[base+4,[0x11,0x41,0x21][voice]]])assert.equal(a.sid8p_write(h,reg,value),1);
  }
  for(const [reg,value]of [[21,3],[22,170],[23,0x97],[24,0x1f]])assert.equal(a.sid8p_write(h,reg,value),1);
};
const native=(mode,rate,commands)=>{
  const result=spawnSync(options['--native-fixture'],['--'+mode,String(rate)],{input:commands.map(c=>c.join(' ')).join('\n')+'\n',maxBuffer:8*1024*1024});
  if(result.error)throw result.error;assert.equal(result.status,0,result.stderr.toString());
  return {pcm:result.stdout,state:JSON.parse(result.stderr.toString())};
};

// Independent JS host policy makes the raw-vs-host boundary explicit. Native
// C++ uses the public helper; both consume the same actual Rust DSP. No source
// imports, npm packages, C64 machine or browser are needed for this checker.
class Host {
  constructor(rate){this.rate=rate;this.h=create(rate);this.phase=0;this.queue=[];this.x=0;this.y=0;this.pole=Math.exp(-2*Math.PI*12/rate);}
  run(n){const pcm=batch(this.h,n);this.phase=(this.phase+n*this.rate)%CLOCK;for(const sample of pcm){const input=sample/32768,output=input-this.x+this.pole*this.y;this.x=input;this.y=output;this.queue.push(Math.fround(output));}}
  write(reg,value){assert(this.queue.length<CAPACITY);this.run(1);assert.equal(a.sid8p_write(this.h,reg,value),1);}
  read(reg){assert(this.queue.length<CAPACITY);this.run(1);return a.sid8p_read(this.h,reg);}
  reset(){assert.equal(a.sid8p_reset(this.h),1);this.phase=0;this.queue=[];this.x=this.y=0;}
  render(count){const output=[];while(output.length<count){if(!this.queue.length)this.run(Math.ceil((Math.min(CAPACITY,count-output.length)*CLOCK-this.phase)/this.rate));const n=Math.min(this.queue.length,count-output.length);output.push(...this.queue.splice(0,n));}return output;}
}

try{
  assert.equal(a.sid8p_create(7999,1),0);assert.equal(a.sid8p_create(96001,1),0);assert.equal(a.sid8p_create(48000,2),0);
  assert.equal(a.sid8p_output(0),0);assert.equal(a.sid8p_read(0,0),256);assert.equal(a.sid8p_run(0,1)>>>0,0xffffffff);assert.equal(a.sid8p_error(0),1);
  const h=create();assert.equal(a.sid8p_calibration(h),0);assert.equal(a.sid8p_cutoff_calibration(h),0);
  assert.equal(a.sid8p_model(h),1);assert.equal(a.sid8p_rate(h),48000);
  assert.equal(a.sid8p_write(h,0,0x9a),1);assert.equal(a.sid8p_read(h,0),0x9a);assert.equal(cycles(h),0);
  assert.equal(a.sid8p_read(h,25),256);assert.equal(a.sid8p_error(h),5);assert.equal(cycles(h),0);
  assert.equal(a.sid8p_write(h,32,0),0);assert.equal(a.sid8p_written(h,0),0x9a);assert.equal(cycles(h),0);
  assert.equal(a.sid8p_set_8580_calibration(h,2),0);assert.equal(a.sid8p_calibration(h),0);
  configure(h);assert(run(h,100003).some(n=>Math.abs(n)>100));
  const before=cycles(h),beforeFrames=frames(h);assert.equal(a.sid8p_run(h,0xffffffff)>>>0,0xffffffff);assert.equal(a.sid8p_error(h),3);
  assert.equal(cycles(h),before);assert.equal(frames(h),beforeFrames);assert.equal(a.sid8p_output_frames(h),0);
  assert.equal(a.sid8p_set_8580_calibration(h,1),1);assert.equal(a.sid8p_set_8580_cutoff_calibration(h,1),1);
  assert.equal(a.sid8p_stop(h),1);assert.equal(a.sid8p_stopped(h),1);assert.equal(a.sid8p_run(h,3011),0);
  assert.equal(cycles(h),before);assert.equal(frames(h),beforeFrames);assert.equal(a.sid8p_written(h,4),0);
  assert.equal(a.sid8p_reset(h),1);assert.equal(cycles(h),0);assert.equal(frames(h),0);assert.equal(a.sid8p_stopped(h),0);
  assert.equal(a.sid8p_calibration(h),1);assert.equal(a.sid8p_cutoff_calibration(h),1);destroy(h);
  const replacement=create();assert.notEqual(replacement,h);assert.equal(a.sid8p_write(h,24,15),0);assert.equal(a.sid8p_written(replacement,24),0);destroy(replacement);
  for(let i=0;i<16;i++)create();assert.equal(a.sid8p_create(48000,1),0);for(const handle of [...handles])destroy(handle);
  checks.push('exports-pointer-offset-invalid-inputs-profiles-Stop-Reset-generation-and-16-instance-limit');

  for(const rate of [8000,44100,48000,96000]){
    const a1=create(rate),a2=create(rate);configure(a1);configure(a2);
    assert.deepEqual(run(a1,100003),run(a2,100003,[1,7,193,509,30000]));assert.equal(cycles(a1),cycles(a2));assert.equal(frames(a1),frames(a2));destroy(a1);destroy(a2);
  }
  const b=create(),br=create(),other=create();configure(b,4);configure(br,4);configure(other,2);
  for(let i=0;i<8;i++){run(other,991+i);assert.deepEqual(run(b,3011+i),run(br,3011+i));if(i===3)a.sid8p_reset(other);}
  destroy(other);assert.deepEqual(run(b,30001),run(br,30001));destroy(b);destroy(br);
  checks.push('exact-batch-partitioning-four-rates-independent-handle-lifetimes');

  if(options['--native-fixture']){
    const self=spawnSync(options['--native-fixture'],['--self-test'],{encoding:'utf8'});assert.equal(self.status,0,self.stderr);assert.equal(JSON.parse(self.stdout).status,'pass');
    for(const rate of [44100,48000,96000]){
      const script=[['w',24,15],['w',0,0x42],['w',1,0x1d],['w',2,0x34],['w',3,8],['w',5,3],['w',6,0xb4],['w',14,0x21],['w',15,9],['w',18,0x10]];
      for(let mask=0;mask<16;mask++)script.push(['w',4,mask*16|1],['w',21,mask&7],['w',22,80+mask*9],['w',23,(mask%16)*16|1],['w',24,((mask%7)+1)*16|15],['c',20003+mask]);
      script.push(['w',4,0x17],['r',27],['c',30001],['r',28],['stop'],['c',91],['reset'],['w',24,15],['w',4,0x21],['c',3011]);
      const handle=create(rate),pcm=[],reads=[];
      for(const [op,x,y]of script){if(op==='w')assert.equal(a.sid8p_write(handle,x,y),1);else if(op==='r')reads.push(a.sid8p_read(handle,x));else if(op==='c')pcm.push(...run(handle,x));else if(op==='reset')a.sid8p_reset(handle);else a.sid8p_stop(handle);}
      const expected=native('raw',rate,script),actual=Buffer.alloc(pcm.length*2);pcm.forEach((value,i)=>actual.writeInt16LE(value,i*2));
      assert.deepEqual(actual,expected.pcm,'Native/WASM exact raw PCM at '+rate);assert.deepEqual(expected.state,{cycles:cycles(handle),frames:frames(handle),reads});comparedRawFrames+=pcm.length;destroy(handle);

      const hostScript=script.filter(c=>c[0]!=='stop').map(c=>c[0]==='c'?['g',Math.max(1,Math.floor(c[1]*rate/CLOCK))]:c),host=new Host(rate),floating=[],hostReads=[];
      for(const [op,x,y]of hostScript){if(op==='w')host.write(x,y);else if(op==='r')hostReads.push(host.read(x));else if(op==='g')floating.push(...host.render(x));else host.reset();}
      const nativeHost=native('host',rate,hostScript);assert.equal(nativeHost.pcm.length,floating.length*4);
      for(let i=0;i<floating.length;i++){const error=Math.abs(floating[i]-nativeHost.pcm.readFloatLE(i*4));maxHostDifference=Math.max(maxHostDifference,error);assert(error<=1e-7,'Native/Web-policy host float tolerance');}
      assert.deepEqual(nativeHost.state,{cycles:cycles(host.h),frames:frames(host.h),reads:hostReads});comparedHostFrames+=floating.length;destroy(host.h);
    }
    checks.push('Native-WASM-all-16-wave-masks-filter-Sync-Ring-bus-and-optional-host-queue-DC-parity');
  }
}finally{for(const h of [...handles])destroy(h);}
const report={passed:true,instrument:'sid8580',format:'standalone-wasm',cpuFree:true,profilesDefaultOff:true,wasmSha256:createHash('sha256').update(wasm).digest('hex'),checks,comparedRawFrames,comparedHostFrames,maxHostDifference};
if(options['--out'])await writeFile(options['--out'],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
