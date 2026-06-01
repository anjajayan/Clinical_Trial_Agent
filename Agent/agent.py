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
    """
    Build and compile a LangGraph agent workflow bound to the provided tools.

    Constructs a StateGraph with an agent node and a tools node. The agent
    invokes the LLM with the current message state, and the tools node
    executes any tool calls returned by the LLM. Edges route between nodes
    based on whether tool calls are present in the response.

    Args:
        tools: A list of LangChain-compatible tools to bind to the LLM.

    Returns:
        A compiled LangGraph workflow (CompiledStateGraph) ready to invoke.
    """
    agent = model.bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        """
        Invoke the LLM agent with the current message history and return the response.

        Args:
            state: The current agent state containing the message history.

        Returns:
            An updated AgentState with the LLM response appended to messages.
        """
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

