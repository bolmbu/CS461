> บันทึกแพตช์รอบก่อน: v1.4.1 แทนที่ส่วนนี้แล้ว ดู BUGFIX_1_4_1_TH.md สำหรับพฤติกรรมปัจจุบัน

# แพตช์ Company Profile / Qwen3

แก้หน้าเตรียม Resume ล่มเมื่อข้อมูลค้นหาหรือ summary.facts ไม่ใช่รายการ
- Frontend ตรวจ array และแสดงข้อความต้นฉบับเมื่อสรุปเดิมรูปแบบไม่ครบ
- Backend ปฏิเสธสรุปที่ไม่มี facts หรือ quote ผิดรูปแบบก่อนบันทึก
- รองรับข้อความคิดที่จบด้วย </think> ก่อน JSON และ JSON code fence
- ยังคงตรวจ exact source quote ไม่ดึง JSON จาก reasoning และไม่ยอมรับ JSON ที่มีข้อความท้าย
- แยกข้อความ Ollama timeout, connection/HTTP error และ JSON ผิดรูปแบบ
- เตือนภาษาไทยเมื่อช่องอ้างอิง CER/WER ว่าง

ตรวจสอบ: Backend tests ผ่าน และ Next production build ผ่านบน Linux
ไม่ได้ทดสอบโมเดลจริงหรือ Windows ในรอบนี้ ไม่รับรองว่าแก้ ECONNRESET ทุกสาเหตุ
ไม่มีการเปลี่ยน proxy timeout หรือ DDGS search ในแพตช์นี้
