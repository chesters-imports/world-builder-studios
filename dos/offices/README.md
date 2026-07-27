# Office snapshots (local only)

Frozen SQLite campuses you can **reseed into** without rebuilding by hand.

**Not committed.** `*.office.db` under this folder is gitignored — real company
dates and roadmaps stay on your machine.

| File | Seed flag | What it holds |
|------|-----------|----------------|
| `betsoft.office.db` | `--seed betsoft` (also `roadmap`, `castaway`) | Betsoft Roadmaps campus snapshot (local). Create by copying your live world (below). |

## Install / reseed

```powershell
# Only works if offices/betsoft.office.db exists locally
py -3.12 -m dos --world worlds/betsoft.world.db --reseed --seed betsoft --textual
```

This **copies** the snapshot onto the world path. It does not invent tickets.

## Create / refresh the snapshot from live play

```powershell
Copy-Item -Force path\to\your\live.world.db offices\betsoft.office.db
```

Do **not** commit that file. Keep it local (or private backup).

## Isolation

Snapshots live only in this DOS tree under `offices/`. Do not push internal
schedules to the public repo.
