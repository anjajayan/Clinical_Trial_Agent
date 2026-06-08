import sys
import asyncio 
from dotenv import load_dotenv
import io
# MCP interface
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools

from Agent.agent import call_trial_agent
from langchain_core.messages import HumanMessage

load_dotenv()

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
server = StdioServerParameters(
    command = sys.executable,
    args = [r"MCP/clinical_research_server.py"]
)

async def main():
    print("Hello from clinical-trial-agent!")
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session: # mcp layer
            await session.initialize()
            tools = await load_mcp_tools(session)
            workflow = call_trial_agent(tools)
            # user_query = "What is the latest published paper in diabetes and what is the latest trial in the same field? "
            user_query =  input('Enter the query for clinical trials agent : ')
            init_state = {'messages': [HumanMessage(content = user_query)]}
            response = await workflow.ainvoke(init_state)
            ai_message = response['messages'][-1].content
            print(f"AI: {ai_message}")
            print(response)





if __name__ == "__main__":
    asyncio.run(main())
