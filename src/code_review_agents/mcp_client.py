import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _read(path: str) -> str:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "code_review_agents.mcp_server"],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("read_source_file", {"path": path})
            text = result.content[0].text
            if result.isError:
                raise RuntimeError(text)
            return text


def read_file_via_mcp(path: str) -> str:
    """Start the MCP server, ask it for a file, and return the contents."""
    return asyncio.run(_read(path))