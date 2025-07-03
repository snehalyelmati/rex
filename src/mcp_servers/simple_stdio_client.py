import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Define server parameters
    server_params = StdioServerParameters(command="python", args=["simple_server.py"])

    # Connect to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize session
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"    - {tool.name}: {tool.description}")

            # Calling tool
            result = await session.call_tool("add", arguments={"a": 2, "b": 3})
            print(f"2 + 3 = {result.content[0].text}")


# Steps to execute,
# - Run the server
# - Run the client
#   - Path of the server should be w.r.t. the location from where the server is run.
if __name__ == "__main__":
    asyncio.run(main())
