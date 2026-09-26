import runpy
from pathlib import Path

import uvicorn

from backend import main


def test_root_health_and_unhealthy_fallback(api_client, monkeypatch):
    root = api_client.get("/")
    assert root.status_code == 200
    assert root.json()["health"] == "/health"

    health = api_client.get("/health")
    assert health.json()["status"] == "healthy"
    assert health.json()["graph_nodes"] == 5

    def fail_graph():
        raise RuntimeError("not ready")

    monkeypatch.setattr(main, "get_chatbot_graph", fail_graph)
    unhealthy = api_client.get("/health")
    assert unhealthy.json() == {"status": "unhealthy", "error": "not ready"}


def test_conversation_id_helpers(api_client):
    generated = main.generate_conversation_id()
    assert generated.startswith("conv_")
    assert len(generated) == 13

    first = main.get_or_create_conversation()
    assert first in main.conversations
    assert main.get_or_create_conversation(first) == first
    second = main.get_or_create_conversation("unknown-id")
    assert second != "unknown-id"
    assert second in main.conversations


def test_chat_creates_conversation_and_tracks_approval(api_client):
    response = api_client.post("/chat", json={"message": "What is my account balance?"})
    assert response.status_code == 200
    result = response.json()
    conversation_id = result["conversation_id"]
    assert result["action_required"] is True
    assert result["action_type"] == "account_number_required"
    assert len(main.conversations[conversation_id]["messages"]) == 2
    assert main.approval_queue[conversation_id]["status"] == "pending"

    follow_up = api_client.post(
        "/chat",
        json={"message": "account number 123456 balance", "conversation_id": conversation_id},
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["customer_details"]["account_number"] == "123456"


def test_chat_rejects_blank_message_and_converts_unexpected_errors(api_client, monkeypatch):
    blank = api_client.post("/chat", json={"message": "   "})
    assert blank.status_code == 400
    assert blank.json()["detail"] == "Message cannot be empty"

    class BrokenGraph:
        def process_message(self, **_kwargs):
            raise RuntimeError("graph failure")

    monkeypatch.setattr(main, "get_chatbot_graph", lambda: BrokenGraph())
    failed = api_client.post("/chat", json={"message": "hello"})
    assert failed.status_code == 500
    assert "graph failure" in failed.json()["detail"]


def test_conversation_start_get_clear_delete_and_list(api_client):
    welcome = api_client.post("/conversation/start", json={})
    assert welcome.status_code == 200
    conversation_id = welcome.json()["conversation_id"]
    assert welcome.json()["response"].startswith("Welcome")

    started = api_client.post("/conversation/start", json={"initial_message": "hello"})
    assert started.status_code == 200
    started_id = started.json()["conversation_id"]
    assert main.conversations[started_id]["messages"]

    detail = api_client.get(f"/conversation/{conversation_id}")
    assert detail.status_code == 200
    assert detail.json()["message_count"] == 0
    assert api_client.get("/conversation/missing").status_code == 404

    assert api_client.post(f"/conversation/{started_id}/clear").status_code == 200
    assert main.conversations[started_id]["messages"] == []
    assert api_client.post("/conversation/missing/clear").status_code == 404

    main.approval_queue[started_id] = {"status": "pending"}
    assert api_client.delete(f"/conversation/{started_id}").status_code == 200
    assert started_id not in main.conversations
    assert started_id not in main.approval_queue
    assert api_client.delete("/conversation/missing").status_code == 404

    listing = api_client.get("/conversations").json()
    assert listing["total"] == len(listing["conversations"])


def test_conversation_generic_error_handlers(api_client):
    main.conversations["bad-date"] = {"created_at": None, "messages": [], "user_context": {}}
    assert api_client.get("/conversation/bad-date").status_code == 500


def test_approval_routes_and_pending_filter(api_client):
    assert api_client.get("/approval/pending").json() == {"pending_approvals": [], "count": 0}
    main.approval_queue.update(
        {
            "pending": {"status": "pending", "action_type": "transfer", "message": "Approve", "timestamp": "now"},
            "approved": {"status": "approved", "action_type": "x", "message": "x", "timestamp": "then"},
        }
    )
    pending = api_client.get("/approval/pending").json()
    assert pending["count"] == 1
    assert pending["pending_approvals"][0]["conversation_id"] == "pending"

    assert api_client.post("/approval/missing/approve").status_code == 404
    approved = api_client.post("/approval/pending/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert api_client.post("/approval/missing/reject").status_code == 404
    rejected = api_client.post("/approval/approved/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_graph_routes(api_client):
    structure = api_client.get("/graph/structure")
    assert structure.status_code == 200
    assert structure.json()["node_descriptions"]["input_validation"] == "Input Validation"
    assert api_client.get("/graph/execution-history/unknown").status_code == 404

    response = api_client.post("/chat", json={"message": "hello"})
    conversation_id = response.json()["conversation_id"]
    history = api_client.get(f"/graph/execution-history/{conversation_id}")
    assert history.status_code == 200
    assert history.json()["final_state"] == "response_generated"
    assert api_client.post("/graph/reset").status_code == 200


def test_customer_memory_routes(api_client):
    started = api_client.post("/conversation/start", json={}).json()
    conversation_id = started["conversation_id"]
    details = api_client.get(f"/customer/{conversation_id}/details")
    assert details.status_code == 200
    assert details.json()["account_number"] is None

    api_client.post("/chat", json={"message": "hello", "conversation_id": conversation_id})
    interactions = api_client.get(f"/customer/{conversation_id}/interactions?limit=1")
    assert interactions.status_code == 200
    assert interactions.json()["total_count"] == 1

    exported = api_client.get(f"/customer/{conversation_id}/export")
    assert exported.status_code == 200
    assert exported.json()["conversation_id"] == conversation_id
    assert api_client.get("/customer/missing/export").status_code == 404

    assert api_client.delete(f"/customer/{conversation_id}/clear").status_code == 200
    assert api_client.get("/customer/missing/details").status_code == 200
    assert api_client.get("/customers/all").json()["total_customers"] >= 1


def test_statistics_and_customer_data_routes(api_client):
    response = api_client.post("/chat", json={"message": "balance"})
    conversation_id = response.json()["conversation_id"]
    stats = api_client.get("/stats").json()
    assert stats["total_conversations"] == 1
    assert stats["total_messages"] == 2
    assert stats["pending_approvals"] == 1

    assert api_client.delete(f"/customer/{conversation_id}/clear").status_code == 200
    assert api_client.get("/customers/all").json()["total_customers"] == 0


def test_start_conversation_error_response(api_client, monkeypatch):
    def fail_conversation(_conversation_id=None):
        raise RuntimeError("cannot create")

    monkeypatch.setattr(main, "get_or_create_conversation", fail_conversation)
    response = api_client.post("/conversation/start", json={})
    assert response.status_code == 500
    assert "cannot create" in response.json()["detail"]


def test_uvicorn_entrypoint_runs(monkeypatch):
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(main.settings, "api_host", "0.0.0.0")
    monkeypatch.setattr(main.settings, "api_port", 8123)
    monkeypatch.setattr(main.settings, "api_debug", True)
    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    monkeypatch.syspath_prepend(str(backend_dir))

    runpy.run_path(str(backend_dir / "main.py"), run_name="__main__")

    assert calls
    assert calls[0][1]["host"] == "0.0.0.0"
    assert calls[0][1]["port"] == 8123
    assert calls[0][1]["reload"] is True
