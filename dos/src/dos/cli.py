"""CLI and Textual entrypoints."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from . import format as fmt
from .commands import dispatch
from .db import connect, get_meta, init_schema, migrate_schema
from .help_cli import help_text_for_query
from .help_ui import HelpPane, parse_help_command
from .history import CommandHistory
from .seed import install_snapshot_seed, is_snapshot_seed, normalize_seed_flavor, seed_world
from .self_ui import (
    TUI_LOG_PANE_MIN_WIDTH,
    TUI_LOG_PANE_WIDTH,
    TUI_SELF_PANE_MAX_WIDTH,
    TUI_SELF_PANE_MIN_WIDTH,
    TUI_SELF_PANE_WIDTH,
    format_self_folio_body,
    format_self_folio_foot,
    format_self_folio_title,
    format_self_home,
    format_self_home_foot,
    format_self_home_title,
    self_add_leaf,
    self_leaf_edit_context,
    self_nav_page,
    self_save_leaf,
)
from .status import format_strip
from .world import World

DEFAULT_WORLD = Path(__file__).resolve().parents[2] / "worlds" / "seed.world.db"
console = Console(highlight=False)

# TUI chrome (exported for tests) — classic DOS blue terminal
# Help is log-native again; width tokens kept for residual tests/CSS
TUI_HELP_PANE_WIDTH = 56
TUI_HELP_PANE_MIN_WIDTH = 48
TUI_HELP_PANE_MAX_WIDTH = 72
# SELF widths re-exported from self_ui (TUI_SELF_PANE_*)

# CGA-ish blue screen: deep blue field, cyan borders, light gray text
TUI_BG = "#0000aa"
TUI_SURFACE = "#0000aa"
TUI_PANEL = "#0000bb"
TUI_BORDER = "#5555ff"
TUI_BORDER_ACCENT = "#55ffff"
TUI_INPUT_BG = "#000066"
TUI_TEXT = "#aaaaaa"
TUI_TEXT_BRIGHT = "#ffffff"
TUI_MUTED = "#5555aa"
TUI_LOGO_FG = "#ffffff"
TUI_LOGO_BG = "#0000ff"


def ensure_world(path: Path, reseed: bool = False, seed: str = "office") -> World:
    """
    Open or create *path*.

    Procedural seeds (office / empty / bootstrap) build into a new SQLite file.
    Snapshot seeds (betsoft / roadmap / castaway) **copy** ``offices/*.office.db``
    onto *path* — use these to restore precious campus labor, never invent it.
    """
    flavor = normalize_seed_flavor(seed)
    path = Path(path)

    if is_snapshot_seed(flavor):
        if reseed or not path.exists():
            install_snapshot_seed(path, flavor)
            console.print(
                fmt.hint(f"Installed office snapshot ({flavor}) · {path}")
            )
        conn = connect(path)
        init_schema(conn)
        migrate_schema(conn)
        return World(conn)

    if reseed and path.exists():
        path.unlink()
    is_new = not path.exists()
    conn = connect(path)
    if is_new or reseed:
        seed_world(conn, flavor=flavor)
        console.print(fmt.hint(f"Seeded world ({flavor}) · {path}"))
    else:
        init_schema(conn)
        migrate_schema(conn)
    return World(conn)


def _is_desc_multiline_start(line: str) -> bool:
    parts = line.strip().split(maxsplit=1)
    if not parts or parts[0].lower() != "@desc":
        return False
    if len(parts) < 2:
        return False
    rest = parts[1].strip().lower()
    # @desc <<  ·  @desc <<studio  ·  @desc on x <<studio
    if rest in ("<<", "{", "<<studio", "{studio"):
        return True
    if rest.endswith("<<") or rest.endswith("<<studio"):
        return True
    return False


def _desc_multiline_studio(line: str) -> bool:
    """Whether multiline @desc should store Studio Text."""
    low = line.strip().lower()
    return "studio" in low and ("<<" in low or "{" in low)


def _is_book_page_multiline_start(line: str) -> bool:
    """folio|book page|leaf add|edit … << or <<studio"""
    low = line.strip().lower()
    for prefix in ("book page ", "folio page ", "book leaf ", "folio leaf "):
        if low.startswith(prefix):
            return "<<" in low
    return False


def _book_page_multiline_studio(line: str) -> bool:
    low = line.strip().lower()
    return "studio" in low and "<<" in low


def _parse_book_page_multiline_start(line: str) -> dict | None:
    """
    Parse folio/book page multiline opener.

    folio page add <name> <title> <<studio
    book page add <name> <<studio          → title empty
    folio leaf edit <name> <n> <<studio
    """
    s = line.strip()
    low = s.lower()
    prefix = None
    for p in ("book page ", "folio page ", "book leaf ", "folio leaf "):
        if low.startswith(p):
            prefix = p
            break
    if prefix is None:
        return None
    rest = s[len(prefix) :].strip()
    for end in ("<<studio", "<<"):
        if rest.lower().endswith(end):
            rest = rest[: -len(end)].strip()
            break
    else:
        return None
    parts = rest.split(maxsplit=1)
    if not parts:
        return None
    action = parts[0].lower()
    if action not in ("add", "append", "edit", "set", "body"):
        return None
    tail = parts[1].strip() if len(parts) > 1 else ""
    studio = _book_page_multiline_studio(line)
    if action in ("edit", "set", "body"):
        tokens = tail.split()
        page_i = None
        page_val = None
        for i, tok in enumerate(tokens):
            if tok.isdigit():
                page_i = i
                page_val = int(tok)
                break
        if page_i is None or page_val is None:
            return None
        book_name = " ".join(tokens[:page_i]).strip()
        if not book_name:
            return None
        return {
            "action": "edit",
            "book_name": book_name,
            "page": page_val,
            "studio": studio,
        }
    return {
        "action": "add",
        "book_and_title": tail,
        "studio": studio,
    }


def _book_page_collect_hint(*, studio: bool) -> str:
    base = "Multiline book page"
    if studio:
        base += " (studio text · chapter section)"
    return (
        f"{base} — each line shown as added (logical lines; wrap doesn't renumber).  "
        f"undo / u = last line.  End with .  or >>"
    )


def _commit_book_page_multiline(
    world: World,
    meta: dict,
    body: str,
) -> str:
    """Build dispatch line after multiline collect; return command string.

    Body from ``MultilineDescDraft`` uses real newlines. Book parsers tokenize
    with ``str.split()``, so newlines must be escaped to ``\\n`` here; store
    path runs ``unescape_desc`` and restores logical lines for numbering.
    """
    from .textutil import escape_desc

    studio = bool(meta.get("studio"))
    body = escape_desc(body or "")
    if meta.get("action") == "edit":
        book_name = meta["book_name"]
        page = meta["page"]
        if studio:
            return f"book page edit {book_name} {page} studio | {body}"
        return f"book page edit {book_name} {page} {body}"
    # add: book_and_title is "book… [title words]"
    book_and_title = (meta.get("book_and_title") or "").strip()
    if not book_and_title:
        title = "Untitled"
        # need book from context — fail at dispatch
        if studio:
            return f"book page add | {title} | studio | {body}"
        return f"book page add | {title} | {body}"
    # Split book vs title with world at call site preferred — use greedy split in dispatch
    # Store as: book page add <book_and_title> with content as studio body
    # Parse: title is last word group if multi-word book... use content as body with title from tail
    # Commit form that parse_lore_add understands after book split:
    # book page add <book> Title | studio | body  OR book page add <book> | Title | studio | body
    if studio:
        # title may be multi-word after book name — leave as "tokens" and let command split
        return f"book page add {book_and_title} | studio | {body}"
    return f"book page add {book_and_title} | {body}"


# End multiline collection
_DESC_END_MARKERS = frozenset({".", ">>", "}"})
# During collection: pop only the last accepted draft line
_DESC_UNDO_TOKENS = frozenset({"undo", "u", "/undo", "-u"})


class MultilineDescDraft:
    """
    In-progress @desc << body: accept lines, undo last line, join on end.

    Pure buffer so REPL/TUI and tests share one path (no parallel reimplementation).
    """

    def __init__(self) -> None:
        self.lines: list[str] = []

    def __len__(self) -> int:
        return len(self.lines)

    def accept(self, line: str) -> None:
        """Append one content line (trailing newline already stripped by caller)."""
        self.lines.append(line)

    def undo_last(self) -> str | None:
        """Remove and return the last content line, or None if draft is empty."""
        if not self.lines:
            return None
        return self.lines.pop()

    def body(self) -> str | None:
        """Joined draft, or None if empty/whitespace-only (cancel)."""
        joined = "\n".join(self.lines)
        return joined if joined.strip() else None

    def feed(self, raw: str) -> str:
        """
        Process one input line during collection.

        Returns one of:
          ``accepted`` — content line stored (caller should echo)
          ``undone`` — last line removed (caller may show status)
          ``empty_undo`` — undo with nothing to pop
          ``done`` — end marker; body available via ``body()``
          ``cancel`` — end marker with empty draft
        """
        s = raw.rstrip("\n\r")
        stripped = s.strip()
        low = stripped.lower()
        if stripped in _DESC_END_MARKERS:
            return "done" if self.body() is not None else "cancel"
        if low in _DESC_UNDO_TOKENS:
            if self.undo_last() is None:
                return "empty_undo"
            return "undone"
        self.accept(s)
        return "accepted"


def _collect_multiline_desc(
    read_line,
    *,
    on_accepted=None,
    on_undone=None,
    on_empty_undo=None,
    history: CommandHistory | None = None,
) -> str | None:
    """
    Read lines until end marker. Echo/undo via optional callbacks.

    ``on_accepted(line, draft)`` — after each content line is stored.
    ``on_undone(removed, draft)`` — after last-line undo.
    ``on_empty_undo(draft)`` — undo when draft has no lines.
    ``history`` — when set, each accepted content line is pushed for up/down
    recall (studio and plain multiline). End markers / undo tokens are not pushed.

    Returns joined body or None if cancelled empty.
    """
    draft = MultilineDescDraft()
    while True:
        try:
            raw = read_line()
        except (EOFError, KeyboardInterrupt):
            break
        action = draft.feed(raw)
        if action == "accepted":
            text = draft.lines[-1]
            if history is not None:
                history.push_content_line(text)
            if on_accepted is not None:
                on_accepted(text, draft)
        elif action == "undone":
            if on_undone is not None:
                # removed line already popped; report count remaining
                on_undone(draft)
        elif action == "empty_undo":
            if on_empty_undo is not None:
                on_empty_undo(draft)
        elif action == "done":
            return draft.body()
        elif action == "cancel":
            return None
    return draft.body()


def _desc_collect_hint(*, studio: bool = False) -> str:
    base = "Multiline @desc"
    if studio:
        base += " (studio text)"
    return (
        f"{base} — each line is shown as added.  "
        f"undo / u = drop last line.  "
        f"End with a line containing only .  (or >>)"
    )


def _world_chrome_label(world_path: Path) -> str:
    """Window / banner file identity — path name, not seed flavor (e.g. The Void)."""
    return world_path.name or str(world_path)


def _dos_logo_markup() -> str:
    """Cute header badge: white DOS on bright blue pill (classic DOS chrome)."""
    return f"[bold {TUI_LOGO_FG} on {TUI_LOGO_BG}] DOS [/]"


def _studio_boot_banner_markup(world_path: Path, world_name: str) -> str:
    """Log-only tips after clear/mount (identity lives in the persistent header bar)."""
    _ = world_path, world_name
    return (
        f"[dim]help / ? or F1 = help in log  ·  folio open = SELF rail (←/→ · e · Esc)[/dim]\n"
        f"[dim]↑ / ↓ previous commands · locate self · clear · cls (clear+look)[/dim]\n"
    )


def _studio_boot_panel(world_path: Path, world_name: str) -> Panel:
    """Rich panel for plain REPL boot / clear."""
    _ = world_name
    file_label = _world_chrome_label(world_path)
    return Panel(
        f"{_dos_logo_markup()}  [dim]{fmt.safe(file_label)}[/dim]\n\n"
        f"[dim]try[/dim]    look · locate self · undo · help · clear\n"
        f"[dim]↑[/dim]       previous commands  ·  "
        f"[dim]tui[/dim]  python -m dos --textual",
        border_style="dim",
        padding=(1, 2),
        title="[bright_cyan]dos[/bright_cyan]",
        title_align="left",
    )


def _clear_repl_screen(
    world_path: Path | None = None,
    world_name: str | None = None,
    *,
    restore_banner: bool = False,
) -> None:
    """Best-effort clear for plain REPL. Banner only if restore_banner (boot)."""
    import os
    import sys

    # Windows terminals often support ANSI; fall back to newlines
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
    except OSError:
        console.print("\n" * 40)
    if (
        restore_banner
        and world_path is not None
        and world_name is not None
    ):
        console.print()
        console.print(_studio_boot_panel(world_path, world_name))
        console.print()


def run_repl(world: World, world_path: Path) -> None:
    name = get_meta(world.conn, "world_name", world_path.name) or world_path.name
    console.print()
    console.print(_studio_boot_panel(world_path, name))
    console.print()

    r = dispatch(world, "look")
    if r.message:
        console.print(r.message)
        console.print()

    history = CommandHistory()
    session = None
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import InMemoryHistory

        class _LinkedPtkHistory(InMemoryHistory):
            """prompt_toolkit up/down shares CommandHistory (incl. studio lines)."""

            def store_string(self, string: str) -> None:  # type: ignore[override]
                super().store_string(string)
                history.push(string)

        ptk_history = _LinkedPtkHistory()
        session = PromptSession(history=ptk_history)
    except ImportError:
        session = None

    def read_prompt(prefix: str = "›") -> str:
        if session is not None:
            from prompt_toolkit.formatted_text import HTML

            return session.prompt(HTML(f"<ansicyan><b>{prefix}</b></ansicyan> "))
        return console.input(f"[bright_cyan]{prefix}[/bright_cyan] ")

    while True:
        console.print(Rule(style="dim"))
        console.print(format_strip(world))
        try:
            line = read_prompt("›")
        except (EOFError, KeyboardInterrupt):
            console.print()
            console.print(fmt.hint("Bye."))
            break

        # Without prompt_toolkit, read_prompt does not store; keep CommandHistory filled.
        # With ptk, store_string already pushed (consecutive dup is a no-op).
        history.push(line)

        # << / <<studio → nano-like buffer editor (desc, book page, lore)
        from .multiline_open import (
            commit_multiline_session,
            parse_multiline_opener,
            seed_initial_body,
            seed_page_title,
        )
        from .text_editor import run_text_editor

        ml = parse_multiline_opener(line)
        if ml is not None:
            console.print(
                fmt.hint(
                    f"Opening editor · {ml.title}  ·  Ctrl+S save  ·  Esc / Ctrl+Q cancel"
                )
            )
            initial = seed_initial_body(world, ml)
            page_title = seed_page_title(world, ml)
            edited = run_text_editor(
                initial=initial,
                title=ml.title,
                studio=ml.studio,
                page_title=page_title,
            )
            if edited is None:
                console.print()
                console.print(fmt.hint("Editor cancelled."))
                console.print(fmt.turn_separator())
                continue
            result = commit_multiline_session(
                world,
                ml,
                edited.body,
                page_title=edited.page_title,
            )
            if result.clear_log:
                _clear_repl_screen(world_path, name)
            if result.message:
                console.print()  # blank after command / editor before result
                console.print(result.message)
                console.print(fmt.turn_separator())
            elif not result.clear_log:
                console.print(fmt.turn_separator())
            if result.quit:
                break
            continue

        result = dispatch(world, line)
        if result.clear_log:
            _clear_repl_screen(world_path, name)
        if result.message:
            console.print()  # blank after typed command before result
            console.print(result.message)
            console.print(fmt.turn_separator())
        elif not result.clear_log:
            console.print(fmt.turn_separator())
        if result.quit:
            break


def run_textual(world: World, world_path: Path) -> None:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.selection import Selection
    from textual.widgets import Footer, Input, RichLog, Static

    from .wiki_ui import make_wiki_reader_screen
    from .history import CommandHistory

    class SelectableWorldLog(RichLog):
        """World log with real mouse text selection + copy.

        Stock RichLog is almost selectable, but two gaps make drag feel
        like “the whole window lights up”:

        1. It never stamps ``offset`` meta on painted segments (plain
           ``Log`` does via ``Strip.apply_offsets``), so the compositor
           cannot resolve a content caret → Textual falls back to
           SELECT_ALL over large widget ranges.
        2. It never paints ``screen--selection`` on the chosen span.

        We mirror Log for those two pieces and export plain text for copy
        (same fix as miwbs).
        """

        ALLOW_SELECT = True

        @staticmethod
        def _stylize_char_range(strip, start: int, end: int, style) -> object:
            """Apply a Rich style to a character range inside a Strip."""
            from rich.segment import Segment
            from textual.strip import Strip

            if end < 0:
                end = sum(len(seg.text) for seg in strip)
            if start >= end:
                return strip
            out: list = []
            pos = 0
            for segment in strip:
                text, seg_style, control = segment
                n = len(text)
                if n == 0:
                    out.append(segment)
                    continue
                seg_start, seg_end = pos, pos + n
                if seg_end <= start or seg_start >= end:
                    out.append(segment)
                else:
                    if seg_start < start:
                        cut = start - seg_start
                        out.append(Segment(text[:cut], seg_style, control))
                        text = text[cut:]
                        seg_start = start
                    if text and seg_start < end:
                        cut = min(len(text), end - seg_start)
                        mid_style = style if seg_style is None else seg_style + style
                        out.append(Segment(text[:cut], mid_style, control))
                        text = text[cut:]
                    if text:
                        out.append(Segment(text, seg_style, control))
                pos = seg_end
            return Strip(out, strip.cell_length)

        def get_selection(self, selection: Selection) -> tuple[str, str] | None:
            if not self.lines:
                return None
            text = "\n".join(strip.text for strip in self.lines)
            if not text:
                return None
            return selection.extract(text), "\n"

        def selection_updated(self, selection: Selection | None) -> None:
            try:
                self._line_cache.clear()
            except Exception:  # noqa: BLE001
                pass
            self.refresh()

        def render_line(self, y: int):
            """Like RichLog, but with selection offsets + highlight (see Log)."""
            from rich.style import Style as RichStyle
            from textual.strip import Strip

            scroll_x, scroll_y = self.scroll_offset
            content_y = scroll_y + y
            width = self.scrollable_content_region.width
            rich_style = self.rich_style
            if content_y >= len(self.lines):
                return Strip.blank(width, rich_style)
            line = self.lines[content_y]
            selection = self.text_selection
            if selection is not None:
                span = selection.get_span(content_y)
                if span is not None:
                    start, end = span
                    if end < 0:
                        end = len(line.text)
                    try:
                        sel_style = self.screen.get_component_rich_style(
                            "screen--selection"
                        )
                    except Exception:  # noqa: BLE001
                        sel_style = RichStyle(reverse=True)
                    line = self._stylize_char_range(line, start, end, sel_style)
            line = line.crop_extend(scroll_x, scroll_x + width, rich_style)
            line = line.apply_offsets(scroll_x, content_y)
            return line.apply_style(rich_style)

    class HistoryInput(Input):
        """Input with ↑ / ↓ command history.

        When a folio is open in SELF and the line is empty, ↑/↓ are left for
        folio body scroll (not history).
        """

        BINDINGS = [
            Binding("up", "hist_up", "Prev cmd", show=False, priority=True),
            Binding("down", "hist_down", "Next cmd", show=False, priority=True),
        ]

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.cmd_history = CommandHistory()

        def check_action(self, action: str, parameters: tuple) -> bool | None:
            if action in ("hist_up", "hist_down"):
                if not (self.value or "").strip():
                    app = self.app
                    if getattr(app, "_self_mode", None) == "folio" and not getattr(
                        app, "_studio_open", False
                    ):
                        return False
            return True

        def action_hist_up(self) -> None:
            nxt = self.cmd_history.up(self.value)
            if nxt is not None:
                self.value = nxt
                self.cursor_position = len(self.value)

        def action_hist_down(self) -> None:
            nxt = self.cmd_history.down(self.value)
            if nxt is not None:
                self.value = nxt
                self.cursor_position = len(self.value)

    class SelfPane(Vertical):
        """Always-on right rail — can take focus for folio keybindings."""

        can_focus = True

        BINDINGS = [
            Binding("left", "folio_prev", "Prev leaf", show=False, priority=True),
            Binding("right", "folio_next", "Next leaf", show=False, priority=True),
            Binding("h", "folio_prev", "Prev", show=False, priority=True),
            Binding("l", "folio_next", "Next", show=False, priority=True),
            Binding("up", "folio_scroll_up", "Scroll up", show=False, priority=True),
            Binding("down", "folio_scroll_down", "Scroll down", show=False, priority=True),
            Binding("escape", "folio_close", "Close folio", show=False, priority=True),
            Binding("q", "folio_close", "Close", show=False, priority=True),
            Binding("e", "folio_edit", "Edit leaf", show=False, priority=True),
            Binding("plus", "folio_add", "Add leaf", show=False, priority=True),
            Binding("shift+equals", "folio_add", "Add leaf", show=False, priority=True),
            Binding("+", "folio_add", "Add leaf", show=False, priority=True),
            Binding("tab", "focus_cmd", "Command", show=False, priority=True),
        ]

        def check_action(self, action: str, parameters: tuple) -> bool | None:
            app = self.app
            if not isinstance(app, StudioApp):
                return False
            if action == "focus_cmd":
                return True
            if app._self_mode != "folio" or app._studio_open:
                return False
            return True

        def action_focus_cmd(self) -> None:
            try:
                self.app.query_one("#cmd", HistoryInput).focus()
            except Exception:  # noqa: BLE001
                pass

        def action_folio_prev(self) -> None:
            self.app.action_self_folio_prev()  # type: ignore[attr-defined]

        def action_folio_next(self) -> None:
            self.app.action_self_folio_next()  # type: ignore[attr-defined]

        def action_folio_scroll_up(self) -> None:
            self.app.action_self_folio_scroll_up()  # type: ignore[attr-defined]

        def action_folio_scroll_down(self) -> None:
            self.app.action_self_folio_scroll_down()  # type: ignore[attr-defined]

        def action_folio_close(self) -> None:
            self.app.action_self_folio_close()  # type: ignore[attr-defined]

        def action_folio_edit(self) -> None:
            self.app.action_self_folio_edit()  # type: ignore[attr-defined]

        def action_folio_add(self) -> None:
            self.app.action_self_folio_add()  # type: ignore[attr-defined]

    class StudioApp(App[None]):
        """World log + always-on SELF rail (inv home; folio open in-rail)."""

        def action_open_url(self, url: str) -> None:
            """Open an external http(s) link from studio text (clickable @click)."""
            from .studio_text import is_openable_url

            u = (url or "").strip()
            if is_openable_url(u):
                self.open_url(u)

        def action_look_at(self, ref: str) -> None:
            """Click a look-list name / bin headline → ``look at <ref>`` as a turn."""
            r = (ref or "").strip()
            if not r:
                return
            self._run_command_line(f"look at {r}")

        # Classic DOS blue: deep blue field, cyan edges, light gray type
        CSS = f"""
        Screen {{
            background: {TUI_BG};
        }}
        #body {{
            height: 1fr;
            background: {TUI_BG};
        }}
        #log {{
            /* ~60% of body — look sheets stay primary */
            width: {TUI_LOG_PANE_WIDTH};
            min-width: {TUI_LOG_PANE_MIN_WIDTH};
            height: 1fr;
            border: solid {TUI_BORDER};
            padding: 1 2;
            background: {TUI_SURFACE};
            color: {TUI_TEXT};
            scrollbar-background: {TUI_BG};
            scrollbar-color: {TUI_BORDER_ACCENT};
        }}
        #self-pane {{
            /* ~40% of body — notebook-width, not a 40-col strip */
            width: {TUI_SELF_PANE_WIDTH};
            min-width: {TUI_SELF_PANE_MIN_WIDTH};
            max-width: {TUI_SELF_PANE_MAX_WIDTH};
            height: 1fr;
            border: solid {TUI_BORDER_ACCENT};
            padding: 0 1;
            background: {TUI_PANEL};
            color: {TUI_TEXT};
            layout: vertical;
        }}
        #self-pane:focus {{
            border: tall {TUI_BORDER_ACCENT};
        }}
        #self-title {{
            height: auto;
            padding: 1 1 0 1;
            color: {TUI_TEXT_BRIGHT};
            border-bottom: solid {TUI_BORDER};
            margin-bottom: 0;
        }}
        #self-scroll {{
            height: 1fr;
            background: {TUI_PANEL};
            scrollbar-background: {TUI_BG};
            scrollbar-color: {TUI_BORDER};
        }}
        #self-body {{
            height: auto;
            padding: 1 1;
            background: {TUI_PANEL};
            /* Folio / inv body: white by default — gray body text is hard to focus */
            color: {TUI_TEXT_BRIGHT};
        }}
        #self-foot {{
            height: auto;
            padding: 0 1 1 1;
            color: {TUI_MUTED};
            border-top: solid {TUI_BORDER};
        }}
        #self-read {{
            height: 1fr;
            layout: vertical;
            background: {TUI_PANEL};
        }}
        #self-studio {{
            height: 1fr;
            layout: vertical;
            background: {TUI_PANEL};
            padding: 0;
        }}
        #self-studio-hint {{
            height: auto;
            color: {TUI_MUTED};
            padding: 0 1;
            background: {TUI_PANEL};
        }}
        #self-studio-title-row {{
            height: 3;
            width: 100%;
            padding: 0 1;
            background: {TUI_PANEL};
            layout: horizontal;
        }}
        #self-studio-title-label {{
            width: auto;
            height: 3;
            content-align: left middle;
            color: {TUI_MUTED};
            padding-right: 1;
        }}
        #self-studio-page-title {{
            width: 1fr;
            height: 3;
            border: solid {TUI_BORDER};
            background: {TUI_INPUT_BG};
            color: {TUI_TEXT_BRIGHT};
            padding: 0 1;
        }}
        #self-studio-body {{
            height: 1fr;
            border: solid {TUI_BORDER_ACCENT};
            margin: 0 1 1 1;
            background: {TUI_INPUT_BG};
            color: {TUI_TEXT_BRIGHT};
        }}
        #self-studio-preview-scroll {{
            height: 1fr;
            border: solid {TUI_BORDER};
            margin: 0 1 1 1;
            background: {TUI_INPUT_BG};
        }}
        #self-studio-preview {{
            height: auto;
            padding: 1 1;
            background: {TUI_INPUT_BG};
            color: {TUI_TEXT_BRIGHT};
        }}
        #self-studio-foot {{
            height: auto;
            padding: 0 1 1 1;
            color: {TUI_MUTED};
            border-top: solid {TUI_BORDER};
        }}
        #cmd {{
            dock: bottom;
            margin: 0 0;
            border: solid {TUI_BORDER_ACCENT};
            background: {TUI_INPUT_BG};
            color: {TUI_TEXT_BRIGHT};
            padding: 0 1;
        }}
        #studio-header {{
            dock: top;
            height: 3;
            background: {TUI_PANEL};
            border-bottom: solid {TUI_BORDER_ACCENT};
            padding: 0 1;
            layout: horizontal;
        }}
        #header-left, #header-center, #header-right {{
            height: 3;
            content-align: center middle;
            color: {TUI_TEXT};
        }}
        #header-left {{
            width: auto;
            min-width: 7;
            content-align: left middle;
            color: {TUI_TEXT_BRIGHT};
            padding: 0 1 0 0;
        }}
        #header-center {{
            width: 1fr;
            content-align: left middle;
            color: {TUI_MUTED};
        }}
        #header-right {{
            width: auto;
            min-width: 12;
            content-align: right middle;
            color: {TUI_BORDER_ACCENT};
        }}
        Footer {{
            background: {TUI_BG};
            color: {TUI_MUTED};
            border-top: solid {TUI_BORDER};
        }}
        """
        BINDINGS = [
            Binding("ctrl+c", "copy_or_quit", "Copy / Quit", show=False),
            # Ctrl+Q: cancel in-rail studio if open, else quit (see action_quit)
            Binding("ctrl+q", "quit", "Quit", show=True),
            Binding("f1", "toggle_help", "Help"),
            # Folio keys when cmd is empty (walk + notebook without focusing rail)
            Binding("left", "self_folio_prev", "Prev leaf", show=False, priority=True),
            Binding("right", "self_folio_next", "Next leaf", show=False, priority=True),
            Binding("up", "self_folio_scroll_up", "Scroll folio", show=False, priority=True),
            Binding("down", "self_folio_scroll_down", "Scroll folio", show=False, priority=True),
            Binding("escape", "self_folio_close", "Close folio", show=False, priority=True),
            # In-rail STUDIO Writer (folio leaf e)
            Binding("ctrl+s", "self_studio_save", "Save leaf", show=False, priority=True),
            Binding("f2", "self_studio_preview", "Preview", show=False, priority=True),
            Binding("alt+p", "self_studio_preview", "Preview", show=False, priority=True),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.help_pane = HelpPane(open=False)  # unused rail; keep for tests
            self._turn = 0
            self._self_mode: str = "home"  # home | folio
            self._open_book_id: str | None = None
            self._folio_page_index: int = 0
            self._studio_open: bool = False
            self._studio_ctx: dict | None = None
            self._studio_preview: bool = False
            self._open_wiki: tuple[str, bool] | None = None

        def check_action(self, action: str, parameters: tuple) -> bool | None:
            """Folio nav/scroll when reading; studio keys only while editing in SELF."""
            if action in (
                "self_studio_save",
                "self_studio_preview",
            ):
                return bool(self._studio_open)
            if action in (
                "self_folio_prev",
                "self_folio_next",
                "self_folio_scroll_up",
                "self_folio_scroll_down",
                "self_folio_close",
            ):
                if self._self_mode != "folio":
                    return False
                # Esc while editing cancels studio (handled in action_self_folio_close)
                if action == "self_folio_close":
                    return True
                if self._studio_open:
                    return False
                try:
                    cmd = self.query_one("#cmd", HistoryInput)
                    if (cmd.value or "").strip():
                        return False
                except Exception:  # noqa: BLE001
                    pass
            return True

        def action_copy_or_quit(self) -> None:
            """Ctrl+C: copy highlighted log text if any, else leave the studio."""
            selected = self.screen.get_selected_text()
            if selected:
                self.copy_to_clipboard(selected)
                self.notify("Copied.", severity="information", timeout=1.5)
                return
            self.exit()

        def action_quit(self) -> None:
            """Ctrl+Q: cancel in-rail leaf edit first; otherwise leave DOS."""
            if self._studio_open:
                self.action_self_studio_cancel()
                return
            self.exit()

        def compose(self) -> ComposeResult:
            with Horizontal(id="studio-header"):
                yield Static("", id="header-left", markup=True)
                yield Static("", id="header-center", markup=True)
                yield Static("", id="header-right", markup=True)
            with Horizontal(id="body"):
                yield SelectableWorldLog(
                    id="log",
                    highlight=False,
                    markup=True,
                    wrap=True,
                    auto_scroll=True,
                )
                with SelfPane(id="self-pane"):
                    with Vertical(id="self-read"):
                        yield Static("", id="self-title", markup=True)
                        with VerticalScroll(id="self-scroll"):
                            yield Static("", id="self-body", markup=True)
                        yield Static("", id="self-foot", markup=True)
                    with Vertical(id="self-studio"):
                        yield Static("", id="self-studio-hint", markup=True)
                        with Horizontal(id="self-studio-title-row"):
                            yield Static(
                                "[dim]Title[/dim]",
                                id="self-studio-title-label",
                                markup=True,
                            )
                            yield Input(
                                value="",
                                placeholder="leaf title",
                                id="self-studio-page-title",
                            )
                        # TextArea constructed via shared STUDIO Writer factory
                        # (id set at construct time — Textual forbids reassigning id)
                        from .text_editor import _make_editor_textarea

                        yield _make_editor_textarea(
                            "", widget_id="self-studio-body"
                        )
                        with VerticalScroll(id="self-studio-preview-scroll"):
                            yield Static("", id="self-studio-preview", markup=True)
                        yield Static(
                            "[dim]Ctrl+S save  ·  Esc cancel  ·  F2 preview[/dim]",
                            id="self-studio-foot",
                            markup=True,
                        )
            yield HistoryInput(
                placeholder="look  ·  folio open  ·  help print  ·  ↑↓ history",
                id="cmd",
            )
            yield Footer()

        def on_mount(self) -> None:
            name = get_meta(world.conn, "world_name", world_path.name) or world_path.name
            file_label = _world_chrome_label(world_path)
            self.title = f"DOS | {file_label}"
            self.sub_title = ""
            # Studio layer starts hidden (read mode default)
            try:
                self.query_one("#self-studio", Vertical).display = False
                self.query_one("#self-studio-preview-scroll", VerticalScroll).display = (
                    False
                )
            except Exception:  # noqa: BLE001
                pass
            self._refresh_studio_header()
            self._refresh_self_pane()
            log = self.query_one("#log", SelectableWorldLog)
            log.write(_studio_boot_banner_markup(world_path, name))
            r = dispatch(world, "look")
            if r.message:
                log.write(r.message)
            log.write(fmt.turn_separator())
            self._refresh_studio_header()
            self.query_one("#cmd", HistoryInput).focus()

        def _refresh_studio_header(self) -> None:
            """
            Persistent top bar:
              left   DOS logo (white on bright blue)
              center (open — no seed chrome)
              right  current location
            """
            from .ids import display_name

            loc = world.player_location()
            loc_name = display_name(loc.name) if loc else "—"

            left = self.query_one("#header-left", Static)
            center = self.query_one("#header-center", Static)
            right = self.query_one("#header-right", Static)
            left.update(_dos_logo_markup())
            center.update("")
            right.update(
                f"[{TUI_MUTED}]@[/] [{TUI_BORDER_ACCENT}]{fmt.safe(loc_name)}[/]"
            )

        def _refresh_self_pane(self) -> None:
            """Render SELF home (inv) or open folio body (read mode only)."""
            if self._studio_open:
                return
            title = self.query_one("#self-title", Static)
            body = self.query_one("#self-body", Static)
            foot = self.query_one("#self-foot", Static)
            if self._self_mode == "folio" and self._open_book_id:
                title.update(
                    format_self_folio_title(
                        world, self._open_book_id, self._folio_page_index
                    )
                )
                markup, idx = format_self_folio_body(
                    world, self._open_book_id, self._folio_page_index
                )
                self._folio_page_index = idx
                body.update(markup)
                foot.update(format_self_folio_foot())
            else:
                self._self_mode = "home"
                title.update(format_self_home_title())
                body.update(format_self_home(world))
                foot.update(format_self_home_foot())
            try:
                scroll = self.query_one("#self-scroll", VerticalScroll)
                scroll.scroll_home(animate=False)
            except Exception:  # noqa: BLE001
                pass

        def _focus_self_pane(self) -> None:
            try:
                self.query_one("#self-pane", SelfPane).focus()
            except Exception:  # noqa: BLE001
                pass

        def _show_self_read(self) -> None:
            try:
                self.query_one("#self-read", Vertical).display = True
                self.query_one("#self-studio", Vertical).display = False
            except Exception:  # noqa: BLE001
                pass

        def _show_self_studio(self) -> None:
            try:
                self.query_one("#self-read", Vertical).display = False
                self.query_one("#self-studio", Vertical).display = True
            except Exception:  # noqa: BLE001
                pass

        def _open_book_reader(self, book_instance_id: str) -> None:
            """Open folio in SELF rail (world log stays live)."""
            if self._studio_open:
                self._self_studio_cancel(silent=True)
            # Close wiki modal if it was up
            if self._wiki_reader_is_top():
                self.pop_screen()
            self._open_wiki = None
            self._open_book_id = book_instance_id
            self._folio_page_index = 0
            self._self_mode = "folio"
            self._show_self_read()
            self._refresh_self_pane()
            self._focus_self_pane()

        def _close_book_reader(self) -> None:
            """Return SELF to inventory home."""
            if self._studio_open:
                self._self_studio_cancel(silent=True)
            self._open_book_id = None
            self._folio_page_index = 0
            self._self_mode = "home"
            self._show_self_read()
            self._refresh_self_pane()
            try:
                self.query_one("#cmd", HistoryInput).focus()
            except Exception:  # noqa: BLE001
                pass

        def action_self_folio_prev(self) -> None:
            if self._self_mode != "folio" or not self._open_book_id:
                return
            self._folio_page_index = self_nav_page(
                world, self._open_book_id, self._folio_page_index, -1
            )
            self._refresh_self_pane()

        def action_self_folio_next(self) -> None:
            if self._self_mode != "folio" or not self._open_book_id:
                return
            self._folio_page_index = self_nav_page(
                world, self._open_book_id, self._folio_page_index, 1
            )
            self._refresh_self_pane()

        def _self_folio_scroll(self, *, y: int) -> None:
            """Scroll open folio body (↑/↓). Leaves stay on ←/→."""
            if self._self_mode != "folio" or self._studio_open:
                return
            try:
                scroll = self.query_one("#self-scroll", VerticalScroll)
                scroll.scroll_relative(y=y, animate=False)
            except Exception:  # noqa: BLE001
                pass

        def action_self_folio_scroll_up(self) -> None:
            self._self_folio_scroll(y=-3)

        def action_self_folio_scroll_down(self) -> None:
            self._self_folio_scroll(y=3)

        def action_self_folio_close(self) -> None:
            if self._studio_open:
                self.action_self_studio_cancel()
                return
            if self._self_mode != "folio":
                return
            self._close_book_reader()
            self.notify("Folio closed · SELF home", timeout=1.5)

        def action_self_folio_add(self) -> None:
            if self._self_mode != "folio" or not self._open_book_id:
                return
            if self._studio_open:
                self.notify(
                    "Finish or cancel the open studio first (Ctrl+S / Esc).",
                    severity="warning",
                )
                return
            try:
                new_idx, msg = self_add_leaf(
                    world, self._open_book_id, self._folio_page_index
                )
            except Exception as e:  # noqa: BLE001
                self.notify(f"Could not add leaf: {e}", severity="error")
                return
            self._folio_page_index = new_idx
            self._refresh_self_pane()
            self.notify(msg, severity="information")
            self.action_self_folio_edit()

        def action_self_folio_edit(self) -> None:
            """Open STUDIO Writer *inside* SELF for the current leaf."""
            from .text_editor import (
                _STUDIO_WRITER_THEME_NAME,
                _editor_hint_markup,
                _studio_writer_textarea_theme,
            )
            from textual.widgets import TextArea

            if self._self_mode != "folio" or not self._open_book_id:
                return
            if self._studio_open:
                return
            ctx = self_leaf_edit_context(
                world, self._open_book_id, self._folio_page_index
            )
            if ctx is None:
                self.notify(
                    "Empty book — press + to add a leaf.",
                    severity="warning",
                )
                return
            self._folio_page_index = int(ctx["page_index"])
            self._studio_ctx = ctx
            self._studio_preview = False
            self._studio_open = True

            try:
                hint = self.query_one("#self-studio-hint", Static)
                hint.update(
                    _editor_hint_markup(
                        ctx["title"],
                        studio=True,
                        with_page_title=True,
                        preview=False,
                    )
                )
                title_in = self.query_one("#self-studio-page-title", Input)
                title_in.value = ctx["prior_title"] or ""
                prev_scroll = self.query_one(
                    "#self-studio-preview-scroll", VerticalScroll
                )
                prev_scroll.display = False
                ta = self.query_one("#self-studio-body", TextArea)
                ta.display = True
                want = ctx["initial"] or ""
                theme = _studio_writer_textarea_theme()
                ta.register_theme(theme)
                ta.theme = _STUDIO_WRITER_THEME_NAME
                if (ta.text or "") != want:
                    ta.load_text(want)
            except Exception as e:  # noqa: BLE001
                self._studio_open = False
                self._studio_ctx = None
                self.notify(f"Could not open studio: {e}", severity="error")
                return

            self._show_self_studio()
            try:
                self.query_one("#self-studio-body", TextArea).focus()
            except Exception:  # noqa: BLE001
                pass

        def _self_studio_exit_to_read(self) -> None:
            self._studio_open = False
            self._studio_ctx = None
            self._studio_preview = False
            self._show_self_read()
            self._refresh_self_pane()
            self._focus_self_pane()

        def action_self_studio_save(self) -> None:
            """Ctrl+S — save leaf title + body, return to folio read in SELF."""
            from textual.widgets import TextArea

            if not self._studio_open or not self._studio_ctx:
                return
            ctx = self._studio_ctx
            try:
                ta = self.query_one("#self-studio-body", TextArea)
                body = ta.text if ta is not None else ""
                new_title = (
                    self.query_one("#self-studio-page-title", Input).value or ""
                ).strip()
            except Exception as e:  # noqa: BLE001
                self.notify(f"Save failed: {e}", severity="error")
                return
            if not (body or "").strip():
                self.notify("Empty buffer — not saved.", severity="warning")
                return
            try:
                self_save_leaf(
                    world,
                    page_id=ctx["page_id"],
                    prior_title=ctx["prior_title"],
                    prior_body=ctx["prior_body"],
                    new_title=new_title,
                    new_body=body,
                    book_name=ctx["book_name"],
                    leaf_n=int(ctx["leaf_n"]),
                )
            except Exception as e:  # noqa: BLE001
                self.notify(f"Save failed: {e}", severity="error")
                return
            self.notify("Leaf saved.", severity="information")
            self._self_studio_exit_to_read()

        def action_self_studio_cancel(self) -> None:
            self._self_studio_cancel(silent=False)

        def _self_studio_cancel(self, *, silent: bool = False) -> None:
            if not self._studio_open:
                return
            if self._studio_preview:
                self.action_self_studio_preview()
                return
            if not silent:
                self.notify("Edit cancelled.", severity="information")
            self._self_studio_exit_to_read()

        def action_self_studio_preview(self) -> None:
            """F2 / Alt+P — toggle markup preview inside SELF studio."""
            from textual.widgets import TextArea

            from .text_editor import (
                _editor_hint_markup,
                _preview_markup,
            )

            if not self._studio_open or not self._studio_ctx:
                return
            ctx = self._studio_ctx
            ta = self.query_one("#self-studio-body", TextArea)
            scroll = self.query_one("#self-studio-preview-scroll", VerticalScroll)
            prev = self.query_one("#self-studio-preview", Static)
            hint = self.query_one("#self-studio-hint", Static)
            if not self._studio_preview:
                prev.update(_preview_markup(ta.text or "", studio=True))
                ta.display = False
                scroll.display = True
                self._studio_preview = True
                self.notify("Preview · F2 back to edit", timeout=2)
            else:
                scroll.display = False
                ta.display = True
                self._studio_preview = False
                ta.focus()
                self.notify("Edit", timeout=1)
            hint.update(
                _editor_hint_markup(
                    ctx["title"],
                    studio=True,
                    with_page_title=True,
                    preview=self._studio_preview,
                )
            )

        def _wiki_reader_is_top(self) -> bool:
            scr = self.screen
            return bool(getattr(scr, "IS_WIKI_READER", False))

        def _close_wiki_reader(self) -> None:
            self._open_wiki = None
            if self._wiki_reader_is_top():
                self.pop_screen()

        def _open_wiki_reader(self, label: str, *, deep: bool = False) -> None:
            """Wiki still uses soft modal for now (SELF folio is the product path)."""
            if self._wiki_reader_is_top():
                self.pop_screen()
            self._open_wiki = (label, deep)
            screen = make_wiki_reader_screen(world, label, deep=deep)

            def _on_wiki_closed(_result: None = None) -> None:
                self._open_wiki = None
                try:
                    self.query_one("#cmd", HistoryInput).focus()
                except Exception:  # noqa: BLE001
                    pass

            self.push_screen(screen, _on_wiki_closed)

        def action_toggle_help(self) -> None:
            """F1: dump help index into the world log (no rail)."""
            log = self.query_one("#log", SelectableWorldLog)
            body = help_text_for_query("")
            self._write_world_turn(log, "help", body)

        def _clear_world_log(self, log: SelectableWorldLog) -> None:
            """Wipe transcript only — no tips banner (clr wants a blank log)."""
            log.clear()
            self._turn = 0

        def _write_world_turn(
            self,
            log: SelectableWorldLog,
            line: str,
            message: str | None,
            *,
            clear_log: bool = False,
        ) -> None:
            """World log turn (help bodies may print here)."""
            if clear_log:
                self._clear_world_log(log)
            # Pure clear/clr: blank log, no › echo, no separator
            if clear_log and not (message or "").strip():
                self._refresh_studio_header()
                self._refresh_self_pane()
                return
            if self._turn > 0:
                log.write(fmt.turn_separator())
            self._turn += 1
            log.write(f"[bright_cyan]›[/bright_cyan] {fmt.safe(line)}")
            if message:
                log.write("")
                log.write(message)
            self._refresh_studio_header()
            # Keep inv home fresh after take/drop/put without stomping open folio
            if self._self_mode == "home":
                self._refresh_self_pane()

        def _run_command_line(self, line: str, *, record_history: bool = True) -> None:
            """Run one command as a world-log turn (typed or click-generated)."""
            log = self.query_one("#log", SelectableWorldLog)
            cmd = self.query_one("#cmd", HistoryInput)
            line = (line or "").strip()
            if not line:
                return

            # << / <<studio → buffer editor screen (desc, book page, lore)
            from .multiline_open import (
                commit_multiline_session,
                parse_multiline_opener,
                seed_initial_body,
                seed_page_title,
            )
            from .text_editor import StudioBufferResult, make_studio_buffer_screen

            ml = parse_multiline_opener(line)
            if ml is not None:
                if record_history:
                    cmd.cmd_history.push(line)
                initial = seed_initial_body(world, ml)
                page_title = seed_page_title(world, ml)
                screen = make_studio_buffer_screen(
                    initial=initial,
                    title=ml.title,
                    studio=ml.studio,
                    page_title=page_title,
                )

                def _on_editor_done(edited: StudioBufferResult | None) -> None:
                    if edited is None:
                        self._write_world_turn(
                            log,
                            line,
                            fmt.hint("Editor cancelled."),
                        )
                    else:
                        result = commit_multiline_session(
                            world,
                            ml,
                            edited.body,
                            page_title=edited.page_title,
                        )
                        self._write_world_turn(
                            log,
                            line,
                            result.message or None,
                            clear_log=result.clear_log,
                        )
                        if result.open_book_id:
                            self._open_book_reader(result.open_book_id)
                        if result.open_wiki:
                            q, deep = result.open_wiki
                            self._open_wiki_reader(q, deep=deep)
                        if result.quit:
                            self.exit()
                            return
                    try:
                        self.query_one("#cmd", HistoryInput).focus()
                    except Exception:  # noqa: BLE001
                        pass

                self.push_screen(screen, _on_editor_done)
                return

            if record_history:
                cmd.cmd_history.push(line)

            # Help → raw world log (no side rail)
            help_arg = parse_help_command(line)
            if help_arg is not None:
                body = help_text_for_query(help_arg)
                self._write_world_turn(log, line, body)
                return

            result = dispatch(world, line)
            if result.open_book_id:
                self._write_world_turn(
                    log,
                    line,
                    fmt.hint(
                        "Folio in SELF  ·  ↑↓ scroll  ·  ←/→ leaves  ·  e edit  ·  Esc home"
                    ),
                    clear_log=result.clear_log,
                )
                self._open_book_reader(result.open_book_id)
            elif result.open_wiki:
                q, deep = result.open_wiki
                self._write_world_turn(
                    log,
                    line,
                    fmt.hint(
                        "Wiki open  ·  scroll  ·  Esc close"
                        + ("  ·  deep" if deep else "")
                    ),
                    clear_log=result.clear_log,
                )
                self._open_wiki_reader(q, deep=deep)
            else:
                self._write_world_turn(
                    log,
                    line,
                    result.message or None,
                    clear_log=result.clear_log,
                )
            if result.quit:
                self.exit()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            line = event.value.strip()
            event.input.value = ""
            if not line:
                return
            self._run_command_line(line)

    StudioApp().run()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dos",
        description="VEN-based MUD-like multiverse world-building studio",
    )
    p.add_argument(
        "--world",
        type=Path,
        default=DEFAULT_WORLD,
        help=f"Path to world SQLite file (default: {DEFAULT_WORLD})",
    )
    p.add_argument(
        "--reseed",
        action="store_true",
        help="Delete and recreate the world from the office seed",
    )
    p.add_argument(
        "--seed",
        choices=("office", "empty", "bootstrap", "betsoft"),
        default="office",
        help=(
            "Seed flavor when creating/reseeding: office (default company campus), "
            "empty (unfurnished suite), bootstrap (bare Herenow for tests), "
            "or betsoft (frozen Roadmaps campus snapshot — Castaway dates & all)"
        ),
    )
    p.add_argument(
        "--textual",
        action="store_true",
        help="Launch Textual TUI (help bar toggled with help / ?)",
    )
    p.add_argument(
        "--command",
        "-c",
        action="append",
        default=[],
        help="Run a command non-interactively (repeatable), then exit",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    world = ensure_world(args.world, reseed=args.reseed, seed=args.seed)

    if args.command:
        for i, c in enumerate(args.command):
            result = dispatch(world, c)
            if result.message:
                if i > 0:
                    console.print()
                console.print(result.message)
            if not result.ok:
                sys.exit(1)
            if result.quit:
                break
        return

    if args.textual:
        run_textual(world, args.world)
    else:
        run_repl(world, args.world)


if __name__ == "__main__":
    main()
