from __future__ import annotations

from textual.theme import Theme

ACCENT = "#ffa62b"
FOREGROUND = "#e8e4de"
MUTED = "#8a8a8a"
BACKGROUND = "#141414"
SURFACE = "#1e1e1e"
PANEL = "#262626"

SEV_OK = "#87af87"
SEV_WARN = "#d7af5f"
SEV_CRIT = "#d75f5f"
TRACK = "#3a3a3a"

WARN_PCT = 70.0
CRIT_PCT = 90.0


def severity_color(pct: float | None) -> str:
    if pct is None:
        return MUTED
    if pct >= CRIT_PCT:
        return SEV_CRIT
    if pct >= WARN_PCT:
        return SEV_WARN
    return SEV_OK


AGY_SWAP_DARK = Theme(
    name="agy-swap-dark",
    primary=ACCENT,
    secondary=MUTED,
    accent=ACCENT,
    foreground=FOREGROUND,
    background=BACKGROUND,
    surface=SURFACE,
    panel=PANEL,
    success=SEV_OK,
    warning=SEV_WARN,
    error=SEV_CRIT,
    dark=True,
    variables={
        "footer-key-foreground": ACCENT,
        "block-cursor-background": PANEL,
        "block-cursor-foreground": FOREGROUND,
        "block-cursor-text-style": "none",
    },
)
