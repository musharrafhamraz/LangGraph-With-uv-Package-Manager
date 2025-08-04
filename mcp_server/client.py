from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

import asyncio

async def main():
    client=MultiServerMCPClient(
        {
            "math":{
                "command":"python",
                "args":["C:\\Users\\PMLS\\Desktop\\uv_langgraph\\mcp_server\\mathserver.py"], ## Ensure correct absolute path
                "transport":"stdio",
            
            },
            "weather": {
                "url": "http://localhost:8000/mcp",  # Ensure server is running here
                "transport": "streamable_http",
            }

        }
    )

    import os
    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")

    tools=await client.get_tools()
    model=ChatGroq(model="llama-3.3-70b-versatile")
    agent=create_react_agent(
        model,tools
    )

    # Math example
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's 3 + 5?"}]}
    )
    print("Math response:", math_response['messages'][-1].content)

    # Current weather example
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in London?"}]}
    )
    print("Weather response:", weather_response['messages'][-1].content)
    
    # Forecast example
    forecast_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather forecast for New York for the next 3 days?"}]}
    )
    print("\nForecast response:", forecast_response['messages'][-1].content)

asyncio.run(main())
