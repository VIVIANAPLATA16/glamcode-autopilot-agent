# 🤖 GlamCode Autopilot Agent
> **Autonomous AI agent for business automation, built with Qwen Cloud**

[![Deploy](https://img.shields.io/badge/deploy-alibaba%20cloud-orange)]()
[![Backend](https://img.shields.io/badge/backend-flask-black)]()
[![Frontend](https://img.shields.io/badge/frontend-next.js%2016-black)]()
[![LLM](https://img.shields.io/badge/llm-qwen--plus-purple)]()

Submitted to the **Qwen Cloud Global AI Hackathon**, Track 4: Autopilot Agent.

## 🌐 Live demo
The backend runs on an Alibaba Cloud ECS instance (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for proof of deployment). There is no public frontend URL yet  the agent is demonstrated via the demo video and the local frontend.

## 🧠 What is GlamCode Autopilot Agent?

GlamCode Autopilot Agent is an autonomous AI agent that runs the day-to-day customer interaction for a service business end to end — answering WhatsApp-style messages, booking appointments, quoting services, and proactively following up with clients without a human writing every reply.

Unlike a simple chatbot that only reacts to messages, the agent also runs **proactive jobs** (reaching out to clients who haven't visited in a while) and routes anything it isn't confident about to a **human review queue** instead of guessing, so a person approves or discards the action before it reaches the client.

## 🎯 Problem it solves

Small service businesses (salons, studios, clinics, and similar appointment-based businesses) typically handle booking manually over WhatsApp:

- ❌ **Slow** — every booking requires a person to read, check availability, and reply.
- ❌ **Inconsistent** — availability and service details are answered from memory, not validated against real data.
- ❌ **Reactive only** — no one follows up with clients who've gone quiet.
- ❌ **All-or-nothing automation** — most automation tools either need constant supervision or are too rigid to trust with real conversations.

GlamCode Autopilot Agent automates the conversation and the follow-up, while keeping a human in the loop for anything it isn't sure about.

## ✨ Features

### 💬 Conversational booking agent
- Understands customer messages and maps them to real services and available time slots (**strict matching** it won't invent a slot or service that doesn't exist).
- Keeps **conversation memory** across turns, so the client doesn't have to repeat context.
- Books, checks, and manages appointments directly against the database.

### 🔁 Proactive follow-up
- Scheduled job that finds clients who haven't visited in a configurable number of days (`DIAS_INACTIVIDAD`) and reaches out to re-engage them, instead of waiting for them to message first.

### 🛡️ Human review queue
- Any conversation or action the agent isn't confident about is escalated with a priority and status instead of being auto-resolved.
- A reviewer can **approve** or **discard** each escalated item from the frontend dashboard.

### 🖥️ Frontend dashboard
- Chat simulator to test the agent's conversation flow.
- Proactive outreach view.
- Human review dashboard to approve/discard escalated cases.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                   CLIENT                     │
│           (WhatsApp-style messages)          │
└───────────────────┬───────────────────────────┘
                    │
┌───────────────────▼───────────────────────────┐
│            Next.js 16 frontend                │
│   /  /proactivo  /revision  (chat simulator,   │
│    proactive view, human review dashboard)    │
└───────────────────┬───────────────────────────┘
                    │  REST API
┌───────────────────▼───────────────────────────┐
│           Flask backend (demo_app.py)          │
│         hosted on Alibaba Cloud ECS            │
│                                                │
│  agente_reservas.py   → booking agent          │
│  revision_humana.py   → escalation + storage   │
└──────────┬─────────────────────┬───────────────┘
          │                     │
┌─────────▼────────┐   ┌────────▼──────────┐
│    Qwen Cloud     │   │      SQLite        │
│  (qwen-plus, via  │   │  conversations,     │
│  OpenAI-compatible│   │  appointments,       │
│  API)             │   │  human review queue  │
└───────────────────┘   └─────────────────────┘
```

## 🛠️ Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js 16, React 19 | App Router, UI |
| Styling | Tailwind CSS v4 | Design system |
| UI components | shadcn, lucide-react | Chat simulator, dashboards |
| Backend | Flask (Python) | REST API |
| LLM | Qwen Cloud (`qwen-plus`), via OpenAI-compatible API | Conversation understanding + generation |
| Database | SQLite | Conversations, appointments, review queue |
| Hosting (backend) | Alibaba Cloud ECS | API + agent runtime |
| Analytics | Vercel Analytics | Frontend usage |

## ⚙️ Installation and setup

### Prerequisites
- Python 3.10+
- Node.js 22+
- A Qwen Cloud API key ([Alibaba Cloud DashScope](https://dashscope-intl.aliyuncs.com))

### 1. Clone the repository
```bash
git clone https://github.com/VIVIANAPLATA16/glamcode-autopilot-agent.git
cd glamcode-autopilot-agent
```

### 2. Backend setup
```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):
```
# Qwen Cloud API (OpenAI-compatible)
QWEN_API_KEY=your_api_key_here
QWEN_API_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# Proactive job: days without visit to consider a client inactive
DIAS_INACTIVIDAD=30
```

Run the backend:
```bash
python demo_app.py
```

### 3. Frontend setup
```bash
cd frontend
npm install
npm run dev
```

The frontend calls the backend API URL configured in `frontend/lib/api.ts` / `.env.local` (not committed).

## 🔌 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/simular-mensaje` | Send a message to the agent and get its response |
| POST | `/api/ejecutar-seguimiento-proactivo` | Trigger the proactive follow-up job |
| GET | `/api/revision-humana` | List items pending human review |
| POST | `/api/revision-humana/<id>/aprobar` | Approve an escalated item |
| POST | `/api/revision-humana/<id>/descartar` | Discard an escalated item |

## 📊 Database schema

```sql
-- Items escalated for human approval
CREATE TABLE revision_humana (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo              TEXT NOT NULL,
  origen            TEXT NOT NULL,
  estado            TEXT NOT NULL DEFAULT 'pendiente',
  prioridad         TEXT NOT NULL DEFAULT 'normal',
  titulo            TEXT NOT NULL,
  descripcion       TEXT,
  mensaje_cliente   TEXT,
  mensaje_respuesta TEXT,
  metadata_json     TEXT
);

-- Conversation turns and the agent's resolution
CREATE TABLE conversaciones (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  mensaje_cliente   TEXT NOT NULL,
  intencion         TEXT,
  herramienta       TEXT,
  respuesta_agente  TEXT,
  escalado_revision INTEGER NOT NULL DEFAULT 0,
  revision_id       INTEGER,
  created_at        TEXT NOT NULL,
  FOREIGN KEY (revision_id) REFERENCES revision_humana(id)
);

-- Appointments booked by the agent
CREATE TABLE citas (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  cliente_nombre   TEXT,
  cliente_telefono TEXT,
  servicio_id      TEXT NOT NULL,
  fecha_hora       TEXT NOT NULL,
  estado           TEXT NOT NULL DEFAULT 'activa',
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL
);

-- Per-turn conversation memory
CREATE TABLE turnos_conversacion (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  conversacion_id  INTEGER NOT NULL,
  rol              TEXT NOT NULL,
  mensaje          TEXT NOT NULL,
  timestamp        TEXT NOT NULL,
  FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
);

CREATE INDEX idx_turnos_conversacion_id ON turnos_conversacion(conversacion_id, id);
```

## 📁 Project structure

```
glamcode-autopilot-agent/
├── backend/
│   ├── agente_reservas.py     # Booking agent: memory + strict matching
│   ├── demo_app.py            # Flask API entry point
│   ├── revision_humana.py     # Human review, storage, and DB schema
│   └── .env.example           # Required environment variables
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Chat simulator
│   │   ├── proactivo/         # Proactive follow-up view
│   │   └── revision/          # Human review dashboard
│   ├── components/            # Chat simulator, nav, UI primitives
│   └── lib/                   # API client and shared data
└── docs/
    ├── DEPLOYMENT.md          # Proof of Alibaba Cloud deployment
    └── architecture.png       # System architecture diagram
```

## 🚀 Deployment

The backend is deployed on an **Alibaba Cloud ECS** instance; the agent calls **Qwen Cloud** (`qwen-plus`) for its reasoning and reply generation. See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full proof of deployment.

## 🗺️ Roadmap

- [x] Conversational booking agent
- [x] Conversation memory
- [x] Strict service/availability matching
- [x] Proactive follow-up job
- [x] Human review queue (approve/discard)
- [x] Frontend connected to backend
- [x] Deployed on Alibaba Cloud ECS
- [ ] 3-minute demo video
- [ ] Devpost submission

## 📄 License

MIT © 2026 Viviana Plata

Built for the Qwen Cloud Global AI Hackathon, Track 4: Autopilot Agent.
