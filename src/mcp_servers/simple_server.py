from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Calculator",
    host="0.0.0.0",
    port=8050,
)


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers `a` and `b` together."""
    return a + b


if __name__ == "__main__":
    # Transport methods: ['stdio', 'sse', 'streamable-http']
    transport = "stdio"

    if transport == "stdio":
        print("Running with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        print("Running with sse transport")
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        print("Running with streamable-http transport")
        mcp.run(transport="streamable-http")
    else:
        raise ValueError(f"Invalid transport format: {transport}")
