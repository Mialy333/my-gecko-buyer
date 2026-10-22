"""The pre-commit key scan: it catches a keypair's shape, and ignores public addresses."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("scan_secrets", ROOT / "scripts" / "scan_secrets.py")
assert spec and spec.loader
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def test_a_keypair_array_is_caught_without_printing_it() -> None:
    body = str(list(range(100, 164)))  # 64 numbers, built here so no key sits in this file
    found = scan.findings_in("notes.json", body)
    assert found and "64-byte array" in found[0]
    assert body not in found[0]


def test_keypair_file_names_are_caught() -> None:
    assert scan.findings_in("devnet-buyer.json", "{}")
    assert scan.findings_in("some/where/my-keypair.json", "{}")
    assert scan.findings_in("mainnet-wallet.json", "{}")  # Friday's real-money key


def test_addresses_and_signatures_are_not_keys() -> None:
    text = (
        "store AzJW94Hpu8wnNpQ9DyCvyann24tmdDKhfdKn9GxFYX5f\n"
        "sig 4yc7jA8LAjpZc3FXyMBbaeYqJMRQmr5Dmwmhj5Nos7Zrm"
        "TzuhftMa76UR6M3UwMLVLXWMXpaXAhhorMieUoXBZzf\n"
    )
    assert scan.findings_in("receipts/4yc7jA8L.md", text) == []


def test_a_secret_assignment_is_caught() -> None:
    assert scan.findings_in(".env", "PRIVATE_KEY=" + "x" * 40)


def test_a_prefixed_secret_name_is_caught() -> None:
    # `\b` sees no word boundary between "_" and "P": SOLANA_PRIVATE_KEY slipped through.
    value = "x" * 40
    assert scan.findings_in(".env", "SOLANA_PRIVATE_KEY=" + value)
    assert scan.findings_in(".env", "OPENAI_API_KEY=sk-" + value)
    assert scan.findings_in(".env", "AWS_SECRET_ACCESS_KEY=" + value)
    assert scan.findings_in("config.py", 'gecko_api_key = "' + value + '"')


def test_a_short_placeholder_or_a_longer_name_is_not_a_secret() -> None:
    assert scan.findings_in(".env.example", "OPENAI_API_KEY=your-key-here") == []
    assert scan.findings_in("notes.md", "API_KEY_ID=" + "x" * 40) == []
