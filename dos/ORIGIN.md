# Origin

**Digital Office Spaces (DOS)** was branched from **World Builder Studio** on 2026-07-20 as a product-focused copy, not a git fork with full history.

| | |
|--|--|
| Source tree | `C:\Builds\world-studio` |
| Source remote (at branch time) | `https://github.com/kitten-lab/aidm-world-studio.git` |
| Source branch tip | `polish/desc-commit-lore-flags-arrow` (plus local uncommitted polish in that tree — copy used on-disk files at branch time) |
| Living desk (ALICE_BOX) | `C:\ALICE_BOX\world-builder-studios\dos` · maker **World Builder Studios** |
| Mausoleum | `C:\Builds\dos` (stale at `7d1f19a` / origin/main — missing SELF rail) |
| True tip when recovered | Grok worktree `C:\Users\theda\.grok\worktrees\builds-dos\dos-digital-office-spaces` (8 commits ahead of mausoleum main) |
| Historical GitHub | `kitten-lab/dos` (graveyard remote — re-island only if Hands says) |
| Package / module / CLI | `dos` |
| Product | Digital Office Spaces (**DOS** — again) |

## Why a clean history

- New product identity and commit story (office collab, not multiverse WBS changelog).
- No baggage from world-studio branches, worlds, or backup DBs.
- Ready for a dedicated GitHub repository and tidy initial commit.

## What was copied

- Python package (renamed `world_studio` → `dos`)
- Tests, docs stubs, scripts, schema, seeds
- Excluded: `.git`, `__pycache__`, egg-info, `worlds/`, `backup-worlds/`, virtualenvs

## ALICE_BOX seat + SELF rail recovery (2026-07-27)

1. First migrate from **`C:\Builds\dos`** (mausoleum = origin/main). World DB loaded; **SELF rail missing**.
2. Found worktree **8 commits ahead**, never merged into Builds main:
   - `1215132` always-on SELF rail, in-rail folios, betsoft seed path  
   - `6bf65f5` cyan folio titles; ↑↓ scroll leaf in SELF  
   - `9e46ba0` STUDIO Writer edits folio leaves inside SELF  
   - `293ac6a` SELF studio TextArea id fix  
   - plus Confluence roadmap import / move aliases commits  
3. Living desk resynced from that worktree tip (**player `worlds/` not clobbered**).

## Product intent (DOS)

Focus the tool on a **world space builder for collaborative digital offices**: agents and humans working across the world and wires; starting with collaborative human storage of **data, schedules, and chats** inside a **TUI** (other front ends optional later; TUI continues).

**Shell direction:** always-on **SELF** right rail (inventory home; folios open in-rail). Soft modal book reader was a temporary measure fix — not the office default.

## Rename note (2026-07-20)

First layout used `digital-office-spaces` / `digital_office_spaces`. Renamed to **`dos`** everywhere that matters (folder, package, module, CLI, GitHub) so the pun lands: terminal DOS, office DOS.
