from typing import Dict, List, Optional, Any, TypedDict, Literal
from datetime import datetime


class UserPreferences(TypedDict):
    """User preferences for LinkedIn article generation."""
    topics: List[str]  # List of topics the user is interested in
    tone: str  # Desired tone of the article (professional, casual, etc.)
    posting_time: str  # Preferred time to post in HH:MM format


class ArticleContent(TypedDict):
    """Content of the generated article."""
    title: str
    content: str
    generated_at: str  # ISO format timestamp


class PostStatus(TypedDict):
    """Status of the LinkedIn post."""
    status: Literal["pending", "approved", "rejected", "posted", "failed"]
    post_url: Optional[str]  # URL of the post if posted successfully
    error_message: Optional[str]  # Error message if posting failed
    posted_at: Optional[str]  # ISO format timestamp when posted


class LogEntry(TypedDict):
    """Log entry for tracking agent actions."""
    timestamp: str  # ISO format timestamp
    action: str  # Action performed (e.g., "content_generation", "posting")
    status: Literal["success", "failure"]
    details: str  # Additional details about the action


class AgentState(TypedDict):
    """State of the LinkedIn Auto-Posting Agent."""
    user_preferences: Optional[UserPreferences]
    article_content: Optional[ArticleContent]
    post_status: Optional[PostStatus]
    logs: List[LogEntry]
    current_time: Optional[str]  # Current time in ISO format
    human_feedback: Optional[Dict[str, Any]]  # Feedback from human in the loop