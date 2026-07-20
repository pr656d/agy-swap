from __future__ import annotations

from textual.theme import Theme

ACCENT = "#d7875f"  # warm terracotta
FOREGROUND = "#e8e4de"  # soft, slightly warm off-white
MUTED = "#8a8a8a"  # secondary text
BACKGROUND = "#141414"
SURFACE = "#1e1e1e"
PANEL = "#262626"

SEV_OK = "#87af87"  # calm green
SEV_WARN = "#d7af5f"  # amber
SEV_CRIT = "#d75f5f"  # soft red
TRACK = "#3a3a3a"  # unfilled bar track

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

