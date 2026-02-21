# 🎯 AI-Powered Smart Attendance System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A production-ready, AI-driven attendance system using real-time face recognition and a RAG-powered chatbot — built for universities and organisations where a single admin operates the system and students are tracked passively by camera.**

[Features](#-features) • [Architecture](#-architecture) • [Project Structure](#-project-structure) • [Getting Started](#-getting-started) • [API Docs](#-api-documentation) • [Tech Stack](#-tech-stack)

</div>

---

## 🏢 Project Context

> Developed under the **Digital Egypt Pioneers Initiative (DEPI)** — Managed by **EYouth** — Supervised by **Eng. Alaa Samir**

### 👥 Team Members

| Name |
|------|
| Abdelrahman Elsayed Elshhawy |
| Mohamed Khairy Eid Elzeblawy |
| Rouaa Sameh Elbadrawy |
| Farida Abdelhalim Mohamed Abdelaal |
| Wasim Ebada Mohamed Abouajaga |
| Mostafa Abdelsadek Mohamed Zayed |

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 👁️ **Face Recognition** | Real-time student identification using ArcFace 512-dim embeddings |
| 🛡️ **Anti-Spoofing** | Liveness detection to prevent photo/video attacks |
| 🤖 **RAG Chatbot** | Admin asks questions in Arabic or English — powered by LLaMA 3 + live PostgreSQL context |
| 📊 **Smart Reports** | Export attendance reports as PDF or Excel |
| 🔑 **Admin-Only Auth** | Single admin account — JWT for browser sessions, static API key for the camera kiosk |
| 🔔 **Notifications** | Automated email alerts to admin for late arrivals |
| 🔐 **JWT Security** | Secure token-based authentication with refresh tokens |
| 🐳 **Dockerized** | One command to run the entire stack |

---
## 📁 Project Structure

```
AI-Powered-Smart-Attendance-System/
│
├── src/
│   ├── api/v1/endpoints/
│   │   ├── auth.py              # Login, logout, token refresh
│   │   ├── attendance.py        # Mark (kiosk key), view, query attendance
│   │   ├── students.py          # Student CRUD + face registration
│   │   ├── reports.py           # PDF / Excel export
│   │   └── chat.py              # Admin chatbot endpoint
│   │
│   ├── services/
│   │   ├── attendance_service.py
│   │   ├── student_service.py
│   │   ├── report_service.py
│   │   ├── notification_service.py
│   │   └── export_service.py
│   │
│   ├── ai/
│   │   ├── detector.py          # RetinaFace — face detection
│   │   ├── embedder.py          # ArcFace (buffalo_l) — 512-dim embedding
│   │   ├── anti_spoofing.py     # Silent Face — liveness detection
│   │   └── recognition_pipeline.py
│   │
│   ├── llm/
│   │   ├── rag_pipeline.py
│   │   ├── context_builder.py
│   │   └── prompts.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── vector_index.py      # FAISS management
│   │   └── security.py          # JWT + bcrypt + get_current_admin() + verify_kiosk_key()
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── admin.py             # The only login account type
│   │   ├── organization.py      # Groups students by faculty / class
│   │   ├── student.py           # No user_id, no password — data record only
│   │   └── attendance.py        # One record per student per day
│   │
│   ├── schemas/                 # Pydantic schemas
│   ├── db/                      # Session + repositories
│   └── main.py
│
├── view/
│   ├── app.py
│   └── pages/
│       ├── dashboard.py
│       ├── students.py
│       ├── camera.py
│       ├── reports.py
│       └── chatbot.py
│
├── scripts/
│   └── create_admin.py          # CLI — creates the first admin (no public signup endpoint)
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
├── migrations/                  # Alembic
├── requirements.txt
├── .env.example
└── README.md
```

## 🏛️ Architecture

### High-Level System Architecture

```
┌──────────────────────────────────────────────────┐
│                  CLIENT LAYER                    │
│                                                  │
│         Streamlit Frontend (5 Pages)             │
│  Dashboard │ Students │ Camera │ Reports │ Chat  │
│                                                  │
│              Admin browser only                  │
└──────────┬───────────────────────────┬───────────┘
           │ JWT (admin pages)         │ X-API-Key (camera kiosk)
           ▼                           ▼
┌──────────────────────────────────────────────────┐
│              API LAYER  (FastAPI)                │
│                                                  │
│   /auth   /attendance   /students   /reports     │
│                   /chat                          │
│                                                  │
│   Admin endpoints  → verify JWT                  │
│   Camera endpoint  → verify kiosk API key        │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│          BUSINESS LOGIC LAYER (Services)         │
│                                                  │
│  AttendanceService │ StudentService              │
│  ReportService     │ NotificationService         │
│  ExportService                                   │
└────────┬──────────────────────────┬──────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌──────────────────────────┐
│   AI PIPELINE   │      │      LLM / RAG PIPELINE  │
│                 │      │                          │
│  1. RetinaFace  │      │  Question                │
│     (Detect)    │      │     → Context Builder    │
│                 │      │     → Prompt Builder     │
│  2. Anti-Spoof  │      │     → LLM Inference      │
│   (Liveness)    │      │     → Answer to Admin    │
│                 │      │                          │
│  3. ArcFace     │      │  (LLaMA 3 via Groq)      │
│    (Embed)      │      └─────────────┬────────────┘
│                 │                    │
│  4. FAISS       │                    │
│   (Search)      │                    │
└────────┬────────┘                    │
         │                             │
         └──────────────┬──────────────┘
                        ▼
┌──────────────────────────────────────────────────┐
│                  DATA LAYER                      │
│                                                  │
│   PostgreSQL DB          FAISS Vector Index      │
│   ─────────────          ────────────────────    │
│   admins                 face_embeddings         │
│   organizations          (512-dim vectors,       │
│   students               keyed by student_id)   │
│   attendance             sub-second search       │
│                                                  │
│   4 tables only — no users/roles/employees       │
│                                                  │
│          Repository Layer (Data Access)          │
└──────────────────────────────────────────────────┘
```

> **Note:** Both the AI Pipeline and LLM/RAG Pipeline sit at the same Business Logic level.
> They are independent components — both read from the Data Layer but serve different purposes:
> - **AI Pipeline** → identifies *who* is present via face matching
> - **LLM Pipeline** → answers *questions* about attendance data in natural language

### Request Lifecycle — Mark Attendance

```
Camera Frame (Streamlit camera page or physical kiosk)
        │
        ▼
POST /api/v1/attendance/mark
  Header: X-API-Key: <KIOSK_API_KEY>    ← static key, not a JWT
        │
        ▼
verify_kiosk_key()
        │
        ├─── ❌ Unauthorized ──────────────────────► 401
        │
        ▼
AttendanceService.mark(image)
        │
        ├──► 1. FaceDetector.detect()       → bounding box
        ├──► 2. AntiSpoofing.is_real_face() → ❌ 400 if spoof
        ├──► 3. FaceEmbedder.embed()        → 512-dim vector
        ├──► 4. VectorIndex.search()        → (student_id, confidence)
        ├──► 5. confidence < threshold?     → ❌ 404 FaceNotFound
        ├──► 6. check_duplicate(today)?     → ✅ 200 already_marked (no duplicate)
        ├──► 7. AttendanceRepository.create()
        ├──► 8. is_late()? → NotificationService.send_alert()
        │
        └──► ✅ 200 OK: { student_name, status, confidence, timestamp }
```

---

### Role & Permission Matrix

```
┌──────────────────────────────────────────────────────┐
│               AUTHENTICATION MODEL                   │
├──────────────────┬─────────────────┬─────────────────┤
│  Caller          │  Credential     │  Access         │
├──────────────────┼─────────────────┼─────────────────┤
│ Admin (browser)  │  JWT token      │  All endpoints  │
│                  │  (30 min)       │  except /mark   │
├──────────────────┼─────────────────┼─────────────────┤
│ Camera kiosk     │  X-API-Key      │  /attendance/   │
│ (machine)        │  (static)       │  mark only      │
├──────────────────┼─────────────────┼─────────────────┤
│ Student          │  — none —       │  Nothing.       │
│                  │                 │  Not a user.    │
└──────────────────┴─────────────────┴─────────────────┘

Admin can do everything:
  ✅ Register students (form + face photos)
  ✅ Delete students (cascades to FAISS)
  ✅ View all attendance records
  ✅ Generate and export PDF / Excel reports
  ✅ Use the AI chatbot (Arabic / English)
  ✅ Manage organisations
```

# 1️⃣ Client Layer (Streamlit Frontend)

Responsible for:

Capturing camera frames

Uploading registration photos for face enrollment

Displaying attendance status

Viewing reports

Interacting with AI chatbot

This layer never directly communicates with the database or AI models.
It only communicates with the API layer.


# 2️⃣ API Layer (FastAPI)

Acts as the gateway of the system.

Responsibilities:

Request validation

JWT verification (all admin endpoints)

Kiosk API key verification (attendance marking endpoint)

Routing requests to business services

Endpoints include:

/auth

/attendance

/students

/reports

/chat

Swagger documentation is automatically available at:

http://localhost:8000/docs


# 3️⃣ Business Logic Layer (Services)

This is the brain of the application.

It orchestrates:

AI Pipeline

Database operations

FAISS index

Notification services

LLM pipeline

Examples:

AttendanceService:

Detect face

Check liveness

Generate embedding

Search FAISS

Check for duplicate record today

Validate confidence threshold

Store attendance record

Trigger late notification

StudentService:

Create DB record first (to get the auto-generated student_id)

Enroll face photos in FAISS using that student_id

Roll back DB record if FAISS enrollment fails

# 4️⃣ AI Pipeline

Steps executed during attendance:

Image → Detect Face → Check Liveness → Extract Embedding → Search FAISS → Identify Student

The embedding is a 512-dimensional numerical vector generated by ArcFace (buffalo_l), normalised to unit length before storage and search.

FAISS performs nearest-neighbor similarity search using IndexFlatL2.

# 5️⃣ LLM / RAG Pipeline

This module handles intelligent queries from the admin.

Steps:

Question → Detect Intent → Query PostgreSQL → Format as plain text → Construct Prompt → LLM Inference → Structured Response

Supported intent types:

Absences — "من الغائبون اليوم؟" / "who was absent today?"

Late arrivals — "من تأخر؟" / "who arrived late?"

Attendance summary — "ما نسبة الحضور؟" / "what is the attendance rate?"

At-risk students — "من في خطر الرسوب؟" / "which students are at risk?"

Configured via environment variables.

# 6️⃣ Data Layer

Two independent storage systems:

PostgreSQL — 4 tables only:

Admins (the only login accounts — no roles, no employees, no student accounts)

Organizations

Students (no user_id, no password — purely a data record identified by face)

Attendance records

FAISS Vector Index:

Stores 512-dimension face embeddings keyed by student_id

Performs sub-second similarity search

The system follows strict data separation:

Images → NOT stored
Embeddings → Stored in FAISS (keyed by student_id)
Metadata → Stored in PostgreSQL

---


## 🔐 Security

- Admin passwords hashed with **bcrypt**
- **JWT** access + refresh tokens
- Camera kiosk authenticates with a static **API key** (`X-API-Key` header) — no JWT issued to machines
- No public signup endpoint — admin accounts created via a CLI script on the server
- Anti-spoofing on every attendance request
- Face embeddings stored as vectors — **no raw images saved**
- `.env` never committed (enforced by `.gitignore`)

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Face AI | OpenCV, RetinaFace, ArcFace (InsightFace buffalo_l) |
| Liveness | Silent Face Anti-Spoofing |
| Vector DB | FAISS |
| LLM / RAG | LLaMA 3 8B via Groq Free API |
| Auth | JWT (python-jose), bcrypt |
| Notifications | smtplib (Gmail SMTP) |
| Export | ReportLab (PDF), openpyxl (Excel) |
| DevOps | Docker, Docker Compose, GitHub Actions |
| Testing | pytest, httpx |

---

## 🗺️ Roadmap

- [ ] Core face recognition pipeline
- [ ] Admin-only authentication (JWT + kiosk API key)
- [ ] RAG-powered chatbot (Arabic + English)
- [ ] PDF & Excel export
- [ ] Docker deployment
- [ ] Real-time WebSocket attendance stream
- [ ] Multi-camera support
- [ ] Automatic daily absence marking (scheduled job)
- [ ] HR systems integration (SAP, Workday)

---

<div align="center">

⭐ **If this project helped you, please give it a star!** ⭐

</div>