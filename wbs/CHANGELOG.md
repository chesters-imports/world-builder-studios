# Changelog

Short record of **shipped** work. Newest first.  
Ideas and doctrine live in [IDEAS.md](IDEAS.md) and [docs/product-map.md](docs/product-map.md).

Format: dated bullets, one line each — what landed, not a full story.

---

## 2026-08-10

- **Play mode:** `--play` shell (IF allowlist); builder verbs refuse with “Not in play.”; help filtered; cognitive verbs reserved as stubs (`consider` / `think` / `feel` / `remember`)
- **Copy-on-play:** play opens `~/.aidm/saves/<world>/current.play.db` (author world safe); `--continue` reopens save without re-applying start
- **Start place:** `start` / `start here` / `start set` / `start clear`; seeds stamp entry; new-game `apply_start_position` moves PC only (objects = whole-world snapshot)
- **Ship chrome:** play banner / TUI title `WBS - {title}`

## 2026-07-16

- **locate self:** avatar where-now readout (replaces status as the preferred verb); bare `locate` same; `locate <code>` reserved/planned; temporary aliases status/sit/whereami/where
- **retime:** `retime HST-NNN when @N` (or `--when` / bare `@N` / `unknown`) rewrites story when on every leg of that event; undo restores prior stamps
- **History where:** each row stores place + realm + timeline ids and snapshotted names; list lines show `Place · Realm / Timeline`
- **Rename history:** `rename` / `call` writes a `rename` life-of-item row on the instance (`Old → New`, optional `when @N` / `--when`, shared `HST-…`)
- **History event codes:** shared `HST-NNN` on all legs of one act; `history HST-001` / `history event …` lists every subject; lines show the code
- **Movement legs expanded:** take/drop also record place + player; spawn onto floor records place `receive`; put/take-from keep vessel; `history me` / `history here`
- **Movement history:** `take` / `drop` / `put` write life-of-item rows; put and take-from also record the vessel (`receive` / `give`); optional `when @N` / `--when N` (default `@unknown`, own craft time per act)
- **Create/spawn flags:** free-order `--type/--name/--desc/--when` (and short `-t -n -d -w`); legacy `|` / `when @N` still work
- **History backbone:** timeline nodes + life-of-item `history_entries`; `create`/`spawn`/`lore` take `when @N` or `when @unknown`; `history nodes|here|on|ven` (extended bag/visit/fold ideas kept in product-map, not built)
- Add [docs/product-map.md](docs/product-map.md) — ADM / Silo / AIDM / Forestry / history doctrine in-repo
- Link product map from [IDEAS.md](IDEAS.md)
- Add this changelog

## 2026-07-16 — initial public tree

- Initial commit: World Studio core (`world_studio`) — lean VEN kinds, folio reader, wiki soft reader, bootstrap Herenow seed, paths vocabulary, tests
- Package name `world-studio` / module `world_studio`; product name AIDM World Studio
