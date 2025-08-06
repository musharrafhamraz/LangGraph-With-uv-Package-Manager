import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Callable

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

# Helper function to run async functions from sync code
def run_async(coro):
    """Run an async function from synchronous code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class MCPClientManager:
    """Class to manage MCP client connections and message processing"""
    
    def __init__(self):
        self.agent = None
        self.model = None
        self.server_configs = {}
        self.is_connected = False
        # Load environment variables
        load_dotenv()
    
    async def connect(self, server_configs: Dict[str, Dict[str, Any]]) -> bool:
        """Connect to MCP servers
        
        Args:
            server_configs: Dictionary of server configurations
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Store server configurations
            self.server_configs = server_configs
            
            # For Streamlit implementation, we'll use a simplified approach
            # without actual MCP client for now
            
            # Create model (using Groq for now, but could be configurable)
            # Ensure GROQ_API_KEY is set in environment
            if not os.getenv("GROQ_API_KEY"):
                raise ValueError("GROQ_API_KEY environment variable not set")
                
            self.model = ChatGroq(model="llama-3.3-70b-versatile")
            
            # Create a simple agent without tools for now
            # In a real implementation, you would connect to the MCP server
            # and get the tools from there
            self.agent = self.model
            
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from servers"""
        self.agent = None
        self.model = None
        self.is_connected = False
    
    async def process_message(self, message: str) -> str:
        """Process a message using the agent
        
        Args:
            message: The message to process
            
        Returns:
            str: The response from the agent
        """
        if not self.is_connected or not self.agent:
            return "Not connected to any servers. Please connect first."
        
        try:
            # Create message payload
            messages = [HumanMessage(content=message)]
            
            # Invoke model directly for now
            # In a real implementation, you would use the agent with tools
            response = await self.model.ainvoke(messages)
            
            # Extract response content
            if response:
                return response.content
            else:
                return "No response from agent"
        except Exception as e:
            return f"Error processing message: {e}"
    
    def get_available_servers(self) -> List[str]:
        """Get list of available servers
        
        Returns:
            List[str]: List of server names
        """
        return list(self.server_configs.keys())
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server
        
        Args:
            server_name: Name of the server
            
        Returns:
            Optional[Dict[str, Any]]: Server configuration or None if not found
        """
        return self.server_configs.get(server_name)

# Helper function to run async functions from sync code
def run_async(async_func, *args, **kwargs):
    """Run an async function from synchronous code
    
    Args:
        async_func: The async function to run
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Any: The result of the async function
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_func(*args, **kwargs))
    finally:
        loop.close()