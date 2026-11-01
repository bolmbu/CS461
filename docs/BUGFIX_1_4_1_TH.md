# แก้บั๊ก v1.4.1

แก้จาก CS461(1).zip ที่ผู้ใช้ส่งมา ไม่ได้เปลี่ยนเป้าหมายในสไลด์หรือฝึกโมเดลใหม่

## การเปลี่ยนแปลง

- เปลี่ยน Next rewrite proxy เป็น same-origin Route Handler รองรับ GET/POST/DELETE, upload และ WAV พร้อม header เวลา TTS กำหนด deadline และแสดง JSON error เมื่อ Backend หลุด
- บังคับ JSON Schema ของผล Qwen3 สำหรับ Profile, คำถาม, FAQ และรายงาน ตรวจรูปแบบซ้ำด้วย Pydantic และจำกัดจำนวน token
- อ่าน JSON ปกติก่อน แล้วจึงลองแยก completed thinking/code fence; ไม่ทำลาย literal </think> ที่อยู่ใน JSON
- Profile ใช้ passage ID ที่ตรวจได้ แล้วแนบ quote จากต้นฉบับจริง ไม่ให้โมเดลพิมพ์ quote เอง ข้อสรุปยังต้องให้คนตรวจความสอดคล้อง
- สรุปไม่ผ่าน/โมเดลไม่พร้อม: เก็บต้นฉบับไว้และแสดง summary_warning โดยไม่มีสรุป AI ปลอม
- ตรวจ arrays/numbers ของ Profile, Interview, Analysis, Report เก่า ป้องกัน .map/.toFixed บนค่าที่หายไป
- เปลี่ยน URL แล้วล้างข้อความ/สถานะตรวจที่อาจค้างมาจากบริษัทเดิม เปิด session แล้วคืนสถานะตรวจจากข้อมูลที่บันทึกจริง
- DDGS ติดตั้งพร้อม baseline; รองรับ href/url ของผลค้น กำหนด timeout และแยกข้อความ missing dependency / ค้นหาไม่ได้ / ไม่พบผล
- ล็อกการเขียนต่อ session ใน process เดียว และตรวจ question_id เพื่อกันคำตอบซ้ำ ป้องกัน double-click ฝั่งเว็บด้วย
- ใช้เวลาจบสัมภาษณ์ในการคำนวณ duration และคืนรายงานที่บันทึกแล้ว แทนการเพิ่มเวลาตอนกลับมาเปิดรายงาน
- ย้าย Whisper inference ออกจาก async event loop, ล็อกการโหลด/ใช้ Whisper/Piper, ลบไฟล์เสียงชั่วคราวแม้มี error
- ปรับไมค์: ข้อความ permission/device error, ปล่อยไมค์เมื่อผิดพลาด, audio MIME, อัดไม่เกิน 3 นาที, แจ้งเมื่อไม่มีคำพูด
- คืนหน่วยความจำ audio URLs, แจ้ง autoplay error, ปิดการเปลี่ยน session ระหว่างงาน และ reset ข้อมูลเก่าที่ไม่ควรตามไป session ใหม่
- /health ตรวจ Piper relative path ด้วยวิธีเดียวกับตัวสังเคราะห์ และแสดง ddgs
- ข้อมูลที่เป็น whitespace อย่างเดียวถูกปฏิเสธ และแสดง API validation เป็นข้อความอ่านได้

## ขอบเขต

ยังเป็น local prototype แบบไม่มี login ไม่ใช่บริการสาธารณะ และเสียงยังเป็น turn-based
ไม่อ้างว่าแก้บั๊กที่เป็นไปได้ทั้งหมด หรือทดสอบฮาร์ดแวร์/ผู้ให้บริการภายนอกทุกเครื่องแล้ว
ดู TEST_REPORT_TH.md สำหรับสิ่งที่รันจริงและสิ่งที่ยังไม่ผ่านการทดสอบ
