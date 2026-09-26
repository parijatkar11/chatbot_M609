"""
Streamlit Frontend for Mortgage Chatbot Application
Provides an interactive interface for mortgage inquiries with conversation history
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = f"http://{os.getenv('API_HOST', '127.0.0.1')}:{os.getenv('API_PORT', 8000)}"
PAGE_TITLE = "Mortgage Chatbot"
PAGE_ICON = "🏦"

# Set page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = {}

if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None

if "await_human_approval" not in st.session_state:
    st.session_state.await_human_approval = False

if "hil_message" not in st.session_state:
    st.session_state.hil_message = ""


# Helper functions
def save_conversation():
    """Save current conversation to history"""
    if st.session_state.current_conversation and st.session_state.messages:
        st.session_state.conversation_history[st.session_state.current_conversation] = {
            "messages": st.session_state.messages.copy(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def load_conversation(conv_id):
    """Load a conversation from history"""
    if conv_id in st.session_state.conversation_history:
        st.session_state.messages = st.session_state.conversation_history[conv_id]["messages"].copy()
        st.session_state.current_conversation = conv_id


def new_conversation():
    """Create a new conversation"""
    save_conversation()
    st.session_state.current_conversation = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.messages = []
    st.session_state.await_human_approval = False
    st.session_state.hil_message = ""


def send_message(user_message: str):
    """Send a message to the API using LangGraph workflow"""
    try:
        with st.spinner("🤔 Processing your message through LangGraph..."):
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": user_message,
                    "conversation_id": st.session_state.current_conversation,
                    "user_context": {}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", "No response received"),
                    "action_required": data.get("action_required", False),
                    "action_type": data.get("action_type", "none"),
                    "nodes_executed": data.get("nodes_executed", [])
                }
            else:
                return {
                    "response": f"Error: {response.status_code}",
                    "action_required": False,
                    "action_type": "error",
                    "nodes_executed": []
                }
    
    except requests.exceptions.ConnectionError:
        return {
            "response": "❌ Error: Cannot connect to backend. Ensure the API is running at " + API_BASE_URL,
            "action_required": False,
            "action_type": "error",
            "nodes_executed": []
        }
    except Exception as e:
        return {
            "response": f"❌ Error: {str(e)}",
            "action_required": False,
            "action_type": "error",
            "nodes_executed": []
        }


def get_api_stats():
    """Get API statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


# ============================================================================
# SIDEBAR: Conversation History and Settings
# ============================================================================
with st.sidebar:
    # Sidebar header
    st.markdown("### 📋 Conversation History")
    
    # New conversation button
    if st.button("➕ New Conversation", use_container_width=True):
        new_conversation()
        st.rerun()
    
    st.divider()
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("**Previous Conversations:**")
        for conv_id, conv_data in st.session_state.conversation_history.items():
            # Display conversation with preview
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                # Show first message as preview
                preview = ""
                if conv_data["messages"]:
                    first_msg = conv_data["messages"][0]["content"][:30]
                    preview = first_msg + "..." if len(first_msg) == 30 else first_msg
                
                if st.button(
                    f"💬 {conv_data['timestamp']}\n_{preview}_",
                    key=f"load_{conv_id}",
                    use_container_width=True
                ):
                    load_conversation(conv_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                    del st.session_state.conversation_history[conv_id]
                    if st.session_state.current_conversation == conv_id:
                        st.session_state.current_conversation = None
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.info("No conversations yet. Start a new one!")
    
    st.divider()
    
    # Customer Memory Section
    if st.session_state.current_conversation:
        st.markdown("### 👤 Customer Memory")
        
        # Try to fetch customer details from API
        try:
            response = requests.get(
                f"{API_BASE_URL}/customer/{st.session_state.current_conversation}/details",
                timeout=5
            )
            if response.status_code == 200:
                customer = response.json()
                
                # Display account number
                if customer.get("account_number"):
                    st.success(f"**Account:** {customer['account_number']}")
                else:
                    st.info("**Account:** Not provided yet")
                
                # Display reason for contact
                if customer.get("reason_for_contact"):
                    reason = customer["reason_for_contact"].replace("_", " ").title()
                    st.info(f"**Reason:** {reason}")
                else:
                    st.info("**Reason:** Will be detected from conversation")
                
                # Display contact date
                if customer.get("contact_date"):
                    st.caption(f"Contact started: {customer['contact_date'][:10]}")
                
                # Expandable: Previous interactions
                if customer.get("previous_interactions"):
                    with st.expander(f"📝 Previous Interactions ({len(customer['previous_interactions'])})"):
                        for i, interaction in enumerate(customer["previous_interactions"][-3:], 1):
                            st.write(f"**{i}. Intent:** {interaction.get('intent', 'N/A')}")
                            st.caption(interaction.get('timestamp', ''))
        except Exception as e:
            st.warning("Unable to load customer memory from server")
            if st.checkbox("Show error details"):
                st.error(str(e))
    
    # Settings section
    st.markdown("### ⚙️ Settings")
    
    # Human In The Loop option
    st.markdown("**Human In The Loop**")
    enable_hil = st.checkbox(
        "Enable Human Approval for Actions",
        value=st.session_state.await_human_approval,
        help="Wait for human approval before executing certain actions"
    )
    
    if enable_hil:
        st.session_state.await_human_approval = True
        hil_timeout = st.slider(
            "Approval Timeout (seconds)",
            min_value=30,
            max_value=300,
            value=120,
            step=30,
            help="How long to wait for human approval"
        )
    else:
        st.session_state.await_human_approval = False
    
    st.divider()
    
    # Model configuration
    st.markdown("**Model Configuration**")
    model_name = st.text_input(
        "Model Name",
        value=os.getenv("MODEL_NAME", "gpt-4"),
        help="LLM model to use"
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Randomness of responses"
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=50,
        max_value=2000,
        value=500,
        step=50,
        help="Maximum response length"
    )


# ============================================================================
# MAIN CONTENT: Banner and Chat Interface
# ============================================================================

# Banner
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; text-align: center;">
            🏦 MORTGAGE CHATBOT
        </h1>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 10px 0 0 0;">
            Ask about mortgages, rates, and loan options
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Current conversation indicator
if st.session_state.current_conversation:
    st.info(f"📍 Conversation: {st.session_state.current_conversation}", icon="ℹ️")
else:
    st.warning("👉 Start a new conversation to begin!", icon="⚠️")


# ============================================================================
# CHAT AREA
# ============================================================================

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
            st.caption(message.get("timestamp", ""))


# ============================================================================
# HUMAN IN THE LOOP STATUS
# ============================================================================

if st.session_state.await_human_approval and st.session_state.hil_message:
    st.warning(f"⏳ **Awaiting Human Approval:** {st.session_state.hil_message}", icon="⏳")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve", use_container_width=True):
            st.session_state.hil_message = ""
            st.rerun()
    with col2:
        if st.button("❌ Reject", use_container_width=True):
            st.session_state.hil_message = ""
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Action cancelled by human reviewer.",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.rerun()


# ============================================================================
# CHAT INPUT
# ============================================================================

st.divider()

# Input area
col1, col2 = st.columns([0.85, 0.15], gap="small")

with col1:
    user_input = st.text_input(
        "Type your message...",
        placeholder="Ask about mortgages, rates, or loan options...",
        key="chat_input",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 Send", use_container_width=True, key="send_button")


# Process user input
if user_input and send_button:
    # Create conversation if needed
    if not st.session_state.current_conversation:
        new_conversation()
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    # Get response from API (with LangGraph processing)
    result = send_message(user_input)
    response_text = result.get("response", "No response received")
    action_required = result.get("action_required", False)
    action_type = result.get("action_type", "none")
    nodes_executed = result.get("nodes_executed", [])
    
    # Add assistant message to history
    message_obj = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    # Include workflow execution details
    if nodes_executed:
        message_obj["workflow_nodes"] = nodes_executed
        message_obj["action_type"] = action_type
    
    st.session_state.messages.append(message_obj)
    
    # Check if human approval is needed
    if st.session_state.await_human_approval and action_required:
        st.session_state.hil_message = f"Requires {action_type} approval"
    
    # Save conversation to history
    save_conversation()
    
    st.rerun()

# ============================================================================
# WORKFLOW EXECUTION DETAILS (Expandable)
# ============================================================================

if st.session_state.messages and any("workflow_nodes" in msg for msg in st.session_state.messages):
    with st.expander("🔍 Workflow Execution Details"):
        for i, message in enumerate(st.session_state.messages):
            if message.get("workflow_nodes"):
                st.subheader(f"Message {i+1}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Workflow Nodes Executed:**")
                    for node in message["workflow_nodes"]:
                        st.code(node, language="text")
                with col2:
                    st.write("**Action Type:**")
                    st.info(message.get("action_type", "none"))


# ============================================================================
# FOOTER
# ============================================================================

st.divider()

# Get API stats
api_stats = get_api_stats()

footer_cols = st.columns(4)

with footer_cols[0]:
    st.caption("📊 Streamlit Frontend")
with footer_cols[1]:
    st.caption("⚡ FastAPI Backend")
with footer_cols[2]:
    st.caption("🔗 LangGraph Workflows")
with footer_cols[3]:
    if api_stats:
        st.caption(f"💬 Conversations: {api_stats.get('total_conversations', 0)}")

# Debug info
if st.checkbox("🐛 Show Debug Info"):
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Session State")
        st.json({
            "current_conversation": st.session_state.current_conversation,
            "message_count": len(st.session_state.messages),
            "hil_enabled": st.session_state.await_human_approval,
            "hil_message": st.session_state.hil_message
        })
    
    with col2:
        st.subheader("API Statistics")
        if api_stats:
            st.json(api_stats)
        else:
            st.warning("Unable to fetch API statistics")
