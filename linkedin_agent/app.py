import streamlit as st
import os
import json
from datetime import datetime
import time
from typing import Dict, List, Any, Optional
import threading
import schedule

from agent_state import AgentState, UserPreferences, ArticleContent, PostStatus, LogEntry
from agent_graph import run_agent
from linkedin_api import LinkedInAPI
from tools import format_article_for_display


# Initialize session state variables
def init_session_state():
    """Initialize Streamlit session state variables."""
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = {
            "user_preferences": {},
            "article_content": None,
            "post_status": None,
            "logs": [],
            "current_time": None,
            "human_feedback": None
        }
    
    if "linkedin_api" not in st.session_state:
        st.session_state.linkedin_api = LinkedInAPI()
    
    if "scheduler_running" not in st.session_state:
        st.session_state.scheduler_running = False
    
    if "scheduler_thread" not in st.session_state:
        st.session_state.scheduler_thread = None


# Function to run the scheduler in a background thread
def run_scheduler():
    """Run the scheduler in a background thread."""
    while st.session_state.scheduler_running:
        schedule.run_pending()
        time.sleep(1)


# Function to start the scheduler
def start_scheduler():
    """Start the scheduler to run the agent at the specified time."""
    if st.session_state.scheduler_running:
        return
    
    # Get the preferred posting time
    preferred_time = st.session_state.agent_state.get("user_preferences", {}).get("posting_time")
    if not preferred_time:
        st.error("Please set your preferred posting time first.")
        return
    
    # Schedule the agent to run at the preferred time
    schedule.every().day.at(preferred_time).do(run_agent_scheduled)
    
    # Start the scheduler in a background thread
    st.session_state.scheduler_running = True
    st.session_state.scheduler_thread = threading.Thread(target=run_scheduler)
    st.session_state.scheduler_thread.daemon = True
    st.session_state.scheduler_thread.start()
    
    st.success(f"Scheduler started. The agent will run daily at {preferred_time}.")


# Function to stop the scheduler
def stop_scheduler():
    """Stop the scheduler."""
    if not st.session_state.scheduler_running:
        return
    
    # Stop the scheduler
    st.session_state.scheduler_running = False
    if st.session_state.scheduler_thread:
        st.session_state.scheduler_thread.join(timeout=1)
        st.session_state.scheduler_thread = None
    
    # Clear all scheduled jobs
    schedule.clear()
    
    st.success("Scheduler stopped.")


# Function to run the agent with the current state
def run_agent_now():
    """Run the agent with the current state."""
    # Run the agent with the current state
    result = run_agent(st.session_state.agent_state)
    
    # Update the session state with the result
    st.session_state.agent_state = result
    
    # Force a rerun to update the UI
    st.experimental_rerun()


# Function to run the agent from the scheduler
def run_agent_scheduled():
    """Run the agent from the scheduler."""
    # Run the agent with the current state
    result = run_agent(st.session_state.agent_state)
    
    # Update the session state with the result
    st.session_state.agent_state = result


# Function to handle LinkedIn authentication
def handle_linkedin_auth():
    """Handle LinkedIn authentication."""
    linkedin_api = st.session_state.linkedin_api
    
    if linkedin_api.is_authenticated():
        st.success("You are already authenticated with LinkedIn.")
        return
    
    # Check if we have a code in the URL query parameters
    query_params = st.query_params.to_dict()
    code = query_params.get("code", [None])[0]
    
    # Get the redirect URI from environment variables
    redirect_uri = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:8502")
    
    if code:
        # Exchange the code for access token
        success = linkedin_api.authenticate(code, redirect_uri)
        
        if success:
            st.success("Successfully authenticated with LinkedIn!")
            # Clear the code from the URL
            st.query_params.clear()
        else:
            st.error("Failed to authenticate with LinkedIn. Please try again.")
    else:
        # Display the authentication button
        auth_url = linkedin_api.get_auth_url(redirect_uri)
        
        st.markdown(f"[Authenticate with LinkedIn]({auth_url})")


# Function to approve or reject the generated content
def handle_content_approval(approved: bool, feedback: str = ""):
    """Handle content approval or rejection.
    
    Args:
        approved: Whether the content is approved.
        feedback: Feedback for rejected content.
    """
    # Update the human feedback in the agent state
    st.session_state.agent_state["human_feedback"] = {
        "approved": approved,
        "feedback": feedback
    }
    
    # Run the agent to process the feedback
    run_agent_now()


# Main Streamlit app
def main():
    """Main Streamlit app."""
    # Initialize session state
    init_session_state()
    
    # Set page title and layout
    st.set_page_config(page_title="LinkedIn Auto-Posting Agent", layout="wide")
    
    # Display the app title
    st.title("LinkedIn Auto-Posting AI Agent")
    
    # Create tabs for different sections of the app
    tab1, tab2, tab3, tab4 = st.tabs(["Setup", "Content", "Scheduling", "Logs"])
    
    # Tab 1: Setup
    with tab1:
        st.header("Setup")
        
        # LinkedIn Authentication
        st.subheader("LinkedIn Authentication")
        handle_linkedin_auth()
        
        # User Preferences
        st.subheader("User Preferences")
        
        # Create a form for user preferences
        with st.form("user_preferences_form"):
            # Get the current preferences
            current_prefs = st.session_state.agent_state.get("user_preferences", {})
            
            # Topic selection (multi-select)
            topics = st.multiselect(
                "Select topics for your LinkedIn articles",
                options=["Technology", "AI", "Machine Learning", "Data Science", "Programming", 
                         "Career Development", "Leadership", "Business", "Marketing", "Entrepreneurship"],
                default=current_prefs.get("topics", [])
            )
            
            # Tone selection (select box)
            tone = st.selectbox(
                "Select the tone for your articles",
                options=["Professional", "Casual", "Enthusiastic", "Informative", "Inspirational"],
                index=0 if not current_prefs.get("tone") else 
                      ["Professional", "Casual", "Enthusiastic", "Informative", "Inspirational"].index(current_prefs.get("tone"))
            )
            
            # Posting time (time input)
            posting_time = st.time_input(
                "Select your preferred posting time",
                value=datetime.strptime(current_prefs.get("posting_time", "09:00"), "%H:%M") if current_prefs.get("posting_time") else datetime.strptime("09:00", "%H:%M")
            )
            
            # Submit button
            submit_button = st.form_submit_button("Save Preferences")
            
            if submit_button:
                # Format the posting time as HH:MM
                posting_time_str = posting_time.strftime("%H:%M")
                
                # Update the user preferences in the agent state
                st.session_state.agent_state["user_preferences"] = {
                    "topics": topics,
                    "tone": tone,
                    "posting_time": posting_time_str
                }
                
                # Run the input collector node
                run_agent_now()
                
                st.success("Preferences saved successfully!")
    
    # Tab 2: Content
    with tab2:
        st.header("Content Generation and Approval")
        
        # Check if user preferences are set
        if not st.session_state.agent_state.get("user_preferences"):
            st.warning("Please set your preferences in the Setup tab first.")
        else:
            # Display the current article content if available
            article_content = st.session_state.agent_state.get("article_content")
            post_status = st.session_state.agent_state.get("post_status", {})
            
            if article_content and post_status.get("status") in ["pending", "rejected"]:
                # Display the article content
                st.subheader("Generated Article")
                st.markdown(format_article_for_display(article_content))
                
                # Approval/Rejection buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve Content"):
                        handle_content_approval(True)
                
                with col2:
                    if st.button("Reject Content"):
                        feedback = st.text_area("Feedback for rejection (optional)")
                        if st.button("Submit Rejection"):
                            handle_content_approval(False, feedback)
            elif post_status and post_status.get("status") == "approved":
                st.success("Content has been approved and is ready for posting.")
                st.markdown(format_article_for_display(article_content))
            elif post_status and post_status.get("status") == "posted":
                st.success(f"Content has been posted to LinkedIn! View it here: {post_status.get('post_url')}")
                st.markdown(format_article_for_display(article_content))
            else:
                # Button to generate new content
                if st.button("Generate New Content"):
                    # Clear any existing article content and post status
                    st.session_state.agent_state["article_content"] = None
                    st.session_state.agent_state["post_status"] = None
                    
                    # Run the content creator node
                    run_agent_now()
    
    # Tab 3: Scheduling
    with tab3:
        st.header("Scheduling")
        
        # Check if user preferences are set
        if not st.session_state.agent_state.get("user_preferences"):
            st.warning("Please set your preferences in the Setup tab first.")
        else:
            # Display the current scheduling status
            if st.session_state.scheduler_running:
                st.success(f"Scheduler is running. Posts will be published daily at {st.session_state.agent_state['user_preferences']['posting_time']}.")
                
                # Button to stop the scheduler
                if st.button("Stop Scheduler"):
                    stop_scheduler()
            else:
                st.info("Scheduler is not running.")
                
                # Button to start the scheduler
                if st.button("Start Scheduler"):
                    start_scheduler()
            
            # Manual posting option
            st.subheader("Manual Posting")
            
            # Check if content is approved and ready for posting
            post_status = st.session_state.agent_state.get("post_status", {})
            if post_status and post_status.get("status") == "approved":
                if st.button("Post Now"):
                    # Set the current time to trigger posting
                    st.session_state.agent_state["current_time"] = datetime.now().isoformat()
                    
                    # Run the agent to process the posting
                    run_agent_now()
            else:
                st.warning("No approved content available for posting. Please generate and approve content first.")
    
    # Tab 4: Logs
    with tab4:
        st.header("Logs")
        
        # Display the logs
        logs = st.session_state.agent_state.get("logs", [])
        
        if not logs:
            st.info("No logs available yet.")
        else:
            # Create a DataFrame from the logs for better display
            import pandas as pd
            
            # Convert logs to DataFrame
            logs_df = pd.DataFrame(logs)
            
            # Sort logs by timestamp (newest first)
            logs_df = logs_df.sort_values(by="timestamp", ascending=False)
            
            # Display the logs
            st.dataframe(logs_df)
            
            # Button to clear logs
            if st.button("Clear Logs"):
                st.session_state.agent_state["logs"] = []
                st.experimental_rerun()


# Run the app
if __name__ == "__main__":
    main()