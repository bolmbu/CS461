import test from 'node:test';
import assert from 'node:assert/strict';
import {profileData,interviewData,analysisData,reportData,apiError} from '../lib/data.mjs';
import {POST,GET} from '../app/backend/[...path]/route.js';

test('legacy incomplete profiles never expose undefined facts to map',()=>{
 for(const summary of [{},{facts:null},{facts:'bad'},{facts:[null,{text:'ok',quote:'source'}]}]) {
  const result=profileData({source:null,summary});
  assert.ok(Array.isArray(result.summary.facts));
  assert.equal(result.source.text,'');
 }
 assert.equal(profileData(null),null);
});
test('old interview/report/analysis arrays and numeric fields have safe defaults',()=>{
 assert.deepEqual(interviewData({turns:null}).turns,[]);
 assert.deepEqual(reportData({dimensions:'bad'}).dimensions,[]);
 assert.equal(analysisData({similarity:null}).similarity.toFixed(3),'0.000');
 assert.deepEqual(analysisData({skills:null}).skills,[]);
});
test('validation details become readable strings',()=>{
 assert.match(apiError({detail:[{loc:['body','reference'],msg:'Field required'}]},422),/reference/);
 assert.equal(apiError({detail:'กรอกข้อมูล'},400),'กรอกข้อมูล');
});
test('bridge preserves binary upload, status, query and TTS metric',async()=>{
 const original=globalThis.fetch;
 try{
  globalThis.fetch=async(url,options)=>{
   assert.equal(new URL(url).pathname,'/voice/transcribe');
   assert.equal(new URL(url).search,'?x=1');
   assert.equal(Buffer.from(options.body).toString(),'audio');
   assert.equal(options.headers['Content-Type'],'audio/webm');
   return new Response('wav',{status:200,headers:{'content-type':'audio/wav','x-tts-ms':'12'}});
  };
  const r=await POST(new Request('http://localhost/backend/voice/transcribe?x=1',{method:'POST',body:'audio',headers:{'content-type':'audio/webm'}}),{params:Promise.resolve({path:['voice','transcribe']})});
  assert.equal(await r.text(),'wav');assert.equal(r.headers.get('x-tts-ms'),'12');
 }finally{globalThis.fetch=original;}
});
test('bridge reports backend connection failure as JSON',async()=>{
 const original=globalThis.fetch;
 try{globalThis.fetch=async()=>{throw new Error('ECONNREFUSED')};
 const r=await GET(new Request('http://localhost/backend/health'),{params:Promise.resolve({path:['health']})});
 assert.equal(r.status,502);assert.match((await r.json()).detail,/Backend/);
 }finally{globalThis.fetch=original;}
});
test('bridge deadline returns 504 JSON and clears wait',async()=>{
 const original=globalThis.fetch, previous=process.env.BACKEND_TIMEOUT_MS;
 try{process.env.BACKEND_TIMEOUT_MS='5';
 globalThis.fetch=async(url,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('timeout'))));
 const r=await GET(new Request('http://localhost/backend/health'),{params:Promise.resolve({path:['health']})});
 assert.equal(r.status,504);assert.match((await r.json()).detail,/เกินเวลา/);
 }finally{globalThis.fetch=original;if(previous===undefined)delete process.env.BACKEND_TIMEOUT_MS;else process.env.BACKEND_TIMEOUT_MS=previous;}
});
test('bridge does not allow encoded path traversal',async()=>{
 const r=await GET(new Request('http://localhost/backend/x'),{params:Promise.resolve({path:['..','health']})});assert.equal(r.status,400);
});
