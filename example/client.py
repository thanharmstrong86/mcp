from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
load_dotenv()
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # Corrected to a valid Gemini model
    api_key=os.getenv("GEMINI_API_KEY_2")
)
client = MultiServerMCPClient(
    {
        "math": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
        },
        "weather": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
        }
    }
)

async def main():
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)

    greet_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "greet thanh"}]}
    )
    print("Greet Response:", greet_response)

    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
    print("Weather Response:", weather_response)

if __name__ == "__main__":
    asyncio.run(main())