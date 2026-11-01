"""Portable local launcher: python launch.py. No activation, .bat, or cloud API."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler
import webbrowser

ROOT = Path(__file__).resolve().parent
BASE_MODULES = ['fastapi','uvicorn','sklearn','pypdf','docx','requests','bs4','multipart','dotenv','ddgs']
AI_GROUPS = {'stt': ('requirements-stt.txt',['faster_whisper']),
             'semantic': ('requirements-semantic.txt',['sentence_transformers','chromadb']),
             'tts': ('requirements-tts.txt',['piper']),
             'research': ('requirements-research.txt',['ddgs'])}


def say(message):
    print(message, flush=True)


def copy_if_missing(source, target):
    if not target.exists():
        shutil.copyfile(source, target)


def choose_port(preferred):
    if not 1 <= preferred <= 65535:
        raise RuntimeError('Port must be between 1 and 65535.')
    for port in range(preferred, min(preferred+50, 65536)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f'No free local port near {preferred}. Close unused app windows and retry.')


def fingerprint(*paths):
    h=hashlib.sha256()
    for path in paths:
        h.update(path.read_bytes())
    return h.hexdigest()


def command(args, cwd=None):
    args=[str(x) for x in args]
    say('\n> '+subprocess.list2cmdline(args))
    try:
        subprocess.run(args, cwd=cwd or ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f'Command failed (exit {exc.returncode}). Check the first error above. If download failed, check internet/proxy/disk space and rerun python launch.py.') from exc


def node_tools(which=shutil.which, platform_name=None):
    node, npm=which('node'), which('npm')
    if not node or not npm:
        raise RuntimeError('Node.js/npm not found. Install Node.js 22+ from https://nodejs.org/ and restart VS Code.')
    version=subprocess.check_output([node,'--version'], text=True).strip()
    try:
        major=int(version.lstrip('v').split('.')[0])
    except ValueError as exc:
        raise RuntimeError('Cannot read Node.js version. Reinstall Node.js 22+ and restart VS Code.') from exc
    if major<22:
        raise RuntimeError(f'Found Node.js {version}; this project requires Node.js 22+. Restart VS Code after updating.')
    # Invoke the real npm JS file through node on Windows: no npm.cmd quoting or shell policy dependency.
    if (platform_name or os.name)=='nt':
        candidates=[Path(npm).parent/'node_modules/npm/bin/npm-cli.js',
                    Path(node).parent/'node_modules/npm/bin/npm-cli.js',
                    Path(npm).resolve().parent/'node_modules/npm/bin/npm-cli.js']
        cli=next((p for p in candidates if p.is_file()), None)
        if cli is None:
            raise RuntimeError('Cannot find npm-cli.js. Repair/reinstall the official Node.js installation including npm.')
        npm_command=[node,str(cli)]
    else:
        npm_command=[npm]
    return node, npm_command, version


def venv_python():
    return ROOT/'backend/.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')


def inspect_venv(python):
    if not python.is_file():
        return None
    try:
        result=subprocess.run([str(python),'-c','import sys,json; print(json.dumps({"prefix":sys.prefix,"version":list(sys.version_info[:2])}))'],
                              capture_output=True,text=True,timeout=15)
        if result.returncode:
            return None
        info=json.loads(result.stdout)
        if info['version'] not in ([3,11],[3,12]):
            return None
        if Path(info['prefix']).resolve() != (ROOT/'backend/.venv').resolve():
            return None
        return info
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return None


def rotate_generated(path):
    # Keep the old generated environment for recovery. Never touch runtime or student data.
    if path.exists():
        backup=path.with_name(path.name+'.backup-'+str(time.time_ns()))
        path.rename(backup)
        say(f'Kept previous generated environment: {backup.name}')


def probe_modules(python, modules, import_modules=False):
    code=('import importlib;[importlib.import_module(x) for x in '+repr(modules)+']') if import_modules else ('import importlib.util,sys;sys.exit(0 if all(importlib.util.find_spec(x) is not None for x in '+repr(modules)+') else 1)')
    try:
        return subprocess.run([str(python),'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20).returncode==0
    except (OSError,subprocess.TimeoutExpired):
        return False


def setup(repair=False):
    if not (3,11)<=sys.version_info[:2]<=(3,12):
        raise RuntimeError('Use Python 3.11 or 3.12. On Windows try: py -3.12 launch.py. On macOS/Linux: python3.12 launch.py.')
    node,npm,node_version=node_tools()
    say('[1/4] Checking Python, Node.js and project paths ...')
    backend,frontend=ROOT/'backend',ROOT/'frontend'
    required=[backend/'requirements.txt',backend/'requirements-tested.txt',frontend/'package-lock.json']
    if any(not p.is_file() for p in required):
        raise RuntimeError('Project files are missing. Extract the complete ZIP, then run launch.py from that extracted project.')
    stamp_path=backend/'.bootstrap.json'
    try:
        stamp=json.loads(stamp_path.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        stamp={}
    if repair:
        rotate_generated(backend/'.venv')
        stamp={}
    python=venv_python()
    if inspect_venv(python) is None or (stamp.get('location') and stamp['location']!=str(ROOT.resolve())):
        rotate_generated(backend/'.venv')
        say('Creating a fresh environment for this computer ...')
        command([sys.executable,'-m','venv',backend/'.venv'])
        stamp={}
    if stamp.get('python_requirements') and not probe_modules(python,BASE_MODULES,import_modules=True):
        say('Existing baseline packages cannot import. Rebuilding generated environment ...')
        rotate_generated(backend/'.venv')
        command([sys.executable,'-m','venv',backend/'.venv'])
        stamp={}
    req_hash=fingerprint(backend/'requirements.txt',backend/'requirements-tested.txt')
    if stamp.get('python_requirements')!=req_hash or not probe_modules(python,BASE_MODULES,import_modules=True):
        say('[2/4] Installing baseline Python packages. First run needs internet ...')
        command([python,'-m','pip','install','--disable-pip-version-check','-r',backend/'requirements.txt'])
        if not probe_modules(python,BASE_MODULES,import_modules=True):
            raise RuntimeError('Baseline packages installed but import failed. Run python launch.py --repair and keep the pip error output.')
        stamp['python_requirements']=req_hash
        stamp_path.write_text(json.dumps(stamp),encoding='utf-8')
    else:
        say('[2/4] Python packages ready.')
    lock_hash=fingerprint(frontend/'package-lock.json')+':'+node_version
    next_cli=frontend/'node_modules/next/dist/bin/next'
    # Include the canonical checkout path: dependencies/caches copied from another path must be reinstalled.
    location=str(ROOT.resolve())
    if repair or stamp.get('npm_lock')!=lock_hash or stamp.get('location')!=location or not next_cli.is_file():
        say('[3/4] Installing web packages for this computer ...')
        command(npm+['ci','--no-audit','--no-fund'],cwd=frontend)
        stamp.update(npm_lock=lock_hash,location=location)
        stamp_path.write_text(json.dumps(stamp),encoding='utf-8')
        # Next build artifacts are generated and can embed the previous absolute path.
        if (frontend/'.next').exists():
            rotate_generated(frontend/'.next')
    else:
        say('[3/4] Web packages ready.')
    copy_if_missing(backend/'.env.example',backend/'.env')
    copy_if_missing(frontend/'.env.example',frontend/'.env.local')
    say('[4/4] Baseline ready. AI/voice model installation is separate; use --doctor to inspect it.')
    return str(python),node


def wait_ready(url,processes,seconds=180,request_timeout=10):
    deadline=time.monotonic()+seconds
    opener=build_opener(ProxyHandler({}))  # localhost must not go through corporate HTTP proxy settings.
    while time.monotonic()<deadline:
        for process in processes:
            code=process.poll()
            if code is not None:
                raise RuntimeError(f'A server stopped before it was ready (exit {code}). Read the error above.')
        try:
            with opener.open(url,timeout=request_timeout) as response:
                if response.status==200:
                    return
        except OSError:
            pass
        time.sleep(.4)
    raise RuntimeError(f'Startup timed out at {url}. Keep the full server error and rerun python launch.py --repair if dependencies are incomplete.')


def stop(process):
    if process.poll() is not None:
        return
    try:
        if os.name=='nt':
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid,signal.SIGTERM)
        process.wait(timeout=6)
    except (OSError,subprocess.TimeoutExpired):
        if process.poll() is None:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            else:
                try:
                    os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                say('A child process did not stop. Close only this project server window manually.')


def doctor():
    say('CoopReady portable diagnostics (does not install packages or download models)')
    say(f'OS: {platform.system()} {platform.machine()} | Python: {platform.python_version()}')
    say(f'Python supported: {(3,11)<=sys.version_info[:2]<=(3,12)}')
    try:
        _,_,version=node_tools()
        say('Node.js: '+version)
    except (RuntimeError,OSError) as exc:
        say('Node.js: '+str(exc))
    python=venv_python()
    say('Project Python environment: '+('ready' if inspect_venv(python) else 'not ready; run python launch.py'))
    for name,(_,modules) in AI_GROUPS.items():
        say(f'{name} packages: '+('installed (models not verified)' if probe_modules(python,modules) else 'missing; run python launch.py --install-ai '+name))
    say('Ollama command: '+('found' if shutil.which('ollama') else 'not found; install from https://ollama.com/download for local LLM'))
    for port in (8001,3000):
        say(f'Preferred port {port}: '+('available' if choose_port(port)==port else 'busy; launcher will select another free port'))
    say('Piper voice and model downloads need separate verification. Nothing here proves AI inference or real audio passed.')


def install_ai(python,groups):
    selected=list(AI_GROUPS) if 'all' in groups else groups
    for name in dict.fromkeys(selected):
        filename,modules=AI_GROUPS[name]
        command([python,'-m','pip','install','--disable-pip-version-check','-r',ROOT/'backend'/filename])
        if not probe_modules(Path(python),modules):
            raise RuntimeError(f'{name} installed incompletely. Check the pip output above.')
    say('Selected AI packages installed. Model weights/voice files are not downloaded by this command.')


def prepare_models(python,groups):
    # Explicit opt-in; downloads may be large and are never part of normal startup.
    for group in dict.fromkeys(groups):
        if group=='llm':
            ollama=shutil.which('ollama')
            if not ollama:
                raise RuntimeError('Install and open Ollama from https://ollama.com/download before --prepare-models llm.')
            command([ollama,'pull','qwen3:4b'])
        elif group=='stt':
            command([python,'-c',"from dotenv import load_dotenv;load_dotenv('.env');import os;from faster_whisper import WhisperModel;WhisperModel(os.getenv('WHISPER_MODEL','small'),device=os.getenv('WHISPER_DEVICE','cpu'),compute_type=os.getenv('WHISPER_COMPUTE_TYPE','int8'));print('Whisper loaded; microphone test still required')"],cwd=ROOT/'backend')
        elif group=='semantic':
            command([python,'-c',"from dotenv import load_dotenv;load_dotenv('.env');import os;from sentence_transformers import SentenceTransformer;m=SentenceTransformer(os.getenv('EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'));print(m.encode(['test']).shape)"],cwd=ROOT/'backend')
    say('Requested model preparation finished. Piper voice must be selected and configured separately.')


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    parser=argparse.ArgumentParser(description='Open CoopReady from VS Code Terminal: python launch.py')
    parser.add_argument('--doctor',action='store_true',help='Inspect requirements without installing anything')
    parser.add_argument('--setup-only',action='store_true')
    parser.add_argument('--repair',action='store_true',help='Recreate generated Python environment and reinstall npm dependencies; preserve .env and runtime data')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--install-ai',nargs='+',choices=[*AI_GROUPS,'all'])
    parser.add_argument('--prepare-models',nargs='+',choices=['llm','stt','semantic'])
    args=parser.parse_args(argv)
    processes=[]
    try:
        if args.doctor:
            doctor()
            return 0
        python,node=setup(repair=args.repair)
        if args.install_ai:
            install_ai(python,args.install_ai)
        if args.prepare_models:
            prepare_models(python,args.prepare_models)
        if args.setup_only or args.install_ai or args.prepare_models:
            return 0
        backend_port,frontend_port=choose_port(8001),choose_port(3000)
        env=dict(os.environ,BACKEND_URL=f'http://127.0.0.1:{backend_port}',FRONTEND_ORIGIN=f'http://127.0.0.1:{frontend_port}',NEXT_TELEMETRY_DISABLED='1')
        options={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
        say(f'\nStarting API (not website): http://127.0.0.1:{backend_port}/docs')
        processes.append(subprocess.Popen([python,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(backend_port),'--env-file','.env'],cwd=ROOT/'backend',env=env,**options))
        wait_ready(f'http://127.0.0.1:{backend_port}/openapi.json',processes)
        say(f'Starting website: http://127.0.0.1:{frontend_port}')
        cli=ROOT/'frontend/node_modules/next/dist/bin/next'
        processes.append(subprocess.Popen([node,str(cli),'dev','--hostname','127.0.0.1','--port',str(frontend_port)],cwd=ROOT/'frontend',env=env,**options))
        wait_ready(f'http://127.0.0.1:{frontend_port}',processes)
        say(f'\nREADY: http://127.0.0.1:{frontend_port}\nKeep this Terminal open. Ctrl+C stops this app.\n')
        if not args.no_browser:
            try:
                webbrowser.open(f'http://127.0.0.1:{frontend_port}')
            except webbrowser.Error:
                say('Open the READY URL manually in your browser.')
        while all(p.poll() is None for p in processes):
            time.sleep(.5)
        raise RuntimeError('A server stopped. Keep its error output, then rerun python launch.py.')
    except KeyboardInterrupt:
        say('\nStopping CoopReady ...')
        return 0
    except (OSError,RuntimeError,subprocess.CalledProcessError,ValueError) as exc:
        say(f'\nERROR: {exc}\nDiagnostics: python launch.py --doctor\nRepair generated dependencies: python launch.py --repair')
        return 1
    finally:
        for process in reversed(processes):
            stop(process)


if __name__=='__main__':
    sys.exit(main())
