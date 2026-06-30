# STORY-BC-04: Test Broadcast

**Status:** Backlog | **ClickUp:** [ACE-2297](https://app.clickup.com/t/86d32cdk3) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb)

## User Story

**AS** Admin/Supervisor
**I WANT TO** ส่ง test broadcast ไปให้ตัวเองหรือสมาชิกทีม
**SO THAT** สามารถตรวจสอบ message appearance ก่อนส่งไปให้ลูกค้า

## Description

Admin/Supervisor สามารถส่ง test broadcast ก่อน send จริง เพื่อตรวจสอบ message appearance โดย test message จะไม่นับ quota และไม่บันทึกใน broadcast history

## Acceptance Criteria

### AC1: Admin สามารถเลือก test recipients
**GIVEN** Admin กำลังตั้งค่า broadcast
**WHEN** กด "Send Test"
**THEN** ระบบแสดง test recipients selector
AND แสดงรายชื่อตัวเองและสมาชิกทีมทั้งหมดที่มี LINE connection
AND อนุญาตให้เลือกได้ไม่เกิน 5 คน

**WHEN** ไม่มีสมาชิกคนไหนมี LINE connection เลย
**THEN** แสดง empty state ใน selector: "ไม่มีสมาชิกที่เชื่อมต่อ LINE"
AND ปุ่ม confirm ส่ง test เป็น disabled

### AC1.1: Validation เมื่อไม่ได้เลือก recipient
**GIVEN** Admin เปิด test recipients selector
**WHEN** Admin ยังไม่ได้เลือกใคร → ปุ่ม confirm เป็น disabled

### AC2: Test message ส่งสำเร็จ
**GIVEN** Admin เลือก test recipients
**WHEN** กด confirm ส่ง test
**THEN** แสดง loading state: "กำลังส่ง test..."

| Case | Condition | Toast | Duration |
|---|---|---|---|
| ส่งสำเร็จทั้งหมด | ส่งไปยัง 3 คนสำเร็จ | "Test sent to 3 recipients" | 3 วินาที |
| ส่งสำเร็จบางส่วน | ส่งไปยัง 3 คน แต่ 1 คนล้มเหลว | "Test sent to 2 recipients, 1 failed" | 4 วินาที |
| ส่งไม่สำเร็จ | API ล้มเหลว | "Test send failed - unknown issue occurs" | 3 วินาที |

### AC3: Test message รองรับ full features
**GIVEN** message มี text และ/หรือ image
**WHEN** ส่ง test
**THEN** recipients ได้รับ message ตามที่ตั้งค่า AND features ทั้งหมด render ถูกต้องใน LINE

### AC4: Test recipients ต้องมี LINE connection
**GIVEN** สมาชิกทีมที่ไม่มี LINE connection
**WHEN** ระบบแสดง test recipients selector → จะไม่มีในลิสนั้น
