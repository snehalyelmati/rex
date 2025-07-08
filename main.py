import asyncio
import logging

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import StdioServerParameters, stdio_client
from PIL.Image import Image

from src.agent.planner_agent import AgentState, build_agent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%m/%d/%y %H:%M:%S",
)

# st.set_page_config(layout="wide")

# MCP Server parameters
server_params = StdioServerParameters(
    command="python",
    args=["src/mcp_servers/git_mcp_server.py"],
    env=None,
)


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
                st.session_state.messages.append(
                    AIMessage(content="Hi there, how can I help?")
                )

            display_chat_history()

            # Prerequisites for Agents
            tools_available = await load_mcp_tools(session)
            tools_by_name = {tool.name: tool for tool in tools_available}
            # st.write("Available tools:", [tool for tool in tools][0])

            agent = await build_agent(tools_available)
            with st.sidebar:
                st.image(agent.get_graph().draw_mermaid_png())

            # Implementing Agentic workflow
            if prompt := st.chat_input("How can I help?"):
                st.chat_message("user").markdown(prompt)
                st.session_state.messages.append(HumanMessage(content=prompt))

                with st.spinner("Thinking..."):
                    # state = AgentState(
                    #     messages=st.session_state.messages, tools=tools_by_name
                    # )
                    # st.session_state.messages = (await agent.ainvoke(state))["messages"]
                    response = await agent.ainvoke(
                        AgentState(input=prompt, messages=st.session_state.messages)
                    )
                    st.write(response)
                    st.session_state.messages.append(
                        AIMessage(response["past_steps"][-1][-1])
                    )

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
