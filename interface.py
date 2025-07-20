import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh
import uuid
import time

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/95a6ae98-d2f2-4cbd-b871-4fc641a1737c"

# Generate session_id only once per session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = None

if "processing" not in st.session_state:
    st.session_state.processing = False

session_id = st.session_state.session_id

st.title("💬 Chat with Webhook Assistant")
st.caption(f"Session ID: {session_id}")


# Function to get webhook response
def get_webhook_response(message):
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={"chatInput": message, "session_id": session_id},
            timeout=60  # Increased to 60 seconds
        )
        response.raise_for_status()
        return response.json().get("reply", response.text)
    except requests.exceptions.Timeout:
        return "⏰ Webhook took too long to respond (more than 60 seconds)"
    except Exception as e:
        return f"❌ Error connecting to webhook: {str(e)}"


# Process pending message if exists
if st.session_state.last_user_message and not st.session_state.processing:
    st.session_state.processing = True

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": st.session_state.last_user_message
    })

    # Get webhook response
    with st.spinner("🤔 Getting webhook response..."):
        start_time = time.time()
        webhook_reply = get_webhook_response(st.session_state.last_user_message)
        elapsed_time = time.time() - start_time

    # Show response time for debug
    st.success(f"✅ Response received in {elapsed_time:.1f} seconds")

    # Add assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": webhook_reply
    })

    # Clear states
    st.session_state.last_user_message = None
    st.session_state.processing = False

    # Force update
    st.rerun()

# Show chat history
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

# Input for new message
if not st.session_state.processing:
    user_input = st.chat_input("Write your message...")
    if user_input:
        st.session_state.last_user_message = user_input
        st.rerun()
else:
    st.chat_input("Processing message...", disabled=True)

# Auto-refresh every 2 seconds only if we're not processing AND there's no pending message
if not st.session_state.processing and not st.session_state.last_user_message:
    st_autorefresh(interval=2000, key="chat_refresh")