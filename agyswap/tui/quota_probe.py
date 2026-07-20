from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

QUOTA_CACHE = Path.home() / ".agy-swap" / "cache" / "quota.json"
QUOTA_API = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota"


def _fetch_for_token(access_token: str) -> dict | None:
    req = urllib.request.Request(
        QUOTA_API,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _find_lowest_remaining(buckets: list[dict]) -> float:
    if not buckets:
        return 1.0
    return min(b.get("remainingFraction", 1.0) for b in buckets)


def _pick_representative_bucket(buckets: list[dict]) -> dict | None:
    if not buckets:
        return None
    for key in ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3.1-flash-lite"):
        for b in buckets:
            if b.get("modelId") == key:
                return b
    return buckets[0]


def map_response(resp: dict) -> dict | None:
    if resp is None:
        return None
    buckets = resp.get("buckets", [])
    if not buckets:
        return None

    remaining = _find_lowest_remaining(buckets)
    used_pct = round((1 - remaining) * 100, 1)

    b = _pick_representative_bucket(buckets)
    resets_at = b.get("resetTime", "") if b else ""

    models = {}
    for b in buckets:
        mid = b.get("modelId", "unknown")
        rem = b.get("remainingFraction", 1.0)
        models[mid] = {
            "remaining": round(rem * 100, 1),
            "used": round((1 - rem) * 100, 1),
            "resets_at": b.get("resetTime", ""),
        }

    return {
        "five_hour": used_pct,
        "five_resets_at": resets_at,
        "seven_day": used_pct,
        "seven_resets_at": resets_at,
        "models": models,
    }


def _extract_access_token(token_raw: str) -> str | None:
    try:
        parsed = json.loads(token_raw)
        return parsed.get("token", {}).get("access_token") or None
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def _fetch_for_email(email: str, access_token: str) -> dict | None:
    resp = _fetch_for_token(access_token)
    if not resp:
        return None
    q = map_response(resp)
    if not q:
        return None
    q["captured_at"] = int(time.time())
    return q


def fetch_and_cache() -> bool:
    from agyswap.switcher import _read_token_backup
    from agyswap.paths import GOOGLE_ACCOUNTS_PATH, SEQUENCE_FILE

    accounts_data: dict[str, dict] = {}

    active_path = GOOGLE_ACCOUNTS_PATH
    if active_path.exists():
        try:
            data = json.loads(active_path.read_text())
            active_email = data.get("active") or ""
            if active_email:
                from agyswap.switcher import _read_current_token
                token = _read_current_token()
                if token:
                    at = _extract_access_token(token)
                    if at:
                        q = _fetch_for_email(active_email, at)
                        if q:
                            accounts_data[active_email] = q
        except Exception:
            pass

    seq_path = SEQUENCE_FILE
    if seq_path.exists():
        try:
            seq = json.loads(seq_path.read_text())
            for num_str, acc_data in seq.get("accounts", {}).items():
                email = acc_data.get("email", "")
                if not email or email in accounts_data:
                    continue
                num = int(num_str)
                token = _read_token_backup(num, email)
                if not token:
                    continue
                at = _extract_access_token(token)
                if not at:
                    continue
                q = _fetch_for_email(email, at)
                if q:
                    accounts_data[email] = q
        except Exception:
            pass

    if not accounts_data:
        return False

    cache = {
        "accounts": accounts_data,
        "captured_at": int(time.time()),
    }
    QUOTA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUOTA_CACHE.write_text(json.dumps(cache, indent=2))
    return True
