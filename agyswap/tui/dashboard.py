from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, ListView, Static

from agyswap.tui.widgets import (
    AccountItem,
    AccountsPanel,
    MenuItem,
)

if TYPE_CHECKING:
    from agyswap.tui.app import AgySwapApp

FLASH_S = 1.5

MenuEntries = list[tuple[str, str]]

_BACK = ("← back", "back")


class AccountPicker(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, items: list[AccountItem], on_select: Callable):
        super().__init__()
        self._accounts = items
        self._on_select = on_select

    def action_cancel(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(*self._accounts, id="picker-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, AccountItem):
            self._on_select(item)
            self.dismiss(None)


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("s", "open_switch", "Switch accounts"),
        Binding("w", "app.open_watch", "Watch"),
        Binding("escape,left", "menu_back", "Back", show=False),
        Binding("q", "app.quit", "Quit"),
        Binding("f", "app.refresh_full", "Refresh", show=False),
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("a", "open_add", "Add", show=False),
    ]

    app: AgySwapApp

    def __init__(self, sw) -> None:
        super().__init__()
        self._sw = sw
        self._menu_stack: list[tuple[str, MenuEntries]] = []
        self._stamps: dict[str, float | None] = {}

    def compose(self) -> ComposeResult:
        yield AccountsPanel(id="accounts-panel")
        yield Static("", id="menu-title")
        yield ListView(id="menu")
        yield Footer()

    async def on_mount(self) -> None:
        self.watch(self.app, "snapshot", self._on_snapshot)
        self.query_one("#menu", ListView).focus()
        await self._push_menu("menu", self._root_entries())

    def _on_snapshot(self, snap: list[dict] | None) -> None:
        menu = self.query_one("#menu", ListView)
        self._flash_updated(snap, menu)
        self.query_one("#accounts-panel").refresh(layout=True)

    def _flash_updated(self, snap: list[dict] | None, listview: ListView) -> None:
        if snap is None:
            return
        new_stamps = {str(r["number"]): r.get("quota_fetched_at") for r in snap}
        if self._stamps:
            changed = {
                num
                for num, ts in new_stamps.items()
                if ts is not None and ts != self._stamps.get(num)
            }
            for item in listview.query(AccountItem):
                if str(item.number) in changed and not item.has_class("flash"):
                    item.add_class("flash")
                    self.set_timer(FLASH_S, partial(item.remove_class, "flash"))
        self._stamps = new_stamps

    def _root_entries(self) -> MenuEntries:
        return [
            ("Switch account…", "switch"),
            ("Watch accounts", "watch"),
            ("Add current account", "add"),
            ("Disable / enable account…", "disable-menu"),
            ("Remove account…", "remove-menu"),
            ("Refresh", "refresh"),
            ("Quit", "quit"),
        ]

    def _remove_entries(self) -> MenuEntries:
        snap = self.app.snapshot
        entries: MenuEntries = [
            (f"{r['number']}  {r['email']}", f"remove:{r['number']}")
            for r in (snap or ())
        ]
        entries.append(_BACK)
        return entries

    def _disable_entries(self) -> MenuEntries:
        snap = self.app.snapshot
        entries: MenuEntries = []
        for r in (snap or ()):
            name = r["email"]
            if r.get("alias"):
                name = f"{r['alias']} ({r['email']})"
            action = "→ enable" if r.get("disabled") else "→ disable"
            state = "  (disabled)" if r.get("disabled") else ""
            entries.append(
                (f"{r['number']}  {name}{state}   {action}", f"disable:{r['number']}")
            )
        entries.append(_BACK)
        return entries

    async def _push_menu(self, title: str, entries: MenuEntries) -> None:
        self._menu_stack.append((title, entries))
        await self._render_menu()

    async def _pop_menu(self) -> None:
        if len(self._menu_stack) > 1:
            self._menu_stack.pop()
            await self._render_menu()

    async def _render_menu(self) -> None:
        title, entries = self._menu_stack[-1]
        crumb = " › ".join(t for t, _ in self._menu_stack)
        self.query_one("#menu-title", Static).update(crumb)
        menu = self.query_one("#menu", ListView)
        await menu.clear()
        await menu.extend(
            MenuItem(label, action_id, muted=(action_id == "back"))
            for label, action_id in entries
        )
        menu.index = 0

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, MenuItem):
            await self._dispatch(item.action_id)

    async def _dispatch(self, action_id: str) -> None:
        app = self.app
        actions: dict[str, Callable[[], None]] = {
            "switch": self.action_open_switch,
            "watch": app.action_open_watch,
            "add": self.action_add,
            "refresh": self.action_refresh,
            "quit": app.exit,
        }
        if action_id == "back":
            await self._pop_menu()
        elif action_id == "disable-menu":
            await self._push_menu("disable / enable", self._disable_entries())
        elif action_id == "remove-menu":
            await self._push_menu("remove account", self._remove_entries())
        elif action_id.startswith("remove:"):
            number = action_id.split(":", 1)[1]
            self.app.do_remove(number)
            await self._pop_menu()
        elif action_id.startswith("disable:"):
            number = action_id.split(":", 1)[1]
            self.app.do_toggle_disabled(number)
            await self._pop_menu()
        else:
            actions[action_id]()

    def action_open_switch(self) -> None:
        snap = self.app.snapshot
        if not snap:
            return
        items = [AccountItem(r) for r in snap if not r.get("disabled")]

        def on_select(item):
            self.app.do_switch(item.number)

        self.push_screen(AccountPicker(items, on_select))

    async def action_menu_back(self) -> None:
        await self._pop_menu()

    def action_refresh(self) -> None:
        self.app.request_refresh()

    def action_add(self) -> None:
        self.app.do_add_current()

    def action_cursor_down(self) -> None:
        self.query_one("#menu", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#menu", ListView).action_cursor_up()
