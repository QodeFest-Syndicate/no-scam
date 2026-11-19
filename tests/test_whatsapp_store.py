import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Barrier

import pytest

from src.service import whatsapp_store
from src.service.whatsapp_store import IncomingMessage, QueueFull, WhatsAppStore


NOW = 1_000_000
SCOPE = "account-a:phone-a"
REPLY = "Pause and verify through a known contact route."


def message(message_id="message-1", sender="sender-1", *, message_at=NOW):
    return IncomingMessage(message_id, sender, "Forwarded message to check", "text", message_at)


@pytest.fixture
def store(tmp_path: Path):
    queue = WhatsAppStore(tmp_path / "queue.sqlite3", SCOPE)
    queue.initialize()
    return queue


def rows(store):
    # Always use an independent connection: uncommitted writes must not pass assertions.
    with closing(sqlite3.connect(store.path)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM jobs ORDER BY rowid")]


def only_row(store):
    result = rows(store)
    assert len(result) == 1
    return result[0]


def assert_terminal(row, state, reason):
    assert row["state"] == state
    assert row["reason"] == reason
    for field in ("text", "sender", "message_id", "reply", "lease"):
        assert row[field] is None, field
    assert row["key"]


def test_pilot_limits_and_time_constants():
    assert whatsapp_store.REPLY_WINDOW == 23 * 60 * 60 + 55 * 60
    assert whatsapp_store.RETENTION == 8 * 24 * 60 * 60
    assert whatsapp_store.LEASE_SECONDS == 120
    assert whatsapp_store.MAX_ATTEMPTS == 5
    assert whatsapp_store.MAX_ACTIVE == 500
    assert whatsapp_store.MAX_PER_SENDER == 20


def test_duplicate_is_durable_across_reopened_store(store):
    incoming = message()
    store.enqueue([incoming, incoming], NOW)
    original = only_row(store)
    assert original["message_id"] == incoming.message_id
    assert original["sender"] == incoming.sender
    assert original["text"] == incoming.text
    assert original["kind"] == incoming.kind
    assert original["message_at"] == incoming.message_at
    assert original["received_at"] == NOW
    assert original["available_at"] == NOW
    assert original["state"] == "pending"
    assert original["attempts"] == 0

    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    reopened.enqueue([incoming], NOW + 10)
    assert only_row(store) == original

    job = reopened.claim(NOW + 10)
    assert job is not None
    assert job.key == original["key"]
    assert job.message_id == incoming.message_id
    assert job.sender == incoming.sender
    assert job.text == incoming.text
    assert job.kind == incoming.kind
    assert job.message_at == incoming.message_at
    assert job.attempts == 1
    assert job.reply is None
    leased = only_row(store)
    assert leased["state"] == "processing"
    assert leased["lease"] == job.lease
    assert leased["lease_until"] == NOW + 10 + whatsapp_store.LEASE_SECONDS
    assert leased["attempts"] == 1
    assert store.claim(NOW + 10) is None


@pytest.mark.parametrize("scope", ["account-b:phone-a", "account-a:phone-b"])
def test_scope_mismatch_refuses_reuse_without_changing_database(store, scope):
    store.enqueue([message()], NOW)
    original = rows(store)
    with pytest.raises(ValueError, match="another account/phone"):
        WhatsAppStore(store.path, scope).initialize()

    with closing(sqlite3.connect(store.path)) as db:
        assert db.execute("SELECT scope FROM identity WHERE id=1").fetchone() == (SCOPE,)
    assert rows(store) == original
    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    assert reopened.claim(NOW) is not None


@pytest.mark.parametrize("state", ["pending", "processing", "sending"])
def test_changed_duplicate_cannot_mutate_original_job(store, state):
    store.enqueue([message()], NOW)
    if state != "pending":
        job = store.claim(NOW)
        assert job is not None
        if state == "sending":
            assert store.prepare_send(job, REPLY, NOW + 1)
    original = only_row(store)
    assert original["state"] == state

    changed = IncomingMessage("message-1", "other-sender", None, "image", NOW + 100)
    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    reopened.enqueue([changed, changed], NOW + 100)
    assert only_row(store) == original


@pytest.mark.parametrize("limit", ["MAX_ACTIVE", "MAX_PER_SENDER"])
def test_queue_full_rolls_back_entire_batch(store, monkeypatch, limit):
    monkeypatch.setattr(whatsapp_store, "MAX_ACTIVE", 10)
    monkeypatch.setattr(whatsapp_store, "MAX_PER_SENDER", 10)
    monkeypatch.setattr(whatsapp_store, limit, 2)
    existing = message("existing")
    store.enqueue([existing], NOW)
    original = rows(store)

    with pytest.raises(QueueFull):
        store.enqueue([existing, message("would-fit"), message("overflow")], NOW + 1)
    assert rows(store) == original

    # The failed batch must not leave either the inserted job or its replay marker.
    store.enqueue([message("would-fit")], NOW + 2)
    persisted = rows(store)
    assert [row["message_id"] for row in persisted] == ["existing", "would-fit"]
    assert persisted[1]["received_at"] == NOW + 2


@pytest.mark.parametrize("limit", ["MAX_ACTIVE", "MAX_PER_SENDER"])
@pytest.mark.parametrize("state", ["pending", "processing", "sending"])
def test_duplicates_acknowledged_at_capacity(store, monkeypatch, limit, state):
    monkeypatch.setattr(whatsapp_store, "MAX_ACTIVE", 10)
    monkeypatch.setattr(whatsapp_store, "MAX_PER_SENDER", 10)
    monkeypatch.setattr(whatsapp_store, limit, 1)
    incoming = message()
    store.enqueue([incoming], NOW)
    if state != "pending":
        job = store.claim(NOW)
        assert job is not None
        if state == "sending":
            assert store.prepare_send(job, REPLY, NOW)
    original = only_row(store)
    assert original["state"] == state

    store.enqueue([incoming, incoming], NOW + 1)
    assert only_row(store) == original
    with pytest.raises(QueueFull):
        store.enqueue([message("new-message")], NOW + 1)
    assert only_row(store) == original


@pytest.mark.parametrize("state", ["pending", "processing", "sending"])
def test_per_sender_cap_does_not_block_other_senders(store, monkeypatch, state):
    monkeypatch.setattr(whatsapp_store, "MAX_ACTIVE", 3)
    monkeypatch.setattr(whatsapp_store, "MAX_PER_SENDER", 1)
    store.enqueue([message()], NOW)
    if state != "pending":
        job = store.claim(NOW)
        assert job is not None
        if state == "sending":
            assert store.prepare_send(job, REPLY, NOW)

    with pytest.raises(QueueFull):
        store.enqueue([message("same-sender")], NOW + 1)
    store.enqueue([message("other-message", "sender-2")], NOW + 1)
    persisted = rows(store)
    assert [(row["sender"], row["state"]) for row in persisted] == [
        ("sender-1", state), ("sender-2", "pending")
    ]


def test_concurrent_claim_from_separate_stores_grants_only_one_lease(store):
    store.enqueue([message()], NOW)
    other = WhatsAppStore(store.path, SCOPE)
    other.initialize()
    barrier = Barrier(2)

    def claim_together(queue):
        barrier.wait(timeout=10)
        return queue.claim(NOW)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(claim_together, queue) for queue in (store, other)]
        results = [future.result(timeout=10) for future in futures]

    jobs = [job for job in results if job is not None]
    assert len(jobs) == 1
    assert results.count(None) == 1
    persisted = only_row(store)
    assert persisted["state"] == "processing"
    assert persisted["attempts"] == jobs[0].attempts == 1
    assert persisted["lease"] == jobs[0].lease
    assert persisted["lease_until"] == NOW + whatsapp_store.LEASE_SECONDS


def test_processing_crash_reclaims_at_lease_boundary_and_fences_stale_job(store):
    store.enqueue([message()], NOW)
    stale = store.claim(NOW)
    assert stale is not None
    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    lease_end = NOW + whatsapp_store.LEASE_SECONDS
    assert reopened.claim(lease_end - 1) is None
    current = reopened.claim(lease_end)
    assert current is not None
    assert current.key == stale.key
    assert current.lease != stale.lease
    assert current.attempts == 2
    assert current.text == stale.text
    original = only_row(store)
    assert original["lease"] == current.lease
    assert original["lease_until"] == lease_end + whatsapp_store.LEASE_SECONDS

    assert not store.prepare_send(stale, "Stale reply", lease_end + 1)
    assert only_row(store) == original
    store.finish(stale, "failed", "stale_worker")
    assert only_row(store) == original
    store.retry(stale, lease_end + 30, "stale_retry")
    assert only_row(store) == original
    # retry's terminal-expiry branch must also respect the replacement lease.
    store.retry(stale, NOW + whatsapp_store.REPLY_WINDOW, "stale_expiry")
    assert only_row(store) == original

    assert reopened.prepare_send(current, REPLY, lease_end + 1)
    reopened.finish(current, "sent", "delivered")
    assert_terminal(only_row(store), "sent", "delivered")


def test_expired_processing_lease_cannot_prepare_without_reclaim(store):
    store.enqueue([message()], NOW)
    job = store.claim(NOW)
    assert job is not None
    original = only_row(store)
    assert not store.prepare_send(job, REPLY, NOW + whatsapp_store.LEASE_SECONDS)
    assert only_row(store) == original


def test_crash_after_prepare_becomes_uncertain_and_never_resends(store):
    incoming = message()
    store.enqueue([incoming], NOW)
    job = store.claim(NOW)
    assert job is not None
    prepared_at = NOW + 30
    assert store.prepare_send(job, REPLY, prepared_at)
    prepared = only_row(store)
    assert prepared["state"] == "sending"
    assert prepared["text"] is None
    assert prepared["reply"] == REPLY
    assert prepared["lease_until"] == prepared_at + whatsapp_store.LEASE_SECONDS

    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    # Preparing a send extends the lease beyond the original processing lease.
    assert reopened.claim(NOW + whatsapp_store.LEASE_SECONDS) is None
    lease_end = prepared_at + whatsapp_store.LEASE_SECONDS
    assert reopened.claim(lease_end - 1) is None
    assert only_row(store) == prepared
    assert reopened.claim(lease_end) is None
    terminal = only_row(store)
    assert_terminal(terminal, "uncertain", "send_interrupted")
    assert terminal["attempts"] == 1
    assert terminal["key"] == job.key

    assert not store.prepare_send(job, "Must not resend", lease_end + 1)
    store.finish(job, "sent", "late_success")
    store.retry(job, lease_end + 1, "late_retry")
    reopened.enqueue([incoming], lease_end + 1)
    assert reopened.claim(lease_end + 1) is None
    assert only_row(store) == terminal


def test_retry_preserves_prepared_reply_and_clears_raw_text_durably(store):
    store.enqueue([message()], NOW)
    first = store.claim(NOW)
    assert first is not None
    assert store.prepare_send(first, REPLY, NOW + 1)
    prepared = only_row(store)
    assert prepared["text"] is None
    assert prepared["reply"] == REPLY

    available_at = NOW + 60
    store.retry(first, available_at, "rate_limited")
    pending = only_row(store)
    assert pending["state"] == "pending"
    assert pending["reason"] == "rate_limited"
    assert pending["available_at"] == available_at
    assert pending["lease"] is None
    assert pending["attempts"] == 1
    assert pending["text"] is None
    assert pending["reply"] == REPLY
    assert pending["sender"] == first.sender
    assert pending["message_id"] == first.message_id

    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    assert reopened.claim(available_at - 1) is None
    assert only_row(store) == pending
    second = reopened.claim(available_at)
    assert second is not None
    assert second.key == first.key
    assert second.lease != first.lease
    assert second.attempts == 2
    assert second.text is None
    assert second.reply == REPLY
    assert reopened.prepare_send(second, second.reply, available_at)
    reopened.finish(second, "sent", "delivered")
    assert_terminal(only_row(store), "sent", "delivered")


@pytest.mark.parametrize("recovery", ["retry", "processing_crash"])
def test_attempts_exhaustion_is_terminal(store, recovery):
    incoming = message()
    store.enqueue([incoming], NOW)
    now = NOW
    for attempt in range(1, whatsapp_store.MAX_ATTEMPTS + 1):
        job = store.claim(now)
        assert job is not None
        assert job.attempts == attempt
        assert only_row(store)["attempts"] == attempt
        if recovery == "retry":
            assert store.prepare_send(job, REPLY, now)
            store.retry(job, now + 1, "transient_failure")
            if attempt < whatsapp_store.MAX_ATTEMPTS:
                assert only_row(store)["state"] == "pending"
            else:
                assert_terminal(only_row(store), "failed", "attempts_exhausted")
            now += 1
        else:
            now += whatsapp_store.LEASE_SECONDS

    assert store.claim(now) is None
    terminal = only_row(store)
    assert_terminal(terminal, "failed", "attempts_exhausted")
    assert terminal["attempts"] == whatsapp_store.MAX_ATTEMPTS
    store.enqueue([incoming], now + 1)
    assert store.claim(now + 1) is None
    assert only_row(store) == terminal


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_reply_window_checked_again_before_send(store, offset):
    window_end = NOW + 30
    incoming = message(message_at=window_end - whatsapp_store.REPLY_WINDOW)
    store.enqueue([incoming], NOW)
    job = store.claim(NOW)
    assert job is not None
    original = only_row(store)
    send_at = window_end + offset
    assert store.prepare_send(job, REPLY, send_at) is (offset < 0)
    if offset < 0:
        persisted = only_row(store)
        assert persisted["state"] == "sending"
        assert persisted["text"] is None
        assert persisted["reply"] == REPLY
    else:
        # The processing lease is still valid; only the reply window has closed.
        assert original["lease_until"] > send_at
        assert only_row(store) == original
        assert store.claim(send_at) is None
        assert_terminal(only_row(store), "expired", "window_closed")


def test_expired_pending_message_is_never_claimed(store):
    incoming = message(message_at=NOW - whatsapp_store.REPLY_WINDOW)
    store.enqueue([incoming], NOW)
    assert store.claim(NOW) is None
    terminal = only_row(store)
    assert_terminal(terminal, "expired", "window_closed")
    assert terminal["attempts"] == 0


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_retry_cannot_schedule_at_or_beyond_reply_window(store, offset):
    store.enqueue([message()], NOW)
    job = store.claim(NOW)
    assert job is not None
    assert store.prepare_send(job, REPLY, NOW)
    available_at = NOW + whatsapp_store.REPLY_WINDOW + offset
    store.retry(job, available_at, "transient_failure")
    persisted = only_row(store)
    if offset < 0:
        assert persisted["state"] == "pending"
        assert persisted["available_at"] == available_at
        assert persisted["lease"] is None
        assert persisted["reply"] == REPLY
        assert persisted["text"] is None
        assert store.claim(available_at) is not None
    else:
        assert_terminal(persisted, "expired", "window_closed")
        assert store.claim(NOW + 1) is None


@pytest.mark.parametrize("state", ["sent", "failed", "uncertain", "expired"])
def test_terminal_fields_scrubbed_immediately_and_marker_retained_for_eight_days(store, state):
    # Retention starts at receipt, not the earlier message timestamp.
    incoming = message(message_at=NOW - 3600)
    store.enqueue([incoming], NOW)
    job = store.claim(NOW)
    assert job is not None
    assert store.prepare_send(job, REPLY, NOW + 1)
    prepared = only_row(store)
    assert prepared["reply"] == REPLY
    assert prepared["sender"] == incoming.sender
    assert prepared["message_id"] == incoming.message_id
    store.finish(job, state, "terminal_result")
    terminal = only_row(store)
    assert_terminal(terminal, state, "terminal_result")
    assert terminal["key"] == job.key
    assert terminal["received_at"] == NOW

    reopened = WhatsAppStore(store.path, SCOPE)
    reopened.initialize()
    reopened.enqueue([incoming], NOW + 2)
    assert only_row(store) == terminal
    purge_at = NOW + whatsapp_store.RETENTION
    assert reopened.claim(purge_at - 1) is None
    assert only_row(store) == terminal
    # Replays neither restore sensitive fields nor extend marker retention.
    reopened.enqueue([incoming], purge_at - 1)
    assert only_row(store) == terminal
    assert reopened.claim(purge_at) is None
    assert rows(store) == []


@pytest.mark.parametrize("state", ["sent", "failed", "uncertain", "expired"])
def test_finishing_processing_job_scrubs_raw_text_and_releases_capacity(store, monkeypatch, state):
    monkeypatch.setattr(whatsapp_store, "MAX_ACTIVE", 1)
    monkeypatch.setattr(whatsapp_store, "MAX_PER_SENDER", 1)
    store.enqueue([message()], NOW)
    job = store.claim(NOW)
    assert job is not None
    assert only_row(store)["text"] is not None
    store.finish(job, state, "terminal_result")
    assert_terminal(only_row(store), state, "terminal_result")

    store.enqueue([message("replacement")], NOW + 1)
    persisted = rows(store)
    assert len(persisted) == 2
    assert persisted[0]["key"] == job.key
    assert persisted[1]["message_id"] == "replacement"
    assert persisted[1]["state"] == "pending"
