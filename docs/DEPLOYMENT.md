# Proof of Alibaba Cloud Deployment

This document demonstrates that the GlamCode Autopilot Agent backend is deployed and running on **Alibaba Cloud**, as required by the hackathon submission guidelines.

## Deployment summary

| Item | Value |
|---|---|
| Cloud provider | Alibaba Cloud |
| Service used | Elastic Compute Service (ECS) |
| Component deployed | Flask backend (`backend/demo_app.py`) |
| Region | _fill in your ECS instance region, e.g. ap-southeast-1_ |
| Instance type | _fill in your ECS instance spec, e.g. ecs.t6-c1m2.large_ |
| Persistence | SQLite database on the ECS instance disk |
| LLM provider | Qwen Cloud (called from the backend) |

> Replace the placeholders above with your actual instance details before final submission. Do not commit real IP addresses, credentials, or `.env.local` values to this file — link to a redacted screenshot instead if needed.

## How the deployment works

1. The Flask backend (`backend/demo_app.py`, `backend/agente_reservas.py`, `backend/revision_humana.py`) runs on an Alibaba Cloud ECS instance.
2. The backend exposes an API that the Next.js frontend calls (configured via `NEXT_PUBLIC_API_URL` or equivalent in `frontend/.env.local`, which is intentionally not committed).
3. Incoming customer messages are processed by the booking agent, which calls **Qwen Cloud** for natural-language understanding and response generation.
4. Bookings and conversation history are persisted to a local **SQLite** database on the ECS instance.
5. Cases the agent is not confident about are routed to the human review flow (`revision_humana.py`) instead of being auto-resolved.

## Evidence

- Backend code that runs on the ECS instance: [`backend/demo_app.py`](../backend/demo_app.py), [`backend/agente_reservas.py`](../backend/agente_reservas.py), [`backend/revision_humana.py`](../backend/revision_humana.py).
- Architecture diagram: [`docs/architecture.png`](architecture.svg).
- _Add here:_ a link or reference to a deployment screenshot (ECS console, running service, or terminal session showing the app live on the instance's public IP/domain), with any sensitive values (raw IPs, tokens) redacted.

## Reproducing the deployment

```bash
# On the Alibaba Cloud ECS instance
git clone https://github.com/VIVIANAPLATA16/glamcode-autopilot-agent.git
cd glamcode-autopilot-agent/backend
pip install -r requirements.txt
python demo_app.py
```

Configure any required environment variables (Qwen Cloud API key, port, etc.) before starting the service. For production use, run behind a process manager (e.g. `systemd` or `pm2`) and a reverse proxy (e.g. Nginx) rather than the Flask dev server.
