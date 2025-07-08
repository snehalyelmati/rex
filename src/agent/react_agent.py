from typing import Annotated, Dict, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tools: Dict[str, BaseTool]


def process(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(
        content="You are a helpful, honest and harmless assistant, do your best to answer the user's query. Depend primarily on the tools available to you."
    )

    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


async def custom_tool_node(state: AgentState):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = state["tools"][tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        result.append(
            AIMessage(
                content=f"Calling tool: `{tool.name}` with Args: `{tool_call['args']}`"
            )
        )
    return {"messages": result}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


async def build_agent(tools):
    # Initialize LLM with tools
    global llm
    llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

    # Building Graph
    graph = StateGraph(AgentState)

    graph.add_node("process_node", process)
    graph.add_node("tools", custom_tool_node)

    graph.add_edge(START, "process_node")
    graph.add_conditional_edges(
        source="process_node",
        path=should_continue,
        path_map={"continue": "tools", "end": END},
    )
    graph.add_edge("tools", "process_node")
    graph.add_edge("process_node", END)

    return graph.compile()
