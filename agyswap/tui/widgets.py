from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import ListItem, Static

from agyswap.tui.theme import (
    ACCENT,
    FOREGROUND,
    MUTED,
    SEV_CRIT,
    SEV_WARN,
    TRACK,
    severity_color,
)

if TYPE_CHECKING:
    from agyswap.tui.app import AgySwapApp

_BAR_FILLED = "━"
_BAR_HALF = "╸"
_BAR_EMPTY = "─"
_BAR_TICK = "┃"

STALE_OK_S = 180


def format_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        h, m = divmod(s // 60, 60)
        return f"{h}h {m}m" if m else f"{h}h"
    d, h = divmod(s // 3600, 24)
    return f"{d}d {h}h" if h else f"{d}d"


def reset_text(resets_at: str | None, now: float) -> str | None:
    if not resets_at:
        return None
    try:
        ts = datetime.fromisoformat(resets_at.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
    remaining = ts - now
    if remaining <= 0:
        return "resets now"
    return f"resets {format_duration(remaining)}"


def reset_clock(resets_at: str | None, now: float) -> str | None:
    if not resets_at:
        return None
    try:
        reset_utc = datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if reset_utc.timestamp() - now <= 0:
        return None
    return reset_utc.astimezone().strftime("%H:%M")


def bar_cells(
    pct: float | None,
    width: int,
    *,
    stale: bool = False,
    threshold: float | None = None,
) -> Text:
    text = Text()
    if pct is None:
        text.append(_BAR_EMPTY * width, style=TRACK)
        return text
    frac = min(max(pct, 0.0), 100.0) / 100.0
    cells = frac * width
    full = int(cells)
    half = (cells - full) >= 0.5 and full < width
    tick_at: int | None = None
    if threshold is not None:
        tick_at = min(width - 1, max(0, round(threshold / 100.0 * width)))
    color = severity_color(pct)
    fill_style = f"{color} dim" if stale else color
    for i in range(width):
        if tick_at is not None and i == tick_at:
            text.append(_BAR_TICK, style=SEV_WARN)
        elif i < full:
            text.append(_BAR_FILLED, style=fill_style)
        elif i == full and half:
            text.append(_BAR_HALF, style=fill_style)
        else:
            text.append(_BAR_EMPTY, style=TRACK)
    return text


def usage_bar(
    label: str,
    pct: float | None,
    suffix: str | None,
    width: int,
    *,
    stale: bool = False,
    threshold: float | None = None,
) -> Text:
    text = Text()
    text.append(f"{label} ", style=MUTED)
    text.append(bar_cells(pct, width, stale=stale, threshold=threshold))
    if pct is None:
        text.append("  —", style=MUTED)
    else:
        color = severity_color(pct)
        text.append(f" {pct:3.0f}%", style=f"{color} dim" if stale else color)
    if suffix:
        text.append(f"  {suffix}", style=MUTED)
    return text


def usage_rows(acc: dict, now: float) -> list[tuple[str, float, str, str]]:
    rows: list[tuple[str, float, str, str]] = []
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        pct = acc.get(f"quota_{key}")
        if pct is None:
            continue
        resets_at = acc.get(f"quota_{key}_resets_at")
        reset = reset_text(resets_at, now)
        clock = reset_clock(resets_at, now) if reset else None
        suffix = reset or ""
        suffix_full = f"{reset} · {clock}" if (reset and clock) else suffix
        rows.append((label, float(pct), suffix, suffix_full))
    return rows


def account_card_text(
    acc: dict,
    width: int,
    *,
    threshold: float | None = None,
    now: float | None = None,
) -> Text:
    now = now if now is not None else time.time()
    text = Text()
    text.append(f"{acc['number']:>2}  ", style=f"bold {FOREGROUND}")
    email = acc["email"]
    text.append(email, style=FOREGROUND)
    if acc.get("alias"):
        text.append(f"  ({acc['alias']})", style=f"bold {ACCENT}")
    if acc.get("active"):
        text.append("   ● active", style=f"bold {ACCENT}")
    if acc.get("disabled"):
        text.append("   (disabled)", style=MUTED)

    fetched_at = acc.get("quota_fetched_at")
    if fetched_at:
        age_s = now - float(fetched_at)
        if age_s > STALE_OK_S:
            text.append(f"   · {format_duration(age_s)} ago", style=MUTED)

    rows = usage_rows(acc, now)
    if not rows:
        text.append("\n    ")
        text.append("quota: N/A  [dim](run agy to populate)[/dim]", style=MUTED)
        return text

    stale = fetched_at and (now - float(fetched_at)) > STALE_OK_S
    label_width = max(len(label) for label, _pct, _suffix, _full in rows)
    bar_width = max(12, min(30, width - 42 - label_width))
    row_overhead = 4 + label_width + 1 + bar_width + 5 + 2
    for label, pct, suffix, suffix_full in rows:
        per_row_overhead = row_overhead - 2 + len(suffix_full)
        if suffix_full != suffix and per_row_overhead <= width:
            suffix = suffix_full
        text.append("\n    ")
        text.append(
            usage_bar(
                f"{label:<{label_width}}",
                pct,
                suffix or None,
                bar_width,
                stale=stale,
                threshold=threshold,
            )
        )
    return text


def mini_account_text(acc: dict, now: float) -> Text:
    text = Text(no_wrap=True, overflow="ellipsis")
    text.append(f"{acc['number']:>2}  ", style=f"bold {MUTED}")
    text.append(acc["email"], style=FOREGROUND)
    if acc.get("alias"):
        text.append(f"  ({acc['alias']})", style=ACCENT)
    if acc.get("disabled"):
        text.append("  (disabled)", style=MUTED)
    text.append("   ")

    fetched_at = acc.get("quota_fetched_at")
    stale = fetched_at and (now - float(fetched_at)) > STALE_OK_S
    parts = 0
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        pct = acc.get(f"quota_{key}")
        if pct is None:
            continue
        pct = float(pct)
        if parts:
            text.append(" · ", style=TRACK)
        color = severity_color(pct)
        text.append(f"{label} ", style=MUTED)
        text.append(f"{pct:.0f}%", style=f"{color} dim" if stale else color)
        if pct >= 100:
            resets_at = acc.get(f"quota_{key}_resets_at")
            reset = reset_text(resets_at, now)
            if reset:
                text.append(f" ({reset})", style=MUTED)
        parts += 1
    if not parts:
        text.append("quota N/A", style=MUTED)
    return text


class AccountsPanel(Static):
    def __init__(self, *, show_minis: bool = True, id: str | None = None) -> None:
        super().__init__(id=id)
        self._show_minis = show_minis

    def on_mount(self) -> None:
        self.watch(self.app, "snapshot", lambda _: self.refresh(layout=True))

    def render(self) -> Text:
        app: AgySwapApp = self.app  # type: ignore[assignment]
        snap = getattr(app, "snapshot", None)
        if snap is None:
            return Text("loading…", style=MUTED)
        if not snap:
            return Text(
                "No managed accounts yet.\n"
                "Use the menu below to add one.",
                style=MUTED,
            )
        now = time.time()
        width = (self.size.width or 80) - 2
        blocks: list[Text] = []
        for r in snap:
            if r.get("active"):
                blocks.append(
                    account_card_text(r, width, threshold=app.threshold_pct, now=now)
                )
            elif self._show_minis:
                blocks.append(mini_account_text(r, now))
        if not blocks:
            return Text("no active managed login", style=MUTED)
        text = Text()
        previous_multiline = False
        for i, block in enumerate(blocks):
            multiline = "\n" in block.plain
            if i:
                text.append("\n\n" if (multiline or previous_multiline) else "\n")
            text.append(block)
            previous_multiline = multiline
        return text


class AccountCard(Static):
    def __init__(self, acc: dict, *, threshold: float | None = None) -> None:
        super().__init__()
        self._acc = acc
        self._threshold = threshold

    def set_account(self, acc: dict) -> None:
        self._acc = acc
        self.refresh(layout=True)

    def render(self) -> Text:
        return account_card_text(
            self._acc, self.size.width or 80, threshold=self._threshold
        )


class AccountItem(ListItem):
    def __init__(self, acc: dict) -> None:
        super().__init__(AccountCard(acc))
        self.number = acc["number"]
        self.email = acc["email"]

    def set_account(self, acc: dict) -> None:
        self.number = acc["number"]
        self.email = acc["email"]
        self.query_one(AccountCard).set_account(acc)


class MenuItem(ListItem):
    def __init__(self, label: str, action_id: str, *, muted: bool = False) -> None:
        style = MUTED if muted else FOREGROUND
        super().__init__(Static(Text(label, style=style)))
        self.action_id = action_id
