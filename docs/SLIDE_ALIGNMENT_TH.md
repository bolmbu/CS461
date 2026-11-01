# สถานะเทียบ CoopReady_AI_Presentation_TH(1).pdf

อ้างอิงเลขหน้า PDF จริง 1–11 ซึ่งตัวเลขสไลด์บนภาพอาจเริ่มต่างกัน

| หน้า PDF | ประเด็นในสไลด์ | โค้ด/สิ่งที่ส่งให้ | สถานะหลักฐาน |
|---|---|---|---|
| 2 | ปัญหา เป้าหมาย Metrics | คงขอบเขตเตรียมความพร้อม ไม่ตัดสินผู้สมัคร | ยังไม่สำรวจขนาดปัญหากับผู้ใช้จริง |
| 3 | Resume + บริษัท + ตำแหน่ง | Next.js form, consent, PDF/DOCX/TXT parser, SQLite session | Backend test DOCX และกรณี PDF สแกน; PDF ข้อความยังต้องตรวจหลาย layout จริง |
| 3 | Company / Role Profile | human-checked baseline; DDGS candidates, public HTML extraction, Qwen3 summary with quote checks | manual profile test ผ่าน; live research/Qwen3 ยังไม่รัน |
| 3, 6 | Resume Baseline | TF-IDF + cosine + keyword evidence | รันจริงกับข้อมูลสมมติ 3 คู่ |
| 6 | Resume Proposed | MiniLM semantic candidates และ threshold labels พร้อม lexical_status เดิม | มีโค้ด ยังไม่โหลดโมเดลหรือประเมินจริง |
| 6 | Interview Baseline | Fixed Question Bank 5 ข้อ ไม่มี adaptive follow-up | API test ครบ 5 ข้อและรายงาน checklist |
| 6, 8 | Interview Proposed | Qwen3 5 คำถามหลัก + 2 follow-ups ตรวจ quote จากคำตอบล่าสุด | contract tests ด้วย mock ผ่าน; ไม่ใช่ผล Qwen3 จริง |
| 6 | Academic FAQ Baseline | TF-IDF retrieval, cited FAQ, no-answer threshold | tests สำหรับค้นตอบ/งดตอบ/หมดอายุ/ไม่อนุมัติผ่าน |
| 6, 7 | RAG Proposed | MiniLM + Chroma persistent + Qwen3 พร้อมตรวจ citation IDs | มีโค้ด ยังไม่โหลดโมเดลหรือประเมินจริง |
| 7 | Next.js + FastAPI + SQLite | frontend/backend แยก, API proxy, history/export/delete, retention | Next production build ผ่าน; FastAPI tests ผ่าน |
| 7, 8 | faster-whisper + Piper | MediaRecorder → local STT → editable transcript → local LLM → Piper WAV | มีโค้ด ไม่มี voice weights แนบ ยังไม่ทดสอบไมค์หรือเสียงจริง |
| 5 | P/R/F1, CER/WER, latency | evaluation endpoints + UI + JSON export | สูตรทดสอบแล้ว; ไม่เท่ากับประเมินโมเดลจริง |
| 9 | Feedback 4–5 มิติพร้อมหลักฐาน | baseline human checklist; proposed 5 dimensions validates quotes and scores | baseline test ผ่าน; Qwen3 feedback จริงยังไม่ทดสอบ |
| 4, 10 | Dataset และ Initial Results | data templates, synthetic report, evaluation protocol | ยังไม่มี dataset ที่คณะอนุมัติหรือ real-user evaluation |
| 11 | Challenges | explicit errors/fallback settings, model readiness, parser scan warning | มี test บางกรณี; ประสิทธิภาพเครื่องทีมยังไม่วัด |

## ความต่างจาก ZIP แรกที่แก้แล้ว

- เปลี่ยน static-only เป็น Next.js + FastAPI ตามสไลด์
- Python server ไม่ใช่แค่เปิดไฟล์ HTML แต่มี API วิเคราะห์ เก็บข้อมูล และเรียกโมเดล
- Baseline Interview กลับเป็น Fixed Bank ตามข้อเสนอ; follow-up ที่อาศัย LLM แยกไป Proposed
- Local voice adapters ใช้ faster-whisper และ Piper; Browser TTS เป็น fallback ที่ติดป้ายชัด
- เพิ่ม Company/Role Profile และหลักฐานที่มา
- ประวัติอยู่ SQLite ไม่หายทุกครั้งที่รีเฟรช
- เพิ่มสูตรประเมินและไฟล์ผลทดลองสมมติ พร้อมรายการที่ยังไม่ได้ทดสอบ

## สิ่งที่ยังไม่ควรพูดว่าเสร็จ

ไม่ควรบอกว่า “ระบบครบตาม MVP และผ่านเสียงสองทางแล้ว” จนกว่าจะติดตั้งโมเดลและทำ acceptance test บนเครื่องทีม
ไม่ควรบอกว่า “โมเดลใหม่ดีกว่า Baseline” เพราะยังไม่มีผลเปรียบเทียบ Proposed
ไม่ควรใช้ F1 จาก 3 ตัวอย่างสมมติเป็น Accuracy หรือความแม่นยำในนักศึกษาจริง
ไม่ควรเรียก pretrained inference ว่า “เทรนโมเดลเอง”

## สิ่งที่แสดงใน progress check ได้หลังรันบนเครื่องทีม

1. โครงสร้าง Next.js/FastAPI และ Baseline ที่รันได้ พร้อมสเปกเครื่อง/versions
2. ผล 3 ตัวอย่างสมมติ ใช้แสดงรูปแบบการประเมินและข้อผิดพลาด เช่น ไพธอน vs Python
3. FAQ source และกรณีที่ควรงดตอบ
4. รายการปัญหาจริงหลังรัน เช่น Ollama ไม่พร้อม Piper ยังไม่มี voice หรือ latency สูง
5. แผนเก็บข้อมูลและทดสอบ Proposed ต่อ โดยระบุว่ายังไม่เสร็จตามจริง
