"""
Debug test script to verify the updated graph functionality
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
    }
]

print("=" * 80)
print("DEBUG: TESTING LANGGRAPH")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n\nTest {i}: {test['message']}")
    print("-" * 80)
    
    result = graph.process_message(
        message=test['message'],
        conversation_id=test['conversation_id']
    )
    
    print(f"Full Result: {result}")
    print(f"\nDetected Intent: {result['user_context'].get('detected_intent', 'unknown')}")
    print(f"Response: '{result['response']}'")
    print(f"Action Required: {result['action_required']}")
    print(f"Account Number: {result['customer_details']['account_number']}")

print("\n" + "=" * 80)
