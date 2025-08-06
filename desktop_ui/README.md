# LangGraph Chat Streamlit UI

A simple Streamlit-based web UI for interacting with LangGraph agents and LLM services. This application allows you to connect to different servers, send messages, and manage chat sessions.

## Features

- **Chat-style Interface**:
  - Sidebar: Session management and server configuration
  - Main area: Chat window showing messages
  - Bottom: Input field to send messages

- **Server Integration**:
  - Connect to different servers by entering the server's URL and API key
  - Save and reuse server configurations

- **Session Management**:
  - Create, load, and delete chat sessions
  - Automatic saving of chat history

## Installation

1. Clone the repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Create a `.env` file in the project root directory
   - Add your API keys (e.g., `GROQ_API_KEY=your_api_key_here`)

## Usage

1. Start the Streamlit application:

```bash
python run_streamlit.py
```

Or directly with Streamlit:

```bash
streamlit run main.py
```

2. Configure the server:
   - Enter the server URL and API key in the sidebar
   - Click "Save Configuration" to save the settings
   - Click "Connect" to establish a connection

3. Create a new chat session:
   - Enter a name in the "New Session Name" field
   - Click "Create Session"
   - Start chatting in the main area

4. Select a server from the dropdown in the chat header

5. Start chatting:
   - Type your message in the input field
   - Press Enter or click "Send"
   - Review and approve/deny/modify the AI response

## Server Configuration

### HTTP Server

- **Name**: A unique name for the server
- **Type**: Select "streamable_http"
- **URL**: The URL of the MCP server (e.g., `http://localhost:8000/mcp`)

### Command-based Server

- **Name**: A unique name for the server
- **Type**: Select "stdio"
- **Command**: The command to run the server (e.g., `python`)
- **Arguments**: Comma-separated list of arguments (e.g., `path/to/mathserver.py`)

## Project Structure

- `app.py`: Main application UI
- `mcp_client.py`: MCP client integration
- `main.py`: Application entry point
- `requirements.txt`: Required dependencies

## Dependencies

- PyQt5: Modern Python GUI toolkit
- langchain: Framework for developing applications powered by language models
- langchain_mcp_adapters: Adapters for MCP servers
- langgraph: Graph-based framework for LLM applications
- langchain_groq: Groq integration for langchain

## License

MIT