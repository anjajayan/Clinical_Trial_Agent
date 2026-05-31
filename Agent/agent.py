from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint



llm = HuggingFaceEndpoint(
repo_id = "Qwen/Qwen2.5-72B-Instruct",
task = 'text-generation',
max_new_tokens = 1024
)
model = ChatHuggingFace(llm=llm)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]



def call_trial_agent(tools):
    agent = model.bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        messages = state['messages']
        response = agent.invoke(messages)

        return {'messages': [response] }

    tool_node = ToolNode(tools)

    # Create a graph
    graph = StateGraph(AgentState)

    graph.add_node('agent_node', agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, 'agent_node')
    graph.add_conditional_edges('agent_node', tools_condition)
    graph.add_edge('tools', 'agent_node')
    
    workflow = graph.compile()
    return workflow

