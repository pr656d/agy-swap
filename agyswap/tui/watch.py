from __future__ import annotations

from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.widgets import ListView, Static

from agyswap.tui.dashboard import AccountListScreen
from agyswap.tui.widgets import AccountItem

if TYPE_CHECKING:
    from agyswap.tui.app import AgySwapApp


class WatchScreen(AccountListScreen):
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

    def __init__(self, sw=None) -> None:
        super().__init__()
        self._selecting = False

    def on_mount(self) -> None:
        self.query_one("#list-title", Static).update(self._WATCH_TITLE)
        super().on_mount()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "select_highlighted" and not self._selecting:
            return False
        return True

    def _index_after_build(
        self, snap: list[dict], first_build: bool, previous: int | None
    ) -> int | None:
        if not self._selecting:
            return None
        return super()._index_after_build(snap, first_build, previous)

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
