# ตั้งค่า Local AI บนเครื่องทีม

## แพ็กเกจ

เปิด Terminal ใน backend:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ai.txt
```

โมเดลมีขนาดใหญ่และใช้ทรัพยากร อย่าใช้ผลจากระบบนี้อ้างว่ามีการ fine-tune: ทุกส่วนเป็น pretrained inference / retrieval ไม่ได้เทรนใหม่

## 1. Ollama / Qwen3

ติดตั้ง Ollama จาก https://ollama.com/download และเปิดโปรแกรม จากนั้น:

```powershell
ollama pull qwen3:4b
ollama list
```

เครื่องที่ทรัพยากรจำกัดอาจลอง qwen3:1.7b และเปลี่ยน OLLAMA_MODEL ใน backend/.env ให้ตรง ถ้า CPU ช้าหรือ timeout ให้ตรวจความเร็วและปรับ OLLAMA_TIMEOUT โดยไม่อ้าง latency ที่ยังไม่วัด

API ใช้ POST /api/chat พร้อม stream=false, format=json, think=false ต้องตรวจรุ่น Ollama และรูปแบบ JSON จากโมเดลจริง
ทดสอบโดยสร้าง session เลือก Proposed แล้วเริ่ม Interview ถ้ารับ JSON หรือข้อความหลักฐานไม่ได้ ระบบจะไม่บันทึกคำตอบ/ผลที่ยังตรวจไม่ผ่าน

## 2. Multilingual MiniLM และ Chroma

ชื่อค่าเริ่มต้น:

sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

ดาวน์โหลดครั้งแรกผ่าน SentenceTransformer เมื่อเรียก Proposed การโหลดครั้งแรกจึงอาจใช้เวลานาน แนะนำ warm up ก่อน demo:

```powershell
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); print(m.encode(['ทดสอบระบบ']).shape)"
```

FAQ Proposed จัดเก็บ embeddings ใน Chroma local และค้นเฉพาะ FAQ ที่ approved หรือ demo ที่อนุญาตและไม่หมดอายุ ก่อนส่ง context ให้ Qwen3
Resume Proposed เก็บ lexical_status เดิม และเพิ่ม semantic candidates; ทักษะที่ไม่ตรงคำแต่ similarity >= SEMANTIC_THRESHOLD จะเป็น Matched แบบ semantic_candidate ต้องให้คนตรวจหลักฐานอีกครั้ง
threshold เริ่มต้น 0.55 เป็นค่าตั้งต้น ไม่ผ่านการปรับเทียบ ต้องจูนบน validation set และประเมิน held-out test set

## 3. faster-whisper

เริ่ม CPU ได้ด้วย .env:

```
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

หน้า Interview กดเริ่มพูดและหยุด เบราว์เซอร์ส่งไฟล์ WebM/MP4 ไป /voice/transcribe และ backend ใช้ faster-whisper โดยตรง แก้ Transcript ก่อนส่งคำตอบได้
โมเดล Whisper จะดาวน์โหลดครั้งแรก หากอินเทอร์เน็ตหรือเครื่องไม่พร้อมให้รอและตรวจ error ห้ามเรียกการพิมพ์คำตอบว่าเป็นผล STT
การใช้ CUDA ต้องตรวจ GPU, CTranslate2 และไลบรารี NVIDIA ให้ตรงกัน ไม่ตั้ง CUDA อัตโนมัติ

## 4. Piper

Piper ไม่ได้พูดทุกภาษาได้เพียงเปลี่ยน language code ต้องมี voice ที่ฝึกมาสำหรับภาษานั้นจริง

- จัดหา model .onnx และ .onnx.json จากแหล่งที่เชื่อถือได้ ตรวจ license ของเสียงก่อนใช้
- ตัวเลือก voices: https://huggingface.co/rhasspy/piper-voices
- โค้ดที่ใช้: https://github.com/OHF-Voice/piper1-gpl
- ตรวจไฟล์ทั้งสอง และกำหนด path แบบ absolute ใน backend/.env

ตัวอย่าง config สำหรับเสียงอังกฤษที่ดาวน์โหลดและตรวจแล้ว:

```
PIPER_MODEL=D:/models/piper/en_US-lessac-medium.onnx
PIPER_LANGUAGE=en
```

เลือก English ตอนสร้าง session จึงจะตรงเสียงนี้ หากใช้ voice ไทยที่ตรวจแล้ว ให้ใช้ PIPER_LANGUAGE=th และ path ของ voice ไทย ไม่แนบหรืออ้างว่าเสียงไทยพร้อมโดยยังไม่ตรวจโมเดล

ทดสอบด้วยปุ่มฟังคำถาม ระบบวัดเวลา synthesize จริงใน header X-TTS-MS และเล่น WAV ในเบราว์เซอร์ หากเกิดข้อผิดพลาดจะไม่เปลี่ยนไป Browser TTS เอง

ถ้าหา Piper voice ไทยที่เหมาะสมไม่ได้: ใช้ English สำหรับ demo local voice ตามขอบเขตที่อาจารย์ยอมรับ หรือหารือปรับเครื่องมือเสียงไทยและแก้สไลด์ให้ตรง ห้ามอ้างว่า Piper ภาษาไทยสำเร็จจาก Browser TTS fallback

Piper ปัจจุบันมีเงื่อนไข GPL และเสียงแต่ละชุดอาจมี license ต่างกัน ก่อนแจก weights หรือเผยแพร่โค้ดรวมต้องตรวจเงื่อนไขจริงของชุดที่ใช้

## 5. DDGS / ข้อมูลบริษัท

กดค้นแหล่งข้อมูล จะได้ candidates ที่ยังไม่ verified ให้ตรวจว่าเป็นเว็บทางการก่อนเลือก URL ปุ่มอ่าน Profile ใช้ requests + BeautifulSoup และไม่รัน JavaScript ในเว็บ
ถ้าเว็บไม่ยอมให้อ่าน ให้ใช้ Official URL พร้อมข้อความที่คนตรวจเอง เป็น fallback ที่มีในสไลด์ ไม่อ้อมข้อจำกัดเว็บไซต์

## เกณฑ์ Voice MVP ที่ยังต้องรันบนเครื่องทีม

1. ใช้ Proposed จริงและเสียง Local ทั้งสองทาง อย่างน้อย 5 รอบ
2. มีคำถามต่อจากคำตอบล่าสุดอย่างน้อย 2 ครั้ง ตรวจความเกี่ยวข้องโดยคน
3. เสียงพูดที่ได้ยินตรงคำถาม และ Transcript แก้ไขได้
4. มีรายงาน 5 มิติ อ้างข้อความจากคำตอบ ไม่แต่งประสบการณ์
5. เก็บ STT / LLM / TTS latency แยกกัน และวัด CER/WER กับเสียงอ้างอิงที่คนตรวจ
6. ค่า voice_turns ในรายงานนับจาก metadata การใช้ faster-whisper และการสร้าง TTS ไม่ยืนยันว่าผู้ใช้ได้ยินเสียงหรือการสนทนามีคุณภาพ ต้องตรวจการทำงานจริงด้วย
