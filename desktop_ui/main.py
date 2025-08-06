import os
import sys
import streamlit as st
import json
from datetime import datetime
import asyncio
from mcp_client import MCPClientManager, run_async

# Ensure the current directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Initialize session state variables if they don't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'sessions' not in st.session_state:
    st.session_state.sessions = {}
    
if 'active_session' not in st.session_state:
    st.session_state.active_session = None
    
if 'client_manager' not in st.session_state:
    st.session_state.client_manager = MCPClientManager()
    
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False

# Main function to run the Streamlit app
def main():
    st.title("LangGraph Chat Interface")
    
    # Sidebar for session management and server configuration
    with st.sidebar:
        st.header("Sessions")
        
        # Create new session
        new_session_name = st.text_input("New Session Name")
        if st.button("Create Session"):
            if new_session_name:
                create_session(new_session_name)
        
        # List and select existing sessions
        st.subheader("Existing Sessions")
        session_names = list(st.session_state.sessions.keys())
        if session_names:
            selected_session = st.selectbox(
                "Select Session", 
                session_names,
                index=session_names.index(st.session_state.active_session) if st.session_state.active_session in session_names else 0
            )
            if st.button("Load Session"):
                load_session(selected_session)
            
            if st.button("Delete Session"):
                delete_session(selected_session)
        
        # Server configuration
        st.header("Server Configuration")
        server_config = load_server_config()
        
        server_url = st.text_input("Server URL", value=server_config.get("default", {}).get("url", "http://localhost:8000"))
        api_key = st.text_input("API Key", value=server_config.get("default", {}).get("api_key", ""), type="password")
        
        if st.button("Save Configuration"):
            save_server_config("default", {"url": server_url, "api_key": api_key})
            st.success("Configuration saved!")
        
        if st.button("Connect"):
            connect_to_server()
    
    # Main chat interface
    if st.session_state.active_session:
        st.subheader(f"Chat: {st.session_state.active_session}")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Input for new message
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if st.session_state.is_connected:
                        response = asyncio.run(st.session_state.client_manager.process_message(prompt))
                    else:
                        response = "Not connected to any server. Please connect first."
                    
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save session
            save_session()
    else:
        st.info("Please create or select a session to start chatting.")

# Session management functions
def create_session(name):
    """Create a new chat session"""
    if name in st.session_state.sessions:
        # Append a number to make the name unique
        i = 1
        while f"{name} ({i})" in st.session_state.sessions:
            i += 1
        name = f"{name} ({i})"
    
    st.session_state.sessions[name] = {
        "name": name,
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    st.session_state.active_session = name
    st.session_state.messages = []
    save_sessions()
    st.rerun()

def load_session(name):
    """Load an existing chat session"""
    if name in st.session_state.sessions:
        st.session_state.active_session = name
        st.session_state.messages = st.session_state.sessions[name].get("messages", [])
        st.rerun()

def delete_session(name):
    """Delete a chat session"""
    if name in st.session_state.sessions:
        del st.session_state.sessions[name]
        if st.session_state.active_session == name:
            st.session_state.active_session = None
            st.session_state.messages = []
        save_sessions()
        st.rerun()

def save_session():
    """Save the current session"""
    if st.session_state.active_session:
        st.session_state.sessions[st.session_state.active_session]["messages"] = st.session_state.messages
        st.session_state.sessions[st.session_state.active_session]["updated_at"] = datetime.now().isoformat()
        save_sessions()

def save_sessions():
    """Save all sessions to file"""
    with open("chat_sessions.json", "w") as f:
        json.dump(list(st.session_state.sessions.values()), f, indent=4)

def load_sessions():
    """Load sessions from file"""
    if os.path.exists("chat_sessions.json"):
        try:
            with open("chat_sessions.json", "r") as f:
                sessions_data = json.load(f)
                for session_data in sessions_data:
                    st.session_state.sessions[session_data["name"]] = session_data
        except (json.JSONDecodeError, KeyError):
            st.session_state.sessions = {}

# Server configuration functions
def load_server_config():
    """Load server configuration from file"""
    if os.path.exists("server_config.json"):
        try:
            with open("server_config.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_server_config(name, config):
    """Save server configuration to file"""
    server_config = load_server_config()
    server_config[name] = config
    with open("server_config.json", "w") as f:
        json.dump(server_config, f, indent=4)

def connect_to_server():
    """Connect to the configured server"""
    server_config = load_server_config()
    if "default" in server_config:
        with st.spinner("Connecting to server..."):
            success = asyncio.run(st.session_state.client_manager.connect({
                "default": server_config["default"]
            }))
            st.session_state.is_connected = success
            if success:
                st.sidebar.success("Connected to server!")
            else:
                st.sidebar.error("Failed to connect to server.")
    else:
        st.sidebar.error("No server configuration found.")

# Load existing sessions on startup
load_sessions()

if __name__ == "__main__":
    main()