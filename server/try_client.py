"""A ten-line client: ask the check server about the recorded "two bags of beans" case.

uv run python server/try_client.py   ->  passed false, field quantity, asked 2, found 1
"""

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from buyer.intent import Context, Menu, parse_intent  # noqa: E402

CASE = json.loads((ROOT / "fixtures" / "cases" / "5-beans.json").read_text())


async def main() -> None:
    menu = Menu.from_list_stores(CASE["calls"]["list_stores"], CASE["context"]["store"])
    intent = asdict(parse_intent(CASE["ask"], menu, Context(**CASE["context"])))
    server = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "server" / "check_server.py")]
    )
    async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        answer = await session.call_tool(
            "check_purchase",
            {"intent": intent, "prepared_answer": CASE["calls"]["prepare_purchase"]},
        )
        print(answer.content[0].text)


asyncio.run(main())
