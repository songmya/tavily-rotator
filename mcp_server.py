import os
from tavily_pool import TavilyPool
from mcp.server.fastmcp import FastMCP

API_KEYS = os.getenv("TAVILY_KEYS").split(",")

pool = TavilyPool(API_KEYS)

mcp = FastMCP("TavilyRotator")

@mcp.tool()
def web_search(query: str) -> str:
    result = pool.search(
        query=query,
        search_depth="advanced",
        max_results=5
    )
    return str(result)

app = mcp.sse_app()