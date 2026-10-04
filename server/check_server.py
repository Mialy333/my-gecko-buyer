"""The part that says no, as an MCP server.

One tool, `check_purchase`: any agent (not only this buyer) can ask "should I sign
this?" and get the same seven-field verdict the buyer uses before it signs. The server
is keyless: it never loads a signer, so it can judge but never pay.

Serve it over stdio:  uv run python server/check_server.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # run as a script from anywhere: import the buyer package
    sys.path.insert(0, str(ROOT))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from buyer.check import check_all  # noqa: E402
from buyer.intent import IntentRecord  # noqa: E402
from buyer.prepared import GeckoRefused, Prepared  # noqa: E402
from server.guard import is_public_url  # noqa: E402

mcp = MCPServer("gecko-check")


def _refused(field: str, asked: Any, found: Any, note: str) -> dict[str, Any]:
    return {"passed": False, "field": field, "asked": asked, "found": found, "note": note}


def check_purchase(
    intent: dict[str, Any], prepared_answer: dict[str, Any], rpc_url: str | None = None
) -> dict[str, Any]:
    """Compare a prepared purchase with the pinned intent; refuse on the first mismatch.

    `intent` is the pinned record (the JSON written to intents/), `prepared_answer` is
    Gecko's prepare_purchase answer. Returns `passed`, and on a refusal the `field`
    that refused with what was `asked` and what was `found`.
    """
    if rpc_url is not None and not is_public_url(rpc_url):
        # Refused before anything is fetched: the URL could point inside the network.
        return _refused("rpc_url", "a public https URL", rpc_url, "refused before any request")
    try:
        record = IntentRecord(**intent)
    except TypeError as error:
        return _refused("intent", "a pinned intent record", sorted(intent), str(error))
    try:
        prepared = Prepared.from_answer(prepared_answer)
    except GeckoRefused:
        return _refused("prepared", "a prepared transaction", "a Gecko refusal", "nothing to sign")
    verdict = check_all(record, prepared)
    if verdict.unwritten is not None:
        unwritten = str(verdict.unwritten)
        return _refused("check", "every check written", "a check not written", unwritten)
    if verdict.refusal is not None:
        r = verdict.refusal
        return _refused(r.field, r.asked, r.found, r.note or "")
    return {
        "passed": True,
        "field": None,
        "asked": None,
        "found": None,
        "note": "every field agrees",
    }


mcp.tool()(check_purchase)


if __name__ == "__main__":
    mcp.run()
