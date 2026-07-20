#!/usr/bin/env python3
"""Statusline capture script for agy -S.

Run: agy -S "python3 -m agyswap.statusline"

Captures the statusline JSON from stdin and writes quota data to the
cache file so agyswap TUI can display it.

Also prints a compact statusline to stdout.
"""
import json
import sys
import time
from pathlib import Path

CACHE = Path.home() / ".agy-swap" / "cache" / "quota.json"


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    context = data.get("context_window", {})
    rate = data.get("rate_limits", {})
    model = data.get("model", {}).get("display_name", "?")
    email_claim = ""
    for token_key in ("access_token", "id_token"):
        full = data.get(token_key, "")
        if not full:
            continue
        try:
            payload_b64 = full.split(".")[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            import base64
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            email_claim = payload.get("email", "")
            if email_claim:
                break
        except Exception:
            continue

    quota = {
        "accounts": {},
        "model": model,
        "captured_at": int(time.time()),
    }

    email = data.get("email", email_claim)

    five = rate.get("five_hour", {})
    seven = rate.get("seven_day", {})

    account_quota = {}
    if five:
        account_quota["five_hour"] = five.get("used_percentage")
        account_quota["five_resets_at"] = five.get("resets_at")
    if seven:
        account_quota["seven_day"] = seven.get("used_percentage")
        account_quota["seven_resets_at"] = seven.get("resets_at")

    if email:
        quota["accounts"][email] = account_quota
    elif account_quota:
        quota["accounts"]["__unknown__"] = account_quota

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(quota, indent=2))

    ctx_tokens = context.get("total_input_tokens", 0)
    ctx_size = context.get("context_window_size", 0)
    five_pct = five.get("used_percentage", "")
    seven_pct = seven.get("used_percentage", "")

    parts = [model]
    if ctx_tokens and ctx_size:
        parts.append(f"Ctx: {ctx_tokens // 1000}k/{ctx_size // 1000}k")
    if five_pct != "":
        parts.append(f"5h: {five_pct}%")
    if seven_pct != "":
        parts.append(f"7d: {seven_pct}%")
    print("  ".join(parts), flush=True)


if __name__ == "__main__":
    main()
