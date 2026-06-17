# 🧠 NeuroNest — AI-Powered Reflective Journal

An AI-powered emotional journaling platform that helps you track moods, write daily reflections, and gain AI-generated emotional insights.

![Tech Stack](https://img.shields.io/badge/React-TypeScript-blue) ![Backend](https://img.shields.io/badge/FastAPI-Python-green) ![Database](https://img.shields.io/badge/MongoDB-Atlas-darkgreen) ![AI](https://img.shields.io/badge/OpenRouter-AI-purple)

---

## ✨ Features

- **📝 Journal Management** — Create, edit, delete, search, and filter journal entries by mood
- **🧠 AI Reflections** — Generate emotional summaries using OpenRouter AI (nvidia/nemotron-3-super-120b-a12b)
- **📊 Mood Tracking** — Visualize mood distribution and trends across your entries
- **📅 Timeline View** — Chronological feed merging journal entries and AI reflections
- **🔒 AES-256-GCM Encryption** — All sensitive data encrypted at rest with HKDF-SHA256 key derivation
- **🎨 Premium Dark UI** — Glassmorphism design with smooth Framer Motion animations

---

## 🏗️ Architecture

```
NeuroNest/
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Config & security
│   │   ├── database/ # MongoDB connection
│   │   ├── models/   # Data models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── utils/    # Helpers
│   └── main.py
│
├── frontend/         # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API layer
│   │   ├── hooks/       # Custom React hooks
│   │   ├── types/       # TypeScript interfaces
│   │   ├── context/     # React Context
│   │   └── routes/      # Router config
│   └── index.html
│
└── README.md
```

### Design Principles
- **Clean Architecture** — Separation of concerns across layers
- **SOLID Principles** — Single responsibility, dependency injection
- **Repository Pattern** — Database access abstracted behind services
- **Type Safety** — Full TypeScript (frontend) + Pydantic (backend)

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **Python** 3.10+ ([download](https://www.python.org/downloads/))
- **MongoDB Atlas** account ([free tier](https://www.mongodb.com/cloud/atlas))
- **OpenRouter** API key ([free](https://openrouter.ai/keys))

### 1. Clone & Configure

```bash
# Navigate to the project
cd Hackathon

# Create backend environment file
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values:

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/neuronest?retryWrites=true&w=majority
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
ENCRYPTION_MASTER_KEY=<generate-below>
FRONTEND_URL=http://localhost:5173
```

**Generate encryption key:**
```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### 2. Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### 3. Start Frontend

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## 📡 API Endpoints

### Journal

| Method | Endpoint              | Description                |
|--------|-----------------------|----------------------------|
| POST   | `/api/journal`        | Create journal entry       |
| GET    | `/api/journal`        | List entries (search, filter, paginate) |
| GET    | `/api/journal/{id}`   | Get single entry           |
| PUT    | `/api/journal/{id}`   | Update entry               |
| DELETE | `/api/journal/{id}`   | Delete entry               |

### Reflections

| Method | Endpoint                    | Description            |
|--------|-----------------------------|------------------------|
| POST   | `/api/reflections/generate` | Generate AI reflection |
| GET    | `/api/reflections`          | List reflections       |
| DELETE | `/api/reflections/{id}`     | Delete reflection      |

### System

| Method | Endpoint   | Description |
|--------|------------|-------------|
| GET    | `/`        | API info    |
| GET    | `/health`  | Health check|

---

## 🔒 Security

- **AES-256-GCM** encryption for all sensitive fields (title, content, mood, AI summaries)
- **HKDF-SHA256** key derivation with per-field random salt
- **12-byte secure IV** generation for each encryption operation
- Fields stored as Base64-encoded ciphertext in MongoDB
- Master key loaded from environment variable (never committed)

---

## 🎨 UI Design

- **Dark glassmorphism** theme with backdrop blur effects
- **Framer Motion** animations (page transitions, card reveals, micro-interactions)
- **Responsive design** — mobile-first with collapsible sidebar
- **Mood visualization** — emoji-coded badges and color-coded bar charts
- **Skeleton loading** states for all data-fetching views
- **Toast notifications** for success/error feedback

---

## 🛠️ Tech Stack

| Layer     | Technology                     |
|-----------|--------------------------------|
| Frontend  | React 19, TypeScript, Vite     |
| Styling   | Tailwind CSS v4                |
| Animations| Framer Motion                  |
| Forms     | React Hook Form + Zod          |
| HTTP      | Axios                          |
| Backend   | FastAPI, Python                |
| Validation| Pydantic v2                    |
| Database  | MongoDB Atlas (Motor driver)   |
| AI        | OpenRouter (nvidia/nemotron)   |
| Encryption| cryptography (AES-256-GCM)     |

---

## 📄 License

This project is for educational/hackathon purposes.
