# Proof of Alibaba Cloud services & APIs

Required by the **Qwen Cloud Global AI Hackathon** submission guidelines:

> *Include Proof of Alibaba Cloud Deployment: You must demonstrate that the backend is running on Alibaba Cloud. Proof must be a link to a code file in their code repo that demonstrates use of Alibaba Cloud services and APIs.*

## 1. Alibaba Cloud API usage (code proof)

The agent’s reasoning engine calls **Qwen Cloud** through the official **OpenAI-compatible DashScope endpoint** on Alibaba Cloud:

**Primary proof file:** [`backend/qwen_client.py`](../backend/qwen_client.py)

Relevant configuration (no secrets in repo):

```python
DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
```

Every reactive classification, appointment extraction, beauty consultation, and proactive message draft goes through `chat_completion()` in that file, authenticated with `QWEN_API_KEY` (DashScope / Qwen Cloud).

Also see: [`backend/.env.example`](../backend/.env.example) — documents `QWEN_API_KEY` and `QWEN_API_BASE_URL`.

## 2. Alibaba Cloud ECS runtime (deployment proof)

| Item | Value |
|---|---|
| Provider | Alibaba Cloud |
| Compute | Elastic Compute Service (ECS) |
| Public API | `http://47.251.39.38:5000` |
| Health | [`GET /api/health`](http://47.251.39.38:5000/api/health) |

Full deployment notes: [`docs/DEPLOYMENT.md`](DEPLOYMENT.md)

```bash
curl -s http://47.251.39.38:5000/api/health
# {"ok":true,"service":"glamcode-autopilot-agent","status":"ok"}
```

## 3. How judges can verify

1. Open [`backend/qwen_client.py`](../backend/qwen_client.py) — DashScope / Alibaba endpoint is hardcoded as default.
2. Hit the live ECS health URL above.
3. Review the architecture diagram in the root [`README.md`](../README.md) (Alibaba ECS + Qwen Cloud + Azure frontend).
