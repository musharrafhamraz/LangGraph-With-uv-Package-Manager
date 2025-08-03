# LangGraph Projects

This repository contains multiple projects demonstrating the use of LangGraph for creating AI agents.

## Projects

### 1. Weather MCP Server

This project demonstrates the use of LangChain's MCP (Model-Calling Protocol) servers with LangGraph to create an AI agent that can interact with weather data services.

### 2. LinkedIn Auto-Posting AI Agent

An AI Agent that automatically generates and posts daily LinkedIn articles based on user preferences using LangGraph. The system includes a frontend UI for configuring preferences, a backend agent flow built with LangGraph, and integration with the LinkedIn API for scheduled posting.

## Weather MCP Server Features

- Real-time weather data retrieval using OpenWeatherMap API
- Weather forecast capabilities for up to 5 days
- Math server for basic calculations
- Integration with LangGraph for AI agent creation
- Uses Groq's LLM for natural language processing

## LinkedIn Auto-Posting Agent Features

- User preference collection (topics, tone, preferred posting time)
- AI content generation using Groq's LLM
- Human-in-the-loop approval workflow
- Scheduled posting to LinkedIn via API
- Comprehensive logging of all agent activities

## Project Structure

### Weather MCP Server

- `mcp_server/`: Contains the MCP server implementations
  - `weather.py`: Weather MCP server with current weather and forecast tools
  - `mathserver.py`: Math MCP server with add and multiply tools
  - `client.py`: Client implementation that connects to both servers
  - `main.py`: Entry point for the application

### LinkedIn Auto-Posting Agent

- `linkedin_agent/`: Contains the LinkedIn agent implementation
  - `agent_state.py`: Defines the state structure for the agent
  - `agent_graph.py`: Implements the LangGraph with nodes for the agent workflow
  - `linkedin_api.py`: Handles LinkedIn API authentication and posting
  - `content_creator.py`: Generates LinkedIn article content using Groq's LLM
  - `tools.py`: Utility functions for time checking, logging, and content formatting
  - `app.py`: Streamlit frontend for user interaction
  - `main.py`: Entry point for running the agent via UI, scheduler, or CLI

## Setup

### Prerequisites

- Python 3.11 or newer
- uv package manager

### Installation

```bash
# Create and activate a virtual environment
uv venv

# Initialize the project
uv init

# Install dependencies
uv pip install -r requirements.txt
```

### API Keys

#### Weather MCP Server

This project uses the OpenWeatherMap API. You'll need to:

1. Sign up for a free API key at [OpenWeatherMap](https://openweathermap.org/api)
2. Replace the placeholder API key in `weather.py` with your own key
3. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

#### LinkedIn Auto-Posting Agent

This project uses the LinkedIn API and Groq's LLM. You'll need to:

1. Create a LinkedIn Developer App at [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Set up OAuth 2.0 with a redirect URI (e.g., http://localhost:8501 for Streamlit)
3. Copy the `.env.example` file in the `linkedin_agent` directory to `.env` and fill in your credentials:
   ```
   LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
   LINKEDIN_REDIRECT_URI=http://localhost:8501
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

### Weather MCP Server

#### Starting the Weather Server

```bash
python mcp_server/weather.py
```

This will start the weather server on http://localhost:8000/mcp

#### Running the Client

In a separate terminal:

```bash
python mcp_server/client.py
```

The client will connect to both the math and weather servers and demonstrate their capabilities.

### LinkedIn Auto-Posting Agent

#### Running the Streamlit UI

```bash
python -m linkedin_agent.main --ui
```

This will start the Streamlit app on http://localhost:8501, where you can:
- Authenticate with LinkedIn
- Set your content preferences (topics, tone, posting time)
- Generate and approve/reject content
- Start/stop the scheduler for automatic posting

#### Running the Scheduler

```bash
python -m linkedin_agent.main --scheduler
```

This will start the scheduler that runs in the background and posts content at the specified time.

#### Running from Command Line

```bash
python -m linkedin_agent.main --topics "AI,Technology" --tone "Professional" --posting-time "09:00"
```

This will run the agent once with the specified parameters and output the results.

## Extending the Projects

### Weather MCP Server

You can extend this project by:

1. Adding more tools to the existing servers
2. Creating new MCP servers for different functionalities
3. Enhancing the client to handle more complex queries

### LinkedIn Auto-Posting Agent

You can extend this project by:

1. Adding more content generation options (e.g., different article formats, image generation)
2. Implementing additional social media platforms (e.g., Twitter, Facebook)
3. Enhancing the content creator with better prompts or different LLM providers
4. Adding analytics to track post performance

## Package Management with uv

```bash
# Add a new package
uv pip install <package_name>

# Update dependencies
uv pip install -U <package_name>
```

