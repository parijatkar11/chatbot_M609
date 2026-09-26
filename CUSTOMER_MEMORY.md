# Customer Memory and State Management

## Overview

The LangGraph workflow now includes a comprehensive customer memory and state management system. This allows the chatbot to:

- **Track customer details** - Account numbers and reasons for contact
- **Maintain conversation history** - Interaction records with intents and responses
- **Extract information** - Automatically detect customer info from messages
- **Provide context** - Use customer history for personalized responses

## Architecture

### CustomerMemoryManager Class

The `CustomerMemoryManager` handles all customer data operations:

```python
class CustomerMemoryManager:
    """Manages customer details and conversation memory"""
    
    # Key methods:
    - initialize_customer(conversation_id, account_number)
    - get_customer_details(conversation_id)
    - update_account_number(conversation_id, account_number)
    - update_reason_for_contact(conversation_id, reason)
    - add_to_interaction_history(conversation_id, message, response, intent)
    - extract_customer_info_from_message(text)
    - get_conversation_context(conversation_id, limit)
    - export_customer_data(conversation_id)
    - clear_customer_data(conversation_id)
    - get_all_customers()
```

### LangGraph Workflow Enhancement

A new node has been added to the workflow:

**Customer Info Extraction Node**
- Runs after input validation
- Extracts account numbers and reasons for contact
- Updates customer memory with extracted information
- Provides context for subsequent nodes

```
INPUT_VALIDATION
    ↓
CUSTOMER_INFO_EXTRACTION  ← NEW NODE
    ↓
INTENT_CLASSIFICATION
    ↓
CONTEXT_RETRIEVAL
    ↓
RESPONSE_GENERATION
    ↓
[OPTIONAL] HUMAN_APPROVAL
```

## Customer Details Storage

### CustomerDetails Structure

```python
{
    "account_number": "123456",           # Customer account number
    "reason_for_contact": "refinance",    # Why customer is contacting
    "contact_date": "2024-01-15T10:30:00",# When conversation started
    "previous_interactions": [             # Interaction history
        {
            "timestamp": "2024-01-15T10:31:00",
            "message": "I want to refinance",
            "response": "I can help with that...",
            "intent": "refinance"
        }
    ],
    "preferences": {}                      # Customer preferences
}
```

### Stored Locally In-Memory

Currently, customer data is stored in-memory using:
- `CustomerMemoryManager.customer_store` - Main customer data dictionary
- `CustomerMemoryManager.conversation_memory` - Interaction history

**For production, implement:**
- Database persistence (PostgreSQL, MongoDB)
- Encryption for sensitive data
- Audit logging
- Data retention policies

## Information Extraction

### Account Number Detection

The system uses regex patterns to extract account numbers from natural language:

```
Patterns matched:
- "account number: 123456"
- "acct: 123456"
- "#123456"
- "my account is 123456"
```

### Reason for Contact Detection

Automatically categorizes customer intent:

```
Categories:
- mortgage_inquiry      → Keywords: mortgage, home loan, financing
- rate_inquiry         → Keywords: rate, interest, apr, apy, percentage
- refinance           → Keywords: refinance, refi, lower payment
- application         → Keywords: apply, application, start, begin
- payment_help        → Keywords: payment, afford, modify, assistance
- account_info        → Keywords: account, status, balance, details
- general_inquiry     → Default category
```

## API Endpoints

### Get Customer Details

```
GET /customer/{conversation_id}/details
```

Returns customer details including account number and reason for contact.

**Response:**
```json
{
    "account_number": "123456",
    "reason_for_contact": "refinance",
    "contact_date": "2024-01-15T10:30:00",
    "previous_interactions": [
        {
            "timestamp": "2024-01-15T10:31:00",
            "message": "I want to refinance",
            "response": "I can help with that...",
            "intent": "refinance"
        }
    ],
    "preferences": {}
}
```

### Get Interaction History

```
GET /customer/{conversation_id}/interactions?limit=10
```

Returns recent customer interactions.

**Response:**
```json
{
    "conversation_id": "conv_abc123",
    "interactions": [
        {
            "timestamp": "2024-01-15T10:31:00",
            "message": "I want to refinance",
            "response": "I can help with that...",
            "intent": "refinance"
        }
    ],
    "total_count": 3
}
```

### Export Customer Data

```
GET /customer/{conversation_id}/export
```

Exports all customer data for a conversation.

**Response:**
```json
{
    "conversation_id": "conv_abc123",
    "customer_data": {
        "account_number": "123456",
        "reason_for_contact": "refinance",
        ...
    },
    "memory": [...]
}
```

### Clear Customer Data

```
DELETE /customer/{conversation_id}/clear
```

Clears all customer data (for privacy or testing).

### Get All Customers

```
GET /customers/all
```

Admin endpoint to retrieve all customer records.

**Response:**
```json
{
    "total_customers": 5,
    "customers": {
        "conv_abc123": { ... },
        "conv_def456": { ... }
    }
}
```

## Frontend Integration

The Streamlit frontend displays customer memory in the sidebar:

### Customer Memory Section

Located in the left sidebar when a conversation is active:

1. **Account Number** - Shows extracted or entered account number
2. **Reason for Contact** - Displays detected reason (auto-detected from conversation)
3. **Contact Date** - Shows when conversation started
4. **Expandable Interactions** - Last 3 interactions with intent tags

### Example Display

```
👤 Customer Memory
━━━━━━━━━━━━━━━━━━
✅ Account: 123456

ℹ️  Reason: Refinance

Contact started: 2024-01-15

📝 Previous Interactions (3)
  ▼ 1. Intent: refinance
    2024-01-15 10:31:00
  ▼ 2. Intent: rate_inquiry
    2024-01-15 10:33:00
  ▼ 3. Intent: application
    2024-01-15 10:35:00
```

## Usage Examples

### Extract Account Number Automatically

User message: "Hi, my account is 234567 and I want to refinance"

**Result:**
- Account number extracted: `234567`
- Reason detected: `refinance`
- Both stored in customer memory automatically

### View Customer Context

```bash
# Get customer details
curl http://localhost:8000/customer/conv_abc123/details

# Get interaction history
curl http://localhost:8000/customer/conv_abc123/interactions?limit=5

# Export all customer data
curl http://localhost:8000/customer/conv_abc123/export
```

## Workflow Node Details

### Customer Info Extraction Node

**Purpose:** Extract and update customer information from user input

**Process:**
1. Initialize customer details if not present
2. Extract account number using regex patterns
3. Detect reason for contact from keywords
4. Update memory with extracted information
5. Provide context for downstream nodes

**Input:**
- Current user message
- Conversation ID

**Output:**
- Updated customer details
- Extracted information
- Customer context

**Example Execution:**

```
Input: "Hello, my account is 456789. I'm interested in refinancing."

Extraction Process:
  - Account number: Regex matches "456789"
  - Reason: Keywords "refinancing" matched to "refinance" category

Output State:
  customer_details: {
    account_number: "456789",
    reason_for_contact: "refinance"
  }
  user_context: {
    customer_context: {
      account_number: "456789",
      reason_for_contact: "refinance",
      recent_interactions: [...]
    }
  }
```

## Chat Response Enhancement

The chat endpoint now returns customer details:

```json
{
    "response": "I can help you with refinancing...",
    "conversation_id": "conv_abc123",
    "action_required": false,
    "action_type": "none",
    "nodes_executed": ["input_validation", "customer_info_extraction", ...],
    "customer_details": {
        "account_number": "456789",
        "reason_for_contact": "refinance"
    }
}
```

## Data Persistence Considerations

### Current Implementation
- In-memory storage
- Lost on server restart
- Suitable for development/testing

### Production Implementation
Recommended architecture:

```python
# Replace in-memory with database
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker

class CustomerRecord(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True)
    account_number = Column(String)
    reason_for_contact = Column(String)
    contact_date = Column(DateTime)
    interactions = Column(JSON)
    preferences = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Implementation Steps

1. **Replace in-memory dictionary** with database queries
2. **Add encryption** for account numbers
3. **Implement audit logging** for all changes
4. **Add data retention policies** (e.g., delete after 90 days)
5. **Add access controls** (who can view customer data)
6. **Enable backups** for disaster recovery

## Privacy & Security

### Current Concerns
- In-memory storage (not encrypted)
- No audit logging
- No access controls
- Data lost on restart

### Recommendations
1. **Encrypt** account numbers and sensitive data
2. **Limit API access** to authenticated users
3. **Add audit logging** for data access
4. **Implement GDPR compliance** (right to be forgotten)
5. **Add data expiration** policies
6. **Use environment variables** for secrets

## Testing

### Test Account Number Extraction

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, my account number is #789456. I want refinance.",
    "conversation_id": "test_conv_1"
  }'

# Check extracted details
curl "http://localhost:8000/customer/test_conv_1/details"
```

### Test Multiple Interactions

```bash
# First message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My account is 111222",
    "conversation_id": "test_conv_2"
  }'

# Second message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your current mortgage rates?",
    "conversation_id": "test_conv_2"
  }'

# View all interactions
curl "http://localhost:8000/customer/test_conv_2/interactions"
```

### Test Data Export

```bash
curl "http://localhost:8000/customer/test_conv_1/export" | jq .
```

## Troubleshooting

### Account number not being detected
- Check that account number format matches expected patterns
- Try different formats: "account: 123456", "acct: 123456", "#123456"

### Reason for contact not detected
- Check that keywords are spelled correctly
- Look at the keyword list for the intended category
- Message may default to "general_inquiry" if no keywords match

### Customer memory not showing in Streamlit
- Ensure backend is running: `http://localhost:8000/health`
- Check browser console for API errors
- Verify conversation_id is correct

### Data lost after server restart
- This is expected with in-memory storage
- Implement database persistence for production

## Future Enhancements

1. **Multi-contact detection** - Track multiple people per account
2. **Sentiment analysis** - Detect customer satisfaction
3. **Topic modeling** - Automatically categorize conversation topics
4. **Predictive analytics** - Predict customer needs
5. **CRM integration** - Connect to external CRM systems
6. **Customer profiling** - Build detailed customer profiles
7. **Cross-conversation learning** - Learn from all customer interactions
8. **Smart routing** - Route to appropriate departments based on history

## Resources

- Main Documentation: [FASTAPI_LANGGRAPH_SERVICE.md](FASTAPI_LANGGRAPH_SERVICE.md)
- Quick Start: [QUICKSTART_LANGGRAPH.md](QUICKSTART_LANGGRAPH.md)
- Source Code: `backend/graph.py`, `backend/main.py`
