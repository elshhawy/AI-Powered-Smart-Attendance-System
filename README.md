# 🎓 AI-Powered Smart Attendance System

🚀 An intelligent attendance automation platform powered by Computer Vision, Machine Learning, and LLM-based academic analytics.

Developed under the **Digital Egypt Pioneers Initiative (DEPI)**  
Managed by **EYouth**  
Supervised by **Eng. Alaa Samir**

---

## 👥 Team

- Abdelrahman El-Sayed El-Shahawy  
- Mohamed Khairy Eid Elzeblawy  
- Rouaa Sameh Elbadrawy  
- Farida Abdelhalim Mohamed Abdelaal  
- Wasim Ebada Mohamed Abouajaga  
- Mostafa Abdel-Sadek Mohamed Zayed 

---

# 📌 Overview

This system automates student attendance using real-time face recognition and transforms attendance records into actionable academic insights using predictive analytics and AI-generated reports.

It eliminates manual processes, prevents proxy attendance, and enables data-driven academic decision-making.

---

# ⚙️ Core Features

### 🟢 Smart Face Recognition
- Real-time face detection (RetinaFace)
- Face embedding extraction (ArcFace)
- Cosine similarity identity matching
- Automatic attendance logging
- Duplicate prevention

### 🟡 Academic Analytics
- Attendance percentage tracking
- Consecutive absence monitoring
- Student ranking system
- Risk prediction (Random Forest)
- Trend visualization

### 🔴 AI Academic Assistant
- Natural language queries
- Automated warning letter generation
- Department performance reports
- RAG-powered policy integration

---

# 🏗 Architecture
```bash
Camera
↓
Face Detection
↓
Face Embedding
↓
Similarity Matching
↓
PostgreSQL Database
↓
Analytics Engine
↓
LLM Report Generator
↓
Dashboard

```
---

# 🛠 Tech Stack

**Computer Vision:** OpenCV, InsightFace (RetinaFace + ArcFace)  
**Backend:** FastAPI  
**Database:** PostgreSQL, FAISS  
**Machine Learning:** Scikit-learn, Pandas, NumPy  
**LLM & NLP:** SentenceTransformers, RAG, OpenAI/Mistral  
**Frontend:** Streamlit / React  
**Deployment:** Docker  

---

# 📊 Key Outcomes

✔ ≥95% face recognition accuracy  
✔ Automated attendance workflow  
✔ Early detection of at-risk students  
✔ AI-generated academic reports  
✔ Modular & scalable architecture  

---

## 📂 Project Structure

```bash
AI-Smart-Attendance-System/
│
├── backend/
│   ├── api/
│   │   ├── attendance.py
│   │   ├── students.py
│   │   └── analytics.py
│   │
│   ├── services/
│   │   ├── attendance_service.py
│   │   ├── analytics_service.py
│   │   └── llm_service.py
│   │
│   ├── models/
│   │   ├── student_model.py
│   │   ├── attendance_model.py
│   │   └── risk_model.py
│   │
│   ├── database.py
│   ├── config.py
│   └── main.py
│
├── face_recognition/
│   ├── detector.py
│   ├── embedder.py
│   └── matcher.py
│
├── llm_module/
│   ├── rag_pipeline.py
│   ├── vector_store.py
│   └── prompts.py
│
├── frontend/
│   └── streamlit_app.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── .env
└── README.md
```
---

# 🔐 Security

- Embeddings stored instead of raw images  
- Role-based access control  
- Encrypted database storage  

---

# 🌟 Vision

Transform traditional attendance systems into intelligent academic intelligence platforms by combining Vision AI, Predictive Modeling, and Large Language Models in one unified system.

---

📌 Developed for professional smart attendance management, leveraging AI-driven face recognition, analytics, and automated reporting to streamline operations and enhance efficiency.

