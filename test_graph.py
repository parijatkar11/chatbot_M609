"""
Test script to verify the updated graph functionality
"""

import sys
sys.path.insert(0, '/Users/parij/deeplearning/chatbot_streamlit_fastapi_langgraph')

from backend.graph import get_chatbot_graph

# Initialize the graph
graph = get_chatbot_graph()

# Test cases
test_cases = [
    {
        "message": "What is my account balance?",
        "conversation_id": "test_conv_1",
        "expected_intent": "balance"
    },
    {
        "message": "I need my account number 123456 and want to check balance",
        "conversation_id": "test_conv_2",
        "expected_intent": "balance"
    },
    {
        "message": "Can I get my statement?",
        "conversation_id": "test_conv_3",
        "expected_intent": "statement"
    },
    {
        "message": "Show me my last transaction",
        "conversation_id": "test_conv_4",
        "expected_intent": "last_transaction"
    },
    {
        "message": "I need a year end statement",
        "conversation_id": "test_conv_5",
        "expected_intent": "year_end_statement"
    },
    {
        "message": "Help me with mortgages",
        "conversation_id": "test_conv_6",
        "expected_intent": "mortgage_info"
    }
]

print("=" * 80)
print("TESTING LANGGRAPH INTENT CLASSIFICATION AND RESPONSE GENERATION")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n\nTest {i}: {test['message']}")
    print("-" * 80)
    
    result = graph.process_message(
        message=test['message'],
        conversation_id=test['conversation_id']
    )
    
    detected_intent = result['user_context'].get('detected_intent', 'unknown')
    print(f"Detected Intent: {detected_intent}")
    print(f"Expected Intent: {test['expected_intent']}")
    print(f"Match: {'✓' if detected_intent == test['expected_intent'] else '✗'}")
    print(f"\nResponse: {result['response']}")
    print(f"Action Required: {result['action_required']}")
    print(f"Action Type: {result['action_type']}")
    print(f"Customer Details: {result['customer_details']}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
