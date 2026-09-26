import pytest

from backend.graph import (
    ChatbotGraph,
    CustomerMemoryManager,
    get_chatbot_graph,
    reset_graph,
)


@pytest.fixture
def graph():
    return ChatbotGraph()


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("What is my account balance?", "balance"),
        ("I need a year end statement", "year_end_statement"),
        ("Show my last transaction", "last_transaction"),
        ("Can I get a statement?", "statement"),
        ("Tell me about a mortgage", "mortgage_info"),
        ("What is the interest rate?", "interest_rates"),
        ("I want to apply", "application"),
        ("Can I refinance my home?", "refinance"),
        ("What is my monthly payment?", "payment"),
        ("What credit score do I need to qualify?", "eligibility"),
        ("Hello there", "general"),
    ],
)
def test_process_message_classifies_intent_and_runs_all_nodes(graph, message, intent):
    result = graph.process_message(message, f"conversation-{intent}")

    assert result["user_context"]["detected_intent"] == intent
    assert result["nodes_executed"] == list(graph.graph["nodes"])
    assert graph.get_execution_history(f"conversation-{intent}")["final_state"] == "response_generated"
    assert graph.get_customer_interactions(f"conversation-{intent}")[-1]["intent"] == intent


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("account number 123456", "123456"),
        ("ACCOUNT # 123456", "123456"),
        ("acct: 123456", "123456"),
        ("#12345678", "12345678"),
        ("my account is 123456", "123456"),
        ("the account no. 123456", "123456"),
        ("no account details", None),
    ],
)
def test_extract_customer_info_patterns(text, expected):
    result = CustomerMemoryManager().extract_customer_info_from_message(text)
    assert result == {"account_number": expected, "reason_for_contact": None}


def test_memory_manager_lifecycle_and_context():
    memory = CustomerMemoryManager()
    first = memory.initialize_customer("c1", "123456")
    memory.update_account_number("c1", "654321")
    memory.update_reason_for_contact("c1", "balance")
    memory.add_to_interaction_history("c1", "balance?", "$500", "balance")
    memory.add_to_interaction_history("c1", "statement", "unavailable", "statement")

    assert first["account_number"] == "123456"
    assert memory.initialize_customer("c1")["account_number"] == "654321"
    assert memory.get_customer_details("c1")["reason_for_contact"] == "balance"
    context = memory.get_conversation_context("c1", limit=1)
    assert context["total_interactions"] == 2
    assert len(context["recent_interactions"]) == 1
    assert context["recent_interactions"][0]["intent"] == "statement"
    assert memory.get_conversation_context("c1", limit=0)["recent_interactions"]
    assert memory.export_customer_data("unknown") == {}
    assert memory.export_customer_data("c1")["conversation_id"] == "c1"
    assert memory.get_all_customers()["c1"]["account_number"] == "654321"

    memory.clear_customer_data("c1")
    memory.clear_customer_data("missing")
    assert memory.get_all_customers() == {}
    assert memory.get_conversation_context("new")["total_interactions"] == 0


def test_customer_info_extraction_updates_customer(graph):
    state = {
        "conversation_id": "c1",
        "current_input": "My account number is 987654",
        "customer_details": {"account_number": None},
        "user_context": {},
    }

    result = graph._extract_customer_info(state)

    assert result["customer_details"]["account_number"] == "987654"
    assert result["user_context"]["customer_context"]["account_number"] == "987654"
    assert result["internal_state"] == "customer_info_extracted"


def test_input_validation_handles_empty_valid_and_oversized(graph):
    state = {"current_input": "   "}
    assert graph._validate_input(state)["internal_state"] == "validation_failed"
    assert state["response"] == "Error: Empty input received"

    state = {"current_input": "x" * 5001}
    assert graph._validate_input(state)["response"] == "Error: Input too long (max 5000 characters)"

    state = {"current_input": " valid "}
    assert graph._validate_input(state)["internal_state"] == "input_validated"


@pytest.mark.parametrize("message", ["balance", "statement", "mortgage", "hello"])
def test_response_generation_sets_expected_action_state(graph, message):
    result = graph.process_message(message, f"response-{message}")

    if message == "balance":
        assert result["action_required"] is True
        assert result["action_type"] == "account_number_required"
    else:
        assert result["action_required"] is False
        assert result["action_type"] == "none"
    assert result["response"]


def test_balance_response_with_account_number(graph, monkeypatch):
    monkeypatch.setattr("backend.graph.random.randint", lambda _low, _high: 500)
    result = graph.process_message("account number 123456 balance", "balance-with-account")

    assert result["response"] == "Your account balance is: $500.00"
    assert result["user_context"]["account_balance"] == 500
    assert result["action_required"] is False
    assert result["customer_details"]["account_number"] == "123456"


def test_context_retrieval_and_user_context(graph):
    state = {
        "conversation_id": "c1",
        "messages": [{"content": "hello"}],
        "user_context": {"detected_intent": "general", "custom": True},
    }

    result = graph._retrieve_context(state)

    assert result["user_context"]["intent"] == "general"
    assert result["user_context"]["message_count"] == 1
    assert result["user_context"]["custom"] is True
    assert result["internal_state"] == "context_retrieved"


def test_graph_structure_and_customer_helpers(graph):
    assert graph.get_graph_structure()["start_node"] == "input_validation"
    assert graph.get_graph_structure()["node_descriptions"]["response_generation"] == "Response Generation"
    assert graph.get_execution_history("unknown") == {}
    assert graph.get_customer_details("c1")["previous_interactions"] == []
    assert graph.get_customer_interactions("c1") == []
    assert graph.export_customer_data("unknown") == {}
    graph.process_message("hello", "c1")
    assert graph.get_all_customers()["c1"]["reason_for_contact"] is None
    graph.clear_customer_data("c1")
    assert graph.export_customer_data("c1") == {}


def test_process_message_stops_on_a_repeated_node(graph):
    graph.graph["edges"] = [("input_validation", "input_validation")]
    result = graph.process_message("hello", "cycle")
    assert result["nodes_executed"] == ["input_validation"]
    assert graph.get_execution_history("cycle")["final_state"] == "input_validated"


def test_graph_singleton_can_be_reset():
    reset_graph()
    first = get_chatbot_graph()
    assert get_chatbot_graph() is first
    reset_graph()
    assert get_chatbot_graph() is not first
    reset_graph()
