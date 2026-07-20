# agy-swap

Multi-account switcher for Antigravity CLI (agy). Easily switch between multiple Google/Gemini accounts without logging out. Track Gemini API quota for every account in a live TUI dashboard.

## Installation

### Using uv (recommended)

```bash
uv tool install agy-swap
```

### Using pipx

```bash
pipx install agy-swap
```

### From source

```bash
git clone https://github.com/pr656d/agy-swap.git
cd agy-swap
uv sync
uv run agyswap help
```

### Updating

```bash
uv tool upgrade agy-swap       # uv
pipx upgrade agy-swap          # pipx
```

## Usage

### Add your first account

Log into agy with your first account, then:

```bash
agyswap add
```

### Add more accounts

Log in with another account, then:

```bash
agyswap add
```

### Switch accounts

Rotate to the next enabled account:

```bash
agyswap switch
```

Or switch to a specific account:

```bash
agyswap switch 2
agyswap switch user@gmail.com
agyswap switch work               # by alias, once set with `agyswap alias 2 work`
```

See them all at a glance:

```bash
agyswap list
```

### Interactive dashboard (TUI)

Run `agyswap tui` for the full-screen dashboard — every account's 5-hour and weekly usage with live progress bars, reset times, and switching, all keyboard-driven. `agyswap watch` opens it straight to the live monitor.

Keyboard shortcuts from the dashboard:

| Key | Action |
|-----|--------|
| `s` | Open account picker to switch |
| `w` | Switch to watch screen |
| `a` | Add current account |
| `f` | Refresh |
| `j`/`k` | Navigate menu |
| `q` | Quit |

### Aliases

```bash
agyswap alias 2 work            # give account 2 the alias "work"
agyswap alias 2 --unset         # remove alias
agyswap alias                   # list all aliases
```

### Disable / enable

Hold an account out of rotation without removing its credentials:

```bash
agyswap disable 2
agyswap enable 2
```

### Remove an account

```bash
agyswap remove 2
```

## Quota data

Quota usage appears in `agyswap list` and the TUI. Two ways to populate it:

- **Automatic (TUI only)** — when agy is running, the TUI probes its local language server via ConnectRPC every 3 seconds and writes quota to cache. No setup needed.
- **Statusline** — run `agy` with the statusline script to capture quota on every prompt:

  ```bash
  agy -S "python3 -m agyswap.statusline"
  ```

  Add it as a shell alias:

  ```bash
  alias agy='agy -S "python3 -m agyswap.statusline"'
  ```

  The script writes to `~/.agy-swap/cache/quota.json` which the TUI and CLI read.

## Limitations

- **Switch does not affect the current agy session** — agy reads its auth token at startup and caches it in memory. Switching accounts only replaces the token on disk/keychain. You must exit the current agy session (or open a new terminal) for the change to take effect. New agy invocations will pick up the swapped account.
- **Quota data** is only available when agy is running (for the automatic TUI probe) or when using the statusline script via `agy -S`.

## How it works

- Backs up OAuth tokens when you add an account (`~/.agy-swap/credentials/`)
- Swaps only the account-specific login by replacing the active token and Google accounts file
- Account credentials stored securely using platform-appropriate methods (macOS Keychain + file fallback)
- Quota fetched from agy's local gRPC language server when running, or captured via the `-S` statusline mechanism

## Data locations

| Data | Path |
|------|------|
| Credential backups | `~/.agy-swap/credentials/` |
| Account registry | `~/.agy-swap/sequence.json` |
| Quota cache | `~/.agy-swap/cache/quota.json` |

## Uninstall

Remove all data:

```bash
rm -rf ~/.agy-swap
```

Then uninstall the tool:

```bash
uv tool uninstall agy-swap
# or
pipx uninstall agy-swap
```

## Requirements

- Python 3.10+
- Antigravity CLI (agy) installed and logged in
- macOS, Linux

## Acknowledgements

Inspired by [claude-swap](https://github.com/realiti4/claude-swap) — multi-account switcher for Claude Code.

## License

MIT
