from typing import Annotated, Dict, List, TypedDict, Any, Optional, Literal, cast
from datetime import datetime
import json
import os
from pathlib import Path

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableConfig
from langchain.schema.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent_state import AgentState, UserPreferences, ArticleContent, PostStatus, LogEntry
from linkedin_api import LinkedInAPI
from tools import check_time_match, log_to_file


# Initialize the LLM
def get_llm():
    """Initialize and return the LLM."""
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)


# Node 1: Input Collector
def input_collector(state: AgentState) -> Dict[str, Any]:
    """Collect and validate user input."""
    # This function is mainly called from the UI
    # The state should already have user_preferences set
    
    if not state.get("user_preferences"):
        # If no user preferences are set, return an error
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "input_collection",
            "status": "failure",
            "details": "No user preferences provided"
        }
        
        return {"logs": state.get("logs", []) + [log_entry]}
    
    # Log successful input collection
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "input_collection",
        "status": "success",
        "details": f"Collected user preferences: {json.dumps(state['user_preferences'])}"
    }
    
    return {"logs": state.get("logs", []) + [log_entry]}


# Node 2: Content Creator
def content_creator(state: AgentState) -> Dict[str, Any]:
    """Generate article content based on user preferences."""
    user_preferences = state.get("user_preferences")
    if not user_preferences:
        # If no user preferences are set, return an error
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "content_creation",
            "status": "failure",
            "details": "No user preferences available for content creation"
        }
        
        return {"logs": state.get("logs", []) + [log_entry]}
    
    # Use LLM to generate article content
    llm = get_llm()
    
    # Create messages for article generation
    system_message = SystemMessage(content="You are a professional LinkedIn content creator. Your task is to create a high-quality article based on the user's preferences.")
    human_message = HumanMessage(content=f"Please create a LinkedIn article about {', '.join(user_preferences['topics'])} with a {user_preferences['tone']} tone. Include a catchy title and well-structured content with paragraphs.")
    
    # Generate the article
    response = llm.invoke([system_message, human_message])
    
    # Parse the response to extract title and content
    # Assuming the LLM returns a format like "Title: XXX\n\nContent: YYY"
    response_text = response.content
    
    # Simple parsing logic - can be improved based on actual LLM output format
    try:
        title_end = response_text.find("\n")
        title = response_text[:title_end].strip()
        if title.startswith("Title:"):
            title = title[6:].strip()
        content = response_text[title_end:].strip()
        if content.startswith("Content:"):
            content = content[8:].strip()
        
        article_content = {
            "title": title,
            "content": content,
            "generated_at": datetime.now().isoformat()
        }
        
        # Log successful content creation
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "content_creation",
            "status": "success",
            "details": f"Generated article with title: {title}"
        }
        
        return {
            "article_content": article_content,
            "logs": state.get("logs", []) + [log_entry],
            "post_status": {"status": "pending", "post_url": None, "error_message": None, "posted_at": None}
        }
    except Exception as e:
        # Log failure in content creation
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "content_creation",
            "status": "failure",
            "details": f"Failed to generate article: {str(e)}"
        }
        
        return {"logs": state.get("logs", []) + [log_entry]}


# Node 3: Human in the Loop for Content Approval
def human_approval(state: AgentState) -> Dict[str, Any]:
    """Wait for human approval of the generated content."""
    # This function is called from the UI when the user approves or rejects the content
    # The state should have human_feedback set by the UI
    
    human_feedback = state.get("human_feedback")
    if not human_feedback:
        # If no human feedback is available, maintain the current state
        return {}
    
    approval_status = human_feedback.get("approved", False)
    feedback_text = human_feedback.get("feedback", "")
    
    if approval_status:
        # Content is approved
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "content_approval",
            "status": "success",
            "details": "Content approved by human reviewer"
        }
        
        # Update post status to approved
        post_status = state.get("post_status", {})
        post_status["status"] = "approved"
        
        return {
            "post_status": post_status,
            "logs": state.get("logs", []) + [log_entry]
        }
    else:
        # Content is rejected, needs revision
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "content_approval",
            "status": "failure",
            "details": f"Content rejected by human reviewer: {feedback_text}"
        }
        
        # Update post status to rejected
        post_status = state.get("post_status", {})
        post_status["status"] = "rejected"
        
        return {
            "post_status": post_status,
            "logs": state.get("logs", []) + [log_entry],
            # Clear the article content to trigger regeneration
            "article_content": None
        }


# Node 4: Scheduler
def scheduler(state: AgentState) -> Dict[str, Any]:
    """Check if it's time to post based on user preferences."""
    user_preferences = state.get("user_preferences")
    post_status = state.get("post_status")
    
    if not user_preferences or not post_status or post_status.get("status") != "approved":
        # If no user preferences or post is not approved, skip scheduling
        return {}
    
    # Get the current time
    current_time = datetime.now()
    current_time_str = current_time.isoformat()
    
    # Track scheduler attempts to prevent infinite recursion
    scheduler_attempts = state.get("scheduler_attempts", 0)
    
    # Debug mode - always post immediately for testing
    debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
    
    # If we've tried too many times or in debug mode, force proceed to posting
    if scheduler_attempts >= 3 or debug_mode:
        return {
            "current_time": current_time_str,
            "scheduler_attempts": 0,  # Reset counter
            "logs": state.get("logs", []) + [{
                "timestamp": current_time_str,
                "action": "scheduling",
                "status": "forced",
                "details": f"Forced posting after {scheduler_attempts} attempts" + (
                    " (debug mode)" if debug_mode else "")
            }]
        }
    
    # Check if the current time matches the preferred posting time
    preferred_time = user_preferences.get("posting_time")
    time_match = check_time_match(current_time, preferred_time)
    
    if time_match:
        # It's time to post
        log_entry = {
            "timestamp": current_time_str,
            "action": "scheduling",
            "status": "success",
            "details": f"Scheduled posting at {current_time_str}"
        }
        
        return {
            "current_time": current_time_str,
            "scheduler_attempts": 0,  # Reset attempts counter on success
            "logs": state.get("logs", []) + [log_entry]
        }
    else:
        # Not time to post yet
        log_entry = {
            "timestamp": current_time_str,
            "action": "scheduling",
            "status": "waiting",
            "details": f"Waiting for preferred posting time: {preferred_time} (attempt {scheduler_attempts + 1}/5)"
        }
        
        return {
            "current_time": current_time_str,
            "scheduler_attempts": scheduler_attempts + 1,  # Increment attempts counter
            "logs": state.get("logs", []) + [log_entry]
        }


# Node 5: Poster
def poster(state: AgentState) -> Dict[str, Any]:
    """Post the article to LinkedIn."""
    article_content = state.get("article_content")
    post_status = state.get("post_status")
    current_time = state.get("current_time")
    
    if not article_content or not post_status or post_status.get("status") != "approved" or not current_time:
        # If no article content or post is not approved or not scheduled, skip posting
        return {}
    
    # Initialize LinkedIn API
    linkedin_api = LinkedInAPI()
    
    try:
        # Post to LinkedIn
        post_url = linkedin_api.post_article(
            title=article_content["title"],
            content=article_content["content"]
        )
        
        # Update post status
        updated_post_status = {
            "status": "posted",
            "post_url": post_url,
            "error_message": None,
            "posted_at": datetime.now().isoformat()
        }
        
        # Log successful posting
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "posting",
            "status": "success",
            "details": f"Posted article to LinkedIn: {post_url}"
        }
        
        return {
            "post_status": updated_post_status,
            "logs": state.get("logs", []) + [log_entry]
        }
    except Exception as e:
        # Update post status with error
        updated_post_status = {
            "status": "failed",
            "post_url": None,
            "error_message": str(e),
            "posted_at": None
        }
        
        # Log posting failure
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "posting",
            "status": "failure",
            "details": f"Failed to post article to LinkedIn: {str(e)}"
        }
        
        return {
            "post_status": updated_post_status,
            "logs": state.get("logs", []) + [log_entry]
        }


# Node 6: Logger
def logger(state: AgentState) -> Dict[str, Any]:
    """Log the agent's actions to a file."""
    logs = state.get("logs", [])
    
    if logs:
        # Log to file
        log_to_file(logs)
    
    # Return the current state unchanged
    return {}


# Define the state graph
def create_agent_graph():
    """Create and return the agent graph."""
    # Initialize the graph with the AgentState type
    graph = StateGraph(AgentState)
    
    # Add nodes to the graph
    graph.add_node("input_collector", input_collector)
    graph.add_node("content_creator", content_creator)
    graph.add_node("human_approval", human_approval)
    graph.add_node("scheduler", scheduler)
    graph.add_node("poster", poster)
    graph.add_node("logger", logger)
    
    # Define the edges (transitions) between nodes
    # Start with input collection
    graph.add_edge(START, "input_collector")
    graph.add_edge("input_collector", "content_creator")
    
    # After content creation, go to human approval
    graph.add_edge("content_creator", "human_approval")
    
    # After human approval, check if content was approved or rejected
    graph.add_conditional_edges(
        "human_approval",
        lambda state: "content_creator" if state.get("post_status", {}).get("status") == "rejected" else "scheduler"
    )
    
    # After scheduling, check if it's time to post
    graph.add_conditional_edges(
        "scheduler",
        lambda state: "poster" if state.get("current_time") and (state.get("scheduler_attempts", 0) >= 3 or 
                                                              state.get("logs", []) and state.get("logs", [])[-1].get("action") == "scheduling" and 
                                                              (state.get("logs", [])[-1].get("status") == "success" or 
                                                               state.get("logs", [])[-1].get("status") == "forced")) else "scheduler"
    )
    
    # After posting, log the results
    graph.add_edge("poster", "logger")
    
    # After logging, end the process
    graph.add_edge("logger", END)
    
    # Compile the graph
    return graph.compile()


# Create a singleton instance of the agent graph with increased recursion limit
agent_graph = create_agent_graph().with_config({"recursion_limit": 500})


# Function to run the agent with initial state
def run_agent(initial_state: AgentState):
    """Run the agent with the given initial state."""
    return agent_graph.invoke(initial_state)