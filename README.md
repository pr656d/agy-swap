# agy-swap

Multi-account switcher for [Antigravity CLI](https://gemini.google.com/code/) (agy).

Manage multiple agy accounts, switch between them, and monitor your Gemini API quota — all from the command line or an interactive TUI dashboard.

## Features

- **Account switching** — rotate through accounts or switch by number/email/alias
- **Clipboard account IDs** — copy account IDs for paste into other contexts
- **TUI dashboard** — real-time account status, quota bars, and watch mode in a terminal UI
- **Quota monitoring** — see your 5-hour and weekly usage at a glance (via `agy` statusline or direct language server probe)
- **Aliases** — give accounts human-readable names
- **Disable/enable** — hold accounts out of rotation without removing them
- **Secure token storage** — credentials backed up to `~/.agy-swap/credentials/`

## Installation

```bash
git clone https://github.com/pr656d/agy-swap.git
cd agy-swap
pip install -e .          # CLI only
pip install -e ".[tui]"   # with TUI dashboard
```

## Usage

```bash
agyswap add              # capture current agy login
agyswap list             # list managed accounts
agyswap switch           # rotate to next account
agyswap switch 2         # switch to account #2
agyswap disable 2        # hold account out of rotation
agyswap enable 2         # return to rotation
agyswap alias 2 work     # set an alias
agyswap tui              # interactive dashboard
agyswap watch            # watch mode dashboard
```

## Quota data

Quota can be captured two ways:

- **Automatically** — the TUI probes agy's local language server via ConnectRPC on each refresh cycle (when agy is running).
- **Via statusline** — run `agy -S "python3 -m agyswap.statusline"` to write quota to `~/.agy-swap/cache/quota.json`.
