import os
import argparse
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import time
import threading
import schedule

# Load environment variables from .env file
from load_env import load_env_file
load_env_file()

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from linkedin_agent.agent_state import AgentState
from linkedin_agent.agent_graph import run_agent


def run_streamlit_app(port=8501):
    """Run the Streamlit app.
    
    Args:
        port: The port to run the Streamlit app on.
    """
    # Get the path to the app.py file
    app_path = Path(__file__).parent / "app.py"
    
    # Run the Streamlit app
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), f"--server.port={port}"]
    subprocess.run(cmd)


def run_scheduled_agent(agent_state):
    """Run the agent with the current state.
    
    Args:
        agent_state: Current agent state.
    """
    # Update the current time in the agent state
    agent_state["current_time"] = datetime.now().isoformat()
    
    # Run the agent
    result = run_agent(agent_state)
    
    # Print a log message
    print(f"Agent run completed at {datetime.now().isoformat()}")
    print(f"Post status: {result.get('post_status', {}).get('status', 'unknown')}")
    
    return result


def run_scheduler(agent_state, interval_minutes=1):
    """Run the scheduler to periodically check if it's time to post.
    
    Args:
        agent_state: Current agent state.
        interval_minutes: Interval in minutes to check if it's time to post.
    """
    # Schedule the agent to run at the specified interval
    schedule.every(interval_minutes).minutes.do(lambda: run_scheduled_agent(agent_state))
    
    # Run the scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped by user.")


def run_agent_cli(topics, tone, posting_time):
    """Run the agent from the command line.
    
    Args:
        topics: List of topics for the article.
        tone: Tone of the article.
        posting_time: Preferred posting time.
    """
    # Create the initial agent state
    initial_state = {
        "user_preferences": {
            "topics": topics,
            "tone": tone,
            "posting_time": posting_time
        },
        "article_content": None,
        "post_status": None,
        "logs": [],
        "current_time": datetime.now().isoformat(),
        "human_feedback": None
    }
    
    # Run the agent
    result = run_agent(initial_state)
    
    # Print the result
    print("Agent execution completed.")
    print(f"Generated article: {result.get('article_content', {}).get('title', 'No title')}")
    print(f"Post status: {result.get('post_status', {}).get('status', 'Unknown')}")
    
    # Print the logs
    print("\nLogs:")
    for log in result.get("logs", []):
        print(f"[{log['timestamp']}] {log['action']} - {log['status']}: {log['details']}")


def main():
    """Main entry point for the LinkedIn Agent application."""
    parser = argparse.ArgumentParser(description="LinkedIn Auto-Posting AI Agent")
    parser.add_argument("--ui", action="store_true", help="Run the Streamlit UI")
    parser.add_argument("--scheduler", action="store_true", help="Run the scheduler")
    parser.add_argument("--interval", type=int, default=1, help="Scheduler interval in minutes")
    parser.add_argument("--topics", nargs="+", help="Topics for the article")
    parser.add_argument("--tone", help="Tone of the article")
    parser.add_argument("--posting-time", help="Preferred posting time (HH:MM)")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit UI")
    
    args = parser.parse_args()
    
    if args.ui:
        # Run the Streamlit UI
        run_streamlit_app(port=args.port)
    elif args.scheduler:
        # Load user preferences from file if available
        prefs_file = os.path.join(os.path.dirname(__file__), "user_preferences.json")
        if os.path.exists(prefs_file):
            import json
            with open(prefs_file, "r") as f:
                user_prefs = json.load(f)
        else:
            # Use default preferences
            user_prefs = {
                "topics": ["Technology", "AI"],
                "tone": "Professional",
                "posting_time": "09:00"
            }
        
        # Initialize agent state
        agent_state = {
            "user_preferences": user_prefs,
            "article_content": None,
            "post_status": None,
            "logs": [],
            "current_time": datetime.now().isoformat(),
            "human_feedback": None
        }
        
        # Run the scheduler
        run_scheduler(agent_state, args.interval)
    elif args.topics and args.tone and args.posting_time:
        # Run the agent from the command line
        run_agent_cli(args.topics, args.tone, args.posting_time)
    else:
        # Print usage information
        parser.print_help()


if __name__ == "__main__":
    main()