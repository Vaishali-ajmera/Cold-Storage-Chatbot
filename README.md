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

## 📁 Project Structure

```
cold_storage_advisory-be/
├── accounts/                 # User authentication & admin settings
│   ├── views.py             # Auth endpoints (signup, login, password reset)
│   ├── sso_views.py         # SSO authentication
│   ├── admin_views.py       # Admin configuration & stats
│   ├── models.py            # User, OTP, SystemConfiguration models
│   └── tasks.py             # Celery tasks for emails
│
├── chat/                     # Chat & session management
│   ├── views.py             # Chat endpoints (ask, mcq, history)
│   ├── models.py            # ChatSession, ChatMessage, DailyQuota
│   ├── services.py          # AI interaction logic
│   ├── tasks.py             # Celery tasks for question processing
│   ├── prompts.py           # LLM prompt construction
│   └── constants.py         # System prompts & message types
│
├── usecase_engine/           # Intake form management
│   ├── views.py             # Intake submission endpoint
│   ├── models.py            # UserInput model
│   └── utils.py             # Onboarding content generation
│
├── advisory/                 # Django project configuration
│   ├── settings/
│   │   ├── base.py          # Common settings
│   │   ├── local_settings.py # Development settings
│   │   └── prod_settings.py  # Production settings
│   ├── celery.py            # Celery configuration
│   └── urls.py              # URL routing
│
├── API_DOCUMENTATION.md      # Comprehensive API documentation
├── requirements.txt          # Python dependencies
└── manage.py
```

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

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=advisory.settings.local_settings

# Database (PostgreSQL for production)
DATABASE_URL=postgres://user:password@localhost:5432/cold_storage_db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis & Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# SSO Configuration
SSO_SECRET_KEY=your-sso-secret-key
SSO_EMAIL_DOMAIN=sso.your-domain.com
```

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

## 🏗️ Architecture

### Request Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Django    │────▶│   Celery    │────▶│   Gemini    │
│             │     │   REST API  │     │   Worker    │     │   AI        │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  PostgreSQL │     │    Redis    │
                    │  Database   │     │   Broker    │
                    └─────────────┘     └─────────────┘
```

### Async Question Processing

1. User submits question via `/ask/`
2. Django validates and queues Celery task
3. Returns `task_id` immediately (202 Accepted)
4. Celery worker processes question:
   - Classifies intent using Gemini
   - Generates response or MCQ
   - Saves to database
5. Frontend polls `/task/<id>/status/` for result

### AI Classification Types

| Classification | Description | Action |
|----------------|-------------|--------|
| `ANSWER_DIRECTLY` | Technical potato storage question | Generate detailed answer |
| `NEEDS_FOLLOW_UP` | Missing critical information | Generate MCQ |
| `META` | Question about the assistant | Short self-introduction |
| `OUT_OF_CONTEXT` | Non-potato storage topic | Polite redirect |

---

## 🌐 Supported Languages

| Code | Language | Native Name |
|------|----------|-------------|
| `en` | English | English |
| `hi` | Hindi | हिन्दी |
| `mr` | Marathi | मराठी |
| `gu` | Gujarati | ગુજરાતી |
| `bn` | Bengali | বাংলা |
| `pa` | Punjabi | ਪੰਜਾਬੀ |

---

## 🔧 Configuration

### System Configuration (Admin)

| Setting | Default | Description |
|---------|---------|-------------|
| `response_tone` | `friendly` | AI response tone (friendly/professional/formal/casual) |
| `response_length` | `moderate` | Response verbosity (concise/moderate/detailed) |
| `max_daily_questions` | `10` | Per-user daily question limit |
| `additional_context` | `` | Extra context for AI |
| `custom_instructions` | `` | Custom AI behavior instructions |

### JWT Token Settings

| Setting | Value |
|---------|-------|
| Access Token Lifetime | 7 days |
| Refresh Token Lifetime | 7 days |
| Auth Header Type | Bearer |

---

## 🧪 Development

### Running Tests

```bash
python manage.py test
```

### Code Formatting

```bash
# Using Black
black .

# Using isort
isort .
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

---

## 📦 Deployment

### Environment Variables (Production)

```env
DJANGO_SETTINGS_MODULE=advisory.settings.prod_settings
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
DATABASE_URL=postgres://user:password@db-host:5432/cold_storage_db
CELERY_BROKER_URL=redis://redis-host:6379/0
```

### Using Docker (Recommended)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Using Gunicorn

```bash
gunicorn advisory.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

For support, please contact the development team or open an issue in the repository.

---

<div align="center">

**Built with ❤️ for Indian Farmers**

</div>
