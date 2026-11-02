from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("code-files")

MAX_BYTES = 100_000


@mcp.tool()
def read_source_file(path: str) -> str:
    """Read a source code file and return its contents.

    Only files inside the current working directory can be read.
    """
    file = Path(path).resolve()
    root = Path.cwd().resolve()

    if not file.is_relative_to(root):
        raise ValueError("Access denied: file is outside the project folder.")
    if not file.is_file():
        raise ValueError(f"File not found: {path}")
    if file.stat().st_size > MAX_BYTES:
        raise ValueError("File is too large to review (limit is 100 KB).")

    return file.read_text()


def main() -> None:
    mcp.run()  # talks over stdio, so never use print() in this file


if __name__ == "__main__":
    main()