import asyncio
import logging
from typing import Annotated, Dict, Sequence, TypedDict

import streamlit as st
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, tool
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph import graph
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import StdioServerParameters, stdio_client

from src.mcp_client.client import MCPOpenAIClient

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%m/%d/%y %H:%M:%S",
)

# MCP Server parameters
server_params = StdioServerParameters(
    command="python",
    args=["src/mcp_servers/git_mcp_server.py"],
    env=None,
)


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


def display_chat_history():
    for message in st.session_state.messages:
        if not message.content or message.content in [None, ""]:
            continue

        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(message.content)


async def main():
    st.header("Repo Explorer - MCP + Agents")

    # Initialize session state
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            if "messages" not in st.session_state:
                st.session_state.messages = []

            display_chat_history()

            # Prerequisites for Agents
            tools = await load_mcp_tools(session)
            tools_by_name = {tool.name: tool for tool in tools}
            # st.write("Available tools:", [tool for tool in tools][0])

            global llm
            llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

            # Building Graph
            graph = StateGraph(AgentState)

            graph.add_node("process_node", process)

            # tool_node = ToolNode(tools=tools)
            graph.add_node("tools", custom_tool_node)

            graph.add_edge(START, "process_node")
            graph.add_conditional_edges(
                source="process_node",
                path=should_continue,
                path_map={"continue": "tools", "end": END},
            )
            graph.add_edge("tools", "process_node")
            graph.add_edge("process_node", END)

            agent = graph.compile()

            # Implementing Agentic workflow
            if prompt := st.chat_input("How can I help?"):
                st.chat_message("user").markdown(prompt)
                st.session_state.messages.append(HumanMessage(content=prompt))

                with st.spinner("Thinking..."):
                    state = AgentState(
                        messages=st.session_state.messages, tools=tools_by_name
                    )
                    st.session_state.messages = (await agent.ainvoke(state))["messages"]

                # Display tool message along with AIMessage
                if len(st.session_state.messages) > 2:
                    tool_response = st.session_state.messages[-2].content
                    if "Calling tool" in tool_response:
                        with st.chat_message("assistant"):
                            st.write(tool_response)

                response = st.session_state.messages[-1].content
                with st.chat_message("assistant"):
                    st.markdown(response)


if __name__ == "__main__":
    asyncio.run(main())
