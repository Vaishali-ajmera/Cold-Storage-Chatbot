# 🥔 Cold Storage Advisory - Backend

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2.8-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.16.1-ff1709?style=for-the-badge&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.1.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

**An AI-powered advisory system for potato cold storage management**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Docs](#-api-documentation) • [Architecture](#-architecture)

</div>

---

## 📋 Overview

**Cold Storage Advisory (Alu Mitra)** is an intelligent advisory system designed to help Indian farmers and cold storage owners with potato storage planning, operations, and optimization. The system uses **Google Gemini AI** to provide contextual, multi-lingual advice on cold storage management.

### 🎯 Key Capabilities

- **🏗️ Build Planning** - Help users plan new cold storage facilities (capacity, design, ROI)
- **⚙️ Operations Optimization** - Advise existing cold storage owners on efficiency, temperature control, and quality maintenance
- **🌐 Multi-lingual Support** - Supports English, Hindi, Marathi, Gujarati, Bengali, and Punjabi
- **💬 Intelligent Chat** - Context-aware conversations with follow-up questions (MCQ-based)
- **📊 Admin Dashboard** - System configuration and usage analytics

---

## ✨ Features

### Authentication & User Management
- ✅ Email/Password Registration & Login
- ✅ SSO Integration (JWT-based external authentication)
- ✅ Password Reset via OTP (Email)
- ✅ User Preferences (language selection)
- ✅ JWT Token Authentication with Refresh

### Chat & Advisory System
- ✅ **Async Processing** - Questions processed via Celery for better UX
- ✅ **Intent Classification** - AI classifies questions into:
  - `ANSWER_DIRECTLY` - Technical potato storage questions
  - `NEEDS_FOLLOW_UP` - Generates MCQ for missing information
  - `META` - Questions about the assistant
  - `OUT_OF_CONTEXT` - Non-potato storage topics
- ✅ **Session Management** - Multiple chat sessions per user
- ✅ **Suggested Questions** - AI-generated follow-up suggestions
- ✅ **Daily Question Quota** - Configurable per-user limits

### Admin Features
- ✅ System Configuration (response tone, length, daily limits)
- ✅ Usage Statistics Dashboard
- ✅ Custom AI Instructions

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | Django 5.2.8 + Django REST Framework 3.16.1 |
| **Database** | PostgreSQL (prod) / SQLite (dev) |
| **Task Queue** | Celery 5.5.3 + Redis 7.1.0 |
| **AI/LLM** | Google Gemini 2.5 Flash |
| **Authentication** | JWT (SimpleJWT) |
| **API Docs** | Swagger/OpenAPI (drf-yasg) |
| **Email** | SMTP (Gmail compatible) |


---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Redis Server
- PostgreSQL (for production)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cold_storage_advisory-be
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:


### 5. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Start Redis Server

```bash
# Linux/Mac
redis-server

# Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:alpine
```

### 7. Start Celery Worker

```bash
celery -A advisory worker -l info
```

### 8. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI:** `http://localhost:8000/swagger/`
- **ReDoc:** `http://localhost:8000/redoc/`

### Comprehensive Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference including:
- All 22 endpoints with request/response formats
- Authentication flows
- Error handling
- Enums and constants

### Quick API Reference

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Auth** | `/signup/` | POST | User registration |
| **Auth** | `/login/` | POST | Email login |
| **Auth** | `/token/refresh/` | POST | Refresh JWT token |
| **Auth** | `/sso/verify-token/` | POST | SSO authentication |
| **User** | `/user/profile/` | GET/POST | Get/Update profile |
| **Intake** | `/intake/` | POST | Submit intake form |
| **Chat** | `/sessions/create/` | POST | Create chat session |
| **Chat** | `/sessions/` | GET | List sessions |
| **Chat** | `/ask/` | POST | Ask question (async) |
| **Chat** | `/mcq-response/` | POST | Answer MCQ (async) |
| **Chat** | `/task/<id>/status/` | GET | Poll task status |
| **Chat** | `/history/<id>/` | GET | Get chat history |
| **Admin** | `/settings/config/` | GET/POST | System configuration |
| **Admin** | `/settings/stats/` | GET | Usage statistics |

---
