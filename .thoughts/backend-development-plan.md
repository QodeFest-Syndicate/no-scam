# no-scam — Backend Development Plan

**Author:** Backend owner
**Date:** 2026-11-19 (QodeFest build day)
**Sources of truth:** [docs/problem-statement.md](../docs/problem-statement.md), [docs/solution-brief.md](../docs/solution-brief.md), [AGENTS.md](../AGENTS.md), `origin/feat/frontend-watchdog` (UI)
**Status:** Draft for team review. `.thoughts/` is gitignored (`.gitignore:225`) — move this to `docs/` if it must be shared.

---

## 1. Where the project stands

| Area | State | Notes |
|---|---|---|
| `src/service/` | Empty (`.gitkeep`) | Greenfield HTTP backend — **your scope** |
| `src/mcp/` | Empty (`.gitkeep`) | Greenfield MCP server — share backend domain logic |
| `src/ai/` | Empty (`.gitkeep`) | Greenfield Qwen/DashScope client layer |
| `src/ui/` | On `origin/feat/frontend-watchdog` only | 4-screen scripted prototype (incoming → assessment → decision → recovery) |
| `docs/` | Problem statement + solution brief | Brief §5 defines the demo; no formal API spec |
| `AGENTS.md` | Swarm role/stage framework | Backend maps to FAASDV + DATENG + AIOSEG roles, stages S2–S7 |
| Tooling | None | No `package.json`, CI, tests, or env config |

**Key fact:** the UI today computes warning signals in the browser with `getWarningSignals()` in `src/ui/script.js` (urgency / unverified link / money request / secrecy regexes). That function is the de-facto contract the backend must replace with an HTTP call — same shape: `{ icon, title, detail }`.

Solution brief §5 explicitly allows a rules-only demo ("A real AI model is not required"), so Qwen is an enhancement, not a blocker for a working demo.

---

## 2. Before you write code — checklist

| # | Item | Why | Status / action |
|---|---|---|---|
| 1 | Node.js ≥ 20 + npm | Runtime | ✓ Node v24.22.1 installed |
| 2 | `DASHSCOPE_API_KEY` from Alibaba Cloud Model Studio | Qwen inference | **Action: request from organizer/team lead** — needed only for AI mode |
| 3 | Region base URL + allowed model names | DashScope endpoint differs by region (e.g. `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`) | **Action: confirm from event handout** |
| 4 | API contract agreement with UI owner | Avoid rework during the 1–2h build | **Action: send §5 of this doc to the frontend dev** |
| 5 | Branch `feat/backend-service` off `main` | Keep `feat/frontend-watchdog` mergeable | Action: create before scaffolding |
| 6 | `.env` + `.env.example` | Secrets never committed (`.env` already gitignored, line 153) | Action: create at scaffold step |
| 7 | Confirm demo boundary | Brief §5: one scripted scenario, fake data, no link fetching, no identity claims | Read §7 guardrails before coding |

---

## 3. Decisions to lock (recommended defaults)

| Decision | Recommendation | Rationale |
|---|---|---|
| Language/stack | TypeScript on Node, single root `package.json` | TS types double as the API contract; no monorepo overhead for 4 folders |
| HTTP framework | Fastify + Zod | Fast, built-in schema validation, small |
| Qwen SDK | `openai` package pointed at DashScope OpenAI-compatible base URL | Qwen exposes the OpenAI chat-completions API; no vendor-specific SDK to learn under time pressure |
| MCP SDK | `@modelcontextprotocol/sdk`, stdio transport | Demo from Qoder; no extra hosting |
| Persistence | None — fake scenarios in a JSON/TS module | Nothing in the brief needs a DB; in-memory keeps the demo hermetic |
| Auth / multi-tenancy | Out of scope | No user accounts in the demo; note this in `/api/meta` |
| AI failure mode | Deterministic rules always run; Qwen enriches when available | Demo must survive no network / no key / timeout |
| UI serving | Fastify `@fastify/static` serves `src/ui/` in dev | Kills CORS issues on demo day; keep API also CORS-open for localhost |
| Package manager | npm (lockfile committed) | Default on machine |

Single root package layout:

```
package.json          # scripts: dev, build, test, start
tsconfig.json
.env.example
src/service/          # server.ts, routes/, domain/{types,rules,recovery}.ts
src/ai/               # qwen.ts (client + prompt + schema validation)
src/mcp/              # server.ts (imports service/domain)
src/ui/               # static demo (from feat/frontend-watchdog)
test/                 # vitest specs for domain rules
```

---

## 4. Target architecture

```
┌──────────────┐   HTTP/JSON   ┌─────────────────────────────┐
│  src/ui      │ ────────────▶ │  src/service (Fastify)      │
│  4 screens   │ ◀──────────── │  POST /api/assess           │
└──────────────┘               │  POST /api/recovery         │
                               │  GET  /api/scenarios, /meta │
┌──────────────┐   MCP stdio   │        │                    │
│ Qoder / MCP  │ ────────────▶ │        ▼                    │
│ client       │               │  src/service/domain         │
└──────────────┘               │  rules.ts · recovery.ts     │
                               │        ▲                    │
┌──────────────┐  MCP stdio    │        │ optional           │
│ src/mcp      │ ──────────────┼────────┘                    │
└──────────────┘               │  src/ai/qwen.ts             │
                               └────────────┬────────────────┘
                                            ▼
                                   DashScope (Qwen) — timeout 8s
```

Rules: `src/mcp` and `src/service` must import the **same** domain module — no duplicated regexes. `src/ai` is a leaf dependency only.

---

## 5. API contract v0 (send this to the UI owner)

### `POST /api/assess`

```jsonc
// request
{
  "message": {
    "sender": "Amir (Son)",
    "familiarContact": true,
    "channel": "whatsapp",
    "text": "Hi Mak, it's me Amir. I need your help urgently! ... https://urgent-family-pay.example ..."
  }
}
```

```jsonc
// 200 response
{
  "assessment": {
    "level": "pause",                 // "no_signals" | "pause"
    "engine": "rules",                // "rules" | "qwen"
    "signals": [
      { "id": "urgency",  "icon": "⏱", "title": "Pressure to act quickly", "detail": "…" },
      { "id": "link",     "icon": "🔗", "title": "Link has not been verified", "detail": "…" },
      { "id": "money",    "icon": "💳", "title": "Unusual money request", "detail": "…" },
      { "id": "secrecy",  "icon": "🙊", "title": "Discourages independent verification", "detail": "…" }
    ],
    "summary": "Amir's account may be familiar, but this request and link are not verified.",
    "disclaimer": "These are warning signs, not proof of a scam. We have not verified who sent this message or inspected the link.",
    "aiAvailable": false
  }
}
```

- Validation: 400 on missing/oversized `text` (cap ~2 000 chars), unknown fields ignored.
- AI mode: same response shape, `engine: "qwen"`, `signals` validated against a strict Zod schema; on any failure fall back to rules silently and set `aiAvailable` accordingly. No 5xx for AI failures.

### Other endpoints

| Method + path | Request | Response |
|---|---|---|
| `GET /health` | — | `{ "status": "ok", "uptime": 12.3 }` |
| `GET /api/scenarios` | — | `{ "scenarios": [ { "id": "amir-payment", "message": {…} } ] }` |
| `POST /api/recovery` | `{ "incident": "clicked_link" \| "entered_credentials" \| "sent_money" \| "shared_info" }` | `{ "steps": [ { "order": 1, "title": "...", "detail": "...", "urgent": false } ], "disclaimer": "…" }` |
| `GET /api/meta` | — | `{ "service": "no-scam", "engine": "rules", "aiEnabled": true, "demoDataOnly": true, "version": "0.1.0" }` |

Recovery content must stay general (brief §5): stop interacting, change password via official app, contact bank via official number, NSRC **997**, tell someone trusted. Never promise recovery or account security.

---

## 6. Build order (time-boxed, each step independently demoable)

| Step | Scope | Est. | Done when |
|---|---|---|---|
| 0 | Scaffold: `package.json`, `tsconfig`, deps (`fastify`, `@fastify/static`, `@fastify/cors`, `zod`, `openai`, `@modelcontextprotocol/sdk`, `tsx`, `vitest`, `typescript`), `.env.example`, `npm run dev` boots `GET /health` | 20 min | `curl localhost:3000/health` returns 200 |
| 1 | Domain: port `getWarningSignals()` regexes into `domain/rules.ts`; add `domain/types.ts`, `domain/recovery.ts`; scenarios module | 30 min | Unit tests for 1 scam sample + 2 benign messages pass |
| 2 | HTTP: `/api/assess`, `/api/recovery`, `/api/scenarios`, `/api/meta`; Zod validation; static-serve `src/ui` | 30 min | `curl` examples from §5 return exact shapes |
| 3 | UI wiring (with frontend owner): replace `getWarningSignals(sampleMessage)` with `fetch('/api/assess')`; keep local rules as offline fallback; render `signals`, `summary`, `disclaimer` | 30 min | UI shows backend-provided signals with network, and still works offline |
| 4 | Qwen: `src/ai/qwen.ts` — system prompt with §7 guardrails, JSON output, 8s timeout, Zod validation, rules fallback; `POST /api/assess?mode=ai` or auto when key present | 45 min | Unplug network → identical demo, `engine:"rules"` |
| 5 | MCP: stdio server exposing `assess_message`, `get_recovery_guidance`, `list_scenarios`, importing same domain | 30 min | Tool call from Qoder returns assessment JSON |
| 6 | Validation + rehearsal: curl script, `npm test`, two demo run-throughs (online + offline), README run instructions | 30 min | §8 criteria all pass |

**MVP = steps 0–3 (~2h) and is demo-complete without Qwen.** Steps 4–5 are stretches; cut step 5 first if behind.

Suggested env vars (`.env.example`):

```
PORT=3000
DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
AI_TIMEOUT_MS=8000
ALLOW_ORIGIN=http://localhost:3000
```

---

## 7. Guardrails (binding — from solution-brief §9)

- Say **"reasons to pause"**, never "this is a scam".
- Say **"verify through a known route"**, never "proves identity".
- Always return the `disclaimer` field; UI must render it.
- `engine` and `aiAvailable` are exposed so the demo can state what is simulated.
- Fake data only; the sample link `urgent-family-pay.example` must never be fetched.
- **Do not add live URL fetching/scanning in this build** — it adds SSRF risk and violates the demo boundary. If it is ever added: block private IP ranges, no redirects, and never output "safe"/"malicious" verdicts.
- Do not log raw message bodies beyond the request lifecycle; never log the API key.
- Qwen prompt must forbid inventing sources, identity claims, and certainty. Model output is validated structurally; failure → rules fallback.

---

## 8. Acceptance criteria (maps to brief §5 completion criteria)

- [ ] UI assessment screen is populated from `POST /api/assess` — not from local regexes (local rules used only as offline fallback).
- [ ] Sample "Amir" message yields 4 signals and `level:"pause"`.
- [ ] Benign message (e.g. "See you at 3pm, call me later") yields `level:"no_signals"`, empty `signals`, and summary that says no known warning signs were found — still verify if money is requested.
- [ ] `engine:"rules"` demo passes with no network and no API key.
- [ ] Recovery response includes NSRC 997 and bank guidance, with no promises of recovery.
- [ ] `npm test` green; `curl` script exercises all five endpoints.
- [ ] `.env` untracked; repo has no secrets or real PII.

---

## 9. Risks and open questions

| Risk | Likelihood | Mitigation |
|---|---|---|
| API key not issued or region endpoint unknown | Medium | Build rules-first; AI is optional (§6 ordering) |
| Frontend stays fully scripted | Medium | Agree contract in §5 before step 3; UI fallback keeps demo alive |
| Qwen returns off-schema or slow output | Medium | Zod validation, 8s timeout, deterministic fallback, low temperature |
| Scope creep into link scanning / call interception / hardware | High | Brief §5 boundary: one text scenario, no link fetch, no interception |
| Demo machine offline at venue | Low | Offline mode is a tested path (step 4 checkpoint) |
| `AGENTS.md` swarm roles pull effort toward S6–S8 (CI/CD, GTM) | Medium | Treat stages as a checklist only; S5 build is the goal today |

Open questions for the team lead:
1. Who owns the UI branch merge, and when can the UI owner pair on step 3?
2. Is a Qwen key available, and which region/model names?
3. Does the demo need the MCP tool path at all, or is HTTP-only enough for judging?

---

## 10. First five actions

1. `git checkout -b feat/backend-service`
2. Request `DASHSCOPE_API_KEY` + region/model list from the organizer.
3. Scaffold step 0 and push an empty `/health` so the UI owner can code against a live URL.
4. Share §5 contract (the JSON example) with the frontend owner.
5. Port the four `getWarningSignals` rules and write the three unit tests (step 1).
