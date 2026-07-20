import argparse
import sys

from agyswap import __version__
from agyswap.switcher import AgySwitcher, AccountNotFoundError, AgyError
from agyswap.paths import GOOGLE_ACCOUNTS_PATH

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def cmd_list(sw: AgySwitcher, args) -> None:
    rows = sw.list_accounts()
    if not rows:
        console.print("[dim]No accounts managed yet.[/dim]")
        console.print("Login with [bold]agy[/bold] first, then run [bold]agyswap add[/bold].")
        return

    table = Table(box=box.ROUNDED)
    table.add_column("#", style="bold")
    table.add_column("Email")
    table.add_column("Alias")
    table.add_column("Status")
    table.add_column("Token")

    for r in rows:
        num = str(r["number"])
        email = r["email"]
        alias = r["alias"] or ""
        status_parts = []
        if r["active"]:
            status_parts.append("[green]active[/green]")
        if r["disabled"]:
            status_parts.append("[yellow]disabled[/yellow]")
        status = " ".join(status_parts) if status_parts else "[dim]—[/dim]"
        token = "[green]✓[/green]" if r["has_token"] else "[red]✗[/red]"
        table.add_row(num, email, alias, status, token)

    console.print(table)
    console.print(f"\n[dim]Active account tracked at: {GOOGLE_ACCOUNTS_PATH}[/dim]")


def cmd_status(sw: AgySwitcher, args) -> None:
    info = sw.status()
    if info["active"] is None:
        console.print("[yellow]No active agy login detected.[/yellow]")
        console.print("Run [bold]agy[/bold] to login, then [bold]agyswap add[/bold].")
        return
    managed = "yes" if info["managed"] else "[yellow]not managed[/yellow]"
    console.print(f"Active account: [bold]{info['active']}[/bold]")
    console.print(f"Managed: {managed}")
    if info["number"]:
        console.print(f"Slot: #{info['number']}")


def cmd_add(sw: AgySwitcher, args) -> None:
    acc = sw.add_current(email_override=args.email)
    console.print(f"[green]Added[/green] account #{acc.number}: {acc.email}")


def cmd_remove(sw: AgySwitcher, args) -> None:
    try:
        acc = sw._resolve_account(args.identifier)
        sw.remove_account(args.identifier)
        console.print(f"[red]Removed[/red] account #{acc.number}: {acc.email}")
    except AccountNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_switch(sw: AgySwitcher, args) -> None:
    try:
        result = sw.switch(args.identifier)
        prev = result["previous"] or "(none)"
        console.print(
            f"Switched: [dim]{prev}[/dim] → [bold green]{result['active']}[/bold green]"
        )
    except (AgyError, AccountNotFoundError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_disable(sw: AgySwitcher, args) -> None:
    try:
        acc = sw.set_disabled(args.identifier, True)
        console.print(f"[yellow]Disabled[/yellow] account #{acc.number}: {acc.email}")
    except AccountNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_enable(sw: AgySwitcher, args) -> None:
    try:
        acc = sw.set_disabled(args.identifier, False)
        console.print(f"[green]Enabled[/green] account #{acc.number}: {acc.email}")
    except AccountNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_alias(sw: AgySwitcher, args) -> None:
    try:
        if args.unset:
            acc = sw.unalias(args.identifier)
            console.print(f"Removed alias for #{acc.number}: {acc.email}")
        elif args.name:
            acc = sw.alias(args.identifier, args.name)
            console.print(f"Set alias [bold]'{args.name}'[/bold] for #{acc.number}: {acc.email}")
        else:
            rows = sw.list_accounts()
            found = False
            for r in rows:
                if r["alias"]:
                    console.print(f"  {r['number']}: {r['alias']} [dim]({r['email']})[/dim]")
                    found = True
            if not found:
                console.print("[dim]No aliases set.[/dim]")
    except AccountNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def cmd_tui(sw: AgySwitcher, args) -> None:
    try:
        from agyswap.tui.app import run_tui
        run_tui(sw, start_watch=False)
    except ImportError:
        console.print("[red]TUI requires textual. Install:[/red]")
        console.print("  pip install 'agy-swap[tui]'")
        sys.exit(1)


def cmd_watch(sw: AgySwitcher, args) -> None:
    try:
        from agyswap.tui.app import run_tui
        run_tui(sw, start_watch=True)
    except ImportError:
        console.print("[red]TUI requires textual. Install:[/red]")
        console.print("  pip install 'agy-swap[tui]'")
        sys.exit(1)


def cmd_statusline(sw, args) -> None:
    if args.setup:
        module = "agyswap.statusline"
        console.print("Add this alias to your shell:")
        console.print(f"  alias agy='agy -S \"python3 -m {module}\" ")
        console.print()
        console.print("Or use it once:")
        console.print(f"  agy -S \"python3 -m {module}\"")
        console.print()
        console.print("[dim]The statusline script captures quota data to[/dim]")
        console.print(f"[dim]  ~/.agy-swap/cache/quota.json[/dim]")
        console.print("[dim]so agyswap TUI can display it.[/dim]")
        return

    from agyswap.statusline import main as sl_main
    sl_main()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agyswap",
        description="Multi-account switcher for Antigravity CLI (agy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  agyswap add              capture current login as a managed account
  agyswap list             list managed accounts
  agyswap switch           rotate to next enabled account
  agyswap switch 2         switch to account #2
  agyswap switch email     switch to account by email
  agyswap disable 2        hold an account out of rotation
  agyswap enable 2         return an account to rotation
  agyswap remove 2         remove an account
  agyswap alias 2 work     set an alias
  agyswap alias 2 --unset  remove an alias
  agyswap tui              interactive dashboard
  agyswap watch            dashboard on the watch page
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="list managed accounts")
    p_status = sub.add_parser("status", help="show current active account")
    p_add = sub.add_parser("add", help="capture current agy login as a managed account")
    p_add.add_argument("--email", help="email for the account (auto-detected if omitted)")

    p_switch = sub.add_parser("switch", help="switch accounts")
    p_switch.add_argument("identifier", nargs="?", help="account number, email, or alias")

    p_remove = sub.add_parser("remove", aliases=["rm"], help="remove an account")
    p_remove.add_argument("identifier", help="account number, email, or alias")

    p_disable = sub.add_parser("disable", help="hold account out of rotation")
    p_disable.add_argument("identifier", help="account number, email, or alias")

    p_enable = sub.add_parser("enable", help="return account to rotation")
    p_enable.add_argument("identifier", help="account number, email, or alias")

    p_alias = sub.add_parser("alias", help="manage account aliases")
    p_alias.add_argument("identifier", nargs="?", help="account number, email, or alias")
    p_alias.add_argument("name", nargs="?", help="alias name")
    p_alias.add_argument("--unset", action="store_true", help="remove alias")

    sub.add_parser("tui", help="launch interactive dashboard")
    sub.add_parser("watch", help="dashboard on the watch page")

    p_sl = sub.add_parser("statusline", help="capture quota data from agy -S")
    p_sl.add_argument("--setup", action="store_true",
                      help="print setup instructions")

    args = parser.parse_args()

    sw = AgySwitcher()

    if not args.command:
        cmd_tui(sw, args)
        return

    dispatch = {
        "list": cmd_list,
        "status": cmd_status,
        "add": cmd_add,
        "switch": cmd_switch,
        "remove": cmd_remove,
        "rm": cmd_remove,
        "disable": cmd_disable,
        "enable": cmd_enable,
        "alias": cmd_alias,
        "tui": cmd_tui,
        "watch": cmd_watch,
        "statusline": cmd_statusline,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(sw, args)


if __name__ == "__main__":
    main()
