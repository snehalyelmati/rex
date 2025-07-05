import asyncio
import logging

import streamlit as st

from src.mcp_client.client import MCPOpenAIClient

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%m/%d/%y %H:%M:%S",
)


async def main():
    st.header("Repo Explorer - MCP + Agents")

    # Initialize session state
    client = MCPOpenAIClient()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # TODO: Standardize with OpenAI message schema
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Initialize MCP connection
    server_name = "git_mcp_server.py"
    server_path = "src/mcp_servers/" + server_name
    await client.connect_to_server(server_path)

    # Build agentic workflow and process requests
    if prompt := st.chat_input("How can I help?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            response = await client.process_query(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Cleanup server connection
    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
