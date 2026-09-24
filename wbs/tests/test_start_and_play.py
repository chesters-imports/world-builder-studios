"""Start place + play-mode allowlist + copy-on-play."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from world_studio.commands import dispatch
from world_studio.db import connect, get_meta
from world_studio.format import plain
from world_studio.play_mode import copy_for_play, open_play_world
from world_studio.seed import seed_world_bootstrap, seed_world_classic
from world_studio.world import World


def _bootstrap() -> World:
    tmp = tempfile.NamedTemporaryFile(suffix=".world.db", delete=False)
    tmp.close()
    conn = connect(Path(tmp.name))
    seed_world_bootstrap(conn)
    return World(conn)


def _classic_path() -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".world.db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    conn = connect(path)
    seed_world_classic(conn)
    conn.close()
    return path


class StartPlaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _bootstrap()

    def test_seed_stamps_start(self) -> None:
        sid = self.world.start_place_id()
        self.assertIsNotNone(sid)
        loc = self.world.player_location()
        assert loc is not None
        self.assertEqual(sid, loc.id)
        self.assertEqual(loc.name, "Herenow")

    def test_start_here_and_show(self) -> None:
        r = dispatch(self.world, "start")
        self.assertTrue(r.ok)
        self.assertIn("Herenow", plain(r.message))
        # dig a place, go there, set start
        dispatch(self.world, "dig Quiet Corner")
        dispatch(self.world, "link north -> Quiet Corner both")
        dispatch(self.world, "go north")
        r = dispatch(self.world, "start here")
        self.assertTrue(r.ok)
        self.assertIn("Quiet Corner", plain(r.message))
        self.assertEqual(
            get_meta(self.world.conn, "start_place_instance_id"),
            self.world.player_location().id,  # type: ignore[union-attr]
        )

    def test_apply_start_moves_player(self) -> None:
        loc0 = self.world.player_location()
        assert loc0 is not None
        dispatch(self.world, "dig Side Room")
        dispatch(self.world, "link east -> Side Room both")
        dispatch(self.world, "go east")
        here = self.world.player_location()
        assert here is not None
        self.assertEqual(here.name, "Side Room")
        # start still Herenow
        ok, note = self.world.apply_start_position()
        self.assertTrue(ok)
        self.assertIn("Herenow", note)
        back = self.world.player_location()
        assert back is not None
        self.assertEqual(back.name, "Herenow")

    def test_start_clear(self) -> None:
        r = dispatch(self.world, "start clear")
        self.assertTrue(r.ok)
        self.assertIsNone(self.world.start_place_id())
        # resolve falls back to player location
        start = self.world.resolve_start_place()
        assert start is not None
        self.assertEqual(start.name, "Herenow")


class PlayModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _bootstrap()
        self.world.mode = "play"

    def test_play_blocks_dig(self) -> None:
        r = dispatch(self.world, "dig Forbidden")
        self.assertTrue(r.ok)
        self.assertIn("Not in play", plain(r.message))
        # place not created
        self.assertIsNone(self.world.find_ven("Forbidden"))

    def test_play_allows_look(self) -> None:
        r = dispatch(self.world, "look")
        self.assertTrue(r.ok)
        self.assertIn("Herenow", plain(r.message))

    def test_play_blocks_create_spawn_desc(self) -> None:
        for cmd in (
            "create thing Rock",
            "spawn Place",
            "@desc something",
            "undo",
            "portal x -> y",
        ):
            r = dispatch(self.world, cmd)
            self.assertIn("Not in play", plain(r.message), msg=cmd)

    def test_play_blocks_lore_add(self) -> None:
        r = dispatch(self.world, "lore add Note | secret")
        self.assertIn("read-only", plain(r.message).lower())

    def test_play_start_is_show_only(self) -> None:
        r = dispatch(self.world, "start here")
        text = plain(r.message)
        self.assertIn("fixed in play", text.lower())
        # start place unchanged
        self.assertIsNotNone(self.world.start_place_id())

    def test_cognitive_stub(self) -> None:
        r = dispatch(self.world, "consider fire")
        self.assertIn("reserved", plain(r.message).lower())


class CopyOnPlayTests(unittest.TestCase):
    def test_copy_does_not_mutate_author(self) -> None:
        path = _classic_path()
        author = World(connect(path))
        start_id = author.start_place_id()
        assert start_id is not None
        # leave start room
        loc = author.player_location()
        assert loc is not None
        exits = author.exits(loc.id)
        self.assertTrue(exits)
        dest = exits[0]["to_instance_id"]
        author.move_player(dest)
        author.conn.close()

        # Reopen author path, open play copy from original file state...
        # Author was mutated above — reseed path for clean author:
        path2 = _classic_path()
        play, play_path = open_play_world(path2, new_game=True)
        self.assertEqual(play.mode, "play")
        ploc = play.player_location()
        assert ploc is not None
        # classic start is cathedral
        self.assertIn("Cathedral", ploc.name)

        # Mutate play: take something if possible, dig must fail
        r = dispatch(play, "dig Hacker Room")
        self.assertIn("Not in play", plain(r.message))

        # Author untouched: no dig in author
        author2 = World(connect(path2))
        self.assertIsNone(author2.find_ven("Hacker Room"))
        self.assertNotEqual(path2.resolve(), play_path.resolve())

    def test_copy_for_play_creates_file(self) -> None:
        path = _classic_path()
        dest = copy_for_play(path, slot="testslot")
        self.assertTrue(dest.is_file())
        self.assertIn("testslot", dest.name)


if __name__ == "__main__":
    unittest.main()
