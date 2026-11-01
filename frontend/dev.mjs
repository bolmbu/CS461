// Small CLI adapter: local runs bind loopback; preview hosts may pass Vite-style flags.
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const incoming=process.argv.slice(2),args=[];
let hasHost=false;
for(let i=0;i<incoming.length;i++){
 const x=incoming[i];
 if(x==='--strictPort')continue;
 if(x==='--host'){args.push('--hostname');hasHost=true;continue;}
 if(x==='--hostname')hasHost=true;
 args.push(x);
}
if(!hasHost)args.push('--hostname','127.0.0.1');
const child=spawn(process.execPath,[require.resolve('next/dist/bin/next'),'dev',...args],{stdio:'inherit',env:{...process.env,NEXT_TELEMETRY_DISABLED:'1'}});
child.on('exit',code=>process.exit(code??1));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
