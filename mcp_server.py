import os
from mcp.server.fastmcp import FastMCP
from tavily_pool import TavilyPool

# 读取多个 Tavily Key
API_KEYS = os.getenv("TAVILY_KEYS").split(",")

pool = TavilyPool(API_KEYS)

mcp = FastMCP("TavilyRotator")

@mcp.tool()
def web_search(query: str) -> str:
    """
    Search the web using Tavily.
    """
    result = pool.search(
        query=query,
        search_depth="advanced",
        max_results=5
    )
    return str(result)

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8000
    )