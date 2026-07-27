# Ideas (not committed to build)

Living list of half-finished concepts and polish intents for **Digital Office Spaces (DOS)** — collaborative office world builder (TUI-first).

**Product lineage (2026-07+):** Branched from **World Builder Studio** (`../world-studio`) as a clean product copy. Sibling trees: **[MIWBS](../miwbs/)**, **[VEN Mentor](../ven-minter/)**. DOS owns the **office collab** cut: shared places, data, schedules, chats for humans + agents.

**Formal product name:** **Digital Office Spaces (DOS)**.

### Seed doctrine (in the offices)

- Default spawn is **already on a company site** (Wire / Workday) — not a fantasy void or cathedral tour.
- Product flavors: **office** · **empty** · **bootstrap**. Companies inside the world use this tool; richer multi-tenant / multi-company seeds later.
- Collab surfaces live **in place** first (books/folios as calendar, channel, handbook); dedicated schedule/chat commands can grow on top.  
**AIDM** is *not* the app title — future narrative agent; **a-men** ladder: [docs/product-map.md](docs/product-map.md).

**Larger product map (Silo / ADM / AIDM / Forestry / history):** see [docs/product-map.md](docs/product-map.md) — durable doctrine in-repo so it is not lost in chat. Includes **shipped** story-when backbone *and* **parked** extended ideas (bags, visit, fold, lock, event VENs).

**Shipped foundation (story when):** `when @N` / `when @unknown` on create/spawn/lore; `history nodes|here|on|ven`. Live with this in the tool before bags/visit.

**Current product stance:** perfect tool use + live with history backbone. Prefer display polish and real play feedback over new ontology. Full history bags / visit / fold — see product-map “Later / parked.”

**Shell direction (2026-07):** always-on **SELF** right rail; folios open *in* SELF so you can still walk the office. Soft modal reader was a temporary fix for measure trust — wrong default for office collab.

---

## Next steps (active build list)

Ordered intent — grab from the top when cutting code. Stay **inside this DOS tree only** (do not edit sibling Builds products).

1. **SELF shell (right, always on)** — **landed (2026-07)**  
   - Fixed-width right rail (`self_ui` / `#self-pane`); world log stays live.  
   - Default home: compact **inventory**.  
   - One chrome column only.

2. **Folio open → SELF content mode** — **landed (2026-07)**  
   - `folio open` / `book open` loads into SELF (not soft modal).  
   - **Esc** returns SELF to inventory home.  
   - Leaf browse in-rail: ←/→ (h/l when rail focused), **`+`** add leaf, quiet toasts.  
   - **No Bible-style line numbers** (`format_page_body(..., numbered=False)`).

3. **In-rail studio loop** — **landed**  
   - Loop: read in SELF → **`e`** → STUDIO Writer **in the rail** → **Ctrl+S** → same leaf read → … → **Esc** cancels edit first, then closes folio.  
   - Command-line `<<studio` (desc / lore / page add) still uses the shared buffer modal.

4. **Help back to the raw log** — **landed (basic)**  
   - Help rail retired from TUI compose; `help` / `?` / `help <verb>` / F1 print into the world log.  
   - Still want **shorter verb-first blurbs** (content rewrite) so learning is not exhausting.

5. **Measure honesty under fixed SELF**  
   - Log width stable (SELF always present).  
   - Authored measure **72** still canonical for studio leaves.  
   - Optional later: soft expand SELF while studio open.

6. **Regression / tests** — **structure locks updated**  
   - SELF-rail expectations in `test_book` / `test_help_ui`. Live TUI play still the real proof.

7. **Roadmaps office pain → Confluence date-list port**  
   - Roleplay of “1 Betsoft slot release” as roadmap object with full map dates was **tedious to produce/insert**.  
   - **Snapshot:** local `offices/betsoft.office.db` (gitignored) · `--seed betsoft` when present.  
   - **Source format (product ops, plain text in Confluence)** — pasteable, not MS Project:

```text
Nov 17, 2025 - Dec 15, 2025: Design Phase & Math Start (4 weeks)

Dec 15, 2025 - Feb 9, 2026: Static Art Phase (7 weeks) + (1 week for Holidays) ← Extra 3 weeks…

Feb 9, 2026: Math and Specs to Devs (4 weeks before All Assets)

Mar 9, 2026: All Assets to Devs

Jul 14, 2026 - Jul 15, 2026: Active Rollout (Tuesday - Wednesday)

July 16, 2026: Global Release (Thursday)

Note: Exclusivity removed
```

   - **Line shapes:**  
     - *Range:* `Mon D, YYYY - Mon D, YYYY: Label (…weeks…) [+ extras] [← note]`  
     - *Point:* `Mon D, YYYY: Label (context) [← note]`  
     - *Blob note:* `Note: …` (or bare trailing notes)  
   - **What to keep in DOS (simplified, matches live Castaway practice):**  
     - Ticket **name** = phase / deliverable label (strip week counts and ← commentary)  
     - Ticket **desc** = date or `start - end` only (system doesn’t need week math)  
     - Optional: stash full raw line / ← notes as **record** on the title bin or ticket once, not in every name  
   - **What to drop on import:** `(N weeks)`, `+ (1 week for Holidays)`, weekday hints in parens, ← margin notes (or fold into one lore/record)  
   - **Target tree (existing pattern):**  
     `Roadmap Location → {year Qn} → {Mon YYYY} → {code - Title} → Production Dates` bin  
     → one **ticket** per date line  
   - **Port UX (landed):**  
     - `import roadmap <<studio` — **Title** = `27BG-111 - The Castaway`, **Body** = Confluence date list  
     - `import roadmap from <folio> [leaf n]` — same fields from a leaf  
     - Spawns **product bin → Production Dates → tickets** on the floor; you `put` into quarter/month  
     - Strips week counts / ← notes / holiday add-ons; `Note:` → product record  
   - **Related:** click-to-open uses **face code**, not name (Castaway vs Castaway GDD).

---

## Focus now (other tool use & presentation)

- **Look sheets** — presence tables, section order, density when rooms get full; progressive disclosure later
- **Ways on look** — restore inline ways (grouped table) for rapid movement without a second command; balance vs clutter in event/portal rooms
- **Action vocabulary** — keep refining verbs/labels (e.g. Ways vs Exits); consistency over novelty
- **Catalog lists** — extend the realm/vens mini-table polish to more lists only when it helps scanning
- **Word choices in hints** — quieter, clearer, less builder-noise
- **`locate <code|name>`** — find instance positions by VEN code / short ref / name (today only `locate self`); retire temporary `status`/`whereami` aliases when this lands
- **Portal link survives take/drop** — **shipped:** binding on app `state_json`; take/drop/put never clear it; only `portal clear`. UX notes on take/reinstall.
- **Content measure 72** — **phase 1 shipped:** `CONTENT_MEASURE`, ASCII turn HR, book `PAGE_VIEW_WIDTH`, studio ruler
- **Leaf title in singular studio** — **shipped:** Title field above body (`e` / `book page edit … <<studio`)
- **Leaf** — formal name for a book page unit in the reader; CLI may still say “page”
- **Book reader modal (soft)** — **shipped, demoted:** full-width soft-dim reader was phase 2; **replace with SELF rail open** (see Next steps). Keep modal code only until SELF lands, then remove.

### SELF + folio + studio (design lock — 2026-07)

**Problem (live):** Soft modal folio reader blocks walking the office with notebooks open; you cannot move materials or yourself while reading. Help rail often left open all day and makes long log lines feel broken / mentally heavy.

**Problem (historical, still true for authoring):** Old ~56-wide book side pane shifted the log so authors could not trust measure-72 layout. Fix = predictable chrome width + internal scroll, not “modal forever.”

| Decision | Lock |
|----------|------|
| **SELF placement** | **Right** rail |
| **SELF visibility** | **Always on** |
| **Desk split** | **~60/40** log : SELF (`3fr` / `2fr`). Was a ~40-col strip — too narrow for folios. 50/50 (`1fr`/`1fr`) is one nudge away if still tight. |
| **SELF home** | Inventory (later: tickets you carry, calendars you install) |
| **Folio open** | Content mode **inside SELF** |
| **Close folio** | **Esc** → back to SELF home |
| **Line numbers** | **Off** in DOS folio reader (product choice) |
| **Help** | **Raw world log** again; prefer bare-verb usage blurb (`print` → how to use print). Not a permanent rail. |
| **Edit loop** | In-pane: browse → `e` → Ctrl+S → next leaf → `e` … → Esc leaves folio |
| **Studio** | Still page-singular; shared STUDIO Writer buffer for desc / lore / folio leaves |
| **World log** | Always free for movement and look while SELF holds materials |
| **Narrow terminals** | Later: collapse rule if dual column becomes unusable — not a reason to drop always-on on normal desks |

**Not preferred:** soft modal as default folio view; help side rail as daily driver; multi-page `<<studio` buffer; bare `a` for add leaf (too easy to fat-finger — keep `+`).

```text
┌──────────────────────────────────────────┬────────────────────┐
│ WORLD LOG (live)                         │ SELF (always)      │
│ look / go / talk / help in log           │ home: inv …        │
│                                          │ open: folio leaves │
│                                          │ edit: e · Ctrl+S   │
│                                          │ Esc: close folio   │
├──────────────────────────────────────────┴────────────────────┤
│ › command                                                     │
└───────────────────────────────────────────────────────────────┘
```

---

## Passed by (capture, not grabbed yet)

Ideas that walked past the desk — keep visible so we do not re-derive from chat. Promote into **Next steps** when ready.

- **SELF width tokens** — pick fixed col budget (e.g. ~36–44) so log measure stays stable; document in CSS constants.
- **Tickets in SELF home** — open / Off Duty / select surface once ticket UX is daily-driver ready.
- **Installed calendars in SELF** — pin schedule folios or calendar bins you “install,” not every room folio.
- **Help rewrite (content)** — shorter verb-first blurbs; cut multi-hop index fatigue; maybe progressive `help print` vs giant cheat sheet.
- **Soft expand SELF while studio open** — optional wider edit column without full-screen modal.
- **Organize leaves in a book** — reorder / remove from reader structure surface (not in singular studio).
- **Wiki dossier in SELF** — same frame language as folio once folio-in-SELF works.
- **Collapse SELF on tiny terminals** — fallback overlay or toggle below N columns.
- **Pin last-opened folio** on SELF home as a one-key resume.
- **Look density / caps** — “+N more”, container-first presence when rooms flood.
- **Ways on look** — still in Focus now; not blocked by SELF work.

---

## Parked (book / leaves)

### Organize leaves in a book
Reorder, remove, and otherwise organize leaves inside a BOK from the reader (or a small structure surface). Not now — add/edit/browse is enough. When promoted: stay out of singular studio; keep leaf ops on the reader (will live in SELF content mode).

---

## Parked — Office Space / Roadmaps (keep simple)

**Context:** Narrative **office** for telecommute product work (igaming, many titles/month). Confluence is disjointed; the bet is a *place* where roadmaps can be held and read. Greg may already have calendar-math in Python — **do not rebuild MS Project in the MUD.**

### Method (live): quarter bin + game things + lore + link-out

**Why not folio-for-GDD + folio-for-schedule first:** too heavy. No tables/images; long GDD in leaves fights the TUI. That is why **outbound links** exist in studio text.

**Spatial shape = tools you already have:**

| Role | Kind | How you read it |
|------|------|-----------------|
| Roadmaps room | `place` | `look` / `look --deep` |
| Quarter calendar (Q3 2026) | `bin` | `look` / `examine Q3` → **Q3** bucket = titles |
| Game / title card | `thing` | `examine --deep Title` → desc + **full lore** |
| Real GDD / art / Jira | URLs in desc or lore | click out of CLI |
| Optional thin dates | field rows on **desc** | not a second folio |

```text
Roadmaps (place)
  └─ Q3 2026 (bin)           ← calendar shelf per quarter
       ├─ Title A (thing)
       ├─ Title B (thing)
       └─ Title C (thing)
  └─ Q4 2026 (bin)
```

**What goes where:**

- **desc** (`@desc studio`): one-screen card — status, key dates (field rows), GDD link.  
- **lore** (`lore on Title add…` + `examine --deep`): phase notes / filler chronology — *not* the GDD.  
- **folio**: only if you want multi-leaf authoring later; **not** required for the board.  
- Move a title to next quarter = `take` / `put` (MUD verbs, not Confluence tree).

**Sketch:**

```text
dig place Roadmaps | Board for quarterly title calendars.
dig bin Q3 2026 | Calendar shelf for Q3 titles.
dig thing Starfall | Title card.
@desc on starfall studio | …
:Status: green
:Soft launch: 2026-09-12
:GDD: https://…
lore on starfall add Kickoff | Math locked; art still open.
put starfall in q3
examine q3
examine --deep starfall
```

### Studio field rows (on the card)

```text
:Design start: 2024-01-03
:Math lock:    2024-02-01
:Art:          2024-03-15
:Release:      2024-07-01
```

On **instance desc** (studio), not only inside folios.

### Lore (primary depth for a title)

| Need | Status |
|------|--------|
| Add lore | **Yes** |
| `examine --deep` / `look --deep` | **Yes** |
| Edit / reorder lore | **No** — live without for board v1 |

### Next gaps (only if this shape hurts)

1. One real quarter + 2–3 titles before more engine.  
2. Lore edit if filler needs correction often.  
3. Optional subtypes `thing/title`, `bin/calendar` — not required.  
4. Greg import / printer much later.

**Do not:** Inline full GDD; phase VEN per micro-step; force every schedule into a folio; calendar-as-truth only inside the MUD.

---

## Design lock — lean VEN roots (**shipped in code**)

**Intent:** Adventure that knows itself — concepts that know how they interact.  
**Not:** invent a full VEN producer yet. **Not:** classic MUD taxonomy sprawl (goal/desire/purpose/feeling/archetype/material/event/realm/timeline all as peer roots).

**Roots are known systems of being** (selectors). **Subtypes** are author-chosen word labels that begin to define rule sets. **Primes** are named species; **instances** are lived copies.

### Proposed root set (7)

| Root | Role (baseline rules) |
|------|------------------------|
| **person** | Lived voice / body of needs; may hold sense, etc. |
| **place** | **Space** — the street, the outside, the ground you stand on. Not “inside of a house.” |
| **bin** | Something **put on** a place (or carried) that **stores** (look placement bucket). House, shelf, Q3 calendar, pouch. Aliases: box, crate, container. Not “everything contains” — all VENs *can* hold; **bin** is the *store* root. |
| **thing** | General “stuff”; expand via subtypes later (app, tool, material…). *Not* leaf-bearing by default. |
| **folio** | **Root** — thing-you-put-leaves-in (da Vinci). Distinct conditional usage already (soft reader, leaves, + leaf, studio, measure 72). Subtypes: **book**, **file-folder**, **sketchbook**, … |
| **symbol** | Abstract sense that acts by meaning (motif, law, sign…). Root of *concept* talk. |
| **sense** | Felt / atmospheric / drive-like presence (feeling, longing, pressure…). |
| **event** | Named occurrence / beat in the world (meeting, knock, launch). Free subtypes. Not history HST codes — those are craft trails. |

### Folio (locked — root, not a subtype of thing)

- **Why root:** already has a full rule set beyond general things (open → leaf reader, leaf stack, STUDIO Writer on a leaf, content measure). That *is* a known system of being.  
- **Why not “just thing”:** `folio/book`, `folio/file-folder`, `folio/sketchbook` are flavors of *leaf-bearing*, not of generic inventory.  
- **Leaf** stays the formal unit of content inside a folio.  
- **Book** demotes from root → **subtype** (or casual prime name) under **folio**.  
- Surface language can migrate book → folio over time; instance codes may keep **BOK-** prefix for a while (legacy kind code) or rebrand later.  
- **STUDIO Writer** (was “BOK Studio”) = shared buffer brand for *all* `<<studio` work (desc, lore, folio leaves) — not folio-only.
### Place vs bin (locked intuition)

- **My street** = **place** (space outside).  
- **My house / shelf / Q3** = **bin** someone put *on* that place; it **stores** (may be enterable later).  
- Prefer: **place** = open space; **bin** = volume that holds. Aliases: box, crate, container.

### Archetype (locked intuition)

- Archetype is **not** a peer of feeling under sense alone.  
- Archetype is closer to **a person of a symbol** — the *persons of symbols*.  
- Root affinity: **person** (type of person) *and/or* born from **symbol** (concept that walks).  
- Implementation options later (pick one when migrating):  
  - `person/archetype`  
  - or symbol that *elevates* / relates as person  
  - or sense that is *person-shaped* — weaker than “archetype ⊂ person of symbol”

### Fold map (today → lean)

| Current kind(s) | Lean home |
|-----------------|-----------|
| person | **person** |
| place | **place** (space; subtypes: road, porch, void… — not “house” as pure place) |
| object, material | **thing** |
| book | **folio** (+ subtype book / file-folder / sketchbook…) |
| concept | **symbol** |
| feeling, goal, desire, purpose | **sense** (subtype or prime) |
| archetype | **person/archetype** (or person-of-symbol) — *not* just sense |
| event | TBD: sense, symbol, or thing-with-rules |
| realm, timeline | layers / chrome — not roots |
| other | drop or rare escape hatch |

### What this is *not*

- Not full VEN producer / freeform ontology editor  
- Not “every kind must have subtypes”  
- Not pen-on-paper→book yet (capacity / elevate later)  
- **File-folder:** `folio/file-folder` (or prime under folio) — not a new root; not a generic thing  

### Shipped (strip pass)

- `KINDS` = person place bin thing folio symbol sense event + realm timeline  
- Aliases at create: book→folio/book, object→thing, feeling→sense/feeling, archetype→person/archetype, …  
- Codes: FOL, THG, SNS, CTR, SYM, … (legacy BOK/OBJ still parse where needed)  
- Look Things = thing/folio/container; Force = person/archetype; sense/event → Happened Here  
- Seeds use normalize on create_ven so old seed strings still work  

**Still soft:** surface commands still say `book open` (resolves folio); full help reword; deep subtype rule sets.

---

## Parked (systems / later)

### Submissions / forms / receipts

A VEN that behaves like a **form** (desk, counter, divine union filing). Using it prints a **receipt** (instance) with formatted fields. Examples: ticket counter, ineffable submissions dept.  
Prefer subtype-first (`object/form` or `book/receipt`) before a full new kind. Not now.

### VEN Studio (sibling app under AIDM)
Deep prime authoring (create, compose, lore, books) outside World Studio; write to `~/.aidm/ven-collector`. World Studio stays the stage; import becomes common. Collector + `.ven` packs are the thin waist already in progress.

### Look density / caps
When rooms hold many objects or ways: “+N more”, container-first presence, avoid flooding look. Related to ways-on-look tradeoff.

### Threshold / feel-first seed
Charged small start (not void, not full story spine); name that can age (not product chrome). Bootstrap now exists as the bare pole; Threshold remains optional middle.

### Progressive help / onboarding
Help and first-room hints tuned for “play as I feel” without drowning in builder commands.

### Cross-world / multi-file
Multiple world files as versions/templates; live portals between DBs deferred. Collector packs for idea migration.

### Extended VEN codes after I/E
World-stamped / expanded codes only when something has traveled; baseline codes stay simple in-DB.

---

## Parked — Consider / description hooks (attention, not inventory)

**Status:** Record only. **Do not build** until gamification / play layer is clearer — easy to convolve with wiki, examine, lore, and symbols.

**Impulse (Bloom / Wick play):** Description as a surface of *noticeable* threads, not only wallpaper. Example authored body:

```text
There was a {fire} here.
```

Player: `consider fire` (aliases TBD: `think`, `about`, `ponder`…) → short card — a **memory / concept residue**, not necessarily a takeable floor prop.

### Why it fits AIDM (if we ever ship it)
- **Prime** = Fire (symbol / concept kind of attention).  
- **Instance** = *this* room’s ash-memory, or local override of a shared concept.  
- Same doctrine as Key/Door: kinds at the root, lived hooks as copies.  
- Distinct from **thing on floor** (take/put/lock) — considerables live in **attention**, not inv.

### Already nearby (do not duplicate first)
| Have | Overlap |
|------|---------|
| Studio `[[wikilink]]` + `wiki` | Named dossier jump |
| `examine` / `look in` | Full object chrome |
| `symbol` / `sense` | Idea + feeling kinds |
| lore on place/instance | Deeper dig |

**Missing mid-weight verb:** not full examine, not full wiki — “I pull that word.”

### Sketch (for later, not a promise)
1. **Marker in text** — `{token}`, or studio-only mark; optional chrome on look.  
2. **Resolve** — place-local hook table and/or marker → symbol / sense-memory / lore.  
3. **Verb** — `consider <token>` → short prose + dim “more: wiki … / lore …”.  
4. **Resolve order (sketch)** — hooks on this place → markers in current desc → unique sense/symbol here → unique prime.  
5. **Seed test** — one Wick hook (`{last call}` → mood/memory) before a framework.

### Explicit non-goals (until play says otherwise)
- Not combat/stats topic trees.  
- Not free-floating strings with no VEN (keep exportable ontology).  
- Not replacing examine for physical props.  
- Not building the full IF conversation graph in one pass.

**Open:** gamification layer (what “considering” *earns* or *costs*) — decide play intent before storage/syntax. Prefer living with Bloom/Wick bins + doors longer.

---

## Shipped (orientation — not a changelog)

Reminders of recent foundations so polish builds on solid ground:

- VEN codes (`XXX-NNN`); instance refs `CODE-0001`
- `~/.aidm/ven-collector` · `vens export` / `ven load` (prime + instance packs)
- Place templates: free-standing `spawn` of place primes; dig still unique primes
- Portal `run` / `logout`; install-in-container; place subtypes; portal binding survives take/reinstall
- Look placement: **Here** (loose in room) + each **bin** name as bucket (shallow kids; empty shows); no kind taxonomy
- Shared-width presence rows (no per-table headers)
- Ways: command + grouped list; look only counts (inline restore parked above)
- Seeds: story, classic, void, **bootstrap** (Nothing + Small note)
- `vens rename` primes; `rename me` avatar
- Catalog tables: realm/timeline list & places, vens list

---

## How to use this file

1. Add ideas under **Parked** with one short paragraph max.  
2. Promote to **Focus now** only if it is presentation / tool clarity, or an explicit exception.  
3. When shipping something from here, move a one-liner into **Shipped** or delete the parked entry.  
4. Do not treat this as a promise to implement everything.

*Last reviewed: 2026-07-17 (consider/hooks parked; Bloom–Wick play before gamification)*
