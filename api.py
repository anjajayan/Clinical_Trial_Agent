from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages  import HumanMessage
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
from langchain_mcp_adapters.tools import load_mcp_tools

from Agent.agent import call_trial_agent
from dotenv import load_dotenv

load_dotenv()

server = StdioServerParameters(
    command = sys.executable,
    args = [r"MCP/clinical_research_server.py"]
)

agent ={}

@asynccontextmanager
async def lifespan(app: FastAPI):
     
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session: # mcp layer
            await session.initialize()
            tools = await load_mcp_tools(session)
            workflow = call_trial_agent(tools)
            agent['workflow'] = workflow
            yield
    
    



class Query(BaseModel):
    question: str


app = FastAPI(lifespan=lifespan)


@app.post("/question/")
async def answer(qn: Query):
    workflow = agent['workflow']
    init_state = {'messages': [HumanMessage(content = qn.question)]}
    response = await workflow.ainvoke(init_state)
    ai_message = response['messages'][-1].content
    return {'response': ai_message}

