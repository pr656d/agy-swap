from pathlib import Path

GEMINI_DIR = Path.home() / ".gemini"
AGY_CLI_DIR = GEMINI_DIR / "antigravity-cli"
AGY_TOKEN_PATH = AGY_CLI_DIR / "antigravity-oauth-token"
GOOGLE_ACCOUNTS_PATH = GEMINI_DIR / "google_accounts.json"
BACKUP_ROOT = Path.home() / ".agy-swap"
SEQUENCE_FILE = BACKUP_ROOT / "sequence.json"
CREDENTIALS_DIR = BACKUP_ROOT / "credentials"
QUOTA_CACHE = BACKUP_ROOT / "cache" / "quota.json"
