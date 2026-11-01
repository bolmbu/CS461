"""Run an honest synthetic smoke benchmark, not the final empirical evaluation."""
import json
import platform
from pathlib import Path
import time
from app.baseline import analyze_resume, label_metrics

root=Path(__file__).resolve().parents[1]
cases=json.loads((root/'data/resume_role_synthetic.json').read_text(encoding='utf-8'))
results=[];truth_all=set();pred_all=set()
for case in cases:
    start=time.perf_counter();out=analyze_resume(case['resume'],case['role_brief']);elapsed=(time.perf_counter()-start)*1000
    truth=set(case['matched_truth']);pred={x['skill'] for x in out['skills'] if x['status']=='Matched'}
    truth_all.update((case['id'],x) for x in truth);pred_all.update((case['id'],x) for x in pred)
    results.append({'id':case['id'],'truth':sorted(truth),'predicted':sorted(pred),'metrics':label_metrics(truth,pred),'elapsed_ms':round(elapsed,3)})
report={'dataset':'3 explicitly synthetic author-labeled examples; not student data or independent human review',
        'method':'TF-IDF cosine + keyword baseline','python':platform.python_version(),'platform':platform.platform(),
        'micro_metrics':label_metrics(truth_all,pred_all),'cases':results,
        'observed_limitation':'Thai transliteration ไพธอน is not in the keyword dictionary; baseline misses Python.',
        'not_tested':['Real student data','Proposed model accuracy','Real Qwen3','MiniLM/Chroma execution','Piper/faster-whisper audio','WER/CER on recorded audio','Human rubric agreement']}
(root/'docs/INITIAL_RESULTS_SYNTHETIC.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
