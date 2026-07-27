# GitHub — DOS (under World Builder Studios)

**Living desk:** `C:\ALICE_BOX\world-builder-studios\` (company island git root)  
**Product bay:** `dos/`  
**Maker:** World Builder Studios

## Company git (local)

```powershell
cd C:\ALICE_BOX\world-builder-studios
git status
git log --oneline
```

Branch: `main`. Birth: company house + DOS with SELF rail.  
**No `origin` yet.** When Hands says: create under **`chesters-imports`**, not `kitten-lab` (Builds / graveyard country).

```powershell
# only after Hands greenlights remote
cd C:\ALICE_BOX\world-builder-studios
gh repo create chesters-imports/world-builder-studios --private --source=. --remote=origin --push
```

## Archaeology (not the living remote)

| Place | Role |
|-------|------|
| `C:\Builds\dos` | Mausoleum · `kitten-lab/dos` · stale pre-SELF tip |
| `~\.grok\worktrees\builds-dos\dos-digital-office-spaces` | Worktree that held SELF rail (8 commits ahead of mausoleum) |

Do not push living-desk work to `kitten-lab/dos` by habit.

## Commit hygiene

- Keep `worlds/` and `*.world.db` out of git (see company `.gitignore`).
- Prefer small, focused commits.
- Do not force-push `main` unless you mean to rewrite history.
