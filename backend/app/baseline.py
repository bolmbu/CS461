"""Transparent baselines. Thresholds are configurable, not validated accuracy."""
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = {
    'Python': ['python'], 'FastAPI': ['fastapi', 'fast api'],
    'SQL': ['sql', 'mysql', 'postgresql', 'sqlite'], 'Git': ['git', 'github', 'gitlab'],
    'REST API': ['rest api', 'restful'], 'JavaScript': ['javascript', 'js'],
    'TypeScript': ['typescript', 'ts'], 'React': ['react', 'reactjs'],
    'Next.js': ['next.js', 'nextjs'], 'Docker': ['docker'],
    'Excel': ['excel'], 'Power BI': ['power bi', 'powerbi'],
    'Figma': ['figma'], 'User Research': ['user research', 'วิจัยผู้ใช้'],
    'Machine Learning': ['machine learning', 'แมชชีนเลิร์นนิง'],
    'YOLO': ['yolo'], 'Teamwork': ['teamwork', 'ทำงานเป็นทีม'],
    'Communication': ['communication', 'การสื่อสาร'],
}


def normalize(text):
    return unicodedata.normalize('NFKC', str(text)).lower().strip()


def terms(text):
    text = normalize(text)
    result = re.findall(r'[a-z0-9]+(?:[.+#][a-z0-9]+)*', text)
    for run in re.findall(r'[ก-๙]+', text):
        result.extend(run[i:i+3] for i in range(max(0, len(run)-2)))
    return result


def contains(text, term):
    text, term = normalize(text), normalize(term)
    if re.search('[ก-๙]', term):
        return term in text
    return re.search(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text) is not None


def rank(query, documents):
    if not documents or not terms(query):
        return []
    vectorizer = TfidfVectorizer(analyzer=terms, lowercase=False)
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return []
    scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
    return sorted([{'index': i, 'score': float(s)} for i, s in enumerate(scores)], key=lambda x: -x['score'])


def chunks(text, size=220, overlap=40):
    # Character windows avoid losing Thai paragraphs or truncating long resumes silently.
    return [text[i:i+size] for i in range(0, len(text), size-overlap) if text[i:i+size].strip()]


def analyze_resume(resume, role_brief):
    required = [name for name, aliases in SKILLS.items() if any(contains(role_brief, a) for a in aliases)]
    rows = []
    for name in required:
        alias = next((a for a in SKILLS[name] if contains(resume, a)), None)
        evidence = ''
        if alias:
            evidence = next((line.strip() for line in re.split(r'[\n!?。]', resume) if contains(line, alias)), alias)
        rows.append({'skill': name, 'status': 'Matched' if alias else 'Not Evidenced', 'evidence': evidence[:1200],
                     'advice': 'เพิ่มบริบท หน้าที่ และผลลัพธ์ที่ทำจริง' if alias else 'หากเคยใช้จริง ให้เพิ่มหลักฐานในเรซูเม่ ไม่ควรอ้างทักษะที่ยังไม่เคยทำ'})
    ranked = rank(role_brief, [resume])
    return {'method': 'TF-IDF + cosine + keyword match', 'similarity': ranked[0]['score'] if ranked else 0,
            'skills': rows, 'dictionary_size': len(SKILLS),
            'limitations': ['Not Evidenced = ไม่พบหลักฐาน ไม่ได้ยืนยันว่าไม่มีทักษะ',
                           'ความคล้ายไม่ใช่ Accuracy หรือโอกาสได้งาน',
                           'จับคู่ได้เฉพาะทักษะในพจนานุกรม; ไม่พบรายการไม่ได้แปลว่าตรงทุกทักษะ']}


def question_bank(role, language='th'):
    if language == 'en':
        return [f'Introduce yourself and explain your interest in {role}.',
                'Describe a project and your own responsibilities.',
                'What difficult problem did you face, and how did you solve it?',
                'How did you handle disagreement while working with others?',
                'What do you want to learn during your placement, and how will you start?']
    return [f'ช่วยแนะนำตัว และเล่าว่าทำไมคุณสนใจตำแหน่ง {role}',
            'เล่าโครงงานที่เคยทำ และหน้าที่ที่คุณรับผิดชอบด้วยตนเอง',
            'ปัญหาที่ยากในโครงงานคืออะไร และคุณแก้ไขอย่างไร',
            'เมื่อทำงานร่วมกับผู้อื่นแล้วเห็นต่างกัน คุณรับมืออย่างไร',
            'คุณอยากพัฒนาอะไรระหว่างฝึกสหกิจ และจะเริ่มเรียนรู้อย่างไร']


def edit_distance(a, b):
    row = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        new = [i]
        for j, y in enumerate(b, 1):
            new.append(min(new[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = new
    return row[-1]


def speech_error(reference, hypothesis):
    # Thai CER removes whitespace consistently. WER is only whitespace tokenized.
    ref = re.sub(r'\s+', '', normalize(reference))
    hyp = re.sub(r'\s+', '', normalize(hypothesis))
    if not ref:
        raise ValueError('Reference must contain text')
    rw, hw = normalize(reference).split(), normalize(hypothesis).split()
    return {'cer': edit_distance(ref, hyp)/len(ref), 'wer_whitespace': edit_distance(rw, hw)/len(rw),
            'note': 'Thai: prefer CER; WER here uses whitespace, not Thai word segmentation. Error rates may exceed 1.'}


def label_metrics(truth, predicted):
    tp = len(truth & predicted); fp = len(predicted-truth); fn = len(truth-predicted)
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall,
            'f1': 2*precision*recall/(precision+recall) if precision+recall else 0.0}
