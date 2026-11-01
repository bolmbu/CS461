import io
import pytest
from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfWriter
from app import main, baseline
from app.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'store', Store(tmp_path))
    monkeypatch.setattr(main.ai, 'ollama_status', lambda: {'reachable':False,'models':[],'configured':'qwen3:4b'})
    with TestClient(main.app) as c:
        yield c


def session(client):
    r = client.post('/sessions',json={'company':'Example (synthetic)','role':'Backend Intern','resume':'Built Python FastAPI REST API and GitHub project','role_brief':'Python, FastAPI, SQL, Git, REST API','consent':True,'language':'th'})
    assert r.status_code == 200
    return r.json()['id']


def test_consent_required(client):
    r=client.post('/sessions',json={'company':'Example','role':'Intern','resume':'Python','role_brief':'Python'})
    assert r.status_code == 400


def test_skill_evidence_and_persistence(client):
    sid=session(client)
    r=client.post(f'/sessions/{sid}/analyze',json={'mode':'baseline'})
    assert r.status_code == 200
    rows={x['skill']:x for x in r.json()['skills']}
    assert rows['SQL']['status']=='Not Evidenced'
    assert rows['Python']['evidence'] in client.get('/sessions/'+sid).json()['resume']
    assert rows['Git']['status']=='Matched'
    assert client.get('/sessions/'+sid).json()['analysis']['mode']=='baseline'


def test_no_short_keyword_substring_false_match():
    assert not baseline.contains('design assets', 'git')
    assert not baseline.contains('typewriters', 'ts')
    assert baseline.contains('GitHub project','github')


def test_docx_parser(client):
    d=Document();d.add_paragraph('Synthetic resume Python FastAPI');out=io.BytesIO();d.save(out)
    r=client.post('/resume/parse',files={'file':('resume.docx',out.getvalue(),'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
    assert r.status_code==200 and 'Python' in r.json()['text']
    assert r.json()['saved_file'] is False


def test_scanned_pdf_rejected(client):
    d=PdfWriter();d.add_blank_page(width=200,height=200);out=io.BytesIO();d.write(out)
    r=client.post('/resume/parse',files={'file':('scan.pdf',out.getvalue(),'application/pdf')})
    assert r.status_code==422 and 'OCR' in r.json()['detail']


def test_unknown_and_invalid_files(client):
    assert client.post('/resume/parse',files={'file':('x.exe',b'not a resume')}).status_code==400
    assert client.post('/resume/parse',files={'file':('bad.pdf',b'invalid')}).status_code==400


def test_faq_approval_expiry_and_no_answer(client):
    base={'question':'เอกสารที่ต้องเตรียม','answer':'SYNTHETIC-ANSWER','source':'Test source','page':'1','version':'test'}
    r=client.post('/faq/import',json={'entries':[dict(base,approved=False),dict(base,approved=True,valid_until='2001-01-01')]})
    assert r.status_code==200
    assert client.post('/faq/ask',json={'question':base['question']}).json()['abstained']
    client.post('/faq/import',json={'entries':[dict(base,approved=True)]})
    r=client.post('/faq/ask',json={'question':base['question']}).json()
    assert not r['abstained'] and r['answer']=='SYNTHETIC-ANSWER'
    assert r['citations'][0]['source']=='Test source'
    assert client.post('/faq/ask',json={'question':'galaxy telescope nebula'}).json()['abstained']


def test_demo_opt_in(client):
    client.post('/faq/import',json={'entries':[{'question':'demo documents','answer':'synthetic','source':'demo','demo':True}]})
    assert client.post('/faq/ask',json={'question':'demo documents'}).json()['abstained']
    r=client.post('/faq/ask',json={'question':'demo documents','allow_demo':True}).json()
    assert r['demo_used'] and not r['abstained']


def test_baseline_interview_completes_five_turns(client):
    sid=session(client)
    r=client.post(f'/sessions/{sid}/interview/start',json={'mode':'baseline'}).json()
    for i in range(5):
        r=client.post(f'/sessions/{sid}/interview/answer',json={'answer':f'Synthetic answer {i}'}).json()
    assert r['done'] and len(r['turns'])==5 and r['followups']==0
    report=client.post(f'/sessions/{sid}/interview/report',json={}).json()
    assert len(report['dimensions'])==5 and all(x['score'] is None for x in report['dimensions'])
    assert report['voice_turns']==0
    assert client.post(f'/sessions/{sid}/interview/answer',json={'answer':'extra'}).status_code==409


def test_proposed_integration_missing_never_silently_falls_back(client,monkeypatch):
    sid=session(client)
    def fail(*args): raise main.ai.IntegrationError('Not installed')
    monkeypatch.setattr(main.ai,'chat_json',fail)
    r=client.post(f'/sessions/{sid}/interview/start',json={'mode':'proposed'})
    assert r.status_code==503 and r.json()['fallback_used'] is False
    assert client.get('/sessions/'+sid).json()['interview'] is None


def test_proposed_seven_turns_with_mock_llm(client,monkeypatch):
    # Contract test only; this is not a run of Qwen3.
    def mocked(system,payload,*args):
        return {'question':'Mock contextual question','evidence_quote':(payload.get('latest_answer') or '') if payload.get('kind')=='follow_up' else ''}, 1.5
    monkeypatch.setattr(main.ai,'chat_json',mocked)
    sid=session(client)
    assert client.post(f'/sessions/{sid}/interview/start',json={'mode':'proposed'}).status_code==200
    for i in range(7):
        response=client.post(f'/sessions/{sid}/interview/answer',json={'answer':f'Mock answer {i}'})
        assert response.status_code==200
    data=response.json()
    assert data['done'] and data['followups']==2
    assert len([x for x in data['turns'] if x['kind']=='follow_up'])==2


def test_bad_followup_quote_does_not_commit_answer(client,monkeypatch):
    monkeypatch.setattr(main.ai,'chat_json',lambda *a: ({'question':'Mock Q','evidence_quote':'invented quote'},1))
    sid=session(client)
    client.post(f'/sessions/{sid}/interview/start',json={'mode':'proposed'})
    assert client.post(f'/sessions/{sid}/interview/answer',json={'answer':'actual answer'}).status_code==502
    assert client.get('/sessions/'+sid).json()['interview']['turns']==[]


def test_missing_piper_returns_actionable_error(client,monkeypatch):
    monkeypatch.setenv('PIPER_MODEL','')
    sid=session(client);client.post(f'/sessions/{sid}/interview/start',json={'mode':'baseline'})
    r=client.post(f'/sessions/{sid}/voice/question')
    assert r.status_code==503 and 'PIPER_MODEL' in r.json()['detail']


def test_profile_manual_verified_and_missing_source(client):
    sid=session(client)
    assert client.post(f'/sessions/{sid}/profile',json={}).status_code==400
    r=client.post(f'/sessions/{sid}/profile',json={'source_text':'Synthetic company develops tools','human_verified':True})
    assert r.status_code==200 and r.json()['human_verified']
    assert r.json()['role_label']=='User-provided Role Brief'


def test_delete_session_removes_resume(client):
    sid=session(client)
    assert client.delete('/sessions/'+sid).status_code==200
    assert client.get('/sessions/'+sid).status_code==404


def test_metrics_on_human_supplied_labels(client):
    r=client.post('/evaluate/skills',json={'truth':['Python','SQL'],'predicted':['Python','Git']}).json()
    assert r['precision']==.5 and r['recall']==.5 and r['f1']==.5
    r=client.post('/evaluate/speech',json={'reference':'hello world','hypothesis':'hello'}).json()
    assert r['wer_whitespace']==.5 and r['cer']==.5
    assert client.post('/evaluate/speech',json={'reference':' ','hypothesis':'hi'}).status_code==422


def test_private_url_rejected():
    with pytest.raises(main.ai.IntegrationError):
        main.ai.check_url('http://127.0.0.1')
    with pytest.raises(main.ai.IntegrationError):
        main.ai.check_url('https://127.0.0.1')


def test_retention_excludes_kb(tmp_path):
    st=Store(tmp_path);sid=st.put('session',{'resume':'delete'});fid=st.put('faq',{'answer':'keep'})
    with st.connect() as db:
        db.execute('UPDATE records SET updated=0')
    st.purge(7)
    assert st.get(sid,'session') is None and st.get(fid,'faq') is not None


def test_startup_probe_does_not_contact_ollama(client, monkeypatch):
    def must_not_call():
        raise AssertionError('The lightweight readiness request must not probe optional models')
    monkeypatch.setattr(main.ai, 'ollama_status', must_not_call)
    response = client.get('/openapi.json')
    assert response.status_code == 200
    assert response.json()['info']['title'] == 'CoopReady AI Local v1.4.1'


def test_ready_is_lightweight_and_has_app_identity(client,monkeypatch):
    monkeypatch.setattr(main.ai,'ollama_status',lambda:pytest.fail('Readiness must not call Ollama'))
    result=client.get('/ready')
    assert result.status_code==200 and result.json()['application']=='CoopReady AI'


@pytest.mark.parametrize('summary', [{}, {'facts': None}, {'facts': 'wrong'}, {'facts': [{'text':'x','quote':123}]}, {'facts': [{'text':'x','quote':'invented'}]}])
def test_profile_preserves_source_and_warns_on_malformed_summary(client, monkeypatch, summary):
    sid = session(client)
    monkeypatch.setattr(main.ai, 'chat_json', lambda *a: (summary, 1))
    r = client.post(f'/sessions/{sid}/profile', json={'source_text':'Company builds tools','summarize_with_llm':True})
    assert r.status_code == 200
    data = client.get('/sessions/'+sid).json()['profile']
    assert data['summary'] is None and data['summary_warning']
    assert data['source']['text'] == 'Company builds tools'


@pytest.mark.parametrize('content', [
    'Reasoning without opening tag</think>\n{"facts":[]}',
    '<think>Reasoning {not json}</think>\n```json\n{"facts":[]}\n```',
    '{"facts":[]}',
])
def test_model_json_accepts_final_object_only(content):
    assert main.ai.parse_model_json(content) == {'facts': []}


@pytest.mark.parametrize('content', ['<think>unfinished {"facts":[]}', 'Hello', '[1]', '{"facts":[]} trailing text'])
def test_model_json_rejects_unfinished_or_invalid_answer(content):
    with pytest.raises(ValueError):
        main.ai.parse_model_json(content)


def test_profile_assigns_source_quote_from_valid_id(client, monkeypatch):
    def model(system, payload, schema):
        assert payload['passages'][0]['source_id']==0
        assert schema.__name__=='CompanySummary'
        return {'facts':[{'text':'Builds tools','source_id':0}],'missing_fields':[]}, 3
    monkeypatch.setattr(main.ai,'chat_json',model)
    sid=session(client)
    r=client.post(f'/sessions/{sid}/profile',json={'source_text':'Company builds tools.','human_verified':True,'summarize_with_llm':True})
    assert r.status_code==200
    assert r.json()['summary']['facts'][0]['quote']=='Company builds tools.'
    assert not r.json()['summary_warning']


def test_profile_bad_source_id_saves_raw_with_warning(client,monkeypatch):
    monkeypatch.setattr(main.ai,'chat_json',lambda *a: ({'facts':[{'text':'x','source_id':99}],'missing_fields':[]},1))
    sid=session(client)
    r=client.post(f'/sessions/{sid}/profile',json={'source_text':'Only source','summarize_with_llm':True})
    assert r.status_code==200 and r.json()['summary'] is None
    assert r.json()['summary_warning'] and r.json()['source']['text']=='Only source'


def test_profile_connection_failure_keeps_raw_explicitly(client,monkeypatch):
    def fail(*a):raise main.ai.IntegrationError('Connection failed')
    monkeypatch.setattr(main.ai,'chat_json',fail)
    sid=session(client)
    r=client.post(f'/sessions/{sid}/profile',json={'source_text':'Company text','summarize_with_llm':True})
    assert r.status_code==200 and r.json()['summary'] is None
    assert 'Connection failed' in r.json()['summary_warning']


def test_url_source_needs_review_after_fetch(client,monkeypatch):
    monkeypatch.setattr(main.ai,'fetch_public_text',lambda *a: {'url':'https://example.com','title':'Example','text':'Company text'})
    sid=session(client)
    r=client.post(f'/sessions/{sid}/profile',json={'url':'https://example.com','human_verified':True})
    assert r.status_code==200 and r.json()['human_verified'] is False


def test_duplicate_answer_rejected_by_question_id(client):
    sid=session(client)
    q=client.post(f'/sessions/{sid}/interview/start',json={}).json()
    body={'answer':'First answer','question_id':q['question_id']}
    assert client.post(f'/sessions/{sid}/interview/answer',json=body).status_code==200
    assert client.post(f'/sessions/{sid}/interview/answer',json=body).status_code==409
    assert len(client.get('/sessions/'+sid).json()['interview']['turns'])==1


def test_simultaneous_duplicate_answers_commit_once(client):
    from concurrent.futures import ThreadPoolExecutor
    sid=session(client)
    q=client.post(f'/sessions/{sid}/interview/start',json={}).json()
    def answer(_):return client.post(f'/sessions/{sid}/interview/answer',json={'answer':'Answer','question_id':q['question_id']}).status_code
    with ThreadPoolExecutor(2) as pool:codes=list(pool.map(answer,range(2)))
    assert sorted(codes)==[200,409]


def test_finished_duration_does_not_grow_when_report_delayed(client,monkeypatch):
    sid=session(client)
    client.post(f'/sessions/{sid}/interview/start',json={})
    client.post(f'/sessions/{sid}/interview/answer',json={'answer':'Hello'})
    final=client.post(f'/sessions/{sid}/interview/finish').json()
    monkeypatch.setattr(main.time,'time',lambda:final['finished']+3600)
    report=client.post(f'/sessions/{sid}/interview/report').json()
    assert report['duration_seconds']<3600


def test_stt_temp_file_cleanup(client,monkeypatch,tmp_path):
    monkeypatch.setattr(main,'DIRECTORY',tmp_path)
    observed=[]
    def stt(path,lang):
        observed.append(path)
        assert path.read_bytes()==b'audio'
        return {'transcript':'hello','stt_ms':1,'engine':'faster-whisper','language':lang}
    monkeypatch.setattr(main.ai,'transcribe',stt)
    r=client.post('/voice/transcribe',files={'file':('x.webm',b'audio')},data={'language':'th'})
    assert r.status_code==200 and r.json()['transcript']=='hello'
    assert observed and not observed[0].exists()
    def fail(*a):raise main.ai.IntegrationError('No model')
    monkeypatch.setattr(main.ai,'transcribe',fail)
    assert client.post('/voice/transcribe',files={'file':('x.webm',b'audio')}).status_code==503
    assert not list(tmp_path.glob('*.webm'))


def test_llm_passes_schema_and_validates_actual_response(monkeypatch):
    seen=[]
    class Reply:
        def raise_for_status(self):pass
        def json(self):return {'done_reason':'stop','message':{'content':'Reasoning</think>{"question":"Hello?","evidence_quote":""}'}}
    def post(*a,**kw):seen.append(kw);return Reply()
    monkeypatch.setattr(main.ai.requests,'post',post)
    out,_=main.ai.chat_json('Question',{},main.Question)
    assert out['question']=='Hello?'
    assert seen[0]['json']['think'] is False
    assert seen[0]['json']['format']['type']=='object'
    assert set(seen[0]['json']['format']['required'])=={'question','evidence_quote'}


def test_literal_reasoning_delimiter_inside_json_is_preserved():
    for prefix in ['', 'thought</think>']:
        assert main.ai.parse_model_json(prefix+'{"text":"literal </think> marker"}')=={'text':'literal </think> marker'}


@pytest.mark.parametrize('kind',['timeout','connection','format','truncated'])
def test_llm_error_categories(monkeypatch,kind):
    class Reply:
        def raise_for_status(self):pass
        def json(self):return {'done_reason':'length' if kind=='truncated' else 'stop','message':{'content':'not json'}}
    def post(*a,**kw):
        if kind=='timeout':raise main.ai.requests.Timeout()
        if kind=='connection':raise main.ai.requests.ConnectionError()
        return Reply()
    monkeypatch.setattr(main.ai.requests,'post',post)
    with pytest.raises(main.ai.IntegrationError) as exc:main.ai.chat_json('test',{})
    assert ('เกินเวลา' if kind=='timeout' else 'เชื่อมต่อ' if kind=='connection' else 'JSON') in str(exc.value)


def test_bad_url_port_is_actionable_error():
    with pytest.raises(main.ai.IntegrationError):main.ai.check_url('https://example.com:invalid')


def test_ddgs_handles_new_url_field(monkeypatch):
    import ddgs
    class Fake:
        def __init__(self,**kwargs):assert kwargs['timeout']==12
        def text(self,*args,**kwargs):return [{'url':'https://example.com','title':'Example'}, {'href':'javascript:bad'}]
    monkeypatch.setattr(ddgs,'DDGS',Fake)
    assert main.ai.search_company('Example')==[{'title':'Example','url':'https://example.com','snippet':'','verified':False}]
