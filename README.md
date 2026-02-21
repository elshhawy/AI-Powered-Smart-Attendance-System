# 🎯 AI-Powered Smart Attendance System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A production-ready, AI-driven attendance system using real-time face recognition, RAG-powered chatbot, and role-based access control — built for schools, universities, and enterprises.**

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
| 👁️ **Face Recognition** | Real-time identification using ArcFace 512-dim embeddings |
| 🛡️ **Anti-Spoofing** | Liveness detection to prevent photo/video attacks |
| 🤖 **RAG Chatbot** | Ask questions in Arabic or English — powered by LLM + FAISS |
| 📊 **Smart Reports** | Export attendance reports as PDF or Excel |
| 👥 **Role-Based Access** | Admin, Teacher/Supervisor, Student/Employee roles |
| 🔔 **Notifications** | Automated email/SMS alerts for absences and late arrivals |
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
│   │   ├── attendance.py        # Mark, view, query attendance
│   │   ├── students.py          # Student CRUD + face registration
│   │   ├── employees.py         # Employee CRUD + face registration
│   │   ├── reports.py           # PDF / Excel export
│   │   └── chat.py              # LLM chatbot endpoint
│   │
│   ├── services/
│   │   ├── attendance_service.py
│   │   ├── auth_service.py
│   │   ├── report_service.py
│   │   ├── notification_service.py
│   │   └── export_service.py
│   │
│   ├── ai/
│   │   ├── detector.py          # RetinaFace / MTCNN
│   │   ├── embedder.py          # ArcFace / FaceNet
│   │   ├── anti_spoofing.py     # Liveness detection
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
│   │   ├── security.py          # JWT + bcrypt
│   │   └── permissions.py       # RBAC decorators
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic schemas
│   ├── db/                      # Session + repositories
│   └── main.py
│
├── view/
│   ├── streamlit_app.py
│   └── pages/
│       ├── 1_dashboard.py
│       ├── 2_register.py
│       ├── 3_attendance.py
│       └── 4_reports.py
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
│         Streamlit Frontend (4 Pages)             │
│   Dashboard │ Register │ Attendance │ Reports    │
└──────────────────────┬───────────────────────────┘
                       │ HTTP Requests
                       ▼
┌──────────────────────────────────────────────────┐
│              API LAYER  (FastAPI)                │
│                                                  │
│   /auth   /attendance   /students   /reports     │
│                   /chat                          │
│                                                  │
│         JWT Validation → Role Check              │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│          BUSINESS LOGIC LAYER (Services)         │
│                                                  │
│  AttendanceService │ AuthService │ ReportService │
│       NotificationService │ ExportService        │
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
│   (Liveness)    │      │     → Answer to User     │
│                 │      │                          │
│  3. ArcFace     │      │  (GPT / Claude / Local)  │
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
│   users                  face_embeddings         │
│   students               (512-dim vectors)       │
│   employees              sub-second search       │
│   attendance                                     │
│   roles                                          │
│   organizations                                  │
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
Camera Frame (Streamlit)
        │
        ▼
POST /api/v1/attendance/mark
        │
        ▼
JWT Validation + Role Check
        │
        ├─── ❌ Unauthorized ──────────────────► 401
        │
        ▼
AttendanceService.mark_attendance(image)
        │
        ├──► 1. FaceDetector.detect()       → bounding box
        ├──► 2. AntiSpoofing.is_real_face() → ❌ 400 if spoof
        ├──► 3. FaceEmbedder.embed()        → 512-dim vector
        ├──► 4. VectorIndex.search()        → (person_id, confidence)
        ├──► 5. confidence < threshold?     → ❌ 404 FaceNotFound
        ├──► 6. AttendanceRepository.create()
        ├──► 7. is_late()? → NotificationService.send_alert()
        │
        └──► ✅ 200 OK: { name, status, confidence, timestamp }
```

---

### Role & Permission Matrix

```
┌──────────────────────────────────────────────────────┐
│                  PERMISSION MATRIX                   │
├─────────────────────┬─────────┬──────────┬───────────┤
│       Action        │  Admin  │ Teacher  │  Student  │
├─────────────────────┼─────────┼──────────┼───────────┤
│ Register person     │   ✅   │   ✅     │    ❌     │
│ Delete person       │   ✅   │   ❌     │    ❌     │
│ Mark attendance     │   ✅   │   ✅     │    ✅     │
│ View all attendance │   ✅   │   ✅     │    ❌     │
│ View own attendance │   ✅   │   ✅     │    ✅     │
│ Generate reports    │   ✅   │   ✅     │    ❌     │
│ Export PDF / Excel  │   ✅   │   ✅     │    ❌     │
│ Use AI chatbot      │   ✅   │   ✅     │    ❌     │
│ Manage orgs / roles │   ✅   │   ❌     │    ❌     │
└─────────────────────┴─────────┴──────────┴───────────┘
```

# 1️⃣ Client Layer (Streamlit Frontend)

Responsible for:

Capturing camera frames

Uploading registration images

Displaying attendance status

Viewing reports

Interacting with AI chatbot

This layer never directly communicates with the database or AI models.
It only communicates with the API layer.


# 2️⃣ API Layer (FastAPI)

Acts as the gateway of the system.

Responsibilities:

Request validation

JWT verification

Role permission checking

Routing requests to business services

Endpoints include:

/auth

/attendance

/students

/employees

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

Validate confidence threshold

Store attendance record

Trigger late notification

# 4️⃣ AI Pipeline

Steps executed during attendance:

Image → Detect Face → Check Liveness → Extract Embedding → Search FAISS → Identify Person

The embedding is a 512-dimensional numerical vector generated by ArcFace.

FAISS performs nearest-neighbor similarity search using IndexFlatL2.

# 5️⃣ LLM / RAG Pipeline

This module handles intelligent queries.

Steps:

Question → Build Context from DB → Construct Prompt → LLM Inference → Structured Response

Supported Free & Open LLM Options:

LLaMA 3 (via Groq Free API)

Mistral 7B (via free API tier)

OpenRouter Free Tier Models

Ollama (Local LLaMA / Mistral – No API cost)

These options allow the system to run completely free in development mode or low-cost in production.

Configured via environment variables.

# 6️⃣ Data Layer

Two independent storage systems:

PostgreSQL:

Users

Roles

Students

Employees

Attendance records

Organizations

FAISS Vector Index:

Stores 512-dimension face embeddings

Performs sub-second similarity search

The system follows strict data separation:

Images → NOT stored
Embeddings → Stored in FAISS
Metadata → Stored in PostgreSQL
---


## 🔐 Security

- Passwords hashed with **bcrypt**
- **JWT** access + refresh tokens
- Role-based access control on every endpoint
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
| Face AI | OpenCV, RetinaFace, ArcFace |
| Vector DB | FAISS |
| LLM / RAG | LLaMA 3(via Groq Free API), Mistral 7B (via free API tier), OpenRouter Free Tier Models

Ollama (Local LLaMA / Mistral – No API cost)
| Auth | JWT (python-jose), bcrypt |
| Notifications | smtplib, Twilio |
| Export | ReportLab (PDF), openpyxl (Excel) |
| DevOps | Docker, Docker Compose, GitHub Actions |
| Testing | pytest, httpx |

---

## 🗺️ Roadmap

- [ ] Core face recognition pipeline
- [ ] Role-based access control
- [ ] RAG-powered chatbot
- [ ] PDF & Excel export
- [ ] Docker deployment
- [ ] Mobile app (React Native)
- [ ] Real-time WebSocket attendance stream
- [ ] Multi-camera support
- [ ] HR systems integration (SAP, Workday)

---

<div align="center">

⭐ **If this project helped you, please give it a star!** ⭐

</div>
