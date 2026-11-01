from contextlib import asynccontextmanager
from datetime import date
from functools import wraps
import re
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import time
from typing import Literal
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from pypdf import PdfReader
from docx import Document
from . import baseline, integrations as ai
from .store import Store
from .schemas import CompanySummary, Question, FAQAnswer, Report

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
configured_data = Path(os.getenv('DATA_DIR', 'runtime')).expanduser()
DIRECTORY = (configured_data if configured_data.is_absolute() else ROOT/configured_data).resolve()
store = Store(DIRECTORY)


@asynccontextmanager
async def lifespan(app):
    store.purge(int(os.getenv('RETENTION_DAYS', '7')))
    yield


app = FastAPI(title='CoopReady AI Local v1.4.1', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000'), 'http://127.0.0.1:3000'],
                   allow_credentials=False, allow_methods=['GET','POST','DELETE'], allow_headers=['Content-Type'])


@app.exception_handler(ai.IntegrationError)
async def integration_error(request: Request, exc: ai.IntegrationError):
    return JSONResponse(status_code=503, content={'detail': str(exc), 'fallback_used': False})


@app.get('/ready')
def ready():
    return {'status': 'ready', 'application': 'CoopReady AI', 'version': '1.4.1', 'local_only': True}


@app.get('/health')
def health():
    voice = ai.piper_model_path()
    versions = {}
    for name in ['fastapi','scikit-learn','pypdf','python-docx','sentence-transformers','chromadb','faster-whisper','piper-tts','ddgs']:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {'status': 'ok', 'baseline_ready': True, 'ollama': ai.ollama_status(),
            'packages': versions, 'piper_files_present': bool(voice and Path(voice).is_file() and Path(str(voice)+'.json').is_file()),
            'piper_language': os.getenv('PIPER_LANGUAGE','en'), 'whisper_model': os.getenv('WHISPER_MODEL','small'),
            'embedding_model': os.getenv('EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'),
            'python': platform.python_version(), 'system': platform.platform(), 'cpu': platform.processor(),
            'retention_days': int(os.getenv('RETENTION_DAYS','7')),
            'note': 'Package/file presence is not proof of model execution. Load/test models on the demo machine.'}


def need_session(sid):
    store.purge(int(os.getenv('RETENTION_DAYS', '7')))
    s = store.get(sid, 'session')
    if not s:
        raise HTTPException(404, 'ไม่พบ session หรือข้อมูลหมดอายุ')
    return s


def session_write(fn):
    @wraps(fn)
    def wrapped(sid, *args, **kwargs):
        with store.session_lock(sid):
            return fn(sid, *args, **kwargs)
    return wrapped


class TextInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class SessionInput(TextInput):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    resume: str = Field(min_length=1, max_length=60000)
    role_brief: str = Field(min_length=1, max_length=20000)
    consent: bool = False
    role_provenance: Literal['User-provided Role Brief','General Role Guidance'] = 'User-provided Role Brief'
    language: Literal['th','en'] = 'th'


@app.post('/sessions')
def create_session(body: SessionInput):
    if not body.consent:
        raise HTTPException(400, 'ต้องยืนยันสิทธิ์และยินยอมเก็บข้อมูลในเครื่องก่อน')
    store.purge(int(os.getenv('RETENTION_DAYS','7')))
    data = body.model_dump()
    data.update({'created': time.time(), 'profile': None, 'analysis': None, 'interview': None})
    sid = store.put('session', data)
    return {'id': sid, 'session': data}


@app.get('/sessions')
def list_sessions():
    store.purge(int(os.getenv('RETENTION_DAYS','7')))
    return [{'id': x['id'], 'company': x['data']['company'], 'role': x['data']['role'], 'updated': x['updated'],
             'has_report': bool((x['data'].get('interview') or {}).get('report'))} for x in store.list('session')]


@app.get('/sessions/{sid}')
def get_session(sid: str):
    return need_session(sid)


@app.delete('/sessions/{sid}')
@session_write
def delete_session(sid: str):
    need_session(sid)
    store.delete(sid)
    return {'deleted': True}


@app.post('/resume/parse')
async def parse_resume(file: UploadFile = File(...)):
    data = await file.read(10_000_001)
    if len(data) > 10_000_000:
        raise HTTPException(413, 'ไฟล์ใหญ่เกิน 10 MB')
    ext = Path(file.filename or '').suffix.lower()
    try:
        if ext == '.pdf':
            pdf = PdfReader(io.BytesIO(data))
            if len(pdf.pages) > 50:
                raise HTTPException(400, 'รับ PDF ไม่เกิน 50 หน้า')
            text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
        elif ext == '.docx':
            # Bound DOCX expansion before decompression.
            import zipfile
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if sum(x.file_size for x in z.infolist()) > 30_000_000:
                    raise HTTPException(400, 'DOCX มีข้อมูลคลายไฟล์ใหญ่เกินขอบเขต')
            doc = Document(io.BytesIO(data))
            text = '\n'.join([p.text for p in doc.paragraphs]+[' '.join(c.text for c in r.cells) for t in doc.tables for r in t.rows])
        elif ext == '.txt':
            text = data.decode('utf-8-sig')
        else:
            raise HTTPException(400, 'รับ PDF ที่มีข้อความ, DOCX หรือ UTF-8 TXT เท่านั้น')
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, 'อ่านไฟล์ไม่ได้ อาจเข้ารหัสหรือรูปแบบผิด') from exc
    if not text.strip():
        raise HTTPException(422, 'ไม่พบข้อความ อาจเป็น PDF สแกน: MVP ไม่ทำ OCR กรุณาใช้ PDF ข้อความหรือ DOCX')
    return {'text': text[:60000], 'characters': len(text), 'truncated': len(text)>60000, 'saved_file': False,
            'warning': 'ตรวจลำดับและความถูกต้องของข้อความ โดยเฉพาะ PDF หลายคอลัมน์ ก่อนสร้าง session'}


class ProfileInput(TextInput):
    url: str = Field(default='', max_length=2000)
    source_text: str = Field(default='', max_length=12000)
    human_verified: bool = False
    summarize_with_llm: bool = False


@app.post('/sessions/{sid}/profile')
@session_write
def profile(sid: str, body: ProfileInput):
    s = need_session(sid)
    if body.source_text.strip():
        source = {'url': body.url, 'title': 'User-provided company source', 'text': body.source_text.strip()}
    elif body.url:
        source = ai.fetch_public_text(body.url)
    else:
        raise HTTPException(400, 'กรอก URL ทางการ หรือวางข้อความอ้างอิง')
    result = {'company': s['company'], 'source': source, 'human_verified': body.human_verified,
              'source_label': 'Company source — human checked' if body.human_verified else 'Company source — unverified',
              'role_label': s.get('role_provenance','User-provided Role Brief'), 'role_brief': s['role_brief'],
              'summary': None, 'llm_ms': None, 'missing_fields': 'ยังไม่ยืนยันธุรกิจ ผลิตภัณฑ์ หรือทักษะเฉพาะบริษัทจากข้อความนี้โดยอัตโนมัติ'}
    if not source.get('text', '').strip():
        raise HTTPException(422, 'แหล่งข้อมูลไม่มีข้อความ กรุณาวางข้อความเกี่ยวกับบริษัท')
    result['summary_warning'] = ''
    if body.summarize_with_llm:
        # The model selects source IDs; exact quotes come from the source, never model memory.
        passages = [p.strip() for p in re.split(r'(?<=[.!?。])\s+|\n+', source['text']) if p.strip()]
        passages = [part for p in passages for part in baseline.chunks(p, size=700, overlap=0)]
        passages = passages[:40]
        try:
            out, ms = ai.chat_json(
                'Summarize company business/products only. Each fact must be directly supported by ONE supplied passage. '
                'Select its integer source_id; do not create quotes. Do not infer hiring or role requirements. '
                'Use facts=[] when no relevant company evidence exists. Return facts and missing_fields.',
                {'company': s['company'], 'passages': [{'source_id': i, 'text': p} for i,p in enumerate(passages)]},
                CompanySummary)
            validated = CompanySummary.model_validate(out)
            if any(f.source_id >= len(passages) for f in validated.facts):
                raise ValueError('Unknown source ID')
            result['summary'] = {'facts': [{'text': f.text, 'quote': passages[f.source_id], 'source_id': f.source_id}
                                          for f in validated.facts], 'missing_fields': validated.missing_fields}
            result['llm_ms'] = ms
            if not validated.facts:
                result['summary_warning'] = 'โมเดลไม่พบข้อมูลบริษัทที่สรุปได้ บันทึกข้อความต้นฉบับไว้แล้ว'
        except (ai.IntegrationError, ValidationError, ValueError) as exc:
            result['summary_warning'] = ('บันทึกข้อความบริษัทแล้ว แต่ยังไม่มีสรุป AI ที่ตรวจผ่าน: '
                                         + (str(exc) if isinstance(exc, ai.IntegrationError) else 'รูปแบบสรุปหรือรหัสหลักฐานไม่ถูกต้อง'))
    if not body.source_text:
        # Reading a URL is not evidence that the user has reviewed the fetched text yet.
        result['human_verified'] = False
        result['source_label'] = 'Company source — unverified'
    s['profile'] = result
    store.put('session', s, sid)
    return result


@app.post('/sessions/{sid}/company-search')
def company_search(sid: str):
    return {'candidates': ai.search_company(need_session(sid)['company']),
            'warning': 'เป็นผู้สมัครแหล่งข้อมูล ต้องเลือกและตรวจเอง ไม่รับรองว่าเป็นเว็บทางการหรือข้อเท็จจริง'}


class ModeInput(TextInput):
    mode: Literal['baseline','proposed'] = 'baseline'


@app.post('/sessions/{sid}/analyze')
@session_write
def analyze(sid: str, body: ModeInput):
    s = need_session(sid)
    start = time.perf_counter()
    result = baseline.analyze_resume(s['resume'], s['role_brief'])
    if body.mode == 'proposed':
        result['semantic_candidates'] = ai.semantic_evidence(s['resume'], [r['skill'] for r in result['skills']])
        threshold = float(os.getenv('SEMANTIC_THRESHOLD','.55'))
        for row, candidate in zip(result['skills'], result['semantic_candidates']):
            row['lexical_status'] = row['status']
            row['semantic_similarity'] = candidate['semantic_similarity']
            row['evidence_type'] = 'keyword' if row['status']=='Matched' else 'none'
            if row['status']=='Not Evidenced' and candidate['semantic_similarity'] >= threshold:
                row.update(status='Matched', evidence=candidate['candidate_evidence'], evidence_type='semantic_candidate',
                           advice='โมเดลเสนอหลักฐานเชิงความหมาย ต้องให้คนตรวจยืนยันว่าอธิบายทักษะนี้จริง')
        result['semantic_threshold'] = threshold
        result['method'] += ' + multilingual MiniLM evidence matching'
        result['limitations'].append('Semantic labels depend on an uncalibrated threshold; preserve lexical_status for comparison and validate all candidates')
    result.update({'mode': body.mode, 'elapsed_ms': round((time.perf_counter()-start)*1000,2)})
    s['analysis'] = result
    store.put('session', s, sid)
    return result


class FAQRow(TextInput):
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(min_length=1, max_length=6000)
    source: str = Field(min_length=1, max_length=1000)
    page: str = Field(default='', max_length=50)
    version: str = Field(default='', max_length=100)
    valid_until: date | None = None
    approved: bool = False
    demo: bool = False


class FAQImport(BaseModel):
    entries: list[FAQRow] = Field(min_length=1, max_length=1000)


@app.post('/faq/import')
def import_faq(body: FAQImport):
    ids = []
    for row in body.entries:
        ids.append(store.put('faq', row.model_dump(mode='json')))
    return {'imported': len(ids), 'ids': ids}


@app.get('/faq')
def faq_list():
    return store.list('faq')


@app.delete('/faq/{fid}')
def delete_faq(fid: str):
    if not store.get(fid,'faq'):
        raise HTTPException(404,'ไม่พบ FAQ')
    store.delete(fid)
    return {'deleted': True}


class FAQQuery(ModeInput):
    question: str = Field(min_length=1, max_length=2000)
    allow_demo: bool = False


@app.post('/faq/ask')
def faq_ask(body: FAQQuery):
    start = time.perf_counter()
    active = []
    for row in store.list('faq'):
        f = row['data']
        if not f.get('approved') and not (f.get('demo') and body.allow_demo):
            continue
        if f.get('valid_until') and date.fromisoformat(f['valid_until']) < date.today():
            continue
        active.append(dict(f, id=row['id']))
    llm_ms = 0
    if body.mode == 'baseline':
        ranked = baseline.rank(body.question, [f['question'] for f in active])
        matches = [{'faq': active[x['index']], 'score': x['score']} for x in ranked[:3] if x['score'] >= float(os.getenv('FAQ_THRESHOLD','.17'))]
    else:
        matches = [x for x in ai.retrieve_semantic(body.question, active, DIRECTORY) if x['score'] >= float(os.getenv('SEMANTIC_THRESHOLD','.55'))]
    answer, citations = 'ยังไม่พบข้อมูลยืนยันในเอกสารที่อนุมัติและยังมีผล กรุณาติดต่ออาจารย์ผู้ประสานงาน', []
    abstained = not matches
    if matches:
        if body.mode == 'baseline':
            answer, citations = matches[0]['faq']['answer'], [matches[0]['faq']]
        else:
            out, llm_ms = ai.chat_json('Answer academic questions only using supplied FAQ. If not supported, abstain. Return {"answer":"...","source_ids":["..."],"abstained":false}. Never invent requirements or dates.',
                                      {'question': body.question, 'sources': [x['faq'] for x in matches]}, FAQAnswer)
            selected = out.get('source_ids', [])
            valid = {x['faq']['id']: x['faq'] for x in matches}
            if out.get('abstained') is True:
                abstained = True
            elif not isinstance(selected,list) or not selected or any(not isinstance(x,str) or x not in valid for x in selected) or not isinstance(out.get('answer'),str):
                raise HTTPException(502, 'โมเดลตอบโดยไม่มีแหล่งอ้างอิงที่ตรวจผ่าน')
            else:
                answer, citations = out['answer'], [valid[x] for x in selected]
    result = {'question': body.question, 'answer': answer, 'abstained': abstained,
              'citations': citations, 'mode': body.mode, 'llm_ms': llm_ms,
              'elapsed_ms': round((time.perf_counter()-start)*1000,2),
              'demo_used': any(c.get('demo') for c in citations),
              'retrieved': [{'id': x['faq']['id'], 'similarity': x['score']} for x in matches]}
    store.put('faq_query', result)
    return result


class InterviewStart(ModeInput):
    pass


def generate_question(s, interview, latest_answer=None):
    base = baseline.question_bank(s['role'], s['language'])[interview['base_index']]
    if interview['mode'] == 'baseline':
        return base, 0, ''
    follow = interview['is_followup']
    out, ms = ai.chat_json('You are a cooperative education interview coach. Ask ONE concise question in the requested language. Ground it in resume, company source, role brief and latest answer. Do not invent company requirements or experience. If kind=follow_up, quote the exact latest answer fragment you build on. Return {"question":"...","evidence_quote":"..."}.',
                          {'language': s['language'], 'resume': s['resume'], 'role': s['role'], 'role_brief': s['role_brief'],
                           'company': s['company'], 'company_profile': s['profile'], 'kind': 'follow_up' if follow else 'main',
                           'topic': base, 'latest_answer': latest_answer, 'history': interview['turns']}, Question)
    question = out.get('question','')
    quote = out.get('evidence_quote','')
    if not isinstance(question,str) or not question.strip() or len(question)>2000:
        raise HTTPException(502,'โมเดลสร้างคำถามไม่ถูกต้อง')
    if follow and (not isinstance(quote,str) or not quote.strip() or quote not in (latest_answer or '')):
        raise HTTPException(502,'คำถามต่อไม่มีหลักฐานตรงจากคำตอบล่าสุด โปรดลองอีกครั้ง')
    return question.strip(), ms, quote if isinstance(quote,str) else ''


@app.post('/sessions/{sid}/interview/start')
@session_write
def interview_start(sid: str, body: InterviewStart):
    s = need_session(sid)
    interview = {'mode': body.mode, 'base_index': 0, 'is_followup': False, 'followups': 0, 'turns': [],
                 'started': time.time(), 'done': False, 'report': None}
    q, ms, quote = generate_question(s, interview)
    interview.update({'question': q, 'question_llm_ms': ms, 'evidence_quote': quote, 'question_id': str(uuid.uuid4())})
    s['interview'] = interview
    store.put('session', s, sid)
    return interview


class AnswerInput(TextInput):
    question_id: str | None = Field(default=None, max_length=100)
    answer: str = Field(min_length=1, max_length=10000)
    stt_ms: float = Field(default=0, ge=0)
    tts_ms: float = Field(default=0, ge=0)
    stt_engine: str = Field(default='typed', max_length=100)


@app.post('/sessions/{sid}/interview/answer')
@session_write
def interview_answer(sid: str, body: AnswerInput):
    s = need_session(sid); interview = s.get('interview')
    if not interview or interview['done']:
        raise HTTPException(409,'ไม่มีรอบสัมภาษณ์ที่กำลังทำ')
    if body.question_id is not None and body.question_id != interview.get('question_id'):
        raise HTTPException(409, 'คำถามเปลี่ยนแล้วหรือส่งคำตอบนี้ไปแล้ว กรุณาเปิด session อีกครั้ง')
    interview['turns'].append({'question': interview['question'], 'answer': body.answer, 'kind': 'follow_up' if interview['is_followup'] else 'main',
                               'base_question': interview['base_index']+1, 'evidence_quote': interview.get('evidence_quote',''),
                               'latency_ms': {'stt': body.stt_ms, 'llm': interview['question_llm_ms'], 'tts': body.tts_ms}, 'stt_engine': body.stt_engine})
    if interview['mode']=='proposed' and not interview['is_followup'] and interview['base_index']<2:
        interview['is_followup'] = True
        interview['followups'] += 1
    else:
        interview['is_followup'] = False
        interview['base_index'] += 1
    if interview['base_index']>=5:
        interview['done'] = True
        interview['finished'] = time.time()
        interview['question'] = ''
    else:
        q, ms, quote = generate_question(s, interview, body.answer)
        interview.update({'question': q, 'question_llm_ms': ms, 'evidence_quote': quote, 'question_id': str(uuid.uuid4())})
    s['interview'] = interview
    store.put('session', s, sid)
    return interview


@app.post('/sessions/{sid}/interview/finish')
@session_write
def interview_finish(sid: str):
    s = need_session(sid); interview = s.get('interview')
    if not interview or not interview['turns']:
        raise HTTPException(409,'ต้องตอบอย่างน้อย 1 ข้อ')
    interview['done'] = True
    interview.setdefault('finished', time.time())
    store.put('session', s, sid)
    return interview


@app.post('/sessions/{sid}/interview/report')
@session_write
def interview_report(sid: str):
    s = need_session(sid); interview = s.get('interview')
    if not interview or not interview['done'] or not interview['turns']:
        raise HTTPException(409,'จบรอบสัมภาษณ์ก่อนสร้างรายงาน')
    if interview.get('report'):
        return interview['report']
    dimensions = ['ความตรงคำถาม','หลักฐานจากประสบการณ์','เหตุผลและขั้นตอน','ความชัดเจนในการสื่อสาร','การเชื่อมกับบทบาทงาน']
    if interview['mode']=='baseline':
        report = {'method':'baseline review checklist; not AI scoring', 'dimensions': [
            {'dimension': d, 'score': None, 'evidence': '', 'feedback': 'ให้ผู้ประเมินตรวจคำตอบตามมิตินี้ ยังไม่มีการให้คะแนนอัตโนมัติ'} for d in dimensions],
                  'action_items': ['เติมสถานการณ์ หน้าที่ สิ่งที่ลงมือทำ และผลลัพธ์จากประสบการณ์จริง'], 'llm_ms':0}
    else:
        out, ms = ai.chat_json('Evaluate practice answers, not employability or personality. Return {"dimensions":[{"dimension":"...","score":1,"evidence":"exact quote from an answer","feedback":"...","example_improvement":"improve structure without inventing experience"}],"action_items":["..."]}. Exactly five dimensions, each score 1-5. Use the requested dimensions in order. Every evidence must be an exact answer quote. Do not infer confidence/personality from voice.',
                              {'dimensions':dimensions,'role':s['role'],'language':s['language'],'answers':interview['turns']}, Report)
        try:
            out = Report.model_validate(out).model_dump()
        except ValidationError as exc:
            raise HTTPException(502, 'รายงานมีรูปแบบไม่ครบ กรุณาสร้างรายงานอีกครั้ง') from exc
        rows = out.get('dimensions', [])
        answers = [t['answer'] for t in interview['turns']]
        if not isinstance(rows,list) or len(rows)!=5 or any(not isinstance(r,dict) or r.get('dimension')!=dimensions[i] or type(r.get('score')) is not int or not 1<=r['score']<=5 or not isinstance(r.get('evidence'),str) or not r['evidence'].strip() or not any(r['evidence'] in a for a in answers) for i,r in enumerate(rows)):
            raise HTTPException(502,'รายงานโมเดลมีคะแนนหรือหลักฐานที่ตรวจไม่ผ่าน ยังไม่บันทึกรายงาน')
        report = dict(out, method='Qwen3 practice feedback; requires human review', llm_ms=ms)
    report.update({'duration_seconds':round(interview.get('finished', time.time())-interview['started'],2), 'turns': interview['turns'],
                   'mode':interview['mode'], 'followups':interview['followups'],
                   'voice_turns':sum(t['stt_engine']=='faster-whisper' and t['latency_ms']['tts']>0 for t in interview['turns']),
                   'warning':'ยังต้องประเมิน Grounding, Follow-up Relevance และ Rubric Agreement กับผู้ตรวจจริง; ไม่ใช้ตัดสินรับเข้าทำงาน'})
    interview['report'] = report
    store.put('session', s, sid)
    return report


@app.post('/voice/transcribe')
async def voice_transcribe(file: UploadFile = File(...), language: Literal['th','en'] = Form('th')):
    data = await file.read(15_000_001)
    if not data or len(data)>15_000_000:
        raise HTTPException(413,'รับไฟล์เสียงที่ไม่ว่างไม่เกิน 15 MB')
    ext = Path(file.filename or '').suffix.lower()
    if ext not in ['.webm','.wav','.mp3','.ogg','.m4a','.mp4']:
        raise HTTPException(400,'ชนิดไฟล์เสียงไม่รองรับ')
    temp = DIRECTORY/(str(uuid.uuid4())+ext)
    try:
        temp.write_bytes(data)
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(ai.transcribe, temp, language)
    finally:
        temp.unlink(missing_ok=True)


@app.post('/sessions/{sid}/voice/question')
def voice_question(sid: str):
    s = need_session(sid); interview=s.get('interview')
    if not interview or interview['done']:
        raise HTTPException(409,'ไม่มีคำถามที่กำลังใช้')
    data, ms = ai.synthesize(interview['question'], s['language'])
    return Response(data, media_type='audio/wav', headers={'X-TTS-MS':str(ms), 'Access-Control-Expose-Headers':'X-TTS-MS', 'Cache-Control':'no-store'})


class SpeechMetric(TextInput):
    reference: str = Field(min_length=1, max_length=10000)
    hypothesis: str = Field(max_length=10000)


@app.post('/evaluate/speech')
def evaluate_speech(body: SpeechMetric):
    try:
        return baseline.speech_error(body.reference, body.hypothesis)
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc


class SkillEvaluation(BaseModel):
    truth: list[str] = Field(max_length=100)
    predicted: list[str] = Field(max_length=100)


@app.post('/evaluate/skills')
def evaluate_skills(body: SkillEvaluation):
    return baseline.label_metrics(set(body.truth), set(body.predicted))


@app.get('/export')
def export():
    return {'sessions':store.list('session'), 'faq_queries':store.list('faq_query'), 'faqs':store.list('faq'),
            'notice':'Contains locally stored personal data. Review before sharing. Metrics are not validated by this export.'}
