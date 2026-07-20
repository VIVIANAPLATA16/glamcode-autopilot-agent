# Proof of Alibaba Cloud Deployment

This document demonstrates that the GlamCode Autopilot Agent backend is deployed and running on **Alibaba Cloud**, as required by the hackathon submission guidelines.

## Deployment summary

| Item | Value |
|---|---|
| Cloud provider | Alibaba Cloud |
| Service used | Elastic Compute Service (ECS) |
| Component deployed | Flask backend (`backend/demo_app.py`) |
| Public endpoint | `http://47.251.39.38:5000` |
| Health check | `http://47.251.39.38:5000/api/health` |
| Debug mode | Disabled (`FLASK_DEBUG` unset, defaults to off) |
| Persistence | SQLite database on the ECS instance disk |
| LLM provider | Qwen Cloud (`qwen-plus`, called from the backend) |

> Note: this is a hackathon demo endpoint, kept open for judge verification. It may be taken down or firewalled after judging.

## How the deployment works

1. The Flask backend (`backend/demo_app.py`, `backend/agente_reservas.py`, `backend/revision_humana.py`) runs on an Alibaba Cloud ECS instance, listening on `0.0.0.0:5000`.
2. The port is open in the instance's Security Group, so the API is reachable directly from the public internet at `http://47.251.39.38:5000`.
3. The Next.js frontend calls this backend via `NEXT_PUBLIC_API_URL` (set in `frontend/.env.local`, not committed to the repo).
4. Incoming customer messages are processed by the booking agent, which calls **Qwen Cloud** (`qwen-plus`, via the OpenAI-compatible API) for natural-language understanding and response generation.
5. Bookings, conversations, and the human review queue are persisted to a local **SQLite** database on the ECS instance.
6. Cases the agent is not confident about are routed to the human review flow (`revision_humana.py`) instead of being auto-resolved.

## Verifying the deployment

From any machine with internet access:

```bash
curl http://47.251.39.38:5000/api/health
```

Expected response:
```json
{"ok":true,"service":"glamcode-autopilot-agent","status":"ok"}
```

## Evidence

- Backend code that runs on the ECS instance: [`backend/demo_app.py`](../backend/demo_app.py), [`backend/agente_reservas.py`](../backend/agente_reservas.py), [`backend/revision_humana.py`](../backend/revision_humana.py).
- Architecture diagram: [`docs/architecture.png`](architecture.png).
- Live health check above, callable by anyone (judges included).

## Reproducing the deployment

```bash
# On the Alibaba Cloud ECS instance
git clone https://github.com/VIVIANAPLATA16/glamcode-autopilot-agent.git
cd glamcode-autopilot-agent/backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# then edit .env: set QWEN_API_KEY, QWEN_API_BASE_URL, QWEN_MODEL, DIAS_INACTIVIDAD

python demo_app.py
```

The app listens on `0.0.0.0:$PORT` (default `5000`). For production use beyond a hackathon demo, run it behind a process manager (e.g. `systemd` or `pm2`) and a reverse proxy (e.g. Nginx) instead of the Flask dev server, and restrict the Security Group to known IPs.
