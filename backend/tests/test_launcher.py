import importlib.util
from pathlib import Path
import socket
import pytest

spec=importlib.util.spec_from_file_location('coop_launcher',Path(__file__).resolve().parents[2]/'launch.py')
launcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_busy_port_is_not_reused():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
        # Avoid an ephemeral port so close to the upper limit that range probing overflows.
        if port>65480:
            pytest.skip('Ephemeral port too close to upper limit')
        assert launcher.choose_port(port)!=port


def test_user_environment_is_preserved(tmp_path):
    source=tmp_path/'example';target=tmp_path/'.env'
    source.write_text('EXAMPLE=1');target.write_text('PIPER_MODEL=user-setting')
    launcher.copy_if_missing(source,target)
    assert target.read_text()=='PIPER_MODEL=user-setting'
    target.unlink()
    launcher.copy_if_missing(source,target)
    assert target.read_text()=='EXAMPLE=1'


def test_early_server_failure_does_not_wait_for_timeout():
    class Exited:
        def poll(self): return 1
    with pytest.raises(RuntimeError,match='stopped'):
        launcher.wait_ready('http://127.0.0.1:1',[Exited()],seconds=1)


def test_readiness_with_real_http_server():
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"openapi":"3.1.0"}')
        def log_message(self,*args):
            pass
    with ThreadingHTTPServer(('127.0.0.1',0),Handler) as server:
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        try:
            launcher.wait_ready(f'http://127.0.0.1:{server.server_port}/openapi.json',[],seconds=3)
            assert seen==['/openapi.json']
        finally:
            server.shutdown();worker.join(timeout=2)


def test_windows_npm_uses_node_without_cmd_shell(tmp_path,monkeypatch):
    node=tmp_path/'Program Files'/'nodejs'/'node.exe'
    npm=node.parent/'npm.cmd'
    cli=node.parent/'node_modules/npm/bin/npm-cli.js'
    cli.parent.mkdir(parents=True);cli.write_text('// npm entry point')
    monkeypatch.setattr(launcher.subprocess,'check_output',lambda *a,**k:'v22.10.0\n')
    resolved,command,version=launcher.node_tools(which=lambda name:str(node if name=='node' else npm),platform_name='nt')
    assert command==[str(node),str(cli)] and resolved==str(node)
    assert all('cmd.exe' not in x for x in command)


def test_copied_venv_with_foreign_prefix_is_rejected(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(launcher,'ROOT',tmp_path)
    executable=tmp_path/'backend/.venv/bin/python'
    executable.parent.mkdir(parents=True);executable.write_text('placeholder')
    monkeypatch.setattr(launcher.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='{"prefix":"/old/computer/backend/.venv","version":[3,12]}'))
    assert launcher.inspect_venv(executable) is None


def test_rotate_generated_preserves_original_files(tmp_path):
    env=tmp_path/'.venv';env.mkdir();(env/'sample').write_text('keep')
    runtime=tmp_path/'runtime';runtime.mkdir();(runtime/'data').write_text('student data')
    launcher.rotate_generated(env)
    assert not env.exists()
    assert next(tmp_path.glob('.venv.backup-*')).joinpath('sample').read_text()=='keep'
    assert (runtime/'data').read_text()=='student data'


def test_doctor_does_not_install_or_write_files(tmp_path,monkeypatch):
    monkeypatch.setattr(launcher,'ROOT',tmp_path)
    monkeypatch.setattr(launcher,'node_tools',lambda:('node',['npm'],'v22.0.0'))
    monkeypatch.setattr(launcher,'choose_port',lambda p:p)
    monkeypatch.setattr(launcher,'command',lambda *a,**k:pytest.fail('Doctor must not install anything'))
    launcher.doctor()
    assert list(tmp_path.iterdir())==[]


def test_missing_node_produces_install_hint():
    with pytest.raises(RuntimeError,match='nodejs.org'):
        launcher.node_tools(which=lambda name:None)
