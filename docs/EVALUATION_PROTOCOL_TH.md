# แผนประเมินตามสไลด์

จำนวน 10–15 company profiles, 20–40 resume-role pairs, 10–15 sessions, 30–50 FAQs และ >=10 edge cases เป็นเป้าหมายเดิม ยังไม่ถือว่าเก็บเสร็จ

## หลักการ
- แบ่ง train/development (ถ้ามี), validation และ held-out test ตาม Resume/บุคคล/เอกสารต้นฉบับก่อนแปลหรือสร้าง variantes ป้องกันข้อมูลรั่ว
- ใช้ข้อมูลทดสอบเดียวกันสำหรับ Baseline และ Proposed ไม่ปรับ threshold บน test
- เก็บรุ่นโมเดล ชื่อ voice, versions, สเปกเครื่อง, วันที่, config และ prompt ที่ใช้
- synthetic demo ใช้ตรวจ workflow ไม่ใช้แทนผู้ประเมินจริงหรือรับรองคุณภาพ

## Resume
ให้คนตรวจป้ายรายทักษะ Matched/Not Evidenced และข้อความหลักฐานที่รองรับ เก็บ truth ตามชื่อ canonical เพื่อคำนวณ P/R/F1 บนชุดเดียวกัน แยก lexical และ semantic labels; similarity ไม่ใช่ Accuracy

## Company / Role
ผู้ตรวจเทียบข้ออ้างแต่ละข้อกับ URL/ข้อความ source ว่ามีหลักฐานตรงหรือไม่ ใช้ Source Precision, groundedness และการยอมบอกเมื่อข้อมูลขาด แยก Company Fact, User-provided Role Brief, General Role Guidance

## FAQ
ชุดคำถามต้องมีคำตอบอ้างอิงที่คณะอนุมัติ หน้า version และข้อไม่มีคำตอบ พร้อมคำถามอิงประกาศเก่าที่ไม่ควรตอบ ตรวจ Correctness, Citation Accuracy, Abstention on no-answer โดยคน ไม่ให้คะแนนจาก similarity อย่างเดียว

## Interview
ผู้ประเมิน 2 คนใช้ rubric เดียวกัน 1–5 ใน 5 มิติ ตรวจความเกี่ยวข้องของ follow-up และหลักฐานคำตอบ รวมถึงความสอดคล้องระหว่างคะแนน AI กับผู้ประเมิน ต้องเก็บคะแนนดิบทั้งสอง ไม่อ้าง rubric agreement หากยังไม่มีข้อมูล

## Voice
เก็บเสียงที่ได้รับอนุญาตและ transcript ที่คนตรวจ ไทย/อังกฤษ สภาพเงียบ/มีรบกวน คำนวณ CER สำหรับไทย และ WER หลังระบุวิธีตัดคำอย่างชัดเจน Endpoint WER ที่ให้เป็น whitespace เท่านั้นไม่ใช่ Thai word segmentation เก็บ STT, LLM, TTS latency แยก และระบุ cold start/warm start ตรวจเสียงที่ผู้ใช้ได้ยินจริงเพิ่มเติม

## ตัวอย่าง edge cases
PDF สแกน, DOCX เสีย, Resume ไม่มีทักษะใน dictionary, ไทยปนอังกฤษ, ไม่มี source บริษัท, URL เปิดไม่ได้, FAQ หมดอายุ, ไม่มีคำตอบใน FAQ, Ollama ปิด, JSON ผิด schema, ข้อความ quote ปลอม, ไม่มี Piper voice, voice ไม่ตรงภาษา, STT ถอดผิด, mic ไม่ได้รับอนุญาต

## ก่อนนำเสนอ
ปรับข้อความ Initial Results ในสไลด์ตามสิ่งที่ทีมรันจริงบนเครื่องตัวเอง ถ้ายังมีเฉพาะข้อมูลสมมติ ให้ระบุชัดว่าเป็น preliminary synthetic smoke test และรายงานข้อจำกัด
