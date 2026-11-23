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

## Optional WhatsApp test-number pilot

Forward or paste fictional suspicious text to Meta's test business number and receive an automatic WatchDog reply. This does not read private chats. The opt-in integration verifies Meta signatures, restricts recipients, queues work durably and defaults to local rules; AI requires separate consent and configuration.

Follow the [WhatsApp setup, backend strategy and rollout gates](docs/whatsapp-test-pilot.md). You need Meta test credentials, a private persistent SQLite directory and a publicly trusted HTTPS callback exposing only the webhook. These resources are not provisioned automatically; live Meta delivery must be verified separately.

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

## Deploy on Alibaba Cloud ECS

The root `Dockerfile` packages the API, static UI, and standalone AI CLI together. `infra/alicloud/` creates one pay-as-you-go Ubuntu 24.04 ECS VM, an encrypted 40 GiB disk, a VPC/vSwitch, and restricted security-group rules. Kuala Lumpur (`ap-southeast-3`) is the default region. There is no database, registry provisioning, load balancer, public TLS, or automatic CI/CD deployment.

**This is a single-server demo, not a highly available production deployment.** ECS, disk, outbound traffic, remote state, and AI calls can incur charges. Nothing is provisioned by building the image or running the mocked Terraform tests. Deployments and rollbacks replace the VM, cause downtime, change its public IP, and require reapplying host secrets and private-registry authentication.

### 1. Build and test the image

Run these commands from the repository root on a machine with Docker and Buildx. The ECS instance must be x86_64, so build for `linux/amd64`:

```bash
docker buildx build --platform linux/amd64 --load -t no-scam:local .
docker run --rm --name no-scam-local -p 127.0.0.1:8000:8000 \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL --security-opt no-new-privileges:true no-scam:local
```

In another terminal, open http://localhost:8000/ and run:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/api/meta
```

Use the browser walkthrough to check assessments and recovery. No secrets or local environment files enter the build context; the image runs as a non-root user and includes an HTTP health check. The container port is fixed at **8000**. To enable live AI locally, add `--env-file .env` to `docker run`; use fictional data only.

Publish the tested image to a registry you control, such as Alibaba Cloud Container Registry (ACR). Create the repository and authenticate using its console-provided instructions first. Publishing uploads application code:

```bash
export IMAGE_REPOSITORY='YOUR_REGISTRY/YOUR_NAMESPACE/no-scam'
export IMAGE_TAG="$(git rev-parse --short HEAD)"
docker tag no-scam:local "$IMAGE_REPOSITORY:$IMAGE_TAG"
docker push "$IMAGE_REPOSITORY:$IMAGE_TAG"
docker buildx imagetools inspect "$IMAGE_REPOSITORY:$IMAGE_TAG"
```

Record the pushed `sha256` digest. Terraform requires `registry/repository@sha256:...`, never `latest`. Keep previous digests for rollback. The base images have version tags; pin their digests too if you require immutable base-image rebuilds.

### 2. Prepare cloud inputs and remote state

You need Terraform **1.7+**, Alibaba Cloud permissions for ECS/VPC/security groups and disk encryption, an existing regional ECS SSH key pair, and a published image. Select an available x86_64 instance with **at least 2 vCPU / 4 GiB RAM**, a compatible zone, and its **Ubuntu 24.04 x86_64 system image ID**; these vary by region and account capacity.

The OSS backend requires a separately managed **private, versioned OSS bucket** and a **TableStore lock table** with a single `LockID` primary key of type `String`. Keep both backend locking fields configured. State objects use server-side encryption and private ACLs. Restrict RAM access to the deployment operator and state resources; retain bucket versions for recovery. Backend resources are not created by this stack, so app teardown cannot delete its own state storage.

```bash
cp infra/alicloud/terraform.tfvars.example infra/alicloud/terraform.tfvars
cp infra/alicloud/backend.hcl.example infra/alicloud/backend.hcl
```

Replace all placeholders. Set `ssh_cidrs` to your administrator public IPv4 with `/32`; the example address is not usable. Leave `http_cidrs = []` for SSH-tunnel-only access. If an IP-restricted **unencrypted** demo endpoint is necessary, explicitly supply its client IPv4 CIDRs (`/24` or narrower). Never send private data over that HTTP endpoint; this configuration intentionally rejects public `0.0.0.0/0` access. A public service needs HTTPS, authentication, and request/rate controls before enabling paid AI calls—CORS is not access control.

Authenticate Terraform through the provider's environment variables or an existing Alibaba Cloud credential profile. Prefer short-lived RAM/STS credentials: `ALICLOUD_ACCESS_KEY`, `ALICLOUD_SECRET_KEY`, and `ALICLOUD_SECURITY_TOKEN`. Do not paste credentials into Terraform files, commands saved in shell history, or backend configuration. Local tfvars, backend config, plans, and state files are gitignored; `.terraform.lock.hcl` should be committed.

### 3. Review and apply

```bash
terraform -chdir=infra/alicloud init -backend-config=backend.hcl
terraform -chdir=infra/alicloud fmt -check -recursive
terraform -chdir=infra/alicloud validate
terraform -chdir=infra/alicloud test
terraform -chdir=infra/alicloud plan -out=deployment.tfplan
# Review the plan and costs before explicitly creating resources.
terraform -chdir=infra/alicloud apply deployment.tfplan
terraform -chdir=infra/alicloud output
```

Cloud-init installs Ubuntu's `docker.io` package and starts the systemd-managed container. The VM needs outbound package-mirror, registry, DNS, and optional AI connectivity. A successful Terraform apply confirms infrastructure creation, **not** application readiness. Verify the selected image boots with IMDSv2, and inspect bootstrap and container status over SSH:

```bash
export ECS_IP="$(terraform -chdir=infra/alicloud output -raw public_ip)"
ssh root@"$ECS_IP" 'cloud-init status --wait'
ssh root@"$ECS_IP" 'systemctl status no-scam --no-pager'
ssh root@"$ECS_IP" 'docker inspect --format "{{.State.Health.Status}}" no-scam'
ssh root@"$ECS_IP" 'journalctl -u no-scam -n 50 --no-pager'
```

Add `-i /path/to/private-key` if your key is not loaded in your SSH agent. The selected Alibaba Ubuntu image must support key-based root SSH. For a **private registry**, log in on the VM as root using a scoped pull credential and `docker login --password-stdin`, then run `systemctl restart no-scam`. Do not put registry passwords in cloud-init. Until authenticated, image pulls fail and systemd retries; stop the unit while performing extended setup. Remove temporary registry credentials when no longer needed, and renew them before future image pulls.

Start the tunnel, leave it running, and open http://localhost:8000/:

```bash
ssh -N -L 127.0.0.1:8000:127.0.0.1:8000 root@"$ECS_IP"
```

Check `/health`, `/api/meta`, the browser walkthrough, and invalid API input. Systemd restarts exited containers; Docker health status is diagnostic and **does not** automatically restart a running but unhealthy container. Logs rotate at 10 MiB with three retained files; configure external monitoring and alerting before production use.

### 4. Add optional AI credentials on the VM

The VM starts in rules-only mode. Over SSH, use `sudoedit /etc/no-scam/app.env` to add only the runtime variables you need, such as `DASHSCOPE_API_KEY`, its matching regional `DASHSCOPE_BASE_URL`, and `QWEN_MODEL`. The Qoder/OpenAI-compatible variables in the configuration reference also work. Use plain `KEY=value` lines without shell `export` or surrounding quotes.

Keep the file owned by root with mode `0600`, then run `systemctl restart no-scam`. Credentials enter the container only at runtime; they are not in the image, cloud-init, or Terraform state. Root and Docker administrators can still inspect container environment variables, so restrict host access. Validate a fictional request with `mode=ai`; `/api/meta` alone does not prove the key works. Outbound TLS protects the AI call, but message data is still sent to the configured provider.

### Updates, rollback, and teardown

- Build, test, and publish a new immutable digest; change `container_image`, review the plan, and apply. Bootstrap/image changes deliberately replace the VM because cloud-init first-boot provisioning does not reliably replay on an ECS user-data update.
- Deletion protection defaults to **true**. Before a planned replacement, first set it to false and apply **only that change**; then update the digest or image in a separate reviewed plan. Restore protection afterward. Reinstall host secrets/private-registry credentials and recheck health after replacement.
- To roll back, repeat that process with the previous known-good digest. No database migration is involved, but local VM data is discarded. Keep secrets in an approved external secret store so they can be restored; do not treat this VM as their only copy.
- Periodically run `terraform plan` to review drift; do not apply unexpected changes blindly.
- For teardown, disable deletion protection in a separate apply, review `terraform plan -destroy`, and explicitly run `terraform destroy`. Remote state storage and registry images remain separately managed and may continue to incur charges.

### Offline infrastructure checks

These commands install the provider and use mocked resources without Alibaba Cloud credentials or provisioning:

```bash
terraform -chdir=infra/alicloud init -backend=false
terraform -chdir=infra/alicloud validate
terraform -chdir=infra/alicloud test
uv run --locked pytest
```

Mocks validate configuration and access restrictions, not real cloud capacity, IAM permissions, Ubuntu boot, registry access, or Docker startup. A Docker build/run and a real reviewed cloud plan plus smoke test are still required before deployment is considered verified.

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
