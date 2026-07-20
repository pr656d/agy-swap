from __future__ import annotations

from functools import partial

from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.worker import WorkerState

from agyswap.tui.dashboard import DashboardScreen
from agyswap.tui.watch import WatchScreen
from agyswap.tui.theme import AGY_SWAP_DARK


class AgySwapApp(App):
    TITLE = "agy-swap"
    CSS_PATH = "agy.tcss"
    ENABLE_COMMAND_PALETTE = False

    POLL_INTERVAL_S = 3.0

    snapshot: reactive[list[dict] | None] = reactive(None)
    busy: reactive[bool] = reactive(False)

    def __init__(self, sw, start_watch: bool = False):
        super().__init__()
        self._sw = sw
        self._start = "watch" if start_watch else "dashboard"
        self._refreshing = False
        self.threshold_pct = None

    def on_mount(self) -> None:
        self.register_theme(AGY_SWAP_DARK)
        self.theme = "agy-swap-dark"
        self.push_screen(DashboardScreen(self._sw))
        if self._start == "watch":
            self.push_screen(WatchScreen(self._sw))
        self.set_interval(self.POLL_INTERVAL_S, self._tick)
        self._tick()

    def _tick(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        self.run_worker(
            partial(self._refresh_blocking),
            thread=True,
            group="refresh",
            exit_on_error=False,
            name="snapshot-refresh",
        )

    def _refresh_blocking(self) -> None:
        try:
            from agyswap.tui.quota_probe import fetch_and_cache
            fetch_and_cache()
            snap = self._sw.list_accounts()
            self.call_from_thread(self._apply_snapshot, snap)
        except Exception:
            self.call_from_thread(self._refresh_done)

    def _apply_snapshot(self, snap: list[dict]) -> None:
        self._refreshing = False
        self.snapshot = snap

    def _refresh_done(self) -> None:
        self._refreshing = False

    def on_worker_state_changed(self, event) -> None:
        if (
            event.state is WorkerState.ERROR
            and event.worker.group == "refresh"
        ):
            self._refreshing = False
            msg = str(event.worker.error)
            self.notify(f"Refresh failed: {msg}", severity="warning", timeout=6)

    def request_refresh(self) -> None:
        self._tick()

    def do_switch(self, number: str) -> None:
        try:
            self._sw.switch(str(number))
        except Exception as e:
            self.notify(f"Switch failed: {e}", severity="error")
        self.request_refresh()

    def do_toggle_disabled(self, number: str) -> None:
        snap = self.snapshot
        if snap is None:
            return
        target_state = None
        for r in snap:
            if str(r["number"]) == str(number):
                target_state = not r.get("disabled", False)
                break
        if target_state is None:
            return
        try:
            self._sw.set_disabled(str(number), target_state)
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")
        self.request_refresh()

    def do_remove(self, number: str) -> None:
        try:
            self._sw.remove_account(str(number))
        except Exception as e:
            self.notify(f"Remove failed: {e}", severity="error")
        self.request_refresh()

    def do_add_current(self) -> None:
        try:
            self._sw.add_current()
        except Exception as e:
            self.notify(f"Add failed: {e}", severity="error")
        self.request_refresh()

    def action_refresh_full(self) -> None:
        self.request_refresh()
        self.notify("Refreshing…", timeout=2)

    def action_open_watch(self) -> None:
        if isinstance(self.screen, WatchScreen):
            return
        self.push_screen(WatchScreen(self._sw))


def run_tui(sw, start_watch: bool = False) -> None:
    app = AgySwapApp(sw, start_watch=start_watch)
    app.run()
