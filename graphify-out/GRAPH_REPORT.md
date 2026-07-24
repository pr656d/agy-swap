# Graph Report - .  (2026-07-24)

## Corpus Check
- Corpus is ~5,802 words - fits in a single context window. You may not need a graph.

## Summary
- 199 nodes · 419 edges · 10 communities (9 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Account Storage Core|Account Storage Core]]
- [[_COMMUNITY_Dashboard Screens|Dashboard Screens]]
- [[_COMMUNITY_Widget Styling|Widget Styling]]
- [[_COMMUNITY_App and Watch Flow|App and Watch Flow]]
- [[_COMMUNITY_README Guide|README Guide]]
- [[_COMMUNITY_CLI Commands|CLI Commands]]
- [[_COMMUNITY_Quota Probe Logic|Quota Probe Logic]]
- [[_COMMUNITY_Package Metadata|Package Metadata]]

## God Nodes (most connected - your core abstractions)
1. `AgySwitcher` - 34 edges
2. `AgySwapApp` - 28 edges
3. `DashboardScreen` - 27 edges
4. `AccountListScreen` - 18 edges
5. `WatchScreen` - 18 edges
6. `Account` - 14 edges
7. `AccountItem` - 12 edges
8. `SwitchScreen` - 11 edges
9. `AccountsPanel` - 11 edges
10. `agy-swap` - 11 edges

## Surprising Connections (you probably didn't know these)
- `AgySwitcher` --uses--> `Account`  [INFERRED]
  agyswap/switcher.py → agyswap/models.py
- `AgySwitcher` --uses--> `SequenceData`  [INFERRED]
  agyswap/switcher.py → agyswap/models.py
- `AgySwapApp` --uses--> `DashboardScreen`  [INFERRED]
  agyswap/tui/app.py → agyswap/tui/dashboard.py
- `AccountListScreen` --uses--> `AgySwapApp`  [INFERRED]
  agyswap/tui/dashboard.py → agyswap/tui/app.py
- `SwitchScreen` --uses--> `AgySwapApp`  [INFERRED]
  agyswap/tui/dashboard.py → agyswap/tui/app.py

## Import Cycles
- 3-file cycle: `agyswap/tui/app.py -> agyswap/tui/dashboard.py -> agyswap/tui/widgets.py -> agyswap/tui/app.py`
- 3-file cycle: `agyswap/tui/app.py -> agyswap/tui/watch.py -> agyswap/tui/widgets.py -> agyswap/tui/app.py`
- 4-file cycle: `agyswap/tui/app.py -> agyswap/tui/watch.py -> agyswap/tui/dashboard.py -> agyswap/tui/widgets.py -> agyswap/tui/app.py`

## Communities (10 total, 1 thin omitted)

### Community 0 - "Account Storage Core"
Cohesion: 0.11
Nodes (24): Account, now_iso(), SequenceData, AccountNotFoundError, AgyError, _atomic_write(), _backup_path(), _delete_token_backup() (+16 more)

### Community 1 - "Dashboard Screens"
Cohesion: 0.09
Nodes (9): AccountListScreen, DashboardScreen, SwitchScreen, AccountItem, MenuItem, ListItem, MenuEntries, Screen (+1 more)

### Community 2 - "Widget Styling"
Cohesion: 0.14
Nodes (15): severity_color(), account_card_text(), AccountCard, AccountsPanel, bar_cells(), format_duration(), mini_account_text(), reset_clock() (+7 more)

### Community 3 - "App and Watch Flow"
Cohesion: 0.11
Nodes (3): AgySwapApp, WatchScreen, App

### Community 4 - "README Guide"
Cohesion: 0.09
Nodes (22): Acknowledgements, Add more accounts, Add your first account, agy-swap, Aliases, Data locations, Disable / enable, From source (+14 more)

### Community 5 - "CLI Commands"
Cohesion: 0.18
Nodes (15): cmd_add(), cmd_alias(), cmd_disable(), cmd_enable(), cmd_list(), cmd_remove(), cmd_status(), cmd_statusline() (+7 more)

### Community 6 - "Quota Probe Logic"
Cohesion: 0.39
Nodes (7): _extract_access_token(), fetch_and_cache(), _fetch_for_email(), _fetch_for_token(), _find_lowest_remaining(), map_response(), _pick_representative_bucket()

## Knowledge Gaps
- **20 isolated node(s):** `agy-swap`, `Using uv (recommended)`, `Using pipx`, `From source`, `Updating` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgySwapApp` connect `App and Watch Flow` to `Dashboard Screens`, `Widget Styling`, `CLI Commands`, `Quota Probe Logic`?**
  _High betweenness centrality (0.308) - this node is a cross-community bridge._
- **Why does `run_tui()` connect `CLI Commands` to `Dashboard Screens`, `App and Watch Flow`?**
  _High betweenness centrality (0.264) - this node is a cross-community bridge._
- **Why does `DashboardScreen` connect `Dashboard Screens` to `Widget Styling`, `App and Watch Flow`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AgySwitcher` (e.g. with `Account` and `SequenceData`) actually correct?**
  _`AgySwitcher` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AgySwapApp` (e.g. with `DashboardScreen` and `WatchScreen`) actually correct?**
  _`AgySwapApp` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `DashboardScreen` (e.g. with `AgySwapApp` and `AccountItem`) actually correct?**
  _`DashboardScreen` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `AccountListScreen` (e.g. with `AgySwapApp` and `AccountItem`) actually correct?**
  _`AccountListScreen` has 5 INFERRED edges - model-reasoned connections that need verification._