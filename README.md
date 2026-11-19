# no-scam — WatchDog AI demo backend

Backend for the WatchDog AI concept described in
[docs/digital-watchdog-master-brief.md](docs/digital-watchdog-master-brief.md).

Given one scripted message from a familiar family account, the service:

1. finds visible reasons to pause (urgency, unverified link, money request, secrecy);
2. shows what was checked, where the result came from and what remains unresolved;
3. offers a safe verification route through a contact the person already trusts;
4. gives calm next steps if the person already clicked, shared details or sent money.

It never claims a message is a scam or safe, never proves identity, and never
fetches the link. Demo data only.

## Stack

| Layer | Choice |
| --- | --- |
| Runtime | Python 3.12 (managed by `uv`) |
| HTTP | FastAPI + Uvicorn + Pydantic v2 |
| AI (optional) | Qwen via DashScope's OpenAI-compatible API |
| MCP | Python MCP SDK (`mcp.server.mcpserver`), stdio transport |
| Tests | pytest + FastAPI TestClient |

## Quickstart

```bash
uv sync
cp .env.example .env          # optional; needed only for Qwen mode
uv run uvicorn src.service.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

If `src/ui/index.html` exists (for example after merging
`feat/frontend-watchdog`), the backend also serves the UI at `/`.

Run the test suite:

```bash
uv run pytest
```

Exercise every endpoint against a running server:

```bash
bash scripts/demo.sh
```

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8000` | Port used by `python -m src.service.main` |
| `DASHSCOPE_API_KEY` | empty | Enables Qwen enrichment; empty means rules-only |
| `DASHSCOPE_BASE_URL` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | DashScope endpoint |
| `QWEN_MODEL` | `qwen-plus` | Model name |
| `AI_TIMEOUT_MS` | `8000` | Qwen timeout; failures fall back to rules |
| `ALLOW_ORIGINS` | localhost 8000/5173/3000 | Comma-separated CORS origins |

`.env` is gitignored. Never commit a real key.

## API

### `POST /api/assess?mode=auto|ai|rules`

```bash
curl -s -X POST "http://localhost:8000/api/assess?mode=rules" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "sender": "Amir (Son)",
      "familiarContact": true,
      "channel": "whatsapp",
      "text": "Hi Mak, it is Amir. Please pay RM500 right now at https://urgent-family-pay.example and do not call me."
    }
  }'
```

Response shape (abridged):

```jsonc
{
  "assessment": {
    "level": "pause",
    "engine": "rules",
    "signals": [
      { "id": "urgency", "icon": "⏱", "title": "Pressure to act quickly", "detail": "…" },
      { "id": "link", "icon": "🔗", "title": "Link has not been verified", "detail": "…" },
      { "id": "money", "icon": "💳", "title": "Unusual money request", "detail": "…" },
      { "id": "secrecy", "icon": "🙊", "title": "Discourages independent verification", "detail": "…" }
    ],
    "summary": "Amir (Son) may be a familiar contact, but this request is not verified. …",
    "disclaimer": "These are warning signs, not proof of a scam. …",
    "aiAvailable": false,
    "checks": [
      { "id": "text_signals", "label": "…", "source": "Demo rules (local, deterministic)", "status": "completed", "result": "4 warning sign(s) found." },
      { "id": "link", "label": "Link destination inspection", "source": "Not available in this demo", "status": "unavailable", "result": "The link was not opened, fetched or scanned." },
      { "id": "contact", "label": "Independent check with Amir (Son)", "source": "A route you already trust — you confirm", "status": "not_run", "result": "…" }
    ]
  }
}
```

- `text` is required, 1–2000 characters. Unknown fields are ignored.
- `engine` is `"rules"` or `"qwen"`; `aiAvailable` states whether Qwen actually answered.
- Qwen runs only when a key is configured and `mode` is `auto` or `ai`. Timeouts,
  network errors, malformed JSON or unsafe language fall back to rules silently.
- Qwen may only select from the four known signal IDs and rewrite explanations.
  The app keeps canonical icons/titles, never drops a rule signal, and rejects
  verdict language such as "definitely" or "is a scam".

### Other endpoints

| Method + path | Response |
| --- | --- |
| `GET /health` | `{ "status": "ok", "uptime": 1.2 }` |
| `GET /api/meta` | service state, `aiEnabled`, `demoDataOnly: true`, version |
| `GET /api/scenarios` | the one scripted `amir-payment` scenario |
| `POST /api/recovery` | ordered next steps for `clicked_link`, `entered_credentials`, `sent_money`, `shared_info` |

```bash
curl -s -X POST http://localhost:8000/api/recovery \
  -H "Content-Type: application/json" \
  -d '{"incident":"sent_money"}'
```

Recovery content is deliberately general: call the bank using the number on
your card or statement, report to NSRC on **997**, make a police report, keep
evidence, stop further payments. It never promises recovery or account security.

## MCP server

The MCP server imports the same domain module as HTTP — no duplicated rules.

```bash
uv run python -m src.mcp.server
```

Tools: `assess_message`, `get_recovery_guidance`, `list_scenarios`.

Example client configuration:

```json
{
  "mcpServers": {
    "no-scam-watchdog": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp.server"],
      "cwd": "C:/Users/Nick/Documents/GitHub/no-scam"
    }
  }
}
```

## Demo boundary and honest claims

- One text scenario with fake data; no real contacts or personal information.
- The sample link is never opened, fetched or scanned. There is no live URL
  scanning, call interception, account access, identity proof or hardware.
- `/api/meta` exposes `demoDataOnly`, `engine` and `aiEnabled` so the demo can
  state what is real and what is simulated.
- The physical companion is represented by the product story, not implemented.
- Missing checks stay `not_run`/`unavailable` instead of becoming implied trust.
- Message bodies are not logged. Qwen mode sends the sample message to
  DashScope; use fake data only.

## Layout

```
src/service/           FastAPI app, config, domain logic
  domain/rules.py      deterministic warning signals + evidence
  domain/recovery.py   after-the-fact guidance
  domain/scenarios.py  scripted demo data
src/ai/qwen.py         Qwen client, guardrails, rules fallback
src/mcp/server.py      MCP stdio tools over the same domain
src/ui/                static demo UI (from feat/frontend-watchdog)
tests/                 pytest suite
scripts/demo.sh        curl walkthrough of all endpoints
```
