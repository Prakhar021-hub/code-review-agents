import argparse
import logging
import sys
from pathlib import Path

from code_review_agents.mcp_client import read_file_via_mcp
from code_review_agents.orchestrator import run_full_review
from code_review_agents.storage import get_run, list_runs


def print_history() -> None:
    runs = list_runs()
    if not runs:
        print("No saved reviews yet.")
        return
    for r in runs:
        print(
            f"#{r['id']}  {r['created_at']}  {r['source_name']}  "
            f"({r['finding_count']} findings)"
        )


def print_run(run_id: int) -> None:
    run = get_run(run_id)
    if run is None:
        sys.exit(f"Error: no saved review with id {run_id}.")
    print(f"Review #{run['id']} of {run['source_name']} ({run['created_at']})\n")
    print(run["report"])


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="review",
        description="Review a source file with a team of AI agents.",
    )
    parser.add_argument("file", nargs="?", help="path to the file to review")
    parser.add_argument(
        "--mcp", action="store_true", help="read the file through the MCP file server"
    )
    parser.add_argument(
        "--history", action="store_true", help="list recent saved reviews"
    )
    parser.add_argument(
        "--show", type=int, metavar="ID", help="show a saved review by its id"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show debug logs"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.history:
        print_history()
        return
    if args.show is not None:
        print_run(args.show)
        return
    if not args.file:
        parser.error("give a file to review, or use --history / --show ID")

    try:
        if args.mcp:
            code = read_file_via_mcp(args.file)
        else:
            code = Path(args.file).read_text()
    except (FileNotFoundError, RuntimeError) as error:
        sys.exit(f"Error: {error}")

    print(run_full_review(code, source_name=args.file))


if __name__ == "__main__":
    main()