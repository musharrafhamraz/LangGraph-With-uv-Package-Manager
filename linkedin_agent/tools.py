from datetime import datetime
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


def check_time_match(current_time: datetime, preferred_time: str) -> bool:
    """Check if the current time matches the preferred posting time.
    
    Args:
        current_time: Current datetime.
        preferred_time: Preferred time in HH:MM format.
        
    Returns:
        bool: True if the current time matches the preferred time, False otherwise.
    """
    if not preferred_time:
        return False
        
    # Parse the preferred time
    try:
        preferred_hour, preferred_minute = map(int, preferred_time.split(':'))
    except (ValueError, AttributeError):
        # If the preferred time is invalid, return False
        return False
    
    # Check if the current hour and minute match the preferred time
    # For testing purposes, we can also check if the current time is within a small window
    # around the preferred time (e.g., within 5 minutes)
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Exact match
    if current_hour == preferred_hour and current_minute == preferred_minute:
        return True
    
    # Within a 5-minute window (for testing)
    time_diff = abs((current_hour * 60 + current_minute) - (preferred_hour * 60 + preferred_minute))
    return time_diff <= 5


def log_to_file(logs: List[Dict[str, Any]], log_file: Optional[str] = None) -> None:
    """Log the agent's actions to a file.
    
    Args:
        logs: List of log entries to write to the file.
        log_file: Path to the log file. If None, a default path will be used.
    """
    if not log_file:
        # Create a default log file in the logs directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a log file with the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"linkedin_agent_{current_date}.log")
    
    # Append the logs to the file
    with open(log_file, "a") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")


def get_current_time() -> str:
    """Get the current time in ISO format.
    
    Returns:
        str: Current time in ISO format.
    """
    return datetime.now().isoformat()


def format_article_for_display(article_content: Dict[str, Any]) -> str:
    """Format the article content for display in the UI.
    
    Args:
        article_content: Dictionary containing the article title and content.
        
    Returns:
        str: Formatted article content for display.
    """
    if not article_content:
        return "No article content available."
    
    title = article_content.get("title", "Untitled")
    content = article_content.get("content", "No content available.")
    generated_at = article_content.get("generated_at", "Unknown time")
    
    # Format the article for display
    formatted_article = f"# {title}\n\n{content}\n\n*Generated at: {generated_at}*"
    
    return formatted_article