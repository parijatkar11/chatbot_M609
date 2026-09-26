"""State-machine workflow for the mortgage chatbot."""

from datetime import datetime
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, TypedDict

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class CustomerDetails(TypedDict):
    account_number: Optional[str]
    reason_for_contact: Optional[str]
    contact_date: Optional[str]
    previous_interactions: List[Dict[str, Any]]
    preferences: Dict[str, Any]


class MessageState(TypedDict):
    messages: List[Dict[str, Any]]
    current_input: str
    conversation_id: str
    customer_details: CustomerDetails
    user_context: Dict[str, Any]
    response: str
    action_required: bool
    action_type: str
    internal_state: str


class CustomerMemoryManager:
    def __init__(self):
        self.customer_store: Dict[str, Dict[str, Any]] = {}
        self.conversation_memory: Dict[str, List[Dict[str, Any]]] = {}

    def initialize_customer(self, conversation_id: str, account_number: Optional[str] = None) -> CustomerDetails:
        if conversation_id not in self.customer_store:
            self.customer_store[conversation_id] = {
                "account_number": account_number,
                "reason_for_contact": None,
                "contact_date": datetime.utcnow().isoformat(),
                "previous_interactions": [],
                "preferences": {},
            }
            self.conversation_memory[conversation_id] = []
        return self.get_customer_details(conversation_id)

    def get_customer_details(self, conversation_id: str) -> CustomerDetails:
        if conversation_id not in self.customer_store:
            self.initialize_customer(conversation_id)
        details = self.customer_store[conversation_id]
        return {
            "account_number": details.get("account_number"),
            "reason_for_contact": details.get("reason_for_contact"),
            "contact_date": details.get("contact_date"),
            "previous_interactions": details.get("previous_interactions", []),
            "preferences": details.get("preferences", {}),
        }

    def update_account_number(self, conversation_id: str, account_number: str) -> None:
        self.initialize_customer(conversation_id)
        self.customer_store[conversation_id]["account_number"] = account_number

    def update_reason_for_contact(self, conversation_id: str, reason: str) -> None:
        self.initialize_customer(conversation_id)
        self.customer_store[conversation_id]["reason_for_contact"] = reason

    def add_to_interaction_history(self, conversation_id: str, message: str, response: str, intent: str) -> None:
        self.initialize_customer(conversation_id)
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "response": response,
            "intent": intent,
        }
        self.customer_store[conversation_id]["previous_interactions"].append(interaction)
        self.conversation_memory[conversation_id].append(interaction)

    def extract_customer_info_from_message(self, text: str) -> Dict[str, Optional[str]]:
        account_number = None
        patterns = [
            r"account\s+(?:number|#|no\.?)\s*:?\s*(\d+)",
            r"acct\s*:?\s*(\d+)",
            r"#(\d{6,10})",
            r"(?:my|the)\s+account\s+(?:is|no\.?)\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account_number = match.group(1)
                break
        return {"account_number": account_number, "reason_for_contact": None}

    def get_conversation_context(self, conversation_id: str, limit: int = 5) -> Dict[str, Any]:
        self.initialize_customer(conversation_id)
        customer = self.customer_store[conversation_id]
        interactions = customer.get("previous_interactions", [])
        return {
            "account_number": customer.get("account_number"),
            "reason_for_contact": customer.get("reason_for_contact"),
            "contact_date": customer.get("contact_date"),
            "recent_interactions": interactions[-limit:],
            "total_interactions": len(interactions),
            "preferences": customer.get("preferences", {}),
        }

    def export_customer_data(self, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self.customer_store:
            return {}
        return {
            "conversation_id": conversation_id,
            "customer_data": self.customer_store[conversation_id],
            "memory": self.conversation_memory.get(conversation_id, []),
        }

    def clear_customer_data(self, conversation_id: str) -> None:
        self.customer_store.pop(conversation_id, None)
        self.conversation_memory.pop(conversation_id, None)

    def get_all_customers(self) -> Dict[str, Dict[str, Any]]:
        return self.customer_store.copy()


class ChatbotGraph:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "gpt-4")
        self.debug_mode = os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true"
        self.timeout = int(os.getenv("LANGGRAPH_TIMEOUT", "60"))
        self.memory_manager = CustomerMemoryManager()
        self.node_history: Dict[str, Dict[str, Any]] = {}
        self.graph = self._initialize_graph()

    def _initialize_graph(self) -> Dict[str, Any]:
        nodes = {
            "input_validation": {"name": "Input Validation", "handler": self._validate_input},
            "customer_info_extraction": {"name": "Customer Info Extraction", "handler": self._extract_customer_info},
            "intent_classification": {"name": "Intent Classification", "handler": self._classify_intent},
            "context_retrieval": {"name": "Context Retrieval", "handler": self._retrieve_context},
            "response_generation": {"name": "Response Generation", "handler": self._generate_response},
        }
        return {
            "nodes": nodes,
            "edges": [
                ("input_validation", "customer_info_extraction"),
                ("customer_info_extraction", "intent_classification"),
                ("intent_classification", "context_retrieval"),
                ("context_retrieval", "response_generation"),
            ],
            "start_node": "input_validation",
            "end_nodes": ["response_generation"],
            "conditional_edges": {},
        }

    def _validate_input(self, state: MessageState) -> MessageState:
        text = state.get("current_input", "").strip()
        if not text:
            state["response"] = "Error: Empty input received"
            state["internal_state"] = "validation_failed"
        elif len(text) > 5000:
            state["response"] = "Error: Input too long (max 5000 characters)"
            state["internal_state"] = "validation_failed"
        else:
            state["internal_state"] = "input_validated"
        return state

    def _extract_customer_info(self, state: MessageState) -> MessageState:
        conversation_id = state["conversation_id"]
        extracted = self.memory_manager.extract_customer_info_from_message(state["current_input"])
        if extracted["account_number"]:
            account_number = extracted["account_number"]
            self.memory_manager.update_account_number(conversation_id, account_number)
            state["customer_details"]["account_number"] = account_number
        state["user_context"]["customer_context"] = self.memory_manager.get_conversation_context(conversation_id)
        state["internal_state"] = "customer_info_extracted"
        return state

    def _classify_intent(self, state: MessageState) -> MessageState:
        text = state.get("current_input", "").lower()
        intents = [
            ("balance", ["account balance", "balance", "how much", "what is my balance"]),
            ("year_end_statement", ["year end", "annual statement", "yearly statement", "tax statement"]),
            ("last_transaction", ["last transaction", "recent transaction", "latest transaction", "last activity"]),
            ("statement", ["statement", "recent statement", "monthly statement", "account statement"]),
            ("mortgage_info", ["mortgage", "loan", "home loan", "financing"]),
            ("interest_rates", ["rate", "interest", "apr", "apy"]),
            ("application", ["apply", "application", "start", "begin"]),
            ("refinance", ["refinance", "refi", "current loan"]),
            ("payment", ["payment", "monthly", "payment amount", "afford"]),
            ("eligibility", ["qualify", "credit", "score", "requirements"]),
        ]
        detected_intent = next((intent for intent, keywords in intents if any(keyword in text for keyword in keywords)), "general")
        state["user_context"]["detected_intent"] = detected_intent
        if detected_intent != "general":
            conversation_id = state["conversation_id"]
            self.memory_manager.update_reason_for_contact(conversation_id, detected_intent)
            state["customer_details"]["reason_for_contact"] = detected_intent
        state["internal_state"] = "intent_classified"
        return state

    def _retrieve_context(self, state: MessageState) -> MessageState:
        state["user_context"].update({
            "intent": state["user_context"].get("detected_intent", "general"),
            "conversation_id": state["conversation_id"],
            "message_count": len(state.get("messages", [])),
        })
        state["internal_state"] = "context_retrieved"
        return state

    def _generate_response(self, state: MessageState) -> MessageState:
        intent = state["user_context"].get("detected_intent", "general")
        account_number = state["customer_details"].get("account_number")
        if intent == "balance":
            if not account_number:
                state["response"] = "To retrieve your account balance, I need your account number. Could you please provide it?"
                state["action_required"] = True
                state["action_type"] = "account_number_required"
            else:
                balance = random.randint(400, 600)
                state["response"] = f"Your account balance is: ${balance:,.2f}"
                state["user_context"]["account_balance"] = balance
                state["action_required"] = False
                state["action_type"] = "none"
        elif intent in {"statement", "last_transaction", "year_end_statement"}:
            state["response"] = "Service not available"
            state["action_required"] = False
            state["action_type"] = "none"
        elif intent == "general":
            state["response"] = "Request not understood. Please suggest one of these intents: balance, statement, last transaction, year end statement"
            state["action_required"] = False
            state["action_type"] = "none"
        else:
            state["response"] = "Service not available"
            state["action_required"] = False
            state["action_type"] = "none"
        state["internal_state"] = "response_generated"
        return state

    def process_message(self, message: str, conversation_id: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state: MessageState = {
            "messages": [], "current_input": message, "conversation_id": conversation_id,
            "customer_details": self.memory_manager.initialize_customer(conversation_id),
            "user_context": user_context or {}, "response": "", "action_required": False,
            "action_type": "none", "internal_state": "initialized",
        }
        current_node = self.graph["start_node"]
        visited_nodes: List[str] = []
        while current_node:
            if current_node in visited_nodes:
                break
            visited_nodes.append(current_node)
            state = self.graph["nodes"][current_node]["handler"](state)
            if current_node in self.graph["end_nodes"]:
                break
            current_node = next((target for source, target in self.graph["edges"] if source == current_node), None)
        intent = state["user_context"].get("detected_intent", "general")
        self.memory_manager.add_to_interaction_history(conversation_id, message, state["response"], intent)
        self.node_history[conversation_id] = {"nodes_executed": visited_nodes, "final_state": state["internal_state"], "timestamp": datetime.utcnow().isoformat()}
        return {
            "response": state["response"], "action_required": state["action_required"], "action_type": state["action_type"],
            "conversation_id": conversation_id, "nodes_executed": visited_nodes,
            "customer_details": {"account_number": state["customer_details"].get("account_number"), "reason_for_contact": state["customer_details"].get("reason_for_contact")},
            "user_context": state["user_context"],
        }

    def get_graph_structure(self) -> Dict[str, Any]:
        return {"nodes": list(self.graph["nodes"]), "edges": self.graph["edges"], "start_node": self.graph["start_node"], "end_nodes": self.graph["end_nodes"]}

    def get_execution_history(self, conversation_id: str) -> Dict[str, Any]:
        return self.node_history.get(conversation_id, {})

    def get_customer_details(self, conversation_id: str) -> CustomerDetails:
        return self.memory_manager.get_customer_details(conversation_id)

    def get_customer_interactions(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.memory_manager.get_conversation_context(conversation_id, limit)["recent_interactions"]

    def export_customer_data(self, conversation_id: str) -> Dict[str, Any]:
        return self.memory_manager.export_customer_data(conversation_id)

    def clear_customer_data(self, conversation_id: str) -> None:
        self.memory_manager.clear_customer_data(conversation_id)

    def get_all_customers(self) -> Dict[str, Dict[str, Any]]:
        return self.memory_manager.get_all_customers()


_chatbot_graph_instance: Optional[ChatbotGraph] = None


def get_chatbot_graph() -> ChatbotGraph:
    global _chatbot_graph_instance
    if _chatbot_graph_instance is None:
        _chatbot_graph_instance = ChatbotGraph()
    return _chatbot_graph_instance


def reset_graph() -> None:
    global _chatbot_graph_instance
    _chatbot_graph_instance = None
