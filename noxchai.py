import streamlit as st
import requests
import json
import uuid
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="centered"
)

# Get secrets
MONICA_API_URL = st.secrets["MONICA_API_URL"]
BOT_CONFIG = {
    "botUid": st.secrets["BOT_UID"],
    "botName": "Chechen"
}

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Utility functions
def create_new_conversation():
    try:
        response = requests.post(f"{MONICA_API_URL}/chat/new", json={
            "botUid": BOT_CONFIG["botUid"],
            "botName": BOT_CONFIG["botName"]
        })
        data = response.json()
        return data.get("conversationId")
    except Exception as e:
        st.error(f"Error creating conversation: {str(e)}")
        return None

def delete_conversation(conversation_id):
    try:
        requests.post(f"{MONICA_API_URL}/chat/delete", json={
            "conversationId": conversation_id
        })
        return True
    except Exception:
        return False

def send_message(message, conversation_id):
    try:
        response = requests.post(
            f"{MONICA_API_URL}/chat",
            json={
                "message": message,
                "conversationId": conversation_id,
                "botUid": BOT_CONFIG["botUid"]
            },
            stream=True
        )
        return response
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return None

def handle_streaming_response(response):
    full_response = ""
    placeholder = st.empty()
    
    try:
        for chunk in response.iter_lines():
            if chunk:
                line = chunk.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('text'):
                            full_response += data['text']
                            placeholder.markdown(full_response)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        st.error(f"Error handling response: {str(e)}")
    
    return full_response

def initialize_user():
    if not st.session_state.conversation_id:
        conversation_id = create_new_conversation()
        st.session_state.conversation_id = conversation_id

def renew_conversation():
    if st.session_state.conversation_id:
        delete_conversation(st.session_state.conversation_id)
    
    conversation_id = create_new_conversation()
    st.session_state.conversation_id = conversation_id
    st.session_state.messages = []
    st.success("Started a new conversation!")

def process_question(question):
    if not st.session_state.conversation_id:
        initialize_user()
    
    if st.session_state.conversation_id:
        st.session_state.messages.append({"role": "user", "content": question})
        
        with st.chat_message("user"):
            st.markdown(question)
        
        with st.chat_message("assistant"):
            response = send_message(question, st.session_state.conversation_id)
            if response:
                ai_response = handle_streaming_response(response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("Failed to get a response. Please try again.")

# Main UI
st.title(f"{BOT_CONFIG['botName']} AI Chat")

# Sidebar with options
with st.sidebar:
    st.header("Options")
    if st.button("Start New Conversation"):
        renew_conversation()
    
    st.divider()
    st.write("CHECHEN")

# Initialize user if needed
initialize_user()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask something..."):
    process_question(prompt)
