from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

QUOTA_CACHE = Path.home() / ".agy-swap" / "cache" / "quota.json"

CONNECT_RPC_PATH = (
    "/google.cloud.businessaicode.v1main.PredictionService/"
    "RetrieveUserQuotaSummary"
)


def _find_agy_pid() -> str | None:
    try:
        r = subprocess.run(
            ["pgrep", "-x", "agy"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().splitlines()[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _find_ports(pid: str) -> list[int]:
    try:
        r = subprocess.run(
            ["lsof", "-p", pid, "-i", "-P", "-n"],
            capture_output=True, text=True, timeout=5,
        )
        ports = []
        for line in r.stdout.splitlines():
            if "(LISTEN)" not in line:
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            addr = parts[8]
            if ":" not in addr:
                continue
            host, port_str = addr.rsplit(":", 1)
            if host in ("127.0.0.1", "localhost"):
                try:
                    ports.append(int(port_str))
                except ValueError:
                    pass
        return ports
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _probe_connectrpc(port: int) -> dict | None:
    url = f"http://127.0.0.1:{port}{CONNECT_RPC_PATH}"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body
    except Exception:
        return None


def discover_and_fetch() -> dict | None:
    pid = _find_agy_pid()
    if pid is None:
        return None
    ports = _find_ports(pid)
    for port in ports:
        result = _probe_connectrpc(port)
        if result is not None and "response" in result:
            return result
    return None


def _get_active_email() -> str | None:
    from agyswap.paths import GOOGLE_ACCOUNTS_PATH
    path = GOOGLE_ACCOUNTS_PATH
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data.get("active") or None
        except (json.JSONDecodeError, OSError):
            pass
    return None


def map_response(resp: dict) -> dict:
    groups = resp.get("response", {}).get("groups", [])

    by_window: dict[str, dict] = {}
    for group in groups:
        for bucket in group.get("buckets", []):
            window = bucket.get("window")
            remaining = bucket.get("remainingFraction", 1.0)
            used_pct = round((1 - remaining) * 100, 1)
            resets_at = bucket.get("resetTime", "")

            if window and (
                window not in by_window
                or used_pct > by_window[window].get("used_pct", 0)
            ):
                by_window[window] = {
                    "used_pct": used_pct,
                    "resets_at": resets_at,
                }

    email = _get_active_email()
    account_quota: dict[str, float | str] = {}

    if "5h" in by_window:
        account_quota["five_hour"] = by_window["5h"]["used_pct"]
        account_quota["five_resets_at"] = by_window["5h"]["resets_at"]
    if "weekly" in by_window:
        account_quota["seven_day"] = by_window["weekly"]["used_pct"]
        account_quota["seven_resets_at"] = by_window["weekly"]["resets_at"]

    accounts: dict[str, dict] = {}
    if email and account_quota:
        accounts[email] = account_quota
    elif account_quota:
        accounts["__unknown__"] = account_quota

    return {
        "accounts": accounts,
        "captured_at": int(time.time()),
    }


def fetch_and_cache() -> bool:
    resp = discover_and_fetch()
    if resp is None:
        return False
    quota = map_response(resp)
    QUOTA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUOTA_CACHE.write_text(json.dumps(quota, indent=2))
    return True
