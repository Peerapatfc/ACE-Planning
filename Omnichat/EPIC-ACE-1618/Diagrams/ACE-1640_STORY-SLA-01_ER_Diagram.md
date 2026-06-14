# STORY-SLA-01: SLA Configuration UI — ER Diagram

**Story:** ACE-1640 — SLA Configuration UI
**Parent Epic:** ACE-1618
**ClickUp Doc Page:** [ER STORY-SLA-01: SLA Configuration UI](https://app.clickup.com/25605274/v/dc/rdd4u-133996/rdd4u-82136)

> v2 is latest — `channel_sla_configs` uses `first_response_value + first_response_unit` instead of `first_response_minutes`

---

## version-1

```mermaid
erDiagram
    workspace_sla_configs["workspace_sla_configs (omnichat-service)"] {
        string id PK
        string tenant_id UK "UNIQUE — 1 config ต่อ workspace"
        boolean enabled "เปิด/ปิด SLA ทั้งระบบ (default: true)"
        int due_soon_minutes "เหลือเวลาน้อยกว่านี้ = due_soon (default: 30)"
        boolean bh_aware "นับเฉพาะ business hours (default: false)"
        datetime created_at
        datetime updated_at
    }

    channel_sla_configs["channel_sla_configs (omnichat-service)"] {
        string id PK
        string tenant_id FK
        string workspace_sla_config_id FK "FK → workspace_sla_configs"
        string channel_type "FACEBOOK | INSTAGRAM | LINE | SHOPEE | LAZADA | TIKTOK"
        boolean enabled "เปิด/ปิด SLA ของ channel นี้ อิสระจาก channel อื่น (default: true)"
        int first_response_minutes "เก็บเป็น minutes เสมอ — UI แปลงเป็น hours/min เอง"
        datetime created_at
        datetime updated_at
    }

    conversations["conversations (omnichat-service) — มีอยู่แล้ว"] {
        string id PK
        string tenant_id
        string channel_type
        datetime waiting_since_at "reset ทุกครั้งที่ลูกค้าทักใหม่หลัง agent ตอบ (null = agent ตอบแล้ว)"
        datetime sla_due_at "deadline ที่ต้องตอบ — คำนวณจาก waiting_since_at + first_response_minutes"
    }

    conversation_sla_events["conversation_sla_events (SLA-02)"] {
        string id PK
        string tenant_id
        string conversation_id FK
        string event_type "due_soon | overdue | resolved"
        datetime sla_cycle_start "= waiting_since_at ของ cycle นี้ — ใช้แยกว่าเป็น cycle ไหน"
        datetime created_at
    }

    workspace_sla_configs ||--o{ channel_sla_configs : "has (via workspace_sla_config_id)"
    channel_sla_configs ||--o{ conversations : "อ่าน config ตอนสร้าง conversation ใหม่ (SLA-02)"
    conversations ||--o{ conversation_sla_events : ""
```

---

## version-2 (latest)

> Key change: `first_response_minutes` → `first_response_value (int)` + `first_response_unit (MINUTES|HOURS)`

```mermaid
erDiagram
    workspace_sla_configs["workspace_sla_configs (omnichat-service)"] {
        string id PK
        string tenant_id UK "UNIQUE — 1 config ต่อ workspace"
        boolean enabled "เปิด/ปิด SLA ทั้งระบบ (default: true)"
        int due_soon_minutes "เหลือเวลาน้อยกว่านี้ = due_soon (default: 30)"
        boolean bh_aware "นับเฉพาะ business hours (default: false)"
        datetime created_at
        datetime updated_at
    }

    channel_sla_configs["channel_sla_configs (omnichat-service)"] {
        string id PK
        string tenant_id FK
        string workspace_sla_config_id FK "FK → workspace_sla_configs"
        string channel_type "FACEBOOK | INSTAGRAM | LINE | SHOPEE | LAZADA | TIKTOK"
        boolean enabled "เปิด/ปิด SLA ของ channel นี้ อิสระจาก channel อื่น (default: true)"
        string first_response_unit "MINUTES | HOURS"
        int first_response_value "ค่าตัวเลขเวลาที่ต้องตอบครั้งแรก — ใช้คู่กับ first_response_unit (เช่น value=2, unit=HOURS = 2 ชั่วโมง)"
        datetime created_at
        datetime updated_at
    }

    conversations["conversations (omnichat-service) — มีอยู่แล้ว"] {
        string id PK
        string tenant_id
        string channel_type
        datetime waiting_since_at "reset ทุกครั้งที่ลูกค้าทักใหม่หลัง agent ตอบ (null = agent ตอบแล้ว)"
        datetime sla_due_at "deadline ที่ต้องตอบ — คำนวณจาก waiting_since_at + first_response_minutes"
    }

    conversation_sla_events["conversation_sla_events (SLA-02)"] {
        string id PK
        string tenant_id
        string conversation_id FK
        string event_type "due_soon | overdue | resolved"
        datetime sla_cycle_start "= waiting_since_at ของ cycle นี้ — ใช้แยกว่าเป็น cycle ไหน"
        datetime created_at
    }

    workspace_sla_configs ||--o{ channel_sla_configs : "has (via workspace_sla_config_id)"
    channel_sla_configs ||--o{ conversations : "อ่าน config ตอนสร้าง conversation ใหม่ (SLA-02)"
    conversations ||--o{ conversation_sla_events : ""
```
