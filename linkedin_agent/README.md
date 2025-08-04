# LinkedIn Auto-Posting AI Agent

An AI Agent that automatically generates and posts daily LinkedIn articles based on user preferences using LangGraph. The system includes a frontend UI for configuring preferences, a backend agent flow built with LangGraph, and integration with the LinkedIn API for scheduled posting.

## Features

- **User Preference Collection**: Set topics, tone, and preferred posting time
- **AI Content Generation**: Generate relevant article content daily using an LLM (Groq)
- **Human-in-the-Loop Approval**: Review and approve/reject generated content before posting
- **Scheduled Posting**: Automatically post to LinkedIn at the specified time
- **Logging**: Track all agent actions and post statuses

## Architecture

The system is built using LangGraph with the following components:

- **Nodes**:
  - InputCollector: Collects user preferences
  - ContentCreator: Generates article content using LLM
  - Human Approval: Allows user to approve or reject content
  - Scheduler: Checks if it's time to post
  - Poster: Posts content to LinkedIn
  - Logger: Logs all actions

- **State**:
  - UserPreferences: Topics, tone, posting time
  - ArticleContent: Generated title and content
  - PostStatus: Status of the post (pending, approved, rejected, posted)
  - Logs: History of agent actions

## Setup

### Prerequisites

- Python 3.9+
- LinkedIn Developer Account and API Credentials

### Installation

1. Install dependencies:

```bash
uv add -r requirements.txt
```

2. Set up LinkedIn API credentials in a `.env` file:

```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8502
```

### Running the Application

#### Using the Streamlit UI

```bash
python -m linkedin_agent.main --ui
```

This will start the Streamlit UI on http://localhost:8501

#### Using the Command Line

```bash
python -m linkedin_agent.main --topics Technology AI --tone Professional --posting-time 09:00
```

#### Running the Scheduler

```bash
python -m linkedin_agent.main --scheduler --interval 5
```

This will run the scheduler to check every 5 minutes if it's time to post.

## Usage

1. **Setup Tab**: Configure LinkedIn authentication and set your preferences
2. **Content Tab**: Generate, review, and approve/reject content
3. **Scheduling Tab**: Start/stop the scheduler or post manually
4. **Logs Tab**: View the history of agent actions

## Project Structure

- `agent_state.py`: Defines the state for the LangGraph agent
- `agent_graph.py`: Implements the LangGraph flow
- `content_creator.py`: Handles article generation using LLM
- `linkedin_api.py`: Manages LinkedIn API authentication and posting
- `tools.py`: Utility functions for time checking, logging, etc.
- `app.py`: Streamlit frontend UI
- `main.py`: Entry point for the application

## Security

- OAuth 2.0 authentication with LinkedIn
- Secure token storage
- No hardcoded credentials

## License

MIT