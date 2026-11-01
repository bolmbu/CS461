"""Real HTTP workflow through Next -> FastAPI -> controlled Ollama stub, not model-quality evaluation.
Run from project root with the backend environment after npm run build in frontend.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx

ROOT=Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--slow-seconds',type=float,default=0)
    args=parser.parse_args()
    class OllamaStub(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def send(self,data):
            raw=json.dumps(data).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)
        def do_GET(self):self.send({'models':[{'name':'qwen3:4b'}]})
        def do_POST(self):
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            fields=data['format'].get('properties',{})
            payload=json.loads(data['messages'][1]['content'])
            if 'facts' in fields:
                time.sleep(args.slow_seconds)
                out={'facts':[{'text':'Synthetic tool company','source_id':0}],'missing_fields':[]}
            elif 'question' in fields:
                out={'question':'Synthetic contextual interview question?', 'evidence_quote':payload.get('latest_answer') or ''}
            elif 'dimensions' in fields:
                out={'dimensions':[{'dimension':d,'score':3,'evidence':payload['answers'][0]['answer'],'feedback':'Synthetic feedback','example_improvement':'Explain actual results'} for d in payload['dimensions']], 'action_items':['Use actual evidence']}
            else:out={'answer':'synthetic','source_ids':[],'abstained':True}
            self.send({'message':{'role':'assistant','content':'Synthetic reasoning</think>\n'+json.dumps(out)},'done':True,'done_reason':'stop'})
    server=ThreadingHTTPServer(('127.0.0.1',0),OllamaStub)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    processes=[]
    checks=[]
    with tempfile.TemporaryDirectory(prefix='coopready-smoke-') as temp:
        backend_port,web_port=free_port(),free_port()
        env=dict(os.environ,DATA_DIR=temp,OLLAMA_URL=f'http://127.0.0.1:{server.server_port}',OLLAMA_MODEL='qwen3:4b',BACKEND_URL=f'http://127.0.0.1:{backend_port}',NEXT_TELEMETRY_DISABLED='1')
        options={'start_new_session':True} if os.name!='nt' else {}
        logs=open(Path(temp)/'servers.log','w+')
        try:
            processes.append(subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(backend_port)],cwd=ROOT/'backend',env=env,stdout=logs,stderr=logs,**options))
            processes.append(subprocess.Popen([shutil.which('node'),str(ROOT/'frontend/node_modules/next/dist/bin/next'),'start','--hostname','127.0.0.1','--port',str(web_port)],cwd=ROOT/'frontend',env=env,stdout=logs,stderr=logs,**options))
            client=httpx.Client(base_url=f'http://127.0.0.1:{web_port}',timeout=200,trust_env=False)
            for _ in range(200):
                if any(p.poll() is not None for p in processes):raise RuntimeError('A server stopped')
                try:
                    if client.get('/backend/ready').status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(.1)
            else:raise RuntimeError('Servers not ready')
            def call(path,data=None):
                r=client.post('/backend'+path,json=data or {})
                assert r.status_code==200,(path,r.status_code,r.text[:300])
                return r.json()
            home=client.get('/')
            assert home.status_code==200
            assert 'รายการฝึกล่าสุด' in home.text and 'เริ่มเตรียมตัว' in home.text
            from bs4 import BeautifulSoup
            document=BeautifulSoup(home.text,'html.parser')
            settings=document.select_one('details.settings-panel')
            assert settings is not None and not settings.has_attr('open')
            checks.append('website + same-origin bridge')
            parsed=client.post('/backend/resume/parse',files={'file':('resume.txt',b'Python FastAPI REST API Git')})
            assert parsed.status_code==200
            s=call('/sessions',{'company':'Synthetic company','role':'Backend Intern','resume':parsed.json()['text'],'role_brief':'Python,SQL,FastAPI','consent':True})
            sid=s['id']
            checks.append('resume text upload + session persistence')
            p=call(f'/sessions/{sid}/profile',{'source_text':'Synthetic company builds tools.','summarize_with_llm':True})
            assert p['summary']['facts'][0]['quote']=='Synthetic company builds tools.'
            checks.append(f'company schema + reasoning parser + source evidence; stub delay {args.slow_seconds}s')
            a=call(f'/sessions/{sid}/analyze',{'mode':'baseline'})
            assert a['skills'] and a['mode']=='baseline'
            for mode,turns in [('baseline',5),('proposed',7)]:
                q=call(f'/sessions/{sid}/interview/start',{'mode':mode})
                for i in range(turns):
                    body={'answer':f'Synthetic real action {i}','question_id':q['question_id']}
                    q=call(f'/sessions/{sid}/interview/answer',body)
                    if i==0:
                        assert client.post(f'/backend/sessions/{sid}/interview/answer',json=body).status_code==409
                assert q['done'] and len(q['turns'])==turns
                report=call(f'/sessions/{sid}/interview/report')
                assert len(report['dimensions'])==5
                assert report['followups']==(2 if mode=='proposed' else 0)
                checks.append(f'{mode} interview {turns} turns + report + duplicate prevention')
            assert call('/faq/ask',{'question':'unknown'})['abstained']
            assert call('/evaluate/speech',{'reference':'hello world','hypothesis':'hello'})['wer_whitespace']==.5
            assert client.get('/backend/export').status_code==200
            assert client.delete('/backend/sessions/'+sid).status_code==200
            assert client.get('/backend/sessions/'+sid).status_code==404
            checks.append('FAQ abstention + CER/WER + export + delete')
            result={'status':'passed','checks':checks,'real_model':False,'real_microphone':False,'ui_version':'1.4.3','system':sys.platform}
            print(json.dumps(result,ensure_ascii=False,indent=2))
            (ROOT/'docs/SMOKE_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception:
            logs.flush();logs.seek(0);print(logs.read()[-5000:],file=sys.stderr);raise
        finally:
            client.close() if 'client' in locals() else None
            for p in reversed(processes):
                if p.poll() is None:
                    if os.name!='nt':os.killpg(p.pid,signal.SIGTERM)
                    else:p.terminate()
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired:p.kill()
            logs.close();server.shutdown();server.server_close()
    return 0

if __name__=='__main__':sys.exit(main())
