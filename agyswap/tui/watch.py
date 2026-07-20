from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, ListView, Static

from agyswap.tui.widgets import AccountItem

if TYPE_CHECKING:
    from agyswap.tui.app import AgySwapApp


class WatchScreen(Screen):
    _WATCH_TITLE = "watching all accounts"
    _SELECT_TITLE = "switch to which account? · enter confirm · esc cancel"

    BINDINGS = [
        Binding("s", "toggle_select", "Switch"),
        Binding("enter", "select_highlighted", "Confirm", priority=True),
        Binding("f", "app.refresh_full", "Refresh", show=False),
        Binding("escape,q", "back", "Back"),
        Binding("down,j", "nav_down", show=False),
        Binding("up,k", "nav_up", show=False),
    ]

    app: AgySwapApp

    def __init__(self, sw) -> None:
        super().__init__()
        self._sw = sw
        self._selecting = False
        self._numbers: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static("", id="list-title")
        yield ListView(id="accounts")
        yield Footer()

    def on_mount(self) -> None:
        self.watch(self.app, "snapshot", self._on_snapshot)
        self.query_one("#list-title", Static).update(self._WATCH_TITLE)
        super().on_mount()

    async def _on_snapshot(self, snap: list[dict] | None) -> None:
        if snap is None:
            return
        listview = self.query_one("#accounts", ListView)
        numbers = [str(r["number"]) for r in snap]
        if numbers != self._numbers:
            first_build = not self._numbers
            previous = listview.index
            await listview.clear()
            await listview.extend(AccountItem(r) for r in snap)
            self._numbers = numbers
            listview.index = (
                self._index_after_build(snap, first_build, previous)
                if numbers
                else None
            )
        else:
            for item, r in zip(listview.query(AccountItem), snap):
                item.set_account(r)

    def _index_after_build(
        self, snap: list[dict], first_build: bool, previous: int | None
    ) -> int | None:
        if first_build:
            return self._active_index(snap)
        return min(previous or 0, len(snap) - 1)

    def _active_index(self, snap: list[dict]) -> int:
        active_email = next((r["email"] for r in snap if r.get("active")), None)
        return next(
            (i for i, r in enumerate(snap) if r["email"] == active_email),
            0,
        )

    def _set_selecting(self, on: bool) -> None:
        self._selecting = on
        listview = self.query_one("#accounts", ListView)
        title = self.query_one("#list-title", Static)
        if on:
            snap = self.app.snapshot
            if snap:
                listview.index = self._active_index(snap)
            listview.focus()
            title.update(self._SELECT_TITLE)
        else:
            listview.index = None
            self.set_focus(None)
            title.update(self._WATCH_TITLE)
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "select_highlighted" and not self._selecting:
            return False
        return True

    def action_toggle_select(self) -> None:
        self._set_selecting(not self._selecting)

    def on_list_view_selected(self, event) -> None:
        if not self._selecting:
            return
        item = event.item
        if isinstance(item, AccountItem):
            self.app.do_switch(item.number)
            self._set_selecting(False)

    def action_select_highlighted(self) -> None:
        if self._selecting:
            self.query_one("#accounts", ListView).action_select_cursor()

    def action_back(self) -> None:
        if self._selecting:
            self._set_selecting(False)
        else:
            self.app.pop_screen()

    def action_nav_down(self) -> None:
        listview = self.query_one("#accounts", ListView)
        if self._selecting:
            listview.action_cursor_down()
        else:
            listview.scroll_down(animate=False)

    def action_nav_up(self) -> None:
        listview = self.query_one("#accounts", ListView)
        if self._selecting:
            listview.action_cursor_up()
        else:
            listview.scroll_up(animate=False)
