import base64
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

from agyswap.models import Account, SequenceData, now_iso
from agyswap.paths import (
    AGY_TOKEN_PATH,
    BACKUP_ROOT,
    CREDENTIALS_DIR,
    GOOGLE_ACCOUNTS_PATH,
    QUOTA_CACHE,
    SEQUENCE_FILE,
)


class AgyError(Exception):
    pass


class AccountNotFoundError(AgyError):
    pass


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        os.write(fd, json.dumps(data, indent=2).encode("utf-8"))
        os.close(fd)
        fd = -1
        os.replace(tmp, str(path))
        os.chmod(path, 0o600)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


KEYCHAIN_SERVICE = "gemini"
KEYCHAIN_ACCOUNT = "antigravity"
KEYCHAIN_PREFIX = "go-keyring-base64:"


def _read_keychain_token() -> Optional[str]:
    try:
        import subprocess
        raw = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE,
             "-a", KEYCHAIN_ACCOUNT, "-w"],
            capture_output=True, text=True, timeout=5
        )
        if raw.returncode != 0 or not raw.stdout.strip():
            return None
        val = raw.stdout.strip()
        if val.startswith(KEYCHAIN_PREFIX):
            encoded = val[len(KEYCHAIN_PREFIX):]
            return base64.b64decode(encoded).decode("utf-8")
        return val
    except Exception:
        return None


def _write_keychain_token(content: str) -> None:
    try:
        import subprocess
        encoded = KEYCHAIN_PREFIX + base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")
        subprocess.run(
            ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE,
             "-a", KEYCHAIN_ACCOUNT, "-w", encoded, "-U"],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        pass


def _delete_keychain_token() -> None:
    try:
        import subprocess
        subprocess.run(
            ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE,
             "-a", KEYCHAIN_ACCOUNT],
            capture_output=True, timeout=5
        )
    except Exception:
        pass


def _read_current_token() -> Optional[str]:
    val = _read_keychain_token()
    if val:
        return val
    if AGY_TOKEN_PATH.exists():
        return AGY_TOKEN_PATH.read_text(encoding="utf-8")
    return None


def _write_current_token(content: str) -> None:
    _write_keychain_token(content)
    AGY_CLI_DIR = AGY_TOKEN_PATH.parent
    AGY_CLI_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(AGY_CLI_DIR), suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        fd = -1
        os.replace(tmp, str(AGY_TOKEN_PATH))
        os.chmod(AGY_TOKEN_PATH, 0o600)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_google_accounts() -> dict:
    data = _read_json(GOOGLE_ACCOUNTS_PATH)
    return data or {"active": "", "old": []}


def _write_google_accounts(data: dict) -> None:
    _write_json(GOOGLE_ACCOUNTS_PATH, data)


def _get_active_email_from_agy() -> Optional[str]:
    data = _read_google_accounts()
    return data.get("active") or None


def _get_email_from_userinfo(token_raw: str) -> Optional[str]:
    try:
        import urllib.request
        data = json.loads(token_raw)
        access_token = data.get("token", {}).get("access_token", "")
        if not access_token:
            return None
        req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            info = json.loads(resp.read().decode("utf-8"))
            return info.get("email") or None
    except Exception:
        return None


def _get_email_from_oauth_creds() -> Optional[str]:
    path = Path.home() / ".gemini" / "oauth_creds.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        id_token = data.get("id_token", "")
        if not id_token:
            return None
        payload_b64 = id_token.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("email")
    except Exception:
        return None


def _backup_path(account_num: int, email: str) -> Path:
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return CREDENTIALS_DIR / f".creds-{account_num}-{safe_email}.enc"


def _save_token_backup(account_num: int, email: str, content: str) -> None:
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    path = _backup_path(account_num, email)
    _atomic_write(path, encoded)


def _read_token_backup(account_num: int, email: str) -> Optional[str]:
    path = _backup_path(account_num, email)
    if not path.exists():
        return None
    try:
        encoded = path.read_text(encoding="utf-8").strip()
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        return decoded if decoded else None
    except Exception:
        return None


def _delete_token_backup(account_num: int, email: str) -> None:
    path = _backup_path(account_num, email)
    if path.exists():
        path.unlink()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        fd = -1
        os.replace(tmp, str(path))
        os.chmod(path, 0o600)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_quota_cache() -> dict:
    data = _read_json(QUOTA_CACHE)
    return data or {}


class AgySwitcher:
    def __init__(self):
        self._ensure_dirs()
        self._seq = self._load_sequence()

    def _ensure_dirs(self) -> None:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        for d in [BACKUP_ROOT, CREDENTIALS_DIR]:
            os.chmod(d, 0o700)

    def _load_sequence(self) -> SequenceData:
        data = _read_json(SEQUENCE_FILE)
        if data is None:
            return SequenceData()
        try:
            return SequenceData.from_dict(data)
        except Exception:
            return SequenceData()

    def _save_sequence(self) -> None:
        self._seq.last_updated = now_iso()
        _write_json(SEQUENCE_FILE, self._seq.to_dict())

    def _next_number(self) -> int:
        if not self._seq.accounts:
            return 1
        return max(self._seq.accounts.keys()) + 1

    def _find_account_by_email(self, email: str) -> Optional[Account]:
        for acc in self._seq.accounts.values():
            if acc.email == email:
                return acc
        return None

    def _find_account_by_number(self, num: int) -> Optional[Account]:
        return self._seq.accounts.get(num)

    def _resolve_account(self, identifier: str) -> Account:
        try:
            num = int(identifier)
            acc = self._find_account_by_number(num)
            if acc:
                return acc
        except ValueError:
            pass
        acc = self._find_account_by_email(identifier)
        if acc:
            return acc
        for acc in self._seq.accounts.values():
            if acc.alias and acc.alias.lower() == identifier.lower():
                return acc
        raise AccountNotFoundError(f"No account found: {identifier}")

    @staticmethod
    def _quota_for_email(email: str) -> dict:
        q = _read_quota_cache()
        quotas = q.get("accounts", {})
        return quotas.get(email, {})

    def list_accounts(self) -> list[dict]:
        active_email = _get_active_email_from_agy()
        rows = []
        for num in self._seq.sequence:
            acc = self._seq.accounts.get(num)
            if not acc:
                continue
            token_raw = _read_token_backup(num, acc.email)
            q = self._quota_for_email(acc.email)
            rows.append({
                "number": num,
                "email": acc.email,
                "alias": acc.alias,
                "disabled": acc.disabled,
                "active": acc.email == active_email,
                "has_token": bool(token_raw),
                "quota_five_hour": q.get("five_hour"),
                "quota_five_resets_at": q.get("five_resets_at"),
                "quota_seven_day": q.get("seven_day"),
                "quota_seven_resets_at": q.get("seven_resets_at"),
                "quota_fetched_at": q.get("captured_at"),
            })
        return rows

    def status(self) -> dict:
        active_email = _get_active_email_from_agy()
        if not active_email:
            return {"active": None, "message": "No active agy login found."}
        acc = self._find_account_by_email(active_email)
        return {
            "active": active_email,
            "managed": acc is not None,
            "number": acc.number if acc else None,
        }

    def add_current(self, email_override: Optional[str] = None) -> Account:
        token_raw = _read_current_token()
        if not token_raw:
            raise AgyError("No active agy token found. Login with agy first.")

        verified_email = _get_email_from_userinfo(token_raw)
        active_email = email_override or verified_email or _get_active_email_from_agy() or _get_email_from_oauth_creds()
        if not active_email:
            active_email = f"account-{self._next_number()}"

        existing = self._find_account_by_email(active_email)
        if existing:
            if verified_email:
                _save_token_backup(existing.number, active_email, token_raw)
                existing.updated_at = now_iso()
                self._save_sequence()
            return existing

        num = self._next_number()
        acc = Account(number=num, email=active_email)
        self._seq.accounts[num] = acc
        if num not in self._seq.sequence:
            self._seq.sequence.append(num)
        _save_token_backup(num, active_email, token_raw)
        self._save_sequence()
        return acc

    def remove_account(self, identifier: str) -> None:
        acc = self._resolve_account(identifier)
        _delete_token_backup(acc.number, acc.email)
        del self._seq.accounts[acc.number]
        if acc.number in self._seq.sequence:
            self._seq.sequence.remove(acc.number)
        self._save_sequence()

    def set_disabled(self, identifier: str, disabled: bool) -> Account:
        acc = self._resolve_account(identifier)
        acc.disabled = disabled
        acc.updated_at = now_iso()
        self._save_sequence()
        return acc

    def switch(self, identifier: Optional[str] = None) -> dict:
        if identifier is None:
            return self._rotate()

        target = self._resolve_account(identifier)
        return self._activate(target)

    def _rotate(self) -> dict:
        active_email = _get_active_email_from_agy()
        accounts = [
            self._seq.accounts[num]
            for num in self._seq.sequence
            if num in self._seq.accounts and not self._seq.accounts[num].disabled
        ]
        if not accounts:
            raise AgyError("No enabled accounts to switch to.")

        if not active_email or not self._find_account_by_email(active_email):
            target = accounts[0]
        else:
            current_idx = next(
                (i for i, a in enumerate(accounts) if a.email == active_email),
                -1,
            )
            target = accounts[(current_idx + 1) % len(accounts)]

        return self._activate(target)

    def _activate(self, target: Account) -> dict:
        token_raw = _read_token_backup(target.number, target.email)
        if not token_raw:
            raise AgyError(
                f"No stored token for {target.email}. "
                f"Login with agy and run 'agyswap add' first."
            )

        target_verified = _get_email_from_userinfo(token_raw)
        if target_verified and target_verified != target.email:
            raise AgyError(
                f"Stored token for {target.email} actually belongs to "
                f"{target_verified}. Login to {target.email} in agy and "
                f"run 'agyswap add' to fix."
            )

        previous_email = _get_active_email_from_agy()
        current_token = _read_current_token()
        if current_token:
            current_verified = _get_email_from_userinfo(current_token)
            if current_verified:
                existing = self._find_account_by_email(current_verified)
                if existing:
                    _save_token_backup(existing.number, current_verified, current_token)

        _write_current_token(token_raw)
        _write_google_accounts({"active": target.email, "old": []})
        self._seq.active_email = target.email
        self._save_sequence()
        return {
            "previous": previous_email,
            "active": target.email,
            "number": target.number,
        }

    def alias(self, identifier: str, alias: Optional[str] = None) -> Account:
        acc = self._resolve_account(identifier)
        if alias is None:
            return acc
        acc.alias = alias
        acc.updated_at = now_iso()
        self._save_sequence()
        return acc

    def unalias(self, identifier: str) -> Account:
        acc = self._resolve_account(identifier)
        acc.alias = None
        acc.updated_at = now_iso()
        self._save_sequence()
        return acc
