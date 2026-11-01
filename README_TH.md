# CoopReady AI v1.4.3 — Portable / Terminal only

ปรับจาก Local v1.4 ให้เปิดจาก VS Code Terminal คำสั่งเดียว ไม่มีไฟล์ batch ใช้ Next.js + FastAPI + SQLite และ Local AI ตามขอบเขตสไลด์เดิม ไม่มี Cloud API และไม่ได้เทรนโมเดลใหม่

## UI v1.4.3 แบบเรียบสำหรับใช้งาน

ใช้แถบเมนูด้านบน โทนขาว/เทา/น้ำเงิน และหน้าภาพรวมที่แสดงรายการฝึกจริงในตาราง
เปลี่ยนหน้าสัมภาษณ์เป็นกล่องข้อความธรรมดา ไม่มีภาพลูกแก้ว ไล่สี หรือแบนเนอร์ตกแต่ง
ยังคงฟังก์ชันและ API ของ v1.4.1 รวมถึงเมนูพับจาก v1.4.2
อัปเดตเฉพาะ UI ได้ด้วย CoopReady_UI_Update.zip โดยแตกทับ root เดิมแล้วเปิด python launch.py ใหม่
รายละเอียด: docs/UI_UPDATE_1_4_3_TH.md

## ประวัติ UI v1.4.2 ใช้งานง่ายขึ้น

หน้าหลักมีเส้นทาง เตรียมเรซูเม่ → ซ้อมสัมภาษณ์ → ดูคำแนะนำ พร้อมคำอธิบายภาษาไทย
เลือกโหมด “ฝึกพื้นฐาน” หรือ “ฝึกด้วย AI” ได้ที่ส่วนบน ข้อมูลบริษัทเป็นส่วนเพิ่มเติม
เครื่องมือวัดผลสำหรับโครงงาน ค่าความคล้าย การจัดการ FAQ และสถานะโมเดลอยู่ในเมนูพับ เปิดดูได้เมื่อจำเป็น
หน้าคำแนะนำแสดงรายงานก่อนประวัติ เสียงยังเป็นการพูดสลับรอบและต้องตั้งค่าโมเดลเหมือน v1.4.1
API/backend ยังเป็นรุ่น 1.4.1 ที่ทดสอบไว้ ไม่มีการเปลี่ยนข้อมูลหรือวิธีเรียกโมเดลในรอบ UI นี้

ถ้าติดตั้ง v1.4.1 อยู่แล้ว ใช้ CoopReady_UI_Update.zip แตกทับ root เดิม จะไม่เปลี่ยน backend/.env, backend/.venv หรือประวัติ
ดู docs/UI_UPDATE_1_4_2_TH.md สำหรับรายการปรับ UI และผลตรวจ

## เวอร์ชันแก้บั๊ก 1.4.1

แตก ZIP ลงโฟลเดอร์ใหม่ เช่น `D:\BU\CS461_Fixed` แล้วเปิดโฟลเดอร์นั้นใน VS Code และรัน `python launch.py` ไม่ต้อง activate หรือใช้ .bat
ต้องติดตั้ง Python 3.11/3.12 และ Node.js 22+ ก่อน ครั้งแรกต้องใช้อินเทอร์เน็ตเพื่อติดตั้งแพ็กเกจ
ดูเลข `v1.4.3` บนเว็บเพื่อยืนยันว่าเปิดโฟลเดอร์ใหม่ถูกต้อง

- ZIP ไม่รวม `.env`, ประวัติผู้ใช้, `.venv`, `node_modules`, โมเดล หรือ Modelfile ที่ผูกกับ path ของเครื่องเก่า
- launcher สร้าง `.env` จากตัวอย่างเมื่อยังไม่มีไฟล์ ใช้โมเดลเดิม `qwen3:4b` ที่ติดตั้งใน Ollama ได้ ไม่ต้องใช้ชื่อ custom nothink
- DDGS รวมอยู่ในแพ็กเกจพื้นฐานแล้ว แต่การค้นหายังขึ้นกับอินเทอร์เน็ตและผู้ให้บริการ หากค้นไม่ได้ให้กรอก URL หรือวางข้อความบริษัท
- หน้าเว็บอ่านผ่าน Route Handler ที่กำหนดเวลารอ Backend เอง ป้องกันการพึ่ง rewrite proxy สำหรับงาน AI ที่นาน ค่าเริ่มต้นรอ 600 วินาที
- ถ้าสรุป AI ไม่ผ่าน จะบันทึกข้อความต้นฉบับพร้อมคำเตือนชัดเจน สรุป AI จะไม่ถูกปลอมขึ้นมา
- สรุปบริษัทเลือก passage ID แล้วระบบแนบข้อความต้นฉบับเป็น quote ต้องให้คนตรวจว่าข้อสรุปสอดคล้องกับหลักฐานจริง
- หากเปลี่ยน URL ข้อความบริษัทเก่าจะถูกล้าง เพื่อไม่ผูกข้อความบริษัทเดิมกับ URL ใหม่
- เสียงเป็นแบบพูดสลับรอบ: เริ่มพูด → หยุดและถอดเสียง → ตรวจข้อความ → ยืนยันและส่ง ยังไม่ใช่ full-duplex realtime

### เปิดส่วน AI / เสียง

รันคำสั่งติดตั้งโดยหยุดเว็บก่อน แล้วเปิดเว็บใหม่หลังติดตั้ง:

```powershell
python launch.py --install-ai semantic stt --prepare-models semantic stt
```

การดาวน์โหลดโมเดลใช้พื้นที่และเวลา ไม่จำเป็นสำหรับ Baseline แบบพิมพ์
Ollama ต้องติดตั้ง/เปิดแยก และมี `qwen3:4b` ก่อนเลือก Proposed
Piper เป็นอีกส่วนหนึ่ง: `python launch.py --install-ai tts` แล้วกำหนด voice ONNX + JSON และภาษาที่ตรงกันตาม `docs/MODEL_SETUP_TH.md`
ถ้ายังไม่มี Piper สามารถติ๊ก Browser TTS สำรองได้ ต้องเลือกเอง และจะไม่นับเป็นผลรัน Piper

### ย้ายประวัติจากโฟลเดอร์เดิม (ถ้าต้องการ)

หยุดทั้งสองโปรแกรมก่อน คัดลอก `backend/runtime` เดิมไปที่ `backend/runtime` ในโฟลเดอร์ใหม่ โดยสำรองของเดิมไว้
อย่าคัดลอก `.venv`, `node_modules`, `.next`, `.bootstrap.json` หรือ Modelfile.nothink เก่ามา
ข้อมูลส่วนตัวอยู่ใน runtime จึงไม่ควรส่งโฟลเดอร์นั้นแนบรายงานหรือแชร์ให้ผู้อื่น

รายละเอียดการเปลี่ยนแปลงและผลตรวจ: `docs/BUGFIX_1_4_1_TH.md` และ `docs/TEST_REPORT_TH.md`

## เริ่มบน Windows

สิ่งที่ต้องติดตั้งบนเครื่องใหม่ก่อน:

- Python **3.11 หรือ 3.12** จาก https://www.python.org/downloads/windows/ เลือก Add python.exe to PATH
- Node.js **22 ขึ้นไป** พร้อม npm จาก https://nodejs.org/
- Chrome/Edge สำหรับไมโครโฟน

ปิดและเปิด VS Code ใหม่หลังติดตั้ง Python/Node เพื่อให้อ่าน PATH ล่าสุด

1. แตก ZIP ลงโฟลเดอร์ใหม่ อย่าเปิดโค้ดจากใน ZIP
2. VS Code > File > Open Folder เลือกโฟลเดอร์ที่มี launch.py
3. Terminal > New Terminal แล้วพิมพ์:

```powershell
python launch.py
```

ครั้งแรกต้องใช้อินเทอร์เน็ตเพื่อติดตั้งแพ็กเกจ อาจใช้เวลาหลายนาที อย่าปิด Terminal ระหว่างติดตั้ง
เมื่อขึ้น `READY: http://127.0.0.1:3000` เว็บจะเปิดให้อัตโนมัติ ใช้ URL ที่แสดงจริงเพราะพอร์ตอาจเปลี่ยนถ้าพอร์ตเดิมถูกใช้
เปิด Terminal ค้างไว้ระหว่างใช้งาน กด Ctrl+C เพื่อหยุด Backend/Frontend ของโปรเจกต์นี้
ครั้งต่อไปใช้คำสั่งเดิม ไม่ต้อง activate .venv หรือเปิดสอง Terminal

ถ้า python หาไม่เจอ แต่มี Python Launcher:

```powershell
py -3.12 launch.py
```

ถ้า Python หลักเป็น 3.13/3.14 ให้ติดตั้ง 3.12 เพิ่มและใช้คำสั่งข้างบน ไม่ต้องถอน Python ที่ใช้โปรเจกต์อื่น

## macOS / Linux

ติดตั้ง Python 3.11/3.12 และ Node.js 22+ แล้วเปิด Terminal ในโฟลเดอร์โปรเจกต์:

```bash
python3.12 launch.py
```

หรือใช้ `python3 launch.py` เมื่อ python3 เป็นรุ่น 3.11/3.12 Linux บางเครื่องต้องติดตั้ง package python3.12-venv ของระบบก่อนสร้าง venv

## ตัวเปิดจัดการอะไรให้

- ใช้ path อ้างอิงจากไฟล์ launch.py ไม่ผูกกับไดรฟ์ D: หรือชื่อโฟลเดอร์ของผู้สร้าง
- สร้าง backend/.venv บนเครื่องปลายทางและใช้ Python ใน venv โดยตรง
- ตรวจ venv เดิมที่รันไม่ได้ ผูกกับ path เก่า หรือแพ็กเกจ Baseline import ไม่ผ่าน แล้วสร้างใหม่เมื่อจำเป็น
- ใช้ Node เรียก npm-cli.js และ Next โดยตรงบน Windows เพื่อลดปัญหา npm.cmd และ shell quoting
- ติดตั้ง Python dependencies ตามรุ่น direct dependencies ที่เคยทดสอบ และ npm ตาม package-lock.json
- ตรวจพอร์ต 8001/3000 ถ้าไม่ว่างจะเลือกพอร์ตถัดไปและเชื่อม Frontend/Backend ให้ตรงกัน ไม่ปิดโปรแกรมอื่น
- ตรวจความพร้อม Backend ผ่าน /openapi.json ซึ่งไม่เรียก Ollama
- ไม่ใช้ HTTP proxy ของระบบสำหรับการรอ localhost
- ไม่เขียนทับ .env เดิม ไม่คัดลอก API key หรือข้อมูลนักศึกษาไปเครื่องใหม่
- เก็บสำเนา environment/cache ที่ต้องสร้างใหม่เป็นชื่อ .backup-* เฉพาะส่วนที่สร้างจาก source ได้ ไม่ลบข้อมูล runtime

การตรวจเหล่านี้ช่วยลดปัญหา แต่ **ไม่รับประกันว่าจะไม่มี error บนทุก OS/สเปก/เครือข่าย** Windows และ macOS ยังต้องทดสอบบนเครื่องจริงเพิ่มเติมตาม TEST_REPORT

## ตรวจเครื่อง / ซ่อม / ติดตั้งอย่างเดียว

```powershell
python launch.py --doctor
python launch.py --repair
python launch.py --setup-only
python launch.py --no-browser
```

- `--doctor`: ไม่ติดตั้งอะไร แสดงรุ่นเครื่อง/แพ็กเกจและสิ่งที่ยังขาด ไม่ได้ยืนยันว่าโมเดลรันจริงแล้ว
- `--repair`: สร้าง Python environment ใหม่และติดตั้ง npm ใหม่ เก็บ .env และข้อมูล runtime ไว้ ใช้เมื่อแพ็กเกจเสียหรือย้าย environment มาไม่สมบูรณ์ หลังซ่อมต้องติดตั้งแพ็กเกจ AI ที่เคยเลือกอีกครั้ง ส่วน model cache เดิมไม่ได้ถูกลบ
- `--setup-only`: เตรียม Baseline แล้วจบ ไม่เปิดเว็บ
- `--no-browser`: เปิดระบบแต่ให้คุณเปิด URL เอง

## ติดตั้ง AI เป็นส่วน ๆ ผ่าน Terminal

ค่าเริ่มต้นใช้ **Baseline** เพื่อให้หน้าเว็บเปิดได้แม้ยังไม่มี Ollama หรือโมเดลเสียง
การติดตั้ง pip package ไม่เท่ากับดาวน์โหลดโมเดล weights และไม่ยืนยันคุณภาพโมเดล

### ถอดเสียงด้วย faster-whisper

```powershell
python launch.py --install-ai stt --prepare-models stt
python launch.py
```

คำสั่งแรกติดตั้งตัวถอดเสียงและโหลดโมเดลตาม backend/.env เริ่มต้นเป็น small/CPU/int8 ครั้งแรกต้องใช้เน็ตและพื้นที่เก็บโมเดล
จากนั้นเริ่มสัมภาษณ์ กดเริ่มพูด > หยุดและถอดเสียง > ตรวจข้อความ > ยืนยันส่ง
เวอร์ชันนี้ยังเป็น turn-based ไม่ใช่ full-duplex หรือ streaming voice assistant

### LLM ผ่าน Ollama

ติดตั้งและเปิด Ollama จาก https://ollama.com/download แล้วรัน:

```powershell
python launch.py --prepare-models llm
python launch.py
```

คำสั่ง prepare นี้ดาวน์โหลด qwen3:4b ตามค่าเริ่มต้นในโครงการ หากคุณเปลี่ยน OLLAMA_MODEL ให้ pull ชื่อโมเดลเดียวกันด้วย Ollama เอง
เริ่มจาก Baseline ถ้ายังไม่พร้อม เมื่อ Ollama พร้อมแล้วเลือก Proposed ในเว็บ

### MiniLM + Chroma / Piper / DDGS

```powershell
python launch.py --install-ai semantic --prepare-models semantic
python launch.py --install-ai tts
python launch.py --install-ai research
```

หรือ `python launch.py --install-ai all` เพื่อติดตั้งแพ็กเกจ AI ทุกกลุ่ม แต่ไม่ได้โหลด model weights ทุกตัวหรือจัดหาเสียง Piper ให้อัตโนมัติ
Piper ต้องมี ONNX และ ONNX.json คู่กันและตรงภาษา เริ่ม English ได้เมื่อคุณมี voice อังกฤษที่ทดสอบแล้ว ไม่อ้างว่าเสียงไทยพร้อมจาก Browser TTS fallback
อ่าน docs/MODEL_SETUP_TH.md เพิ่มเติม

## ย้ายโปรเจกต์ไปเครื่องอื่น

ส่ง ZIP source ที่แนบนี้ แล้วให้เครื่องใหม่ทำขั้นตอนเริ่มต้นด้านบน ไม่คัดลอกของเหล่านี้ข้ามเครื่อง:

- backend/.venv และ .venv.backup-*
- frontend/node_modules และ .next*
- backend/.bootstrap.json
- backend/.env และ frontend/.env.local (อาจมี path/config เฉพาะเครื่อง)
- backend/runtime, resume จริง, logs และไฟล์เสียงนักศึกษา

ตัวเปิดจะสร้าง config จาก .env.example และ dependencies ของเครื่องใหม่เอง
โมเดลที่ดาวน์โหลดโดย Ollama/Hugging Face อยู่ใน cache ของแต่ละเครื่อง ต้องเตรียมใหม่หรือย้ายตามวิธีที่ผู้พัฒนาโมเดลรองรับ แยกจาก ZIP source นี้
ถ้าต้องย้ายประวัติจริง ต้องได้รับอนุญาตและวางแผนย้าย SQLite/runtime แยกต่างหาก ไม่ส่งรวมกับ source โดยไม่ตรวจข้อมูลส่วนตัว

## Workflow ตามสไลด์

1. เตรียม Resume PDF ที่มีข้อความ / DOCX / TXT และยืนยันสิทธิ์ก่อนอัปโหลด
2. ระบุบริษัท ตำแหน่ง และ Role Brief ที่คุณมีอยู่แล้ว
3. สร้าง session แล้ววางข้อความ/Official URL ของบริษัทเพื่อทำ human-checked profile
4. วิเคราะห์ Resume: Baseline TF-IDF + keyword หรือ Proposed MiniLM evidence
5. ฝึกสัมภาษณ์: Fixed Bank 5 ข้อ หรือ Proposed Qwen3 + 2 follow-ups พร้อม quote
6. FAQ: นำเข้าข้อมูลที่คณะรับรองพร้อมหน้าและเวอร์ชัน หรือใช้ demo แบบมีป้ายสมมติ
7. Results: เปิดประวัติ ส่งออกผล ตรวจ CER/WER และ Precision/Recall/F1 จากข้อมูลอ้างอิงที่คนใส่

ข้อมูลที่เก็บใน SQLite ไม่หายเมื่อรีเฟรช เปิด session เดิมได้จากหน้าประวัติ
Company Research ไม่ค้นตำแหน่งเปิดรับ วันสมัคร ลิงก์สมัคร และไม่ยื่นสมัครแทนอาจารย์

## ข้อจำกัดและข้อมูลส่วนบุคคล

- ไม่รองรับ OCR ของ PDF สแกน และ PDF หลายคอลัมน์อาจอ่านลำดับผิด ต้องตรวจข้อความ
- Not Evidenced หมายถึงไม่พบหลักฐาน ไม่ได้ยืนยันว่าไม่มีทักษะ
- TF-IDF/embedding similarity ไม่ใช่ Accuracy หรือโอกาสได้งาน
- FAQ สมมติไม่ใช่ประกาศมหาวิทยาลัย ต้องนำเข้าข้อมูลที่ตรวจแล้วก่อนใช้งานจริง
- ใช้โมเดล Local ไม่ได้แปลว่าคำตอบถูกเสมอ รายงานและคะแนนต้องให้คนตรวจ
- ข้อความ Resume/คำตอบอยู่ backend/runtime ตาม DATA_DIR; ค่าเริ่มต้น retention 7 วัน ตรวจล้างตอนเปิด/สร้าง/เรียกรายการ session ไม่ใช่บริการล้างเมื่อแอปปิด
- ไฟล์เสียงชั่วคราวถูกลบหลังถอด; แอปยังไม่เก็บไฟล์เสียงเพื่อประเมิน WER/CER ต้องจัดชุดทดสอบเสียงที่ได้รับอนุญาตแยกเอง
- FAQ เก็บจนลบ Chroma cache ชุดเก่าอาจยังอยู่แม้ลบ FAQ แต่ระบบไม่ค้นชุดเก่า ต้องปิด backend แล้วลบ runtime/chroma หากต้องการลบเวกเตอร์ทั้งหมดจริง
- ไม่มีระบบ login/multi-user ใน localhost จึงไม่เปิดพอร์ตสาธารณะ
- Browser TTS สำรองอาจใช้ผู้ให้บริการของเบราว์เซอร์ ไม่ถือเป็นผลทดสอบ Piper

## ทดสอบ

หลัง `python launch.py --setup-only` บน Windows:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
```

มี pytest.ini กำหนด pythonpath ให้แล้ว จึงรันจากโฟลเดอร์หลักได้ หรือเข้า backend แล้วใช้ `.venv\Scripts\python.exe -m pytest tests -q`
รัน `evaluate_baseline.py` จาก backend เพื่อสร้างผลชุดสมมติ 3 ตัวอย่างตาม INITIAL_RESULTS_SYNTHETIC.json ไม่ใช้แทนผลข้อมูลนักศึกษาจริง
หน้าเว็บทดสอบ build ด้วย `npm run build` ใน frontend

## ไฟล์หลัก

- launch.py: เปิด/ตรวจ/ซ่อม/ติดตั้งผ่าน Terminal
- backend/app/: API, Baseline, Local model adapters, SQLite
- frontend/app/: หน้าเว็บ Next.js
- data/: FAQ template และข้อมูลสมมติ
- docs/: เทียบสไลด์ วิธีเตรียมโมเดล แผนประเมิน และสถานะการทดสอบ
