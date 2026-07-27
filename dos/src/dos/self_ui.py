"""SELF right rail — always-on personal surface for inventory + open folio.

Design lock (see IDEAS.md):
  - Right, always on
  - Home = inventory (later: tickets, installed calendars)
  - Folio open loads here; Esc returns home
  - No Bible-style line numbers on folio body
  - World log stays live while materials are open
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .world import World

# Desk split: world log ~60% · SELF ~40% (fr units in cli CSS).
# Min width keeps the rail usable on medium terminals; no low max-width cap.
TUI_SELF_PANE_WIDTH = "2fr"  # share of body row (log is 3fr → ~60/40)
TUI_SELF_PANE_MIN_WIDTH = 48
# Soft ceiling only for absurd ultrawides — still far wider than old 40-col strip
TUI_SELF_PANE_MAX_WIDTH = 96

# Log column share (paired with SELF width in cli CSS)
TUI_LOG_PANE_WIDTH = "3fr"
TUI_LOG_PANE_MIN_WIDTH = 40

SelfMode = Literal["home", "folio"]

# Folio wrap measure inside SELF (~40% of a typical desk; scrolls if longer)
SELF_FOLIO_BODY_WIDTH = 56

_NEW_LEAF_BODY_SEED = "…"


def format_self_home(world: World) -> str:
    """Compact inventory body for SELF home (reuses inv command output)."""
    from .commands import dispatch

    r = dispatch(world, "inv")
    body = (r.message or "").strip()
    if not body:
        return "[dim](empty hands)[/dim]"
    return body


def format_self_home_title() -> str:
    from . import format as fmt

    return (
        f"[bold {fmt.ACCENT}]SELF[/bold {fmt.ACCENT}]  "
        f"[dim]inventory · folio open loads here[/dim]"
    )


def format_self_folio_title(world: World, book_id: str, page_index: int) -> str:
    from .book import format_status_markup, page_index_after_nav
    from .ids import display_name

    book = world.get_instance(book_id)
    if book is None:
        return "[dim]SELF · folio missing[/dim]"
    name = display_name(book.name)
    safe = str(name).replace("\\", "\\\\").replace("[", "\\[")
    try:
        code = world.short_ref_of(book_id)
    except Exception:  # noqa: BLE001
        code = book.ven_code or "—"
    pages = list(world.list_book_pages(book_id))
    count = len(pages)
    idx = page_index_after_nav(page_index, 0, count)
    n = idx + 1 if count else 0
    status = format_status_markup(world.book_status(book_id))
    return (
        f"[bold]{safe}[/bold]  [dim]·[/dim]  [dim]{code}[/dim]\n"
        f"{status}  [dim]·[/dim]  leaf {n}/{count}"
    )


def format_self_folio_body(
    world: World, book_id: str, page_index: int
) -> tuple[str, int]:
    """
    Return (markup body, clamped page_index).

    Product: no line numbers in the SELF reader.
    """
    from .book import format_page_body, page_index_after_nav

    book = world.get_instance(book_id)
    if book is None:
        return "[dim]Book missing.[/dim]", 0
    pages = list(world.list_book_pages(book_id))
    count = len(pages)
    idx = page_index_after_nav(page_index, 0, count)
    if count == 0:
        body = format_page_body(
            page_index=0,
            page_count=0,
            title="",
            body="",
            width=SELF_FOLIO_BODY_WIDTH,
            numbered=False,
        )
        return body, 0
    page = pages[idx]
    body = format_page_body(
        page_index=idx,
        page_count=count,
        title=page["title"] or "",
        body=page["body"] or "",
        width=SELF_FOLIO_BODY_WIDTH,
        numbered=False,
    )
    return body, idx


def format_self_folio_foot() -> str:
    return (
        "[dim]↑↓ scroll  ·  ←/→ leaves  ·  + leaf  ·  e edit  ·  Esc home[/dim]"
    )


def format_self_home_foot() -> str:
    return "[dim]folio open · materials stay here while you walk[/dim]"


def self_nav_page(
    world: World, book_id: str, page_index: int, delta: int
) -> int:
    from .book import page_index_after_nav

    pages = list(world.list_book_pages(book_id))
    return page_index_after_nav(page_index, delta, len(pages))


def self_add_leaf(world: World, book_id: str, page_index: int) -> tuple[int, str]:
    """
    Insert a leaf after the current one.

    Returns (new_page_index, notify_message). Raises on hard failure.
    """
    from .book import page_index_after_nav
    from .commands import _push_book_page_delete_undo
    from .ids import display_name
    from .studio_text import prepare_stored_text

    book = world.get_instance(book_id)
    if book is None:
        raise RuntimeError("Book missing.")

    pages = list(world.list_book_pages(book_id))
    count = len(pages)
    if count == 0:
        insert_at = 1
        new_index = 0
    else:
        page_index = page_index_after_nav(page_index, 0, count)
        insert_at = page_index + 2
        new_index = page_index + 1

    seed_body = prepare_stored_text(_NEW_LEAF_BODY_SEED, studio=True)
    before = len(list(world.list_book_pages(book_id)))
    pid = world.add_book_page(
        book_id,
        "",
        seed_body,
        position=insert_at,
    )
    after = len(list(world.list_book_pages(book_id)))
    if after <= before:
        raise RuntimeError("Leaf was not created (count unchanged).")

    _push_book_page_delete_undo(
        world,
        book_id,
        pid,
        f"add leaf {display_name(book.name)}",
    )
    pages_now = list(world.list_book_pages(book_id))
    new_index = next(
        (i for i, p in enumerate(pages_now) if p["id"] == pid),
        min(new_index, max(0, len(pages_now) - 1)),
    )
    msg = f"Leaf added · leaf {new_index + 1}/{len(pages_now)}"
    return new_index, msg


def self_leaf_edit_context(
    world: World, book_id: str, page_index: int
) -> dict[str, Any] | None:
    """
    Snapshot for opening studio on the current leaf.

    Returns None if empty book / missing. Keys: page_id, prior_title,
    prior_body, leaf_n, book_name, initial, title.
    """
    from .book import page_index_after_nav
    from .ids import display_name
    from .studio_text import strip_studio_header

    book = world.get_instance(book_id)
    if book is None:
        return None
    pages = list(world.list_book_pages(book_id))
    if not pages:
        return None
    idx = page_index_after_nav(page_index, 0, len(pages))
    page = pages[idx]
    prior_body = page["body"] or ""
    initial = strip_studio_header(prior_body)
    if initial.strip() == _NEW_LEAF_BODY_SEED:
        initial = ""
    leaf_n = idx + 1
    return {
        "page_id": page["id"],
        "prior_title": page["title"] or "",
        "prior_body": prior_body,
        "leaf_n": leaf_n,
        "book_name": display_name(book.name),
        "initial": initial,
        "title": f"leaf {leaf_n} · {display_name(book.name)} · studio",
        "page_index": idx,
    }


def self_save_leaf(
    world: World,
    *,
    page_id: str,
    prior_title: str,
    prior_body: str,
    new_title: str,
    new_body: str,
    book_name: str,
    leaf_n: int,
) -> None:
    from .commands import _push_book_page_title_body_undo
    from .studio_text import prepare_stored_text

    stored = prepare_stored_text(new_body, studio=True)
    world.set_book_page_title_by_id(page_id, new_title)
    world.set_book_page_body_by_id(page_id, stored)
    if new_title != prior_title or stored != prior_body:
        _push_book_page_title_body_undo(
            world,
            page_id,
            prior_title,
            prior_body,
            f"leaf edit {book_name} {leaf_n}",
        )
