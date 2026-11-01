# ผลตรวจ v1.4.1

## รันผ่านจริง

- Python 3.12 บน Linux / Node 24: Backend + launcher pytest 57 tests ผ่าน
- Node frontend regression tests 7 tests ผ่าน: legacy data normalization, readable errors, bridge binary/status/headers, connection error, timeout, invalid path
- แตก source ลงโฟลเดอร์ใหม่ที่มีช่องว่างและภาษาไทย แล้วรัน python launch.py --no-browser จริง: ติดตั้ง Python/npm ใหม่ครบ เปิดหน้าเว็บ 200 และ /backend/ready ยืนยัน version 1.4.1 ผ่านบน Linux
- Next.js production build ผ่าน และมี /backend/[...path] route
- scripts/smoke_web.py --slow-seconds 31: เปิด Next และ FastAPI จริง ส่งคำขอ HTTP ผ่าน same-origin route ไป controlled Ollama stub ที่ส่ง reasoning ปน JSON และจำลองตอบช้า 31 วินาที ผ่าน
- HTTP smoke: upload TXT, create/reload session, Profile schema + source ID, baseline skill matching, baseline 5 รอบ, proposed 7 รอบ/2 follow-ups, report 5 มิติ, duplicate answer prevention, FAQ abstention, CER/WER, export, delete
- Unit tests: DOCX/invalid PDF/scanned PDF, consent, FAQ approval/expiry/demo, schema/output failure, preserving raw source, interview transaction failure, simultaneous duplicate answers, temp audio cleanup, retention และ launcher checks
- มี Starlette/httpx deprecation warning 1 รายการใน pytest ไม่มี test failure

## ยังไม่ยืนยัน

- ไม่มี Ollama/Qwen3 หรือ MiniLM/Chroma inference จริงใน environment ทดสอบนี้ ผล proposed ใช้ stub ไม่ใช่คะแนนความแม่นยำโมเดล
- ไม่ได้ทดสอบไมค์ ลำโพง faster-whisper หรือ Piper กับไฟล์เสียงจริง/ภาษาไทย
- ดาวน์โหลด Chromium สำหรับทดสอบคลิกหน้าเว็บไม่สำเร็จ จึงไม่มี browser interaction test ครบทุกปุ่ม; build/HTTP/Node tests ไม่ได้ทดแทนการทดสอบนี้
- ลองเปิด storemesh.com จาก Python แล้ว DNS ไม่สำเร็จใน environment นี้ จึงยังยืนยันการอ่านเว็บนั้นหรือ DDGS live บนเครื่องผู้ใช้ไม่ได้; DDGS package ติดตั้งได้และ unit contract ผ่าน
- ยังไม่ได้รันบน Windows/macOS จริง ไม่รับประกันว่าไม่มี error จากระบบปฏิบัติการ ไดรเวอร์ หรือเครือข่าย

## รันทดสอบซ้ำ

จาก root โปรเจกต์ หลังติดตั้ง baseline:

Windows: backend\.venv\Scripts\python.exe -m pytest -q
macOS/Linux: backend/.venv/bin/python -m pytest -q

Frontend: cd frontend แล้ว npm test และ npm run build
HTTP smoke: ใช้ Python ของ backend รัน scripts/smoke_web.py --slow-seconds 31 จาก root หลัง build frontend
SMOKE_RESULTS.json เป็นผลรันทดสอบ HTTP รอบนี้

ไฟล์ dataset/metrics เดิมที่ระบุ synthetic ยังคงเป็นข้อมูลสมมติ ไม่ใช่การประเมินนักศึกษาจริง

## UI v1.4.2

ผลทดสอบ 31 วินาทีของ v1.4.1 เก็บใน SMOKE_RESULTS_1_4_1.json
SMOKE_RESULTS.json เป็น HTTP smoke รอบ UI v1.4.2 ซึ่งใช้ stub ไม่หน่วงเวลา
ดู UI_UPDATE_1_4_2_TH.md สำหรับการตรวจ UI รอบนี้

## UI v1.4.3

ปรับเป็นแถบเมนูด้านบนและตารางประวัติ ผล smoke ล่าสุดใน SMOKE_RESULTS.json ระบุ ui_version 1.4.3
Frontend regression 7 tests และ production build ผ่าน; ไม่มี browser click/microphone tests ใหม่
