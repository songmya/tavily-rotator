import os
from tavily_pool import TavilyPool
from mcp.server.fastmcp import FastMCP
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

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

app = mcp.sse_app(
    allowed_hosts=["*"]
)

# Cloudflare / 内网必须
app.add_middleware(ProxyHeadersMiddleware)