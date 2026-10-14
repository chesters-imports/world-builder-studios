"""Play shell: command allowlist and copy-on-play session helpers.

Studio remains the full builder face. Play is policy + a disposable DB copy —
not a second simulation engine.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from .db import connect, get_meta
from .ven_pack import aidm_home
from .world import World

# Canonical verbs allowed in play mode (first token after shorthand expand).
# Builder verbs (dig, create, spawn, @desc, …) are refused quietly.
PLAY_COMMANDS: frozenset[str] = frozenset(
    {
        # movement
        "look",
        "l",
        "go",
        "g",
        "paths",
        "path",
        "exits",
        "x",
        "ways",
        "waypoints",
        "way",
        "map",
        "graph",
        "locate",
        "status",
        "sit",
        "situation",
        "whereami",
        "where",
        # inventory / env
        "inv",
        "inventory",
        "i",
        "take",
        "get",
        "drop",
        "put",
        "install",
        "examine",
        "exam",
        "inspect",
        "in",
        "open",
        # portals (use, not author bind)
        "run",
        "activate",
        "use",
        "enter",
        "unlock",
        "lock",
        "logout",
        "logoff",
        "log-out",
        # people / talk
        "who",
        "talk",
        "dialogs",
        "dialog",
        # read media / lore / wiki
        "folio",
        "book",
        "read",
        "lore",
        "wiki",
        # session
        "help",
        "?",
        "clear",
        "clr",
        "quit",
        "exit",
        "q",
        # start is show-only in play (set/clear blocked in handler)
        "start",
        # reserved cognitive lane (soft stubs until a title enables them)
        "consider",
        "think",
        "feel",
        "remember",
        "wonder",
    }
)

# Help index category titles shown in play (studio shows all).
PLAY_HELP_CATEGORIES: frozenset[str] = frozenset(
    {
        "MOVEMENT",
        "ENV CONTROLS",
        "COMMUNICATION",
        "LORE",
        "SESSION",
    }
)

# Cognitive verbs: reserved names with a quiet stub (not full engines yet).
COGNITIVE_STUBS: frozenset[str] = frozenset(
    {"consider", "think", "feel", "remember", "wonder"}
)


def is_play_mode(world: World) -> bool:
    return (getattr(world, "mode", "studio") or "studio").lower() == "play"


def play_allows_command(cmd: str) -> bool:
    return cmd.lower() in PLAY_COMMANDS


def saves_root(*, create: bool = True) -> Path:
    """User-level play saves: ~/.aidm/saves/"""
    d = aidm_home() / "saves"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def world_save_dir(world_path: Path, *, create: bool = True) -> Path:
    stem = world_path.stem
    # strip common double suffixes: name.world.db → name
    if stem.endswith(".world"):
        stem = stem[: -len(".world")]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem) or "world"
    d = saves_root(create=create) / safe
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def copy_for_play(
    author_path: Path,
    *,
    slot: str = "current",
) -> Path:
    """
    Copy author world into a play save slot. Never writes the author file.

    slot ``current`` is the default continuing save path for later load work.
    """
    author_path = author_path.resolve()
    if not author_path.is_file():
        raise FileNotFoundError(f"World not found: {author_path}")
    dest_dir = world_save_dir(author_path, create=True)
    dest = dest_dir / f"{slot}.play.db"
    # SQLite may have -wal/-shm; copy main file after a connect checkpoint if needed.
    shutil.copy2(author_path, dest)
    return dest


def open_play_world(
    author_path: Path,
    *,
    new_game: bool = True,
    slot: str = "current",
) -> tuple[World, Path]:
    """
    Open a play-mode World on a disposable copy of *author_path*.

    new_game=True: recopy from author and apply start position.
    new_game=False: reopen existing slot if present (continue), else new.
    """
    author_path = author_path.resolve()
    dest_dir = world_save_dir(author_path, create=True)
    dest = dest_dir / f"{slot}.play.db"
    if new_game or not dest.is_file():
        dest = copy_for_play(author_path, slot=slot)
        conn = connect(dest)
        world = World(conn)
        world.mode = "play"
        world.apply_start_position()
        return world, dest
    conn = connect(dest)
    world = World(conn)
    world.mode = "play"
    return world, dest


def play_title_banner(world: World, world_path: Path) -> str:
    """Ship chrome: WBS - {Game Title}."""
    name = get_meta(world.conn, "world_name", "") or ""
    name = str(name).strip() or world_path.stem
    return f"WBS - {name}"


def filter_help_categories(
    categories: Iterable[tuple[str, list]],
    *,
    mode: str = "studio",
) -> list[tuple[str, list]]:
    if (mode or "studio").lower() != "play":
        return list(categories)
    return [(t, items) for t, items in categories if t in PLAY_HELP_CATEGORIES]
