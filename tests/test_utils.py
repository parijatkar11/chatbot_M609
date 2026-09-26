import logging
from datetime import datetime

from backend.utils import (
    ApprovalManager,
    ConversationManager,
    extract_entities,
    format_timestamp,
    log_event,
    sanitize_input,
)


def test_conversation_manager_lifecycle():
    manager = ConversationManager()
    assert manager.get_conversation("missing") is None
    assert manager.get_messages("missing") == []

    created = manager.create_conversation("c1")
    assert created["status"] == "active"
    assert created["messages"] == []
    manager.add_message("c1", "user", "Hello")
    manager.add_message("c2", "assistant", "Welcome")
    assert manager.get_messages("c1")[0]["content"] == "Hello"
    assert manager.get_conversation("c2")["messages"][0]["role"] == "assistant"

    manager.clear_messages("c1")
    manager.clear_messages("unknown")
    assert manager.get_messages("c1") == []
    assert "c1" in manager.get_all_conversations()

    manager.delete_conversation("c2")
    manager.delete_conversation("unknown")
    assert manager.get_conversation("c2") is None


def test_approval_manager_pending_and_transitions():
    manager = ApprovalManager()
    assert manager.get_approval("missing") is None
    manager.approve("missing")
    manager.reject("missing")

    manager.create_approval("c1", "transfer", "Approve transfer")
    manager.create_approval("c2", "close", "Close account")
    assert manager.get_pending() == {"c1": manager.get_approval("c1"), "c2": manager.get_approval("c2")}
    manager.approve("c1")
    assert manager.get_approval("c1")["status"] == "approved"
    assert "approved_at" in manager.get_approval("c1")
    manager.reject("c2")
    assert manager.get_approval("c2")["status"] == "rejected"
    assert "rejected_at" in manager.get_approval("c2")
    assert manager.get_pending() == {}


def test_format_timestamp_handles_datetime_and_other_values():
    value = datetime(2024, 1, 2, 3, 4, 5)
    assert format_timestamp(value) == "2024-01-02T03:04:05"
    assert format_timestamp("already-formatted") == "already-formatted"
    assert format_timestamp(42) == "42"


def test_extract_entities_reports_all_indicators():
    entities = extract_entities("Email me at a@example.com about $20")
    assert entities == {
        "has_email": True,
        "has_phone": True,
        "has_currency": True,
        "text_length": len("Email me at a@example.com about $20"),
        "word_count": 6,
    }
    plain = extract_entities("hello world")
    assert plain["has_email"] is False
    assert plain["has_phone"] is False
    assert plain["has_currency"] is False


def test_sanitize_input_normalizes_whitespace_and_limits_length():
    assert sanitize_input("  hello  \n   there  ") == "hello there"
    assert sanitize_input("x" * 5000) == "x" * 5000
    assert sanitize_input("x" * 5001) == "x" * 5000


def test_log_event_uses_info_level(caplog):
    with caplog.at_level(logging.INFO, logger="backend.utils"):
        log_event("message_received", {"conversation_id": "c1"})
    assert "Event: message_received" in caplog.text
    assert "conversation_id" in caplog.text
