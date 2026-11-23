# WhatsApp forwarding pilot: plan and backend strategy

Status: local implementation for Meta's test number, not a public launch or Meta approval. Reference material checked on 2026-11-19. Use fictional messages only.

## Product boundary and low-action experience

The official WhatsApp Business Platform cannot read a person's private conversation with a suspected scammer. It delivers messages addressed to the WatchDog business number. The person forwarding a message is the recipient of the analysis, **not the suspected original author**.

One-time setup: the operator registers a test recipient in Meta, gives them the pilot notice below, obtains agreement, and adds their international number to the local allowlist. They save the Meta test number as WatchDog. Thereafter: long-press suspicious text, Forward, select WatchDog, Send. WatchDog automatically replies to that message; no `/scan`, menu, login, or repeated consent prompt is required. Pasting text also works. WhatsApp controls the number of taps; this is not passive monitoring or literally one tap.

Suggested notice before allowlisting:

> This is a fictional-data-only test of WatchDog scam-warning assistance. Forwarded text goes through Meta to our server. Local rules identify some warning signs, not whether a message is safe or fraudulent. We do not identify the original sender or open links. Pending text and your reply address are kept for at most 24 hours, then removed from the active queue; a hashed replay marker remains for eight days. Do not send credentials, financial details or private conversations. Optional AI additionally sends the text, but not your WhatsApp identity/profile, to the operator's configured AI provider. Agree separately before the operator enables AI. Contact the pilot operator to withdraw or request deletion.

The single allowlist is a small, manually consented cohort, not a production consent-management system. Keep `WHATSAPP_ANALYSIS_MODE=rules` until every allowed participant has agreed to the configured AI processor. Removing a recipient and restarting stops processing their queued jobs. An operator must handle deletion requests and backups; there is no public administration endpoint.

## Architecture and execution plan

1. Authenticate Meta verification and event delivery; filter to one configured WABA, phone-number ID and recipient allowlist.
2. Normalize text with `sender="Original sender unknown"` and `familiar_contact=False`. Never infer identity from a forwarded user's profile or phone number.
3. Commit a bounded durable inbox/outbox transaction, then return HTTP 200. Do not wait for analysis or an outbound request in the webhook.
4. A worker started by FastAPI's lifespan leases jobs from SQLite, invokes the existing rules/Qwen assessment in a thread, builds a short safe reply and sends through Meta's Graph API.
5. Persist outcomes, handle retries/restarts and remove sensitive job fields. Verify locally with fake Meta transport before any live pilot.

```text
Forwarding user -> Meta Cloud API -> public HTTPS /webhooks/whatsapp
                                      | signature + scope + limits
                                      v
                               SQLite inbox/outbox on persistent disk
                                      | leased background worker
                                      v
                          local rules -> optional configured Qwen
                                      | fixed warning/guidance formatting
                                      v
                           Meta messages API -> forwarding user
```

This is a **single-server pilot**, not FaaS or a multi-tenant service. SQLite avoids adding Redis or another managed service before the pilot proves useful. It supports atomic deduplication and restart recovery, but is neither highly available nor suitable for shared network filesystems/serverless ephemeral storage. Run one Uvicorn worker on one host. Later move the queue to a transactional managed database plus independently scaled workers before scaling beyond one host; preserve the same identity and deduplication contract.

## Trigger contract and budgets

| Boundary | Contract |
| --- | --- |
| GET `/webhooks/whatsapp` | Require `hub.mode=subscribe`, constant-time verify-token match and a nonempty bounded challenge; echo challenge as plain text. Disabled integration returns 404. |
| POST `/webhooks/whatsapp` | JSON, at most 256 KiB, exact raw-body HMAC-SHA256 authenticated using the Meta app secret and `X-Hub-Signature-256`. Never authenticate POST using the verify token. |
| Envelope | `object=whatsapp_business_account`; process only `entry.id=WHATSAPP_WABA_ID`, `changes.field=messages`, `value.messaging_product=whatsapp`, matching `metadata.phone_number_id`. |
| Messages | At most 100 messages per envelope; phone-number-based `from`, stable ID and integer timestamp required. Only allowed senders can enqueue. Ignore status-only and other-account events without replying. BSUID-only events are not supported in this pilot. |
| Text | Up to 2,000 characters, matching the existing assessment contract. Empty/long text and non-text messages get a fixed text-only guidance reply, not a partial assessment. Attachments are neither stored nor fetched. |
| Time | Ignore events over five minutes in the future or older than 23 h 55 min. Recheck the original event's deadline immediately before sending; never reset it on redelivery. The five-minute margin is conservative relative to Meta's 24-hour customer-service window. |
| Queue | Maximum 500 active jobs total and 20 per sender. New batch acceptance is atomic; capacity/storage failure returns 503 so Meta can retry. Duplicate IDs still acknowledge even at capacity. |
| Execution | One background worker; 120-second fenced lease; one-second idle interval; at most five processing attempts. Existing AI timeout is at most 30 seconds. Graph connect timeout 5 s, read/write 10 s with bounded response reading; response at most 64 KiB. |
| Target | Webhook acknowledgement under two seconds on healthy local disk, and a rules reply within ten seconds under light load are targets, not measured production SLAs. Queue age determines user latency under load. |

GET challenge responses and invalid requests do not create jobs. POST rejects bad signatures (403), malformed scoped payloads (400), oversized bodies/batches (413), and wrong media types (415). Unsubscribed fields, non-allowed users, stale events and delivery statuses are acknowledged without work. Malformed scoped batches are rejected as a whole, never partially acknowledged; diagnose repeated 400s as a contract mismatch without logging payloads.

## Delivery, replay and failure strategy

The queue binds its database to the configured WABA/phone-number pair. Deduplication hashes that scope and Meta's message ID; changing a sender/text in a replay never mutates an accepted job. The database must not be reused with another account. A persisted reply is reused on safe retry instead of invoking AI again.

- `pending -> processing -> sending -> sent` means Meta accepted the reply, **not that the handset received it**. Delivery status callbacks do not generate replies; this pilot does not track handset delivery.
- A process lost while `processing` can be reclaimed after its lease expires. Lease tokens fence out stale workers.
- A process lost while `sending`, a read/write timeout, a malformed success response, or an HTTP 5xx response is `uncertain`: Meta may already have accepted the message. Do not automatically resend it.
- Explicit HTTP 429 rejection and failures known to occur before sending (connect/pool failures) retry with exponential backoff, jitter and bounded `Retry-After`. Five unsuccessful attempts end in `failed`.
- Other HTTP errors, including expired tokens and unverified recipients, are `failed`. Fix credentials or recipient setup and ask the tester to forward again (a new message ID), within a new service window. Do not blindly replay the database.
- Jobs beyond their original reply window are `expired`, not free-form messages sent outside the window. Production follow-up after 24 hours would need approved templates and applicable consent; templates are outside scope.

There is **no exactly-once delivery claim**: a local transaction cannot atomically commit Meta's external send. Quarantining ambiguous sends chooses avoiding duplicate warnings over silently claiming guaranteed delivery. Uncertain replies may require the tester to resend. No retry loops run inside webhook requests.

## Privacy, threat model and backing storage

Forwarded free text and destination numbers are restricted data even though the permitted pilot content is fictional. The operator owns the server/queue; Meta and any enabled AI provider are separate processing boundaries. The operator must approve the processing region and cross-border arrangements before real data is considered.

| Threat | Implemented control / deployment requirement |
| --- | --- |
| Forged/replayed webhook | Raw-body HMAC before parsing; scoped account/phone; stable durable deduplication and timestamp limits. |
| Unwanted cost or unsolicited messages | Explicit pilot allowlist checked on receive and processing; bounded body/batch/queue; no proactive messaging. Add ingress rate/connection limits before exposing the callback. |
| Prompt injection, malicious link or identity confusion | Existing rules/Qwen guardrails; unknown original author; only canonical signal titles in replies; no echoed suspicious text, link fetch, contact action or untrusted AI prose. |
| Secret/PII disclosure | No request/response bodies or recipient IDs in application logs; redacted credential repr; disabled access logs in the documented server command. Configure reverse proxy logs to omit query strings, headers and bodies: GET verification includes the verify token in its URL. |
| Queue theft or loss | Dedicated owner-only directory on encrypted persistent disk, including journal/backups; least-privilege runtime user. SQLite is not itself encrypted. Never commit or bake the queue or tokens into an image. |
| Database/account mix-up | Persisted scope binding; one cohort and account per database. This is not a tenant isolation certification. |
| Partial delivery/crash | Fenced leases, persisted reply and explicit uncertainty quarantine. |

Active text/address/message ID/reply fields are cleared immediately on terminal outcome, or at expiry (within 24 hours of the original event while the worker is running). Hashed identifiers, state, timestamps and fixed reason codes remain for eight days after receipt, exceeding Meta's documented seven-day retry period. SQLite uses secure deletion and rollback journaling, but filesystem snapshots, SSD remanence and backups can outlive SQL deletion; this is **not forensic erasure**. Maintenance runs through the worker, including on restart. If the service is stopped, retention cleanup resumes only on restart; the operator must not leave abandoned volumes/backups indefinitely.

For the initial fictional-data pilot, prefer no content-bearing backups: losing the disk can lose accepted jobs and deduplication, which is an explicit non-HA limitation. If backups are needed, use SQLite's online backup API (or stop the service before copying), encrypt them in the approved region, restrict access and expire within 24 hours. A restored snapshot can omit already-sent markers and duplicate a reply: do not resume outbound processing blindly. Quarantine uncertain/restored work and have testers forward again; preserve available recent replay markers. Preserve this disk across app upgrades, and drain jobs before any replacement. The current Terraform scaffold replaces its VM on bootstrap/image changes and does not provide a separately persistent application data disk.

No PDPA/GDPR/SOC2 certification, image scan, infrastructure review or live penetration-test result is implied. Public launch is blocked on policy eligibility, privacy/legal review, encrypted storage and backup controls, production secrets, HTTPS/rate controls, cost limits, operator monitoring and deployed validation.

## Meta test-number setup

1. In Meta for Developers, create/configure a business app with the WhatsApp use case and the business portfolio/WABA requested by Meta. In WhatsApp API Setup, locate the test business number, its **phone-number ID**, **WABA ID**, and temporary access token. The displayed phone number is not its API ID.
2. Add and verify each test recipient in Meta's test-number recipient list. Obtain the pilot agreement above and separately add those numbers to `WHATSAPP_ALLOWED_SENDERS` in digits-only international format (no `+`, spaces or punctuation). Both lists must allow the recipient.
3. Copy `.env.example` to an ignored `.env` if one does not already exist; do not overwrite existing credentials. Configure the WhatsApp section. Generate a high-entropy verify token separately from the Meta app secret and access token. Keep secrets out of chat, screenshots, shell arguments, source control and Terraform state.
4. Set an absolute `WHATSAPP_DB_PATH` in a dedicated, precreated directory writable only by the app user, e.g. `C:/Users/Nick/Documents/GitHub/no-scam/var/whatsapp/inbox.sqlite3` locally, or `/var/lib/no-scam/whatsapp/inbox.sqlite3` on a server. The application does not create or change directory permissions for you. Use encrypted storage and enforce Windows ACLs or Linux owner-only permissions.
5. Keep rules mode initially. Sync dependencies, then run from the repository root:

   ```sh
   uv sync --locked
   uv run uvicorn src.service.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --timeout-graceful-shutdown 90
   ```

   The webhook and reply worker start together when `WHATSAPP_ENABLED=true`. There is no second worker command. Incomplete enabled configuration or an unavailable/mismatched database fails startup rather than accepting undeliverable jobs. Normal browser functionality is unchanged when WhatsApp is disabled.

6. Arrange a publicly trusted HTTPS callback through an approved tunnel or reverse proxy to this server. Publish **only exact `/webhooks/whatsapp` GET and POST**, with a 256 KiB body limit, connection/rate limits and redacted/disabled access logs. Do not publish `/api/assess`, `/docs`, the rest of the browser backend or plaintext port 8000 as a shortcut. No tunnel, TLS certificate, firewall or public deployment is created by this implementation.
7. In Meta's WhatsApp webhook configuration, enter your HTTPS callback plus `/webhooks/whatsapp` and the matching verify token; complete verification. Subscribe the app to the WABA's `messages` webhook field/account as directed in Meta's console. Verify an actual inbound event reaches the right app/account, not just the challenge.
8. From an allowed recipient, send/forward fictional text to Meta's **test number**. WatchDog should send an automatic contextual reply. If the temporary token expires, replace it in runtime configuration and restart. Treat temporary tokens as short-lived; check their actual expiry in Meta.
9. Only after separate AI agreement, set `WHATSAPP_ANALYSIS_MODE=auto`, configure the existing Qwen provider and restart. The reply labels whether Qwen was available; failures fall back to rules. This mode transmits full submitted text to the configured model provider (free-text PII is not automatically redacted), without forwarding the sender's profile, phone number or webhook envelope.

Use `WHATSAPP_GRAPH_VERSION=v23.0` only if that version is still supported for your app; it matches Meta's documented get-started example, not a claim to be the latest version. An explicit version is required so upgrades can be tested. Outbound URL is fixed to `https://graph.facebook.com/<version>/<phone-number-id>/messages`; credentials cannot select an arbitrary host. Requests use `messaging_product`, `recipient_type=individual`, `to`, `type=text`, `text.preview_url=false` and `context.message_id`.

For the existing read-only Docker image, mount a dedicated persistent directory at the configured database parent, writable by container UID/GID 10001, and supply secrets via the protected runtime env file. Keep the rest of the root filesystem read-only. The ECS service template currently has **no such mount or public HTTPS proxy**; do not enable WhatsApp there without deliberately provisioning these. No cloud settings are changed by this feature.

## Operations, rollback and acceptance

Application logs record only event names/outcome reason codes (queue unavailable, worker failure, sent, failed, uncertain, expired); no raw messages, phone IDs, Graph bodies or credentials. HTTPX transport logging is suppressed for the Graph sender. The operator should inspect local aggregate queue state/count/oldest age, monitor free disk and worker process health, and alert on queued age above two minutes, any uncertain/failed reply, recurring 503s, expired tokens and certificate expiry. `/health` remains process liveness, **not proof of Meta or worker delivery**. No hosted dashboard/alerts are provisioned.

Stop the service before account/secret changes, update protected runtime configuration, and restart. Keep the database with the same account. To roll back the application, first stop ingestion/worker and drain or quarantine pending work; do not run old code over a newer database schema or delete the queue to fix an error. `WHATSAPP_ENABLED=false` stops routes/worker; it does not erase data. Operator deletion/retention work still applies to a disabled queue.

Local test matrix: challenge valid/invalid/disabled; exact-body signature/tampering; malformed and oversized bodies; batches and account/recipient filtering; empty/long/non-text guidance; status-only/no loops; duplicate/restart/concurrent claims; durable-commit failure/backpressure; original timestamps and 24-hour boundary; AI fallback and no identity leakage; Graph acceptance/rate limits/auth errors/timeouts; crash after send and fenced leases; terminal data clearing/retention; existing app regressions. Run `WATCHDOG_LLM=offline uv run --locked pytest` with network calls mocked. Tests must disable live WhatsApp credentials by default.

Validation recorded on 2026-11-19: all 199 offline tests passed, including 113 WhatsApp tests. The same 113 WhatsApp tests passed on Python 3.12.13 (the container's Python minor version). One integration test starts a real local Uvicorn HTTP listener, accepts a signed POST, and verifies automatic background delivery using an injected fake Meta transport; it also checks the existing health/meta endpoints. No Meta credentials, public callback, handset delivery, Docker build or cloud deployment was exercised.

Live acceptance (requires the operator's Meta account and HTTPS endpoint): verify challenge, forward one fictional scam example and one neutral message, check contextual replies and analysis labels, send an image and oversized text, redeliver a signed event without a duplicate reply, restart with pending work, simulate token expiry safely, inspect logs for secrets and verify restricted callback exposure. Record actual outcomes separately; passing local mocks is not proof of Meta setup or handset delivery.

## Backing sources and rollout gates

- [Meta get started](https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started): test resources, recipient setup, tokens and send example.
- [Create a webhook endpoint](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint/): trusted HTTPS, verification and signature validation.
- [Webhook overview](https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/overview): subscriptions, event delivery and retries.
- [Send messages](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages): text messages and customer-service messaging.
- [Pricing](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing): market/category rates and current service-message rules. Incoming user messages are not charged by Meta; do not assume all service replies are free. The page checked for this plan describes charging from 2026-10-01 with a 1,000-service-message monthly allowance for applicable ordinary traffic; confirm your account/market and actual bill before rollout.
- [AI providers](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/ai-providers): special eligibility/restrictions and pricing. A narrow scam-assistance purpose does not by itself prove exemption or Meta approval. Obtain confirmation from Meta or an authorized provider before public launch; geography can matter.

Rollout: local mocked verification -> consented fictional-data Meta test-number pilot -> measured reliability/cost and explicit policy/privacy sign-off -> approved production number, scoped system-user token, production storage/monitoring and deployed tests -> wider onboarding. Production system-user token setup should grant only required messaging permissions/assets (`whatsapp_business_messaging`; management permissions only for needed setup operations). Public onboarding, templates, media/OCR/voice, delivery receipts, billing, passive inbox access and real-user production compliance remain out of scope.
