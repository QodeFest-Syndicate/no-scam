# WatchDog AI

**Pause. Check through a trusted route. Decide with clearer evidence.**

![WatchDog AI safety hub showing the fictional family-message scenario](Screenshot%202026-11-19%20141846.png)

WatchDog AI (`no-scam`) is a scam-awareness prototype that helps people understand an unusual message—even when it appears to come from someone they know. It highlights reasons to pause, explains what has and has not been checked, and offers practical next steps.

The demo follows a fictional message from **Amir (Son)** asking for an urgent **RM500** payment. It is not a scam detector or proof of anyone's identity.

**Start here:** [Run the demo](#run-the-demo) · [Try the walkthrough](#try-the-walkthrough) · [Enable optional AI](#optional-qwen-ai) · [Developer guide](#developer-guide) · [Troubleshooting](#troubleshooting)

## What you can try

- **Understand the request:** spot urgency, an unverified link, a money request, and pressure not to call.
- **Explore a safer check:** verify the specific request using a contact route you already trust.
- **Read the evidence:** distinguish observed warning signs from checks that have not happened.
- **Get support after acting:** see general guidance for clicking a link, sharing details, or sending money.

> **Demo only.** The browser loads its fictional scenario, assessment, evidence, and recovery guidance from the backend API. When configured, Qwen analyses the sample message. Family checks remain simulated; nobody is contacted and the example link is never opened.

## Run the demo

### 1. Check the prerequisites

You will need:

- **Python 3.11 or newer.**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** to install dependencies and run the app.
- A web browser.

No Node.js, frontend build, AI account, or API key is required. Dependency installation needs internet access; the browser walkthrough and rules-based assessments work locally afterward.

### 2. Install dependencies

Clone or download this repository, then open a terminal in the `no-scam` folder and run:

```bash
uv sync
```

### 3. Start the app

```bash
uv run uvicorn src.service.main:app --reload --port 8000
```

Keep that terminal open while using the app. Press **Ctrl+C** to stop it.

### 4. Open it in your browser

| Page | Address |
| --- | --- |
| **Interactive demo** | http://localhost:8000/ |
| API explorer for developers | http://localhost:8000/docs |
| Server health check | http://localhost:8000/health |

The same server serves both the frontend and API—there is no second development server to start.

## Try the walkthrough

1. Read the fictional message on **My safety hub**.
2. Select **Understand this message** to see the four warning signs.
3. Select **See how WatchDog checks**, then **Run simulated check**. No call is made, and the request stays unverified.
4. Open the **Evidence report** to see what is known and what remains unresolved.
5. Visit **My decision** to explore verification steps, pausing, or the risks of continuing.
6. Open **Get help**, choose what happened, and review the suggested next steps. Use **Restart demo** to start over.

## What is real, and what is simulated?

| Component | Current behavior |
| --- | --- |
| Browser walkthrough | Fetches the sample, assessments, evidence, and recovery guidance from the API |
| Assessment API | Runs local rules against supplied text; optionally uses Qwen |
| Qwen integration | Live enrichment when configured; the browser labels live AI and local rules separately |
| Family verification | Simulated only; no calls, messages, or identity checks |
| Link checking | Links are never opened, fetched, or scanned |
| Physical companion | Product concept only; no connected hardware |

**Use fictional data only.** Live Qwen requests send message content to the configured Qoder/OpenAI-compatible gateway or DashScope. The service does not log message bodies, but this prototype should not be used with private messages, credentials, or real financial details.

Warning signs are **not proof of fraud**, and finding no signs does **not** mean a message is safe. Recovery suggestions are general guidance, not a guarantee of recovering money or securing an account. The demo includes Malaysia-specific guidance; confirm current official procedures before any real-world use.

## Optional Qwen AI

These settings enable AI enrichment for both the **HTTP API and browser walkthrough**. Without a key, the browser uses local rules.

For an existing Qoder workspace `.env`, the backend uses `QODER_API_KEY`, `QODER_HOST`, and `OPENAI_ENDPOINT` directly. `OPENAI_BASE_URL` can supply the complete endpoint instead, and `OPENAI_API_KEY` is accepted when `QODER_API_KEY` is empty. Leave `DASHSCOPE_API_KEY` empty for this route; a nonempty DashScope key selects the direct DashScope configuration instead.

1. If you do not already have a `.env` file, copy `.env.example` to `.env` in the repository root.
2. Set your DashScope key in `.env`:

   ```dotenv
   DASHSCOPE_API_KEY=your_dashscope_api_key
   ```

3. Restart the server.
4. Open the browser walkthrough and select **Understand this message**. The result identifies whether live Qwen or local rules answered. You can also use the [API explorer](http://localhost:8000/docs) with `POST /api/assess?mode=ai`.

`.env` is gitignored. **Never commit a real key.**

### Choose an assessment mode

Pass the mode as a query parameter, for example `/api/assess?mode=rules`.

| Mode | Behavior |
| --- | --- |
| `auto` (default) | Tries Qwen when configured; falls back to local rules if AI is unavailable or its response is rejected |
| `rules` | Uses local rules only; never calls Qwen |
| `ai` | Requires a usable Qwen response; returns HTTP `503` if one is unavailable |

Check `assessment.engine` (`rules` or `qwen`) and `assessment.aiAvailable` to see what actually answered. `/api/meta` reports configuration, not proof that a live AI request succeeded. The browser uses strict `ai` mode when configured; a failed call shows retry and an explicit local-rules option instead of silently labelling a fallback as AI.

### Configuration reference

Defaults work for the local demo. See `.env.example` for a ready-to-copy template.

| Variable | Default | What it controls |
| --- | --- | --- |
| `DASHSCOPE_API_KEY` | Empty | Enables Qwen requests when set |
| `DASHSCOPE_BASE_URL` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | DashScope API endpoint |
| `QWEN_MODEL` | `qwen-plus` | Model for direct DashScope enrichment |
| `QODER_API_KEY` / `OPENAI_API_KEY` | Empty | Gateway credentials, used when the DashScope key is empty |
| `QODER_HOST` + `OPENAI_ENDPOINT` | Empty | Gateway host and API path |
| `OPENAI_BASE_URL` | Empty | Complete gateway URL; overrides host + path |
| `WATCHDOG_MODEL` | `qwen3.8-flash` | Model for gateway enrichment |
| `AI_TIMEOUT_MS` | `8000` (DashScope), `30000` (gateway) | AI timeout in milliseconds; accepted range is 1,000–30,000 |
| `ALLOW_ORIGINS` | `http://localhost:8000,http://localhost:5173,http://localhost:3000` | Comma-separated allowed browser origins |
| `PORT` | `8000` | Port for `uv run python -m src.service.main`; the quickstart command uses `--port` instead |

## Developer guide

### Stack and project layout

The project uses **FastAPI, Uvicorn, and Pydantic v2**, with a plain **HTML/CSS/JavaScript** frontend. Optional AI support uses Qwen through DashScope's OpenAI-compatible API. A separate LangGraph workflow and CLI live in `src/ai/`.

```text
src/ui/               Static browser walkthrough
src/service/          HTTP API, configuration, rules, and recovery guidance
src/service/ai/       Qwen API client and response guardrails
src/ai/               Separate AI workflow and command-line interface
src/mcp/              Model Context Protocol tools using the local rules
tests/                Automated tests
scripts/demo.sh       API walkthrough using curl
docs/                 Product concept and project briefs
```

### Run checks

From the repository root:

```bash
uv run pytest
```

The test suite disables live DashScope calls; you do not need an API key.

With the server running, use a **second terminal** to exercise the API:

```bash
bash scripts/demo.sh
```

This script needs Bash and curl; on Windows, use Git Bash. Its automatic-mode request may call Qwen if you have configured a key.

### API reference

Use http://localhost:8000/docs to send requests in your browser and inspect full request and response schemas.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Server status and uptime |
| `GET` | `/api/meta` | Configured engine, AI configuration state, demo flag, and version |
| `GET` | `/api/scenarios` | The scripted `amir-payment` scenario |
| `POST` | `/api/assess` | Warning signs, explanations, and evidence for a message |
| `POST` | `/api/recovery` | Ordered next steps after an incident |

<details>
<summary>Example API requests (Bash / Git Bash)</summary>

Assess a fictional message without calling AI:

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

`message.sender` (1–120 characters) and `message.text` (1–2,000 characters) are required. `familiarContact` defaults to `true`, and `channel` defaults to `whatsapp`. Unknown fields are ignored.

The response contains an `assessment` with:

- `level`: `pause` or `no_signals`—neither is a safety verdict.
- `signals`: warning signs with explanations.
- `checks`: the source, status, and result of each check; missing checks stay `not_run` or `unavailable`.
- `summary` and `disclaimer`: context and limitations.
- `engine` and `aiAvailable`: whether local rules or Qwen supplied the assessment.

Qwen output is constrained to the four known warning signs and cannot remove a sign found by local rules.

Request guidance after sending money:

```bash
curl -s -X POST "http://localhost:8000/api/recovery" \
  -H "Content-Type: application/json" \
  -d '{"incident":"sent_money"}'
```

Supported incidents: `clicked_link`, `entered_credentials`, `sent_money`, and `shared_info`.

</details>

### MCP tools

The **Model Context Protocol (MCP)** server lets compatible clients use the same local rules and recovery guidance as the HTTP API. It runs separately over standard input/output and does not require the web server or Qwen.

```bash
uv run python -m src.mcp.server
```

Available tools: `assess_message`, `get_recovery_guidance`, and `list_scenarios`.

<details>
<summary>Example MCP client configuration</summary>

Replace `/absolute/path/to/no-scam` with your checkout's absolute path. On Windows, use forward slashes, such as `C:/projects/no-scam`.

```json
{
  "mcpServers": {
    "no-scam-watchdog": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/no-scam", "run", "python", "-m", "src.mcp.server"]
    }
  }
}
```

</details>

### Standalone AI workflow

To explore the separate CLI without a live model:

```bash
uv run watchdog-ai --list-demos
uv run watchdog-ai --demo familiar-link --mode offline
```

This workflow is separate from the browser walkthrough and HTTP assessment API.

## Troubleshooting

| Problem | What to try |
| --- | --- |
| `uv` is not found | Install uv using the prerequisites link, then reopen your terminal. |
| Imports or dependencies are missing | Run `uv sync` from the repository root, then use the `uv run` commands above. Use `pyproject.toml` for the full app; `requirements.txt` covers the standalone AI workflow. |
| Port 8000 is already in use | Change the startup command to `--port 8001`, then open http://localhost:8001/. |
| The browser cannot connect | Keep the server terminal open, check it for startup errors, and make sure the browser address matches the port. |
| The browser shows local rules or AI unavailable | Check the server's key, matching endpoint, and model configuration; restart the server and reload the page. A live failure offers retry or explicit local rules. |
| `mode=ai` returns `503` | Check your key, endpoint, model access, and connectivity; restart after configuration changes. Use `mode=rules` to continue without AI. |

## More about the project

- [Problem statement](docs/problem-statement.md)
- [Solution brief](docs/solution-brief.md)
- [Full WatchDog concept and demo boundaries](docs/digital-watchdog-master-brief.md)
